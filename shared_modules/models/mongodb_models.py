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

"""
@author karsten jeschkies <jeskar@web.de>

Definitions of all MongoDB models used by the news filterer and its programs.
"""

from mongoengine import *


class Vendor(Document):
    name = StringField()
    url = StringField()
    feed_url = StringField()
    config = StringField()

class Features(EmbeddedDocument):
    version = StringField()
    data = DynamicField()

class Article(Document):
    vendor = ReferenceField(Vendor)
    url = URLField()
    author = StringField()
    headline = StringField()
    clean_content = StringField()
    content = StringField()
    features = EmbeddedDocumentField(Features)
    date = DateTimeField() #the date the article was saved
    
    meta = {
            'indexes': ['date']
            }

class RankedArticle(Document):
    '''
    Defines a ranked article for user with ObjectId == user_id.
    user_id is not a reference.
    '''
    user_id = ObjectIdField()
    article = ReferenceField(Article)
    rating = FloatField()
    
    meta = {
            'indexes': ['user_id']
            }
    
class Feedback(Document):
    '''
    User feedback. Can be:
    - a read article
    - a deleted article (not implemented)
    - a starred article (not implemented)
    '''
    article = ReferenceField(Article)
    user_id = ObjectIdField()
    
    meta = {
            'indexes': ['user_id']
            }
    
class ReadArticleFeedback(Feedback):
    '''
    User intrinsic feedback.
    Indicates that the article was read by user with ObjectId == user_id
    score is a float calculated from reading time indicating importance of 
    article (not implemented).
    '''
    score = FloatField()

    
class UserModel(Document):
    '''
    The learnt user model...
    '''
    user_id = ObjectIdField()
    version = StringField()
    data = DynamicField()
    
    meta = {
            'indexes': ['user_id']
            }

class User(Document):
    '''
    User credentials saved in database.
    
    password is a sha256 hashed hexdigest
    
    Ranked and feedback articles are saved in their own collections.
    '''
    email = StringField(required=True)
    name = StringField()
    password = StringField(required=True)
    subscriptions = ListField(ReferenceField(Vendor))
    
    meta = {
            'indexes': ['email']
            }
