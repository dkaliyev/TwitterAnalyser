import tweepy

auth = tweepy.OAuthHandler('1bsrahHDFzRHbr9lMADNwXFhU', 'F0xbMnkO7eHH3QxJrH9oxAq63T59BdUIYczYdQAvLDqGdrPOAc')
auth.set_access_token('2464862775-0qoQdD0tSR9CIs95ePK3Rrdn5fDa8VHSu29UJWa', 'dl4CqY4KcxeU5QTKGuFqNUSAZw9ZCz3i3UAnn44wArFbQ')
api = tweepy.API(auth)

#tweets = api.home_timeline()
user = api.get_user('goodnews')
for status in tweepy.Cursor(api.user_timeline, screen_name='goodnews', include_rts=False).items():
    print status.text
#print user.screen_name
