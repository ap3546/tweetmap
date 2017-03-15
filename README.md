# Cryptocurreny Tweetmap with Trends

The goal of this project was to gain experience developing and deploying a web application using AWS Cloud services.
The web application collects tweets from a live stream and processes them to display certain tweets, that contain keywords, on GoogleMaps.

In this project, we used the Twitter Streaming API to fetch tweets from the twitter hose in real-time.
Then we used AWS ElasticSearch to store the tweets on the backend and query them efficiently.
A web UI allows users to search for a few keywords to filter tweets and render them in the map.
The website is deployed on AWS Elastic Beanstalk in an auto-scaling environment.
As a bonus, we used ElasticSearch’s geospatial feature that shows tweets that are within a 300km radius from the point the user clicks on the map.
The app was developed in Python with Flask.