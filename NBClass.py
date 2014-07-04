'''
Created on 1 Jul 2014

@author: daniyar
'''

import collections, itertools
import nltk.classify.util, nltk.metrics
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import movie_reviews, stopwords
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
from nltk.probability import FreqDist, ConditionalFreqDist
import pickle

class NBClass(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        
    def word_feats(self, words):
        return dict([(word, True) for word in words]) 
    def best_word_feats(self, words):
        word_fd = FreqDist()
        label_word_fd = ConditionalFreqDist()
         
        for word in movie_reviews.words(categories=['pos']):
            word_fd.inc(word.lower())
            label_word_fd['pos'].inc(word.lower())
         
        for word in movie_reviews.words(categories=['neg']):
            word_fd.inc(word.lower())
            label_word_fd['neg'].inc(word.lower())
         
        # n_ii = label_word_fd[label][word]
        # n_ix = word_fd[word]
        # n_xi = label_word_fd[label].N()
        # n_xx = label_word_fd.N()
         
        pos_word_count = label_word_fd['pos'].N()
        neg_word_count = label_word_fd['neg'].N()
        total_word_count = pos_word_count + neg_word_count
         
        word_scores = {}
         
        for word, freq in word_fd.iteritems():
            pos_score = BigramAssocMeasures.chi_sq(label_word_fd['pos'][word],
                (freq, pos_word_count), total_word_count)
            neg_score = BigramAssocMeasures.chi_sq(label_word_fd['neg'][word],
                (freq, neg_word_count), total_word_count)
            word_scores[word] = pos_score + neg_score
         
        best = sorted(word_scores.iteritems(), key=lambda (w,s): s, reverse=True)[:10000]
        bestwords = set([w for w, s in best])
        return dict([(word, True) for word in words if word in bestwords])
    def best_bigram_word_feats(self, words, score_fn=BigramAssocMeasures.chi_sq, n=200):
        bigram_finder = BigramCollocationFinder.from_words(words)
        bigrams = bigram_finder.nbest(score_fn, n)
        d = dict([(bigram, True) for bigram in bigrams])
        d.update(self.best_word_feats(words))
        return d