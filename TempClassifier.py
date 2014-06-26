from Classifier import TweetClassifier

import nltk
from sklearn.naive_bayes import BernoulliNB
from nltk import SklearnClassifier
import pickle
from time import ctime


if __name__ == "__main__":
    cl = TweetClassifier(_proportion=1, _feat_limit = 1000)
    cl.generate_training_set()
    print "Training started..."
    print ctime()
    #NBClassifier = SklearnClassifier(BernoulliNB()).train(cl.training_set)
    classifier = nltk.NaiveBayesClassifier.train(cl.training_set)
    print "Training done!"
    print ctime()
    f = open('NaiveBayesv2.pickle', 'wb')
    pickle.dump(classifier, f)
    f.close()
    print nltk.classify.accuracy(classifier, cl.devtest_set)