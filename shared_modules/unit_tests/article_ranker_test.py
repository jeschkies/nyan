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
Created on 20.09.2012

@author: karsten jeschkies <jeskar@web.de>
'''
from article_ranker import ArticleRanker 
from feature_extractor.extractors import EsaFeatureExtractor
from FillTestDatabase import fill_database, clear_database
import logging
from models.mongodb_models import *
from mongoengine import *
import unittest
from utils.helper import load_config

logger = logging.getLogger("unittesting")

#Connect to test database
connect("nyan_test", port = 20545)

class ArticleRankerTest(unittest.TestCase):


    def setUp(self):
        fill_database()
        config_ = load_config(file_path = "/media/sdc1/Aptana Studio 3 Workspace/configs/config.yaml",
                              logger = logger)
        self.feature_extractor = EsaFeatureExtractor(prefix = config_['prefix'])
        self.ranker = ArticleRanker(extractor = self.feature_extractor)
        self.article_as_dict = {'news_vendor': 'TechCrunch', 
                                'author': "MG Siegler",
                                'link': "http://www.techcrunch.com",
                                'headline': "Again Apple",
                                'clean_content': "Fooobaaar!",
                                'content': "<p>Fooobaaar!</p>",
                                'features': {'version': '1.0',
                                            'data': [(1, 0.5),
                                                     (3, 0.6)
                                                    ]
                                            }
                                }

    def tearDown(self):
        clear_database()

    def test_get_vendor_false(self):
        vendor = self.ranker.get_vendor({'news_vendor': 'not in db'})
        
        self.assertEqual(vendor, None)
        
    def test_get_vendor(self):
        vendor = self.ranker.get_vendor(self.article_as_dict)

        self.assertEqual(vendor.config, 'vendor config')
        
    def test_save_article_false(self):
        vendor = self.ranker.get_vendor(self.article_as_dict)  
        stored_article = self.ranker.save_article(vendor, 
                                                  {'headline': "Everything else is missing."})
        
        self.assertEqual(stored_article, None)
        
    def test_save_article(self): 
        vendor = self.ranker.get_vendor(self.article_as_dict)  
        stored_article = self.ranker.save_article(vendor, self.article_as_dict)
        
        self.assertEqual(stored_article.author, 'MG Siegler')
        
    def test_save_rating(self):
        vendor = self.ranker.get_vendor(self.article_as_dict)  
        stored_article = self.ranker.save_article(vendor, self.article_as_dict)
        user = User.objects(name = "Karsten Jeschkies").first()
        self.ranker.save_rating(user=user, article = stored_article, rating = 1.0)
        
        user.reload()
        ranked_articles = RankedArticle.objects(user_id = user.id)
        self.assertEqual(3, ranked_articles.count())
        self.assertEqual(1.0, ranked_articles[0].rating) 

    def test_rank_article(self):
        pass
        #some error in genism. probably because some features are not quite right
        self.ranker.rank_article(self.article_as_dict)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()