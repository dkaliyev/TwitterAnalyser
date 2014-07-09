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




app = Flask(__name__)
app.config['MONGO2_DBNAME'] = 'classification'
mongo = PyMongo(app, config_prefix='MONGO2')

tweets_fields = set(['clasfId', 'classId', 'text', 'tweet_id'])
classification_fields = set(['classification', 'classes'])
global_ids = {}
classifier = None

class MyTweet(dict):
    pass

auth = tweepy.OAuthHandler('1bsrahHDFzRHbr9lMADNwXFhU', 'F0xbMnkO7eHH3QxJrH9oxAq63T59BdUIYczYdQAvLDqGdrPOAc')
auth.set_access_token('2464862775-0qoQdD0tSR9CIs95ePK3Rrdn5fDa8VHSu29UJWa', 'dl4CqY4KcxeU5QTKGuFqNUSAZw9ZCz3i3UAnn44wArFbQ')
api = tweepy.API(auth)


#tweets = api.home_timeline()
#user = api.get_user('goodnews')

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
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

@app.route("/", methods=["GET"])
def index():
    tweets = []
    print "Request received"
    try:
        #for status in tweepy.Cursor(api.user_timeline, screen_name='goodnews', include_rts=False, count=5).items():
        statuses = tweepy.Cursor(api.user_timeline, screen_name='goodnews', include_rts=False, count=30).items(30)
        for status in statuses:
            #print "Getting"
            d = MyTweet()
            #print "Created class inst"
            #print tweets.append(status)
            #print status._json['id']
            setattr(d, "id", status._json['id'])
            #setattr(d, "id", 7549804)
            #print "set first attr", d.id
            setattr(d, "screen_name", status._json["user"]["screen_name"])
            setattr(d, "name",status._json["user"]["name"])
            setattr(d, "text", status._json["text"])
            setattr(d, "ava", status._json["user"]["profile_image_url_https"])
            setattr(d, "date", arrow.get(mktime(strptime(status._json["created_at"],"%a %b %d %H:%M:%S +0000 %Y"))).humanize())
            #setattr(d, "text", "test status")
            tweets.append(d)
    except tweepy.TweepError as err:
            print err.str()
    print "Done parsing"
    print tweets
    classifications = get_classifications()
    global_ids.update(get_ids(classifications))
    #return Response(json.dumps(tweets),  mimetype='application/json')
    return render_template("ClientSideTweet.html", tweets=tweets, classifications=classifications)


def get_classifications():
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
                return Response(json.dumps({"Error":"The keys do not match, please try again"}), mimetype='application/json')
            if len(data['classes']) == 0:
                return Response(json.dumps({"Error":"You must provide at least 2 classes"}), mimetype='application/json')
            tmp['dateCreated'] = strftime("%Y-%m-%dT%H:%M:%SZ", localtime())
            tmp['classification'] = data['classification']
            tmp['classes'] = []
            for _class in data['classes']:
                tmp['classes'].append({'_id':ObjectId(), 'name':_class})
            _id = mongo.db.classifications.insert(tmp)
            if _id != None:
                _id = str(_id)
                ob[_id] = [str(_class['_id']) for _class in tmp['classes']]
                global_ids.update(ob)
                return Response(json.dumps({"id":_id}), mimetype='application/json')
            else:
                return Response(json.dumps({"id":"-1"}), mimetype='application/json')
        
                

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
            return Response(json.dumps({"Error":"Please first create class!"}))
    keys = global_ids.keys()
    tmp = {}
    ids = []
    res = request.get_json()
    print res
    if "content" not in res.keys():
        return Response(json.dumps({"id":"-1", "Error":"Invalid format"}), mimetype='application/json')
    content = res['content']
    for data in content:
        print data
        d_keys = set(data.keys())
        if len(d_keys)!=4 or len(tweets_fields.intersection(d_keys)) != len(tweets_fields):
            return Response(json.dumps({"Error":"The keys do not match, please try again"}))
        if data['clasfId'] not in keys:
            return Response(json.dumps({"Error":"Cannot match classification id"}))
        if data['classId'] not in global_ids[data['clasfId']]:
            return Response(json.dumps({"Error":"Cannot match class id"}))
        for key, value in data.iteritems():
            tmp[key] = value
        tmp['date'] = strftime("%Y-%m-%dT%H:%M:%SZ", localtime())
        tmp['_id'] = ObjectId()
        _id = mongo.db.tweets.insert(tmp)
        if _id != None:
            _id = str(_id)
            ids.append({data["tweet_id"]:_id})
            #
        else:
            ids.append({data["tweet_id"]:"None"})
            #return Response(json.dumps({"id":"-1", "Error":"Could not insert into database"}), mimetype='application/json')

    return Response(json.dumps({"status":1, "ids":ids}), mimetype='application/json')        
@app.route("/classifier", methods=["POST"])
def main():
    global classifier
    data = request.get_json()
    try:
        tweet = data['tweet']
        classification = data['classification']
    except KeyError:
        return Response(json.dumps({"Error":"The keys do not match, please try again"}), mimetype='application/json')
    if classifier == None:
        classifier = {}
        f = {}
        try:
            f = open("%s.pickle" % classification)
        except IOError:
            return Response(json.dumps({"Status": 1, "Error":"Cant open the file"}), mimetype='application/json')     
        classifier[classification] = pickle.load(f)
        tweet = word_indicator(tweet)
        result = classifier[classification].classify(tweet)
        return Response(json.dumps({"Status": 0, "Result":result}), mimetype='application/json')
    else:
        if classification not in classifier.keys():
            try:
                f = open("%s.pickle" % classification)
            except IOError:
                return Response(json.dumps({"Status": 1, "Error":"Cant open the file"}),mimetype='application/json')     
            classifier[classification] = pickle.load(f)
        tweet = word_indicator(tweet)
        result = classifier[classification].classify(tweet)
        return Response(json.dumps({"Status": 0, "Result":result}), mimetype='application/json')
    
if __name__ == '__main__':
    app.run(debug=True)