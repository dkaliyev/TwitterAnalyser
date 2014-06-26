import nltk
import re
from nltk.corpus import stopwords
from sklearn.naive_bayes import BernoulliNB
from sklearn.svm import SVC
from nltk import SklearnClassifier
from os import listdir
import pickle
import random
from time import ctime


class TweetClassifier:
    def __init__(self, _proportion = 0.001, _feat_limit = 2000):
        self.tweets = []
        self.test_tweets = []
        self.word_features = []
        self.devtest_set = {}
        self.training_set = {}
        self.proportion = _proportion
        self.feat_limit = _feat_limit


    def read_files1(self):
        count = 1500000
        lines = []
        train_tweet_cnt = count * 0.75
        english_stops = set(stopwords.words('english'))
        print "Reading files..."
        print ctime()
        f = open('Sentiment Analysis Dataset.csv', "rU")
        line = f.readline()
        line = f.readline()
        for i in range(count):
            lines.append(line)
            line = f.readline()
        f.close()
        random.shuffle(lines)
        i = 0
        for line in lines:
            #print line
        #while line != "":
            spl_line = line.split(',')
            words_filtered = [e.lower() for e in spl_line[3].strip('. \t\n\r').split() if len(e) >=3 and e.lower() not in english_stops]
            no_filtered = [e.lower() for e in spl_line[3].strip('. \n\t\r').split() if len(e) >=2]
            if i <= train_tweet_cnt:
                self.tweets.append((words_filtered, 'positive' if spl_line[1]=='1' else 'negative'))
            else:
                self.test_tweets.append((words_filtered, 'positive' if spl_line[1]=='1' else 'negative'))
            #line = f.readline()
            i+=1
        print ctime()
        print "Reading done. %s training tweets" % train_tweet_cnt
        #random.shuffle(self.tweets)
        self.tweets = self.tweets[:int(len(self.tweets)*self.proportion)]
        #random.shuffle(self.test_tweets)
        self.test_tweets = self.test_tweets[:int(len(self.test_tweets)*self.proportion)]
        print "Final count %s tweets %s test tweets" % (len(self.tweets), len(self.test_tweets))
        f.close()


    def get_words_in_tweets(self, tweets):
        all_words = []
        for(words, sentiment) in tweets:
            all_words.extend(words)
        return all_words

    def get_word_features(self, _wordlist):
        wordlist = nltk.FreqDist(_wordlist)
        word_features = wordlist.keys()
        print "Total %s, >0 %s" % (wordlist.N(), wordlist.B())
        return word_features[:self.feat_limit]

    def extract_features(self, document):
        document_words = set(document)
        features = {}
        for word in self.word_features:
            features['%s' % word] = (word in document_words)
        return features

    def generate_training_set(self):
        self.read_files1()
        print ctime()
        print "Getting word features..."
        self.word_features = self.get_word_features(self.get_words_in_tweets(self.tweets))
        print "Generating training set..."
        print ctime()
        print "Done"
        self.training_set = nltk.classify.apply_features(self.extract_features, self.tweets)
        self.devtest_set = nltk.classify.apply_features(self.extract_features, self.test_tweets)

    def init_classifiers(self):
        classifiers = {}
        classifier_modules = {'NaiveBayesClassifier': nltk.NaiveBayesClassifier,
            'DecisionTreeClassifier': nltk.DecisionTreeClassifier,
            'MaxentClassifier': nltk.MaxentClassifier,
            'WekaClassifier': nltk.classify.WekaClassifier ,
            'BernoulliNB': SklearnClassifier(BernoulliNB()),
            'SVC': SklearnClassifier(SVC(), sparse = False)}

        #classifier_names = ['NaiveBayesClassifier', 'DecisionTreeClassifier',
             #'MaxentClassifier', 'WekaClassifier', 'BernoulliNB',
             #'SVC']
        classifier_names = ['NaiveBayesClassifier', 'DecisionTreeClassifier',
             'MaxentClassifier']
        files_list = listdir('.\classifier_pickles')
        for classifier in classifier_names:
            if "%s.pickle" % classifier in files_list:
                print "%s pickle found. Loading..." % classifier
                f = open('.\classifier_pickles\%s.pickle' % classifier)
                classifiers['%s' % classifier] = pickle.load(f)
                f.close()
            else:
                print "Training %s" % classifier
                print ctime()
                if classifier == 'MaxentClassifier':
                    classifiers['%s' % classifier] = classifier_modules[classifier].train(self.training_set, 'GIS', max_iter=10)
                else:
                    classifiers['%s' % classifier] = classifier_modules[classifier].train(self.training_set)
                f = open('.\classifier_pickles\%s.pickle' % classifier, 'wb')
                pickle.dump(classifiers['%s' % classifier], f)
                f.close()
                print ctime()
                print "Ended"
        print "Training done!"
        return classifiers

    def test_tweet(self, classifiers, tweet):
        for name, classifier in classifiers.iteritems():
            print name
            if name != 'DecisionTreeClassifier':
                classifier.show_most_informative_features(10)
            print classifier.classify(self.extract_features(tweet.split()))

    def test_classifiers(self,classifiers):
        print "Testing the classifiers: "
        for name, classifier in classifiers.iteritems():
            print name
            print nltk.classify.accuracy(classifier, self.devtest_set)
        print "Testing done"

if __name__ == '__main__':
    cl_class = TweetClassifier()
    #read_files()
    #word_features = get_word_features(get_words_in_tweets(tweets))
    #training_set = nltk.classify.apply_features(extract_features, tweets)
    #classifier = nltk.NaiveBayesClassifier.train(training_set)
    #test(classifier)
    cl_class.generate_training_set()
    classifiers = cl_class.init_classifiers()
    cl_class.test_classifiers(classifiers)
    tweet1 = "I had terrible experience with Apple store customer service"
    tweet2 = "Those pair of shoes bought from Clarks are awesome"
    tweet3 = "Just murdered a man"
    cl_class.test_tweet(classifiers, tweet1)
    cl_class.test_tweet(classifiers, tweet2)
    cl_class.test_tweet(classifiers, tweet3)


