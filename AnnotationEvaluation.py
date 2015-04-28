#!/usr/bin/python3

"""
 Computes the kappa score for annotators and keeps only the annotations (and
 their event candidates) about which the annotators agree.
"""

import os,sys

class AnnotationEvaluation:
    
    def __init__(self):
        self.dataSets = os.listdir('data/')
        # voor het gemak gaan we uit van twee annotators
        self.annotation1 = {}
        self.annotation2 = {}
        self._loadAnnotations()
        # in welke categorie staat het event (0,1,2,3,4,5)?
        self.categoryEval = [[],[]]
        # is het een event (0) of niet (1)?
        self.eventEval = [[],[]]
        self._makeAnnotationLists()
        self.eventKappa = self._calculateKappa(self.eventEval)
        self.categoryKappa = self._calculateKappa(self.categoryEval)
        # TODO presentatie resultaten
        print("eventKappa:", eventKappa)
        print("categoryKappa:", categoryKappa)
        
        ###
        # Kappa evaluatie
        ###
        # Boek van IR (streng?):
        # kappa above 0.8: good
        # kappa between 0.67 and 0.8: fair
        # kappa below 0.67: dubious
        ###
        # http://www.stattutorials.com/SPSS/TUTORIAL-SPSS-Interrater-Reliability-Kappa.htm
        # J. Richard Landis and Gary G. Koch. 1977. The Measurement of Observer Agreement for Categorical Data. Biometrics, 33:159–174.
        # Poor agreement: < 0
        # Slight agreement: 0.0 – 0.20
        # Fair agreement: 0.21 – 0.40
        # Moderate agreement: 0.41 – 0.60
        # Substantial agreement: 0.61 – 0.80
        # Almost perfect agreement: 0.81 – 1.00
        
    def _calculateKappa(judgeArray):
        judgeDicts = []
        judgeAmount = len(judgeArray)   # totale aantal judges
        judgeTotal = len(judgeArray[0]) # totale aantal judgements voor 1 judge
        
        rankList = []  # mogelijke judgementwaarden bijhouden
        agreeCount = 0 # hoe vaak waren de judges het eens?
        # voor iedere rank alle judges bijlangs gaan
        for i in range(judgeTotal):
            agree = True
            for j in range(judgeAmount):
                if i == 0:
                    # nieuwe judge, voeg een lege dict toe aan de judge dictionaries
                    judgeDicts.append({})
                if j == 0:
                    # nieuwe rank, reset de rank van de vorige kolom
                    prevRank = judgeArray[j][i]
                
                curRank = judgeArray[j][i]
                
                if curRank not in rankList:
                    rankList.append(curRank)
                
                # voeg huidige rank toe aan dictionary van huidige judge
                if curRank in judgeDicts[j]:
                    judgeDicts[j][curRank] += 1
                else:
                    judgeDicts[j][curRank] = 1

                if agree:
                    # de judges zijn het eens zolang ze het eens zijn met de
                    # judge die voor hen kwamen (voor de huidige rank)
                    if curRank != prevRank:
                        agree = False
                prevRank = curRank
                    
            if agree:
                agreeCount += 1
                
        # p(A): in hoeveel procent v/d gevallen waren de judges het eens
        pA = agreeCount / judgeTotal

        # p(E): kans dat judges het eens waren
        pE = 0
        for rank in rankList:
            curChance = 1
            for d in judgeDicts:
                if rank in d:
                    curChance *= d[rank]/judgeTotal
                else:
                    # rank is niet aanwezig voor judge, dus kans is 0
                    curChance *= 0
            pE += curChance

        try:
            kappa = round((pA - pE)/(1 - pE), 2)
        except ZeroDivisionError:
            print("Can't divide by zero.")
            return None
        
        return kappa
        
    def _makeAnnotationLists(self):
        for geoHash in self.annotation1:
            for times in self.annotation1[geoHash]:
                anno1 = self.annotation1[geoHash][times]
                anno2 = self.annotation2[geoHash][times]
                
                self.categoryEval[0].append(anno1)
                if anno1:
                    self.eventEval[0].append(1)
                else:
                    self.eventEval[0].append(0)
                
                self.categoryEval[1].append(anno2)
                if anno2:
                    self.eventEval[1].append(1)
                else:
                    self.EventEval[1].append(0)
        
    def _loadAnnotations(self):
        for i, dataset in enumerate(self.dataSets):
            print("{}: {}".format(i, dataset))
        choice = int(input("Select dataset: "))
        
        self.datasetName = self.dataSets[choice]
        
        fnames = []
        # kijk of bestanden in data/gekozenDataSet beginnen met /annotation_
        for f in os.listdir("data/" + self.dataSets[choice]):
            if f.startswith("/annotation_"):
                fnames.append(f)
                
        if len(fnames) != 2:
            print("Sorry, this script will only work for two annotators.")
            sys.exit()
        
        self.annotation1 = open("data/" + self.dataSets[choice] + fname[0])
        self.annotation2 = open("data/" + self.dataSets[choice] + fname[0])
        self.candidates = json.load(jsonFile)
        
if __name__ == "__main__":
    AnnotationEvaluation()