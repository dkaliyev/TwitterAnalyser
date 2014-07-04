import tweepy
from flask import Flask
from flask import request
from flask import Response
from flask import json

auth = tweepy.OAuthHandler('1bsrahHDFzRHbr9lMADNwXFhU', 'F0xbMnkO7eHH3QxJrH9oxAq63T59BdUIYczYdQAvLDqGdrPOAc')
auth.set_access_token('2464862775-0qoQdD0tSR9CIs95ePK3Rrdn5fDa8VHSu29UJWa', 'dl4CqY4KcxeU5QTKGuFqNUSAZw9ZCz3i3UAnn44wArFbQ')
api = tweepy.API(auth)

app = Flask(__name__)

#tweets = api.home_timeline()
user = api.get_user('goodnews')

@app.route("/", methods=["GET"])
def index():
    tweets = []
    for status in tweepy.Cursor(api.user_timeline, screen_name='goodnews', include_rts=False).items():
        print tweets.append(status)
#print user.screen_name
    
    
    

