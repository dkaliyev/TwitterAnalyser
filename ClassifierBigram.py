import pickle
import nltk
import random
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
from nltk.corpus import stopwords
from utils import *


class ClassifierBigram(object):
    """description of class"""
    def __init__(self, _prop=1):
        self.tweets = []
        self.bestwords = []
        self.proportion = _prop

    def read_files(self, featx):
        count = 1500000
        lines = []
        english_stops = set(stopwords.words('english'))
        timed_print("Reading NB pickle")

        f = open('NaiveBayesv6.1.pickle')
        NBclassifier = pickle.load(f)
        f.close()

        timed_print("Done")

        most_inf = NBclassifier.most_informative_features(100)
        self.bestwords = [w for (w,s) in most_inf]
        
        timed_print("Reading dataset")
        f = open('Sentiment Analysis Dataset.csv', "rU")
        line  = f.readline()
        line = f.readline()
        negfeats = []
        posfeats = []
        for i in range(count):
            lines.append(line)
            line = f.readline()
        f.close()
        timed_print("Done")

        timed_print("Generating feature sets")
        random.shuffle(lines)
        count = int(count*self.proportion)
        for i in range(count):
            line = lines.pop()
            spl_line = line.split(',')
            #words_filtered = [e.lower() for e in spl_line[3].strip('. \t\n\r').split() if len(e) >=3 and e.lower() not in english_stops]
            no_filtered = [e.lower() for e in spl_line[3].strip('. \n\t\r').split() if len(e) >=2]
            
            if spl_line[1] == '1':
                posfeats.append((featx(no_filtered), 'pos'))
            else:
                negfeats.append((featx(no_filtered), 'neg'))

        negcutoff = len(negfeats)*3/4
        poscutoff = len(posfeats)*3/4
 
        trainfeats = negfeats[:negcutoff] + posfeats[:poscutoff]
        testfeats = negfeats[negcutoff:] + posfeats[poscutoff:]
        timed_print("Done")

        return (trainfeats, testfeats)

    def train_classifier(self):
        trainfeats, testfeats = self.read_files(self.best_bigram_word_feats)

        timed_print("Training the classifier")
        classifier = nltk.MaxentClassifier.train(trainfeats, algorithm='IIS')
        timed_print("Done")

        timed_print("Writing pickle")
        f = open('MaxentV1.pickle', 'wb')
        pickle.dump(classifier, f)
        f.close()
        timed_print("Done")

        timed_print("Calculating the accuracy")
        print nltk.classify.accuracy(classifier, testfeats)
        timed_print("Done")

    def best_word_feats(self, words):
        return dict([(word, True) for word in words if word in self.bestwords])

    def best_bigram_word_feats(self, words, score_fn=BigramAssocMeasures.chi_sq, n=200):
        #timed_print("Finding best collocations")
        bigram_finder = BigramCollocationFinder.from_words(words)
        bigrams = bigram_finder.nbest(score_fn, n)
        d = dict([(bigram, True) for bigram in bigrams])
        #timed_print("Done")

        #timed_print("Updating feature set")
        d.update(self.best_word_feats(words))
        #timed_print("Done")

        return d
