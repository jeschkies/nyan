NYAN
====

NYAN is a news filtering engine written in Python and some Ruby.

It was mainly written for my master's thesis. You can find the details 
[here](http://www.blackmagiclabs.com/portfolio/work/master-thesis.html).

The filter is made up of several programs which pass messages to each other over 
STOMP. I used [CoilMQ](https://github.com/hozn/coilmq/) as a broker.

The *feed_crawler* crawls news sites for news articles.
The *feature_extractor* converts news articles to a gensim feature model.
The *article_ranker* ranks incoming news articles according to a learned user model.
The *user_model_trainer* captures the user's interests in a user model which is 
used by the *article_ranker*.

The programs can be easily used on their own.

The *frontend* is good for fast prototyping.

You should note that most code was written for academic purposes and was never 
used for commercially. Saving complete news articles might not be legal.


How to setup and usage
======================

Basically, the crawler, feature extractor, ranker have to be started. They use a 
config file to connect to the STOMP broker. You should read the corresponding chapter 
in my thesis paper to get the whole setup. 

The front end can be run on Apache with FastCGU. You can find a German how to 
[here](http://uberspace.de/dokuwiki/cool:flask#deployment_mit_fastcgi).

I used [daemontools](http://cr.yp.to/daemontools.html) to make each program a daemon. 
Some can be run a a daemon without daemontools. However, I don't recommend that.

For model training see shared_models/learn_on_articles.

Dependencies and Requirements
=============================

The system uses a MongoDB database.

All programs depend on several libraries. The following list might not be complete.

### feed_crawler
- nokogiri
- feedzirra
- log4r
- psych
- dbi
- stomp

### article_ranker, feature_extractor
- yaml
- gensim
- numpy, scipy
- stomp.py
- Scitkit-learn

### frontend
- flask
- flask-login plugin
- mongoengine



Licensing
=========
Most code is licensed under MIT License. 

Some code is taken from other libraries with different licenses. Such cases are marked.
