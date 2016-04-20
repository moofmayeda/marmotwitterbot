#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import tweepy, requests, json, inspect, urllib
from multidimensional_urlencode import urlencode
from configobj import ConfigObj
from random import randint

config = ConfigObj('config.txt')
auth = tweepy.OAuthHandler(config['CONSUMER_KEY'], config['CONSUMER_SECRET'])
auth.set_access_token(config['ACCESS_KEY'], config['ACCESS_SECRET'])
api = tweepy.API(auth)
myUserID = api.me().id
url = config['BASE_URL'] + "/filter_tracks"
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
    self.url = config['BASE_URL'] + "/browse/" + str(id)

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
      if search_params:
        data = urlencode({"q": search_params, "limit": 14, "order":"rolling_rank DESC"})
        response = requests.get(url + "?" + data)
        if response.ok:
          if response.json():
            # if genre match found, send to genre page rather than track page?
            # energies browse?energy=Low-Medium|Medium
            # genres ?genres=Country+Spiritual
            # mood search=%20Ethereal
            # combo ?energy=Medium|Low-Medium&arc=ascending&instruments=Banjo+Strings&genres=Country+Spiritual
            api.update_status("Check out " + response.tracks()[0].url + ", it might be just what you need right now!", status.id)
          else:
            get_random_tracks(status)
        else:
          print "NOT OK"
          response.raise_for_status()
      else:
        data = urlencode({"q": {"search": [status.text.replace("#marmomood", "")]}, "limit": 14, "order":"rolling_rank DESC"})
        response = requests.get(url + "?" + data)
        if response.ok:
          if response.json():
            api.update_status("Check out " + response.tracks[0].url + ", it might be just what you need right now!", status.id)
          else:
            get_random_tracks(status)
        else:
          response.raise_for_status()

def get_random_tracks(status):
  data = urlencode({"limit": 10, "order":"rolling_rank DESC"})
  response = requests.get(url + "?" + data)
  if response.ok:
    if response.json():
      api.update_status("I couldn't find anything like that. Why don't you check out " + response.tracks()[randint(0,9)].url + ", it's one of our hottest songs right now!", status.id)
    else:
      api.update_status("Your search was so specific, I couldn't find anything. Please try again.", status.id)
  else:
    response.raise_for_status()

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
myStream.filter(track=['#marmomood'], async=True)
