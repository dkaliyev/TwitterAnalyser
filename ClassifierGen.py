'''
Created on 3 Jul 2014

@author: daniyar
'''

import pickle
from pymongo import MongoClient
from _collections import defaultdict
import re
from nltk.tokenize.regexp import wordpunct_tokenize
from nltk.classify.naivebayes import NaiveBayesClassifier
from time import sleep
from nltk.corpus import stopwords
import gc

db = {}
tweets_collection = {}
classifications_collection = {}

global_count = {}

def connect(db_name, tweets_collection_name, classification_collection_name):
    global db, classifications_collection, tweets_collection
    client = MongoClient('localhost', 27017)
    db = client[db_name]
    tweets_collection = db[tweets_collection_name]
    classifications_collection = db[classification_collection_name]
    
    
def start():
    global classifications_collection, tweets_collection, global_count
    sw = stopwords.words('english')
    thr = 5
    refactored_tweets = {}
    records = tweets_collection.find()
    for record in records:
        tweet = record['text']
        tmp_classifiers = record['classifiers']
        for clasfId, classId in tmp_classifiers.iteritems():
            if clasfId not in refactored_tweets.keys():
                refactored_tweets[clasfId] = []
            refactored_tweets[clasfId].append({'text': tweet, 'classId':classId})
    
    records = None

    gc.collect()    

    for classification in classifications_collection.find():
        tweets = []
        classification_name = classification['classification']
        classification_id = str(classification["_id"])
        
        classes = classification['classes']
        
        #records = tweets_collection.find({"clasfId":classification_id})

        records = []
        try:
            records = refactored_tweets[classification_id]
        except KeyError:
            print "No tweets for classification ", classification_name
            continue
        records_count = len(records)
        print classification_name, records_count

        if classification_id in global_count.keys():
            if int(records_count/thr)>global_count[classification_id]:
                print "Exceeded threshold. Training started"
                for record in records:
                    tweet = record['text']
                    class_id = record['classId']
                    class_label = get_class_label(class_id, classes)
                    feats = features_from_tweet(tweet, class_label, word_indicator, stopwords=sw)
                    
                    tweets.append(feats)
                classifier = NaiveBayesClassifier.train(tweets)
                f = open("%s.pickle"%classification_name, 'wb')
                pickle.dump(classifier, f)
                f.close()
                global_count[classification_id] = int(records_count/thr)
            else:
                pass
        else:
            global_count[classification_id] = int(records_count/thr)
            if global_count[classification_id] >=1:
                print "New classification or just started monitor"
                for record in records:
                    tweet = record['text']
                    class_id = record['classId']
                    class_label = get_class_label(class_id, classes)
                    feats = features_from_tweet(tweet, class_label, word_indicator, stopwords=sw)
                    
                    tweets.append(feats)
                classifier = NaiveBayesClassifier.train(tweets)
                f = open("%s.pickle"%classification_name, 'wb')
                pickle.dump(classifier, f)
                f.close()

def get_class_label(_id, classes):
    for _class in classes:
        if str(_class['_id'])==_id:
            return _class['name']
    return None
        
def preprocess_tweet(_tweet):
    #tweet = re.sub(r'(@[a-zA-Z0-9]+)|(http://[a-zA-Z0-9]*(.com|.ru|.org|.uk|.us|.net|.ly)+[/a-zA-Z0-9]*)', '', _tweet)
    tweet = re.sub(r'(@[a-zA-Z0-9]+)|(http://[a-zA-Z0-9]*[.][a-zA-Z]+[/a-zA-Z0-9]*)|([".#]+)', '', _tweet)            
    return tweet
        
def word_indicator(tweet, **kwargs):
    features = defaultdict(list)
    tweet_words = get_tweet_words(tweet, **kwargs)
    for w in tweet_words:
        features[w] = True
    return features

def get_tweet_words(_tweet, stopwords = []):
    tweet = preprocess_tweet(_tweet)
    user_set = set(["http", "://"])
    tweet_words = set(wordpunct_tokenize(tweet.lower()))
    tweet_words = tweet_words.difference(stopwords)
    tweet_words = tweet_words.difference(user_set)
    tweet_words = [w for w in tweet_words if len(w)>2]
    return tweet_words

def features_from_tweet(tweet, label, extractor, **kwargs):
    features = extractor(tweet, **kwargs)
    return (features, label)

if __name__ == "__main__":
    connect("classification", "tweets_test1", "classifications")
    while True: 
        start()
        sleep(10)
                      
            
