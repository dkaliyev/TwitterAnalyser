import tweepy
from flask import Flask
from flask import request
from flask import Response
from flask import json
import time
import arrow

class MyTweet(dict):
	pass

auth = tweepy.OAuthHandler('1bsrahHDFzRHbr9lMADNwXFhU', 'F0xbMnkO7eHH3QxJrH9oxAq63T59BdUIYczYdQAvLDqGdrPOAc')
auth.set_access_token('2464862775-0qoQdD0tSR9CIs95ePK3Rrdn5fDa8VHSu29UJWa', 'dl4CqY4KcxeU5QTKGuFqNUSAZw9ZCz3i3UAnn44wArFbQ')
api = tweepy.API(auth)

app = Flask(__name__)

#tweets = api.home_timeline()
#user = api.get_user('goodnews')

@app.route("/", methods=["GET"])
def index():
    tweets = []
    for status in tweepy.Cursor(api.user_timeline, screen_name='goodnews', include_rts=False).items():
    	d = MyTweet()
        #print tweets.append(status)
        setattr(d, "id", status._json['id'])
        setattr(d, "screen_name", status._json["user"]["screen_name"])
        setattr(d, "text", status._json["text"])
        setattr(d, "date", arrow.get(time.mktime(time.strptime(status._json["created_at"],"%a %b %d %H:%M:%S +0000 %Y"))).humanize())
        tweets.append(d)
    return Response(json.dumps(classifications),  mimetype='application/json')
#print user.screen_name
    
    
    

