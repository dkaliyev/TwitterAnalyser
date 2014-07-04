'''
Created on 1 Jul 2014

@author: daniyar
'''
from flask import Flask
from flask import request
from flask import Response
from flask import json
from flask.ext.pymongo import PyMongo
from time import strftime, localtime
from bson.objectid import ObjectId
import copy
import pickle
from ClassifierGen import word_indicator


app = Flask(__name__)
app.config['MONGO2_DBNAME'] = 'classification'
mongo = PyMongo(app, config_prefix='MONGO2')

tweets_fields = set(['clasfId', 'classId', 'text'])
classification_fields = set(['classification', 'classes'])
global_ids = {}
classifier = None


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
    
@app.route('/classification', methods=['GET', 'POST'])
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
        tmp = {}
        ob = {}
        data = request.get_json()
        d_keys = set(data.keys())
        if len(d_keys)!=len(classification_fields) or len(classification_fields.intersection(d_keys)) != len(classification_fields):
            return Response(json.dumps({"Error":"The keys do not match, please try again"}))
        if len(data['classes']) == 0:
            return Response(json.dumps({"Error":"You must provide at least 2 classes"}))
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
    res = request.get_json()
    content = res['content']
    for data in content:
        print data
        d_keys = set(data.keys())
        if len(d_keys)!=3 or len(tweets_fields.intersection(d_keys)) != len(tweets_fields):
            return Response(json.dumps({"Error":"The keys do not match, please try again"}))
        if data['clasfId'] not in keys:
            return Response(json.dumps({"Error":"Cannot match classification id"}))
        if data['classId'] not in global_ids[data['clasfId']]:
            return Response(json.dumps({"Error":"Cannot match class id"}))
        for key, value in data.iteritems():
            tmp[key] = value
        tmp['date'] = strftime("%Y-%m-%dT%H:%M:%SZ", localtime())
        _id = mongo.db.tweets.insert(tmp)
        if _id != None:
            _id = str(_id)
            return Response(json.dumps({"id":_id}), mimetype='application/json')
        else:
            return Response(json.dumps({"id":"-1", "Error":"Could not insert into database"}), mimetype='application/json')

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
    app.run()