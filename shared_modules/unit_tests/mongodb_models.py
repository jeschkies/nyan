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
Created on 06.09.2012

@author: karsten jeschkies <jeskar@web.de>
'''

from datetime import datetime
import logging
from models.mongodb_models import *
from mongoengine import *
import time
import unittest

logger = logging.getLogger("unittesting")

#Connect to test database
connect("nyan_test", port = 20545)

class UserFetchCase(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                        level=logging.DEBUG)
        
        #Fill Database
        #If adding works is checked in tests
        
        #add user
        karsten = User(name = "Karsten Jeschkies", email = "jeskar2@web.de",
                       password= "1234")
        karsten.save()

    def tearDown(self):
        #remove user
        karsten = User.objects(name = "Karsten Jeschkies")
        karsten.delete(safe=True)    

    def test_fetch_user(self):
        #karsten aus datenbank holen
        karsten = User.objects(name = "Karsten Jeschkies").first()
        
        self.assertIsNotNone(karsten)

    def test_fail_find(self):
        no_user = User.objects(name="not found").first()

        self.assertIsNone(no_user)
        
class VendorFetchCase(unittest.TestCase):
    
    def setUp(self):
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                            level=logging.DEBUG)
        
        #Fill Database
        #If adding works is checked in tests
        
        #add vendor
        vendor = Vendor(name="techcrunch", config="vendor config")
        vendor.save()
        
    def tearDown(self):
        vendor = Vendor.objects(name = "techcrunch")
        vendor.delete(safe=True)
        
    def test_fetch_vendor(self):
        techcrunch = Vendor.objects(name = "techcrunch").first()
        
        self.assertIsNotNone(techcrunch)
        
    def test_fail_find(self):
        no_vendor = Vendor.objects(name = "not found").first()
        
        self.assertIsNone(no_vendor)
        
class ArticleFetchCase(unittest.TestCase):
    
    def setUp(self):
        #add vendor
        vendor = Vendor(name="techcrunch", config="vendor config")
        vendor.save()
        
        #create features
        features = Features(version = '1.0')
        features.data = [(1, 0.5), (3, 0.6)]
        
        #add article
        article = Article(vendor = vendor, url ="http://www.techcrunch.com", 
                          author ="MG Siegler", clean_content = "Apple rocks!",
                          date = datetime.now())
        article.features = features
        article.save()
        self._id = article.id
        
    def tearDown(self):
        Vendor.objects(name="techcrunch").delete()
        Article.objects(author="MG Siegler").delete()
        
    def test_fetch_article(self):
        article = Article.objects(id = self._id).first()
        
        self.assertIsNotNone(article)
        self.assertIsNotNone(article.features)
        self.assertEqual(article.features.version, '1.0')
        
    def test_fetch_by_date(self):
        time.sleep(3)
        articles = Article.objects(date__lt=datetime.now())
        
        self.assertGreaterEqual(len(articles), 1)
        
    def test_features_data(self):
        article = Article.objects(id = self._id).first()
        
        #Tuples are converted to lists by mongodb
        self.assertEqual([[1, 0.5], [3, 0.6]], article.features.data)
        
class SubscriptionsTestCase(unittest.TestCase):
    
    def setUp(self):
        
        #add vendor
        vendor = Vendor(name="techcrunch", config="vendor config")
        vendor.save()
        
        #create features
        features = Features(version = '1.0')
        features.data = [(1, 0.5), (3, 0.6)]
        
        #add article
        article = Article(vendor = vendor, url ="http://www.techcrunch.com", 
                          author ="MG Siegler", clean_content = "Apple rocks!")
        article.features = features
        article.save()
        
        #add user
        karsten = User(name = "Karsten Jeschkies", email = "jeskar@web.de",
                       password= "1234")
        karsten.save()
        
        #add subscription
        karsten.subscriptions.append(vendor)
        karsten.save()
        
    def tearDown(self):
        Vendor.objects().delete()
        User.objects().delete()
        
    def test_fetch_subscriptions(self):
        user = User.objects(name="Karsten Jeschkies").first()
        
        vendor = Vendor.objects(name="techcrunch").first()
        
        self.assertIsNotNone(user)
        self.assertEqual(len(user.subscriptions), 1)
        self.assertEqual(vendor.id, user.subscriptions[0].id)
        
    def test_add_and_remove_subscription(self):
        vendor = Vendor.objects(name="techcrunch").first()
        
        new_vendor = Vendor(name="mashable")
        new_vendor.save()
        
        User.objects(name="Karsten Jeschkies").update_one(add_to_set__subscriptions=new_vendor)
        
        #retrieve user from db to see if new_vendor was saved
        user = User.objects(name="Karsten Jeschkies").first()
        
        self.assertIn(new_vendor, user.subscriptions)
        
        #remove new_vendor
        User.objects(name="Karsten Jeschkies").update_one(pull__subscriptions=new_vendor)
        
        user.reload()
        
        self.assertNotIn(new_vendor, user.subscriptions)
        self.assertIn(vendor, user.subscriptions)
        
    def test_get_article_for_subscription(self):
        user = User.objects(name="Karsten Jeschkies").first()
        
        articles = Article.objects(vendor__in=user.subscriptions)
        
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].author, "MG Siegler")
        
class FeedbackTestCase(unittest.TestCase):
    
    def setUp(self):
        
        #add article
        article = Article(url ="http://www.techcrunch.com", 
                          author ="MG Siegler", clean_content = "Apple rocks!")
        article.save()
        
        #add user
        user = User(name = "Karsten Jeschkies", password="1234", 
                    email="jeskar@web.de")
        user.save()
        
        #add feedbakc
        feedback = ReadArticleFeedback(user_id = user.id, 
                                       article=article, score = 1.0)
        feedback.save()
        
    def tearDown(self):
        Article.objects().delete()
        User.objects().delete()
        Feedback.objects().delete()
        
    def test_get_feedback(self):
        user = User.objects(name="Karsten Jeschkies").first()
        feedback = ReadArticleFeedback.objects(user_id = user.id)
        
        self.assertEqual(feedback[0].score, 1.0)
        
class RenkedArticlesTestCase(unittest.TestCase):
    
    def setUp(self):
        user = User(name="Karsten Jeschkies", password="1234",
                    email="jeskar@web.de")
        user.save()
        
        #ranked article 1
        ranked_article_1 = RankedArticle(user_id = user.id, rating=0.6)
        ranked_article_1.save()
        
        #ranked article 2
        ranked_article_2 = RankedArticle(user_id = user.id, rating=0.4)
        ranked_article_2.save()
        
    def tearDown(self):
        User.objects().delete()
        RankedArticle.objects().delete()
        
    def test_get_top_ranked_articles(self):
        user = User.objects(name="Karsten Jeschkies").first()
        
        top_articles = (a.rating for a in RankedArticle.objects(user_id = user.id) if a.rating > 0.5)
        
        self.assertIn(0.6, top_articles)     
        
class UserTestCase(unittest.TestCase):
    
    def setUp(self):
        
        user = User(name="Karsten Jeschkies", email="jeskar@web.de", 
                    password ="1234")        
        user.save()
        
        learned_profile = UserModel()
        learned_profile.data = [(1, 0.5), (3, 0.6)]
        learned_profile.version='1.0'
        learned_profile.user_id = user.id
        learned_profile.save()
        
    def tearDown(self):
        User.objects().delete()
        
    def test_get_learned_profile(self):
        user = User.objects(name="Karsten Jeschkies").first()
        learned_profile = UserModel.objects(user_id = user.id).first()
        
        self.assertIn([1, 0.5], learned_profile.data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
