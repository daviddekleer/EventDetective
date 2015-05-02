#!/usr/bin/python3

"""
##############
EventDetective2
##############
Detecteert events gegeven dataset
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

class EventDetective2:

    def __init__(self):
        self.dataSets = os.listdir('data/')
        self.candidates = {}
        self._loadDataSet()
        
    def _loadDataSet(self):
        for i, dataset in enumerate(self.dataSets):
            print("{}: {}".format(i, dataset))
        choice = int(input("Select a dataset with classifiers: "))
        
        with open("data/" + self.dataSets[choice] + "/categoryClassifier.bin", 'rb') as binFile:
            self.classifierCat = pickle.load(binFile)

        with open("data/" + self.dataSets[choice] + "/eventClassifier.bin", 'rb') as binFile:
            self.classifierBi = pickle.load(binFile)
        
        choice = int(input("Select a dataset with event candidates that need event detection: "))

        with open("data/" + self.dataSets[choice] + "/eventCandidates.json") as jsonFile:
            self.candidates = json.load(jsonFile)
            
# DEMO
if __name__ == "__main__":
    detective = EventDetective2()