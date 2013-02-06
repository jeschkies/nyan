#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
The MIT License (MIT)
Copyright (c) 2012-2013 Karsten Jeschkies <jeskar@web.de>

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to use, 
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
Software, and to permit persons to whom the Software is furnished to do so, 
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

'''
Created on 19.09.2012

@author: karsten jeschkies <jeskar@web.de>

A small script which is used by other unit tests to fill a mongodb test database 
with data for testing.
'''

from datetime import datetime
import logging
from models.mongodb_models import *
from mongoengine import *

def clear_database():
    Vendor.objects().delete()
    User.objects().delete()
    Article.objects().delete()
    RankedArticle.objects().delete()
    Feedback.objects().delete()

def fill_database():
    #drop everything
    clear_database()
    
    #add vendors
    vendor = Vendor(name="TechCrunch", config = "vendor config")
    vendor.save()
    
    vendor2 = Vendor(name="AllThingsD", config = "vendor config 2")
    vendor2.save()
    
    #create features
    features = Features(version = '1.0')
    features.data = [(1, 0.4), (3, 0.6)]
    
    #add articles
    article1 = Article(vendor = vendor, url ="http://www.techcrunch.com", 
                      author ="MG Siegler",
                      clean_content = u"The good times can’t last forever.\
                                 Eventually the music dies off, the \
                                 balloons pop and everyone goes home.\
                                 Without sounding the hyperbole alarm,\
                                 let’s look at the facts. Apple’s stock \
                                 price has declined steadily since \
                                 September 19, two days before the iPhone 5 \
                                 was released. Shares are off 25 percent since \
                                 September. The stock price closed at a \
                                 six-month low today. The price is still \
                                 up 30 percent on the year but far from its \
                                 74 percent increase a few months back.",
                      content = u"The good times can’t last forever. \
                                 Eventually the music dies off, the \
                                 balloons pop and everyone goes home.\
                                 Without sounding the hyperbole alarm,\
                                 let’s look at the facts. Apple’s stock \
                                 price has declined steadily since \
                                 September 19, two days before the iPhone 5 \
                                 was released. Shares are off 25 percent since \
                                 September. The stock price closed at a \
                                 six-month low today. The price is still \
                                 up 30 percent on the year but far from its \
                                 74 percent increase a few months back.",
                      headline = u"Apple", date = datetime.now())
    article1.features = features
    article1.save()
    
    article2 = Article(vendor = vendor, url ="http://www.techcrunch.com", 
                      author =u"MG Siegler",
                      clean_content = u"It’s speedy, and for a streaming music \
                          service like Spotify making the jump from desktop \
                          software to the browser, that’s of the utmost \
                          importance. This is just an early beta of what will \
                          rollout next year, so I’ll forgive the missing \
                          features and say I was impressed with the feel. But \
                          discovery still has a long way to go to unlock the \
                          potential of near infinite music.",
                      content = u"<p>Apple rocks <i>again</i>!</p>",
                      headline = u"Spotify, too", date = datetime.now())
    article2.features = features
    article2.save()
    
    article3 = Article(vendor = vendor2, url ="http://www.allthingsd.com", 
                      author =u"MG Fake", 
                      clean_content = u"Sony makes a lot of really nice things, \
                          but it has never taken smartphones seriously. That’s \
                          to change if Sony Mobile’s sales chief, Dennis van \
                          Schie, is to be believed. Speaking to the Financial \
                          Times Deutschland, he basically acknowledged that \
                          Sony’s current phone lineup does not have a direct \
                          competitor to the iPhone or Galaxy S III. “We will \
                          create in the near future a flagship model that can \
                          compete with Apple’s iPhone and Samsung’s Galaxy S III,”\
                          he said. A spokeswomen also noted that the model will\
                          be available at CES and Mobile World Congress in the \
                          first part of 2013.",
                      content = u"<p>Apple sucks! ..bad</p>",
                      headline = u"Sony = Bad", date = datetime.now())
    article3.features = features
    article3.save()
    
    #add user
    user = User(name = u"Karsten Jeschkies", 
                password = u"88360b44f9cfc611dbb93f43770c54c56619677fc59dbfb45bb90dac004427f3",
                email = u"jeskar@web.de")
    
    #add subscription
    user.subscriptions.append(vendor)
    user.subscriptions.append(vendor2)
    user.save()
    
    #add rank articles
    ranked_article1 = RankedArticle(user_id= user.id, 
                                    article=article1, rating = 0.7)
    ranked_article1.save()
    
    ranked_article2 = RankedArticle(user_id= user.id,
                                    article=article2, rating = 0.4)
    ranked_article2.save()
    
    ranked_article3 = RankedArticle(user_id= user.id,
                                    article=article3, rating = 0.4)
    ranked_article3.save()
    
    #add feedback
    feedback1 = ReadArticleFeedback(user_id = user.id,
                                    article=article1, score = 1.0)
    feedback2 = ReadArticleFeedback(user_id = user.id, 
                                    article=article2, score = 1.0)
    
    feedback1.save()
    feedback2.save()
    #user.read_articles.append(feedback2)
    
    #add learned user profile
    user_model = UserModel(version = "1.0",
                           user_id = user.id,
                           data = features.data)
    user_model.save()
    
    #save
    user.save()

if __name__ == '__main__':
    
    connect("nyan_test")
    
    fill_database()
