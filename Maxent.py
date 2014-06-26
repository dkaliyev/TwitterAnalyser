from Classifier import TweetClassifier

import nltk
import pickle
from time import ctime

if __name__ == '__main__':
	f = open('NaiveBayesv6.pickle')
	classifier = pickle.load(f)
	cl = TweetClassifier()
	f.close()
	word_features = [w for (w, s) in classifier.most_informative_features(150)]
	print ctime(), "Generating training set"
	cl.generate_training_set(word_features)
	
	print ctime(), "Training started..."
	maxent = nltk.MaxentClassifier.train(cl.training_set, algorithm = 'IIS')
	print ctime(), "Training done..."

	print "Testing"
	print nltk.classify.accuracy(maxent, cl.devtest_set)