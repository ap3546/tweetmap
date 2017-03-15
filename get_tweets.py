'''
This script is supposed to run continuously along the app lifespan to catch
desired tweets from stream and push them into the elastic search engine.
'''
import tweepy
import random
import time

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection

import requests
import os.path
import json

# Variables that contains the user credentials to access Twitter API
access_token = "access_token"
access_token_secret = "access_token_secret"
consumer_key = "consumer_key"
consumer_secret = "consumer_secret"

kws = ["Trump", "ethereum", "bitcoin", "factom", "litecoin", "monero", "ripple", "zcash", "golem", "the"]

host = 'search-twittmap-gcds3wfs2vumozclk6my2anjda.us-east-1.es.amazonaws.com'
ind = 'twitter'
mapping_type = 'tweet'
AWS_ACCESS_KEY = "AWS_ACCESS_KEY"
AWS_SECRET_KEY = "AWS_SECRET_KEY"
REGION = "us-east-1"

awsauth = AWS4Auth(AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION, 'es')

es = Elasticsearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

class MyStreamListener(StreamListener):
    def on_data(self, data):
        if data:
            tweet = json.loads(data)
            try:
                if 'geo' in tweet and tweet['geo']:
                    for key in kws:
                        if key.lower() in tweet['text'].lower(): # not case-sensitive
                            tweet_data = {'keyword': key.lower()}
                            if 'coordinates' in tweet and tweet['coordinates']:
                                tweet_data['coordinates'] = tweet['coordinates']['coordinates']
                            else:
                                tweet_data['coordinates'] = None
                            if 'text' in tweet and tweet['text']:
                                tweet_data['text'] = tweet['text']
                            else:
                                tweet_data['text'] = None
                            if 'created_at' in tweet and tweet['created_at']:
                                tweet_data['timestamp'] = tweet['created_at']
                            else:
                                tweet_data['timestamp'] = None
                            if 'user' in tweet and tweet['user']:
                                tweet_data['author'] = tweet['user']['name']
                            else:
                                tweet_data['author'] = None

                            print tweet
                            es.index(index=ind, doc_type=mapping_type, id=tweet['id'], body=json.dumps(tweet_data))
                    return True

            except Exception as e:
                print("Error: " + str(e))
                return True
        return True

    def on_error(self, status_code):
        if status_code == 420:
            print "Error: Too many calls... need to sleep..."
            nsecs = random.randint(80, 100)
            time.sleep(nsecs)
        else:
            print "Err: " + str(status_code)
        return True

if __name__ == '__main__':
    listener = MyStreamListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    # defaults to False
    overwrite = False

    stream = Stream(auth, listener)

    with open('elastic_config.json') as f:
        try:

            mapping = json.dumps(json.load(f))

            if not es.indices.exists(index=ind):
                print es.indices.create(index=ind, body=mapping)

            if overwrite:
                print es.indices.delete(index=ind, ignore=[400, 404])
                print es.indices.create(index=ind, body=mapping)

            stream.filter(track=kws, locations=[-180, -90, 180, 90])
        except Exception as e:
            print "Error: " + str(e)