'''
Created on 1 Jul 2014

@author: daniyar
'''
from flask import Flask
from flask import request
from flask import Response
from flask import json
from flask.ext.pymongo import PyMongo
from time import strftime, localtime, strptime, mktime
from bson.objectid import ObjectId
import copy
import pickle
from ClassifierGen import word_indicator
import tweepy
from flask import render_template
from flask import url_for
from flask import make_response, request, current_app
from functools import update_wrapper
import arrow
from datetime import timedelta
import urllib2




app = Flask(__name__, static_url_path='')
app.config['MONGO2_DBNAME'] = 'classification'
mongo = PyMongo(app, config_prefix='MONGO2')

tweets_fields = set(['clasfId', 'classId', 'text', 'tweet_id'])
classification_fields = set(['classification', 'classes'])
search_fields = set(['include', 'exclude', 'count', 'categories', 'screen_name'])
global_ids = {} # used to globally maintain list of ids
classifier = None
mode = 0 # 0:online, 1:offline
global_tweets = []

class MyTweet(dict):
    pass

auth = tweepy.OAuthHandler('1bsrahHDFzRHbr9lMADNwXFhU', 'F0xbMnkO7eHH3QxJrH9oxAq63T59BdUIYczYdQAvLDqGdrPOAc')
auth.set_access_token('2464862775-0qoQdD0tSR9CIs95ePK3Rrdn5fDa8VHSu29UJWa', 'dl4CqY4KcxeU5QTKGuFqNUSAZw9ZCz3i3UAnn44wArFbQ')
api = tweepy.API(auth)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    """
        Required for cross domain requests
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@app.route("/", methods=["GET", "POST"])
def index():
    tweets = []
    data = {}
    if request.method == "GET":
        if not mode:
            data = json.load(urllib2.urlopen('http://cp.nowtrendin.com/search/for_tweets/?count=10&categories=corporate/hilco'))
        else:
            print "Offline mode"
            global global_tweets
            tweets = global_tweets
    else:
        params = request.form
        q_keys = params.keys()
        # check form parameter names
        if len(q_keys)!=len(search_fields) or len(search_fields.intersection(q_keys)) != len(search_fields):
            return Response(json.dumps({"Status": "1", "Error":"The keys do not match, please try again"}), mimetype='application/json')
        # construct url parameters string
        param_str = "?"
        for key, value in params.iteritems():
            param_str+= "%s=%s&" % (key, value)
        trimmed_str = param_str[:len(param_str)-1]
               
        data = json.load(urllib2.urlopen('http://cp.nowtrendin.com/search/for_tweets/%s' % trimmed_str))

    # create tweets list    
    for key, value in data.iteritems():
        d = MyTweet()

        setattr(d, "id", key)

        setattr(d, "screen_name", value["screen_name"])
        setattr(d, "name",value["real_name"])
        setattr(d, "text", value["tweet"])
        setattr(d, "ava", value["profile_image_url"])
        setattr(d, "created_at", value["created_at"])
        setattr(d, "date", value["time_since"])

        tweets.append(d)
    classifications = get_classifications()
    global_ids.update(get_ids(classifications))

    return render_template("ClientSideTweet.html", tweets=tweets, classifications=classifications)


def get_classifications():
    """
        Get classifications from database.
    """
    classifications = []
    clfs = mongo.db.classifications.find({}, {"dateCreated":0})
    for clf in clfs:
        tmp = {}
        tmp['_id'] = str(clf['_id'])
        tmp['classification'] = clf['classification']
        tmp['classes'] = []
        for _class in clf['classes']:
            tmp['classes'].append({'name':_class['name'], '_id':str(_class['_id'])})
        classifications.append(tmp)
    return classifications

def get_ids(classifications):
    """
        Extract ids only. Result object is in form: {classification_id: [class1_id, class2_id, ...]}
    """
    ids = {}
    for classification in classifications:
        tmp = []
        for _class in classification['classes']:
            tmp.append(_class['_id'])
        ids[classification['_id']] = tmp
    return ids

@app.route('/classification', methods=['GET', 'POST', 'OPTIONS'])    
@crossdomain(origin="*")    
def classification():
    """
        Retrieve or create new classification. If method is GET, return all available 
        classifications. If method is POST, create new classification and return its ID
    """
    global global_ids
    if request.method == 'GET':
        classifications = get_classifications()
        global_ids.update(get_ids(classifications))
        return Response(json.dumps(classifications),  mimetype='application/json')
    else:
        if request.method == 'POST':
            tmp = {}
            ob = {}
            data = request.get_json()
            d_keys = set(data.keys())
            if len(d_keys)!=len(classification_fields) or len(classification_fields.intersection(d_keys)) != len(classification_fields):
                return Response(json.dumps({"status":"1", "Error":"The keys do not match, please try again"}), mimetype='application/json')
            if len(data['classes']) == 0:
                return Response(json.dumps({"status":"1", "Error":"You must provide at least 2 classes"}), mimetype='application/json')
            current_clsfs = get_classifications()
            for clsf in current_clsfs: 
                if clsf['classification'] == data['classification']:
                    return Response(json.dumps({"status":"1", "Error":"Classification already exists"}), mimetype='application/json')
            tmp['dateCreated'] = strftime("%Y-%m-%dT%H:%M:%SZ", localtime())
            tmp['classification'] = data['classification']
            tmp['classes'] = []
            tmp_classes = []
            for _class in data['classes']:
                tmp['classes'].append({'_id':ObjectId(), 'name':_class})
            _id = mongo.db.classifications.insert(tmp)
            if _id != None:
                _id = str(_id)
                ob[_id] = [str(_class['_id']) for _class in tmp['classes']]
                global_ids.update(ob)
                tmp["_id"] = _id
                tmp_classes = [{"_id":str(_class['_id']), "name":_class['name']} for _class in tmp['classes']]
                tmp['classes'] = tmp_classes
                return Response(json.dumps({"status":"0", "content":tmp}), mimetype='application/json')
            else:
                return Response(json.dumps({"status":"1", "Error":"Cant insert new classification into database"}), mimetype='application/json')
        

@app.route('/trainer', methods=['POST'])
def trainer():
    global global_ids
    """
        Assign class to the tweet and save it to database
    """
    
    if global_ids == {}:
        classifications = get_classifications()
        global_ids = copy.deepcopy(get_ids(classifications))
        if global_ids == {}:
            return Response(json.dumps({"status":"1", "Error":"Please first create class!"}), mimetype='application/json')
    keys = global_ids.keys()
    tmp = {}
    ids = {}
    res = request.get_json()
    if "content" not in res.keys():
        return Response(json.dumps({"status":"1", "Error":"Invalid format"}), mimetype='application/json')

    content = res['content']
    try:
        tmp["tweet_id"] = content["tweet_id"]
        tmp["classf_id"] = content["classf_id"]
        tmp["class_id"] = content["class_id"]
        tmp["text"] = content["text"]
    except KeyError:
        return Response(json.dumps({"status":"1", "Error":"Invalid format"}), mimetype='application/json')

    if tmp['classf_id'] not in keys:
            return Response(json.dumps({"status":"1", "Error":"Cannot match classification id"}))
    if tmp['class_id'] not in global_ids[tmp['classf_id']]:
        return Response(json.dumps({"status":"1", "Error":"Cannot match class id"}))    
    ids[tmp['tweet_id']] = tmp['class_id']    
    tmp['last_updated'] = strftime("%Y-%m-%dT%H:%M:%SZ", localtime())    
    tweets = list(mongo.db.tweets_test1.find({'tweet_id':tmp['tweet_id']}))
    if tweets == []:
        _id = mongo.db.tweets_test1.insert({'_id':ObjectId(), 'tweet_id':tmp['tweet_id'], 'classifiers':{tmp['classf_id']:tmp['class_id']}, 'last_updated':tmp['last_updated'], 'text':tmp['text']})   
        if _id != None:
            ids[tmp['tweet_id']] = tmp['class_id']
        else:
            ids[tmp['tweet_id']] = "None"
    else:
        classifiers = tweets[0]['classifiers']
        classifiers[tmp['classf_id']] = tmp['class_id']
        mongo.db.tweets_test1.update({'tweet_id':tmp['tweet_id']}, {"$set":{'classifiers': classifiers, 'last_updated':tmp['last_updated']}})

    return Response(json.dumps({"status":0, "ids":ids}), mimetype='application/json')


@app.route('/clear', methods=['POST'])
def clear():
    global global_ids
    """
        Remove specified classification from a tweet
    """
    
    if global_ids == {}:
        classifications = get_classifications()
        global_ids = copy.deepcopy(get_ids(classifications))
        if global_ids == {}:
            return Response(json.dumps({"status":"1", "Error":"Please first create class!"}), mimetype='application/json')
    keys = global_ids.keys()
    tmp = {}
    ids = {}
    res = request.get_json()
    if "content" not in res.keys():
        return Response(json.dumps({"status":"1", "Error":"No content"}), mimetype='application/json')

    content = res['content']
    try:
        tmp["tweet_id"] = content["tweet_id"]
        tmp["classf_id"] = content["classf_id"]
    except KeyError:
        return Response(json.dumps({"status":"1", "Error":"Invalid format"}), mimetype='application/json')

    if tmp['classf_id'] not in keys:
            return Response(json.dumps({"status":"1", "Error":"Cannot match classification id"}))  
    
    tmp['last_updated'] = strftime("%Y-%m-%dT%H:%M:%SZ", localtime())    
    tweets = list(mongo.db.tweets_test1.find({'tweet_id':tmp['tweet_id']}))
    if tweets == []:
        return Response(json.dumps({"status":"1", "Error":"Tweet doesnt exist"}), mimetype='application/json')
    else:
        classifiers = dict(tweets[0]['classifiers'])
        if tmp['classf_id'] in classifiers.keys():
            del classifiers[tmp['classf_id']]
            mongo.db.tweets_test1.update({'tweet_id':tmp['tweet_id']}, {"$set":{'classifiers': classifiers, 'last_updated':tmp['last_updated']}})
            return Response(json.dumps({"status":0}), mimetype='application/json')
        else:
            return Response(json.dumps({"status":1, "Error": "IDs dont match"}), mimetype='application/json')        

@app.route("/classifier", methods=["POST"])
def main():
    """
        Classify a tweet
    """
    data = request.get_json()
    try:
        tweet = data['tweet']
        classification = data['classification']
    except KeyError:
        return Response(json.dumps({"status":"1", "Error":"The keys do not match, please try again"}), mimetype='application/json')
    try:
        f = open("%s.pickle" % classification)
    except IOError:
        return Response(json.dumps({"Status": 1, "Error":"Cant open the file"}), mimetype='application/json')
    classifier = pickle.load(f)
    _tweet = word_indicator(tweet)
    result = classifier.classify(_tweet)
    return Response(json.dumps({"Status": 0, "Result":result}), mimetype='application/json')

    
if __name__ == '__main__':
    if mode:
        f = open("statuses.pickle")
        global_tweets = pickle.load(f)
        f.close()
    app.run(debug=True)