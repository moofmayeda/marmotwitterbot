#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import tweepy, requests, json, inspect, urllib
from multidimensional_urlencode import urlencode
from configobj import ConfigObj

config = ConfigObj('config.txt')
auth = tweepy.OAuthHandler(config['CONSUMER_KEY'], config['CONSUMER_SECRET'])
auth.set_access_token(config['ACCESS_KEY'], config['ACCESS_SECRET'])
api = tweepy.API(auth)
myUserID = api.me().id
url = "http://marmosetmusic.dev:5000/filter_tracks"
dict = {'energy': ['Low', 'Low-Medium', 'Medium', 'Medium-High', 'High'], 'genres': ['Ambient', 'Beats', 'Blues & Jazz', 'Country', 'Electronic', 'Folk', 'Orchestral', 'Pop', 'Rock', 'Soulful', 'Spiritual', 'World'], 'arc': ['Steady', 'Ascending', 'Descending', 'Middle Crescendo', 'Multiple Crescendos', 'Frenetic'], 'keywords': ['Acoustic', 'Bass', 'Bold', 'Calming', 'Electronic', 'Enlightening', 'Ethereal', 'Flat', 'Folk', 'Happy', 'Harmonic', 'Heavy', 'Indie', 'Inspiring', 'Instrumental', 'Lo-fi', 'Loud', 'Melodic', 'Orchestral', 'Pop', 'Powerful', 'Progressive', 'Rhythmic', 'Sad', 'Soft', 'Solo', 'Soothing', 'Soulful', 'Spiritual', 'Stirring', 'Unplugged', 'Uplifting', 'Vocal'], 'instruments': ['Acoustic Guitar', 'Banjo', 'Big Drums', 'Drum Machine', 'Electric Guitar', 'Glockenspiel/Toy Piano', 'Horns/Brass', 'Mandolin', 'Oohs & Ahhs', 'Organ', 'Piano', 'Stomps/Claps', 'Strings', 'Synthesizer', 'Ukulele'], 'mood': ['A Journey', 'Angelic', 'Anthemic', 'Bouncy', 'Bright', 'Burdened', 'Calm', 'Cinematic', 'Classic', 'Cold', 'Confident', 'Dark', 'Depressed', 'Dynamic', 'Ecstatic', 'Emotional', 'Empowering', 'Energetic', 'Epic', 'Ethereal', 'Exciting', 'Powerful', 'Precise', 'Pumped', 'Quirky', 'Rebellious', 'Reflective', 'Revelatory', 'Romantic', 'Sentimental', 'Sexy', 'Silly', 'Sinister', 'Slick', 'Sombre', 'Sparse', 'Sporadic', 'Stoic', 'Upbeat', 'Vulnerable', 'Whimsical', 'Youthful', 'Feminine', 'Fun', 'Gritty', 'Honorable', 'Hopeful', 'Human', 'Imaginative', 'Industrial', 'Inspiring', 'Intimate', 'Light', 'Masculine', 'Meandering', 'Mechanical', 'Minimal', 'Mischievous', 'Mysterious', 'Optimistic', 'Organic', 'Pensive', 'Playful', 'Positive']}

class Response(object):
  def tracks(self):
    if not hasattr(self, '_tracks'):
      result = []
      for track in self.json():
        result.append(Track(track['id'], track['title']))
      self._tracks = result
    return self._tracks

for method_name, method in inspect.getmembers(Response, inspect.ismethod):  
    setattr(requests.models.Response, method_name, method.im_func)

class Track(object):
  def __init__(self, id, title):
    self.id = id
    self.title = title
    self.url = "http://marmosetmusic.dev:5000/browse/" + str(id)

#override tweepy.StreamListener to add logic to on_status
class MyStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        print(status.text)
        print(status.id)
        print(status.in_reply_to_status_id)
        print(status.user.id)
        if status.in_reply_to_status_id is None:
          search_params = {}
          for word in status.text.split(" "):
            results = [k for k, v in dict.iteritems() if word.capitalize() in v]
            if results:
              search_params.setdefault(results[0], []).append(word.capitalize())
          print search_params
          if search_params:
            # http://marmosetmusic.dev:5000/filter_tracks?q%5Bmood%5D%5B%5D=classic&q%5Binstruments%5D%5B%5D=Banjo&q%5Binstruments%5D%5B%5D=Mandolin&limit=14&order=rolling_rank+DESC
            # http://marmosetmusic.dev:5000/filter_tracks?q[mood][]=classic&q[instruments][]=Banjo
            data = urlencode({"q": search_params, "limit": 14, "order":"rolling_rank DESC"})
            print data
            response = requests.get(url + "?" + data)
            print("The response contains {0} properties".format(len(response.json())))
            if response.ok:
              print "OK"
              if response.json():
                # if genre match found, send to genre page rather than track page
                api.update_status("Check out " + response.tracks()[0].url + ", it might be just what you need right now!", status.id)
              else:
                # add random shuffle if no results found
                api.update_status("Your search was so specific, I couldn't find anything. Please try again.", status.id)
            else:
              print "NOT OK"
              response.raise_for_status()
          else:
            # search with artist
            # http://marmosetmusic.dev:5000/filter_tracks?q%5Bsearch%5D%5B%5D=happy+bouncy&limit=14&order=rolling_rank+DESC
            # strip and encode original status
            data = urlencode({"q": {"search": [status.text.replace("#marmomood", "")]}, "limit": 14, "order":"rolling_rank DESC"})
            response = requests.get(url + "?" + data)
            print("The response contains {0} properties".format(len(response.json())))
            if response.ok:
              print "OK"
              if response.json():
                api.update_status("Check out " + response.tracks[0].url + ", it might be just what you need right now!", status.id)
              else:
                api.update_status("Your search was so specific, I couldn't find anything. Please try again.", status.id)
            else:
              print "NOT OK"
              response.raise_for_status()

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
myStream.filter(track=['#marmomood'], async=True)
