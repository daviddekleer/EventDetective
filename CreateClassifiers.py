#!/usr/bin/python3

"""
#################
CreateClassifiers
#################
Creates category & event/no-event classifier given a dataset
"""
import features
import os, sys, json, pickle
from collections import defaultdict, Counter
import nltk
from math import log, log2
from sklearn.naive_bayes import MultinomialNB, GaussianNB, BernoulliNB
from sklearn.svm import LinearSVC, SVC, NuSVC
from sklearn.linear_model import SGDClassifier
from nltk.classify.scikitlearn import SklearnClassifier
import random
from modules import tabulate
import features

class CreateClassifiers:

    def __init__(self):
        self.ITERATIONS = 1
        self.dataSets = os.listdir('data/')
        self.idf = Counter()
        self.annotation = {}
        self.candidates = {}
        self.table = []
        self.cm = []
        self.mostInformativeBi = []
        self.mostInformativeCat = []
        self.accBi  = 0.0
        self.accCat = 0.0
        self.baselineBi = 0.0
        self.choice = 0
        self.__loadDataSet()
        self.calculateIDF()
        self.createFeatureTypes()
        self.classifyNLTK()
        self._saveClassifiers()

    def __loadDataSet(self):
        for i, dataset in enumerate(self.dataSets):
            print("{}: {}".format(i, dataset))
        self.choice = int(input("Select dataset: "))
        
        with open("data/" + self.dataSets[self.choice] + "/sanitizedAnnotation.json") as jsonFile:
            self.annotation = json.load(jsonFile)

        with open("data/" + self.dataSets[self.choice] + "/sanitizedEventCandidates_cleaned.json") as jsonFile:
            self.candidates = json.load(jsonFile)

    def _saveClassifiers(self):
        print("Saving the category and event classifier...")
        
        with open("data/" + self.dataSets[self.choice] + "/categoryClassifier.bin", "wb") as f:
            pickle.dump(self.classifierCat,f)
            
        with open("data/" + self.dataSets[self.choice] + "/eventClassifier.bin", "wb") as f:
            pickle.dump(self.classifierBi,f)

    def calculateIDF(self):
        n = 0        
        for geohash in self.candidates:
            for timestamp in self.candidates[geohash]:
                # een tweet is een document (niet een cluster)
                for tweet in self.candidates[geohash][timestamp]:
                    self.idf.update(set(tweet['tokens']))
                    n += 1
        for word in self.idf:
            self.idf[word] = log(n/self.idf[word])   
    
    def selectDataset(self):
        dataset = []
        for h in self.candidates:
            for t in self.candidates[h]:
                dataset.append( (self.candidates[h][t],self.isEvent(h,t), self.eventType(h,t) ) )
        
        random.shuffle(dataset)
        trainSplit = int(0.8 * len(dataset))
        self.trainData = dataset[:trainSplit]
        self.testData = dataset[trainSplit:]

    def classifyNLTK(self):
        print("\nClassifying events...\n")
        for i in range(self.ITERATIONS):
            print("Iteration {}".format(i+1))
            print("###########")
            self.selectDataset()
            self.testCat = []
            self.trainCat = []
            self.testBi = []
            self.trainBi = []
        
            #first train category classifier
            print("### TRAINING STEP 1: Training category classifier (Naive Bayes with word features) ###")
            for candidate, event, label in self.testData:
                featuresCat = self.wordFeatureSelector(candidate)
                self.testCat.append((featuresCat, label))         
            
            for candidate, event, label in self.trainData:
                featuresCat = self.wordFeatureSelector(candidate)
                self.trainCat.append((featuresCat, label))

            # MultinomialNB lijkt hier net zo goed als de nltk naive bayes classifier, maar is wel wat sneller
            self.classifierCat = SklearnClassifier(MultinomialNB()).train(self.trainCat)
                
            print("### TRAINING STEP 2: Training event/non-event classifier (Naive Bayes with category & other features) ###")
            #second step train the event/no event classifier
            for candidate, event, label in self.testData:
                featuresBi = self.featureSelector(candidate)   
                self.featureKeys = featuresBi.keys()
                self.testBi.append((featuresBi, event)) 
            
            for candidate, event, label in self.trainData:
                featuresBi = self.featureSelector(candidate)
                self.featureKeys = featuresBi.keys()
                self.trainBi.append((featuresBi, event))

            self.classifierBi = nltk.NaiveBayesClassifier.train(self.trainBi) #SklearnClassifier(LinearSVC()).train(trainBi)
            self.calculateStats(i)
            print("###########")
            
        self.printStats()

    def calculateStats(self, i):
        '''Function to calculate all stats'''
        #self.table is for binary classifier
        #self.cm is for category classifier
        #self.mostInformativeBi is for binary
        #self.mostInformativeCat is for category
        #self.accBi  is accuracy for binary
        #self.accCat is accuracy for category
        # TODO meer stats voor cat?

        #calculate cm for this iteration
        ref = []
        tagged =[]
        for f, e in self.testCat:
            ref.append(self.classifierCat.classify(f))
            tagged.append(e)

        cm = nltk.ConfusionMatrix(ref, tagged)
        self.cm.append(cm)
        aCat = nltk.classify.accuracy(self.classifierCat,self.testCat)
        self.accCat += aCat

        #calculate precision and recall for this iteration
        refsets = defaultdict(set)
        testsets = defaultdict(set)
        baseline = defaultdict(set)

        for n, (feats, label) in enumerate(self.testBi):
            refsets[label].add(n)
            observed = self.classifierBi.classify(feats)
            testsets[observed].add(n)
            baseline['event'].add(n)

        aBi = nltk.classify.accuracy(self.classifierBi,self.testBi)
        self.accBi += aBi

        baseL = nltk.metrics.precision(refsets['event'], baseline['event']) #precision event
        self.baselineBi += baseL

        pEvent = nltk.metrics.precision(refsets['event'], testsets['event']) #precision event
        rEvent = nltk.metrics.recall(refsets['event'], testsets['event']) #recall event
        fEvent = nltk.metrics.f_measure(refsets['event'], testsets['event']) #f score

        pNoEvent = nltk.metrics.precision(refsets['noEvent'], testsets['noEvent']) #precision no event
        rNoEvent = nltk.metrics.recall(refsets['noEvent'], testsets['noEvent']) #recall no event
        fNoEvent = nltk.metrics.f_measure(refsets['noEvent'], testsets['noEvent']) #f score no event

        self.table.append([i+1,round(baseL, 2), round(aBi, 2), round(aCat, 2),round(pEvent,2), round(rEvent,2),round(fEvent,2),round(pNoEvent,2), round(rNoEvent,2), round(fNoEvent,2)])

    def printStats(self):
        it = self.ITERATIONS
        print("\n### EVALUATION STEP 1: Confusion matrices for the category classifier:\n")
        for i in range(it):
            print("Iteration {}".format(i+1))
            print("###########")
            print(self.cm[i])
        print("### EVALUATION STEP 2: Classification using features: {} | training set size: {} & test set size: {}\n".format(", ".join(self.featureKeys),len(self.trainBi), len(self.testBi)))
        print(tabulate.tabulate(self.table, headers=['#', 'Baseline', 'Accuracy Bi', 'Accuracy Cat', 'Pre. Event','Rec. Event','F. Event','Pre. Non-event','Rec. Non-event','F. Non-Event']))
        print("Avg accuracy = {}".format(round(self.accBi / (it) , 2)))
        print("Avg baseline accuracy (everything is an event)= {}\n".format(round(self.baselineBi / (it) , 2)))

    def createFeatureTypes(self):
        '''get all possible word features'''
        featureTypes = Counter()
        for g in self.candidates:
            for t in self.candidates[g]:
                candidate = self.candidates[g][t]
                for row in candidate:
                    featureTypes.update(row['tokens'])
        
        for f in featureTypes:
            featureTypes[f] = featureTypes[f] * self.idf[f]

        self.features = [word for word, n in featureTypes.most_common(800)]
    
    def wordFeatureSelector(self, candidate):
        candidateFeatures = {}
        for row in candidate:
            for feature in self.features:
                if feature in row['tokens']:
                    candidateFeatures[feature] = True
                else:
                    if feature not in candidateFeatures:
                        candidateFeatures[feature] = False 
        return candidateFeatures     

    def featureSelector(self, cluster):
        featuresDict = {}
        #featuresDict['overlap'] = features.wordOverlap(cluster)
        #featuresDict['overlapSimple'] = features.wordOverlapSimple(cluster)
        featuresDict['overlapUser'] = features.wordOverlapUser(cluster)
        #featuresDict['nUsers'] = features.uniqueUsers(cluster)
        #featuresDict['nTweets'] = features.nTweets(cluster)
        #featuresDict['atRatio'] = features.atRatio(cluster) 
        featuresDict['overlapHashtags'] = features.overlapHashtags(cluster)
        #featuresDict['averageTfIdf'] = features.averageTfIdf(cluster, self.idf)
        featuresDict['category'] = self.classifierCat.classify(self.wordFeatureSelector(cluster))
        featuresDict['location'] = features.location(cluster) # locatie maakt niet heel veel uit
        return featuresDict

    def eventType(self,geohash,timestamp):
        # return values {strings gebruiken?}
        eventTypes = {0:"geen event", 1:"sport", 2:"entertainment", 3:"bijeenkomst", 4:"incident", 5:"anders"}
        return eventTypes[self.annotation[geohash][timestamp]]
        
    def isEvent(self,geohash,timestamp):
        # waarden groter/kleiner dan 0 zijn True, gelijk aan 0 is False
        if self.annotation[geohash][timestamp]:
            return 'event'
        else:
            return 'noEvent'

# DEMO
if __name__ == "__main__":
    detective = CreateClassifiers()