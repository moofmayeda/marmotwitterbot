#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import tweepy, requests, json, inspect, urllib, os
from multidimensional_urlencode import urlencode
from random import randint

auth = tweepy.OAuthHandler(os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET'])
auth.set_access_token(os.environ['ACCESS_KEY'], os.environ['ACCESS_SECRET'])
api = tweepy.API(auth)
url = os.environ['BASE_URL'] + "/filter_tracks"
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
    self.title = title.rstrip()
    self.url = os.environ['BASE_URL'] + "/browse/" + str(id)

  def display_title(self, max):
    return self.title if len(self.title) <= max else self.title[:(max-3)] + "..."

def tweet_random_result(status):
  data = urlencode({"limit": 10, "order":"rolling_rank DESC"})
  response = requests.get(url + "?" + data)
  if response.ok:
    if response.json():
      random_track = random.choice(response.tracks())
      message = '''@{0} I couldn't find that. Why don't you check out "{1}," it's one of our hottest songs: {2}'''.format(status.user.screen_name, random_track.title, shorten_url(random_track.url))
      api.update_status(shorten_message(message, random_track), in_reply_to_status_id = status.id)
    else:
      message = "@{0} your search was so specific, I couldn't find anything. Please try again.".format(status.user.screen_name)
      api.update_status(message, in_reply_to_status_id = status.id)
  else:
    response.raise_for_status()

def tweet_positive_result(response, status, search_params):
  random_track = random.choice(response.tracks())
  message = '''@{0} have you heard "{1}," it might be just what you need: {2}'''.format(status.user.screen_name, random_track.title, shorten_url(build_search_url(search_params)))
  api.update_status(shorten_message(message, random_track), in_reply_to_status_id = status.id)

def shorten_url(longUrl):
  response = requests.get("https://api-ssl.bitly.com/v3/shorten?access_token=" + os.environ['BITLY_TOKEN'] + "&longUrl=" + urllib.quote_plus(longUrl) + "&format=txt")
  return response.content.rstrip()

def shorten_message(message, track):
  length = len(message.replace(track.title, ""))
  return message.replace(track.title, track.display_title(140-length))

def build_search_url(search_params):
  result = ""
  for k, v in search_params.items():
    result += "&" + k + "=" if k != 'mood' else "&" + "search" + "="
    if k == 'arc':
      result += "+".join([w.lower() for w in v])
    elif k == 'energy':
      result += "|".join(v)
    else:
      result += "+".join(v)
  return os.environ['BASE_URL'] + "/browse?" + result[1:]

#override tweepy.StreamListener to add logic to on_status
class MyStreamListener(tweepy.StreamListener):

  def on_status(self, status):
    search_params = {}
    for word in status.text.split(" "):
      results = [k for k, v in dict.iteritems() if word.capitalize() in v]
      if results:
        search_params.setdefault(results[0], []).append(word.capitalize())
    if search_params:
      data = urlencode({"q": search_params, "limit": 5, "order":"rolling_rank DESC"})
      response = requests.get(url + "?" + data)
      if response.ok:
        if response.json():
          tweet_positive_result(response, status, search_params)
        else:
          tweet_random_result(status)
      else:
        response.raise_for_status()
    else:
      search_params['search'] = [status.text.replace("#marmomood", "")]
      data = urlencode({"q": search_params, "limit": 1, "order":"rolling_rank DESC"})
      response = requests.get(url + "?" + data)
      if response.ok:
        if response.json():
          tweet_positive_result(response, status, search_params)
        else:
          tweet_random_result(status)
      else:
        response.raise_for_status()

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
myStream.filter(track=['#marmomood'], async=True)
