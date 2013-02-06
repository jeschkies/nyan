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
from feature_extractor.extractors import EsaFeatureExtractor, TfidfFeatureExtractor
from naive_bayes import GaussianNB
from user_models import UserModelCentroid, UserModelBayes, UserModelSVM
from FillTestDatabase import fill_database, clear_database
import logging
from models.mongodb_models import Article,  User, UserModel
from mongoengine import *
import numpy as np
import unittest
from utils.helper import load_config

logger = logging.getLogger("unittesting")

class UserModelCentroidTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                            level=logging.DEBUG)
            
        
        config = load_config(file_path = "/home/karten/Programmierung/frontend/config.yaml",
                                  logger = logger,
                                  exit_with_error = True)
        
        #Connect to test database
        connect("nyan_test", port = 27017)
        fill_database()
        #connect(config['database']['db-name'], 
        #        username= config['database']['user'], 
        #        password= config['database']['passwd'], 
        #        port = config['database']['port'])

        self.user_id = User.objects(email = u'jeskar@web.de').first().id
        
        #self.feature_extractor = EsaFeatureExtractor(prefix = config['prefix'])
        self.feature_extractor = TfidfFeatureExtractor(prefix = config['prefix'])
        self.trainer = UserModelCentroid(self.user_id,
                                         extractor = self.feature_extractor)

    def tearDown(self):
        clear_database()

    @unittest.skip("not for now")
    def test_train(self):
        self.trainer.train()
        
        self.assertAlmostEqual(self.trainer.learned_user_models_data[0][1], 
                               0.1553, 4)
        
    @unittest.skip("no saving yet")
    def test_save(self):
        self.trainer.train()
        self.trainer.save()
        
        user_model = UserModel.objects(user_id = self.user_id).first()
        
        self.assertAlmostEqual(user_model.data[0][1], 
                               0.0021, 4)    
        
class NaiveBayesTest(unittest.TestCase):
    
    def setUp(self):
        self.X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])
        self.Y = np.array([1, 1, 1, 2, 2, 2])
        
    def tearDown(self):
        pass
    
    @unittest.skip("working")
    def test_with_array(self):
        clf = GaussianNB()
        clf.fit(self.X, self.Y)
        result = clf.predict([[-0.8, -1]])
        
        self.assertEqual(result, [1])
        
    @unittest.skip("working")
    def test_with_generator(self):
        tmpX = (sample for sample in self.X)
        
        clf = GaussianNB()
        clf.fit(tmpX, self.Y)
        result = clf.predict([[-0.8, -1]])
        
        self.assertEqual(result, [1])      
        
class UserModelBayesTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                            level=logging.DEBUG)
            
        
        config = load_config(file_path = "/home/karten/Programmierung/frontend/config.yaml",
                             logger = logger,
                             exit_with_error = True)
        
        #Connect to test database
        connect("nyan_test", port = 27017)
        fill_database()
        #connect(config['database']['db-name'], 
        #        username= config['database']['user'], 
        #        password= config['database']['passwd'], 
        #        port = config['database']['port'])

        self.user_id = User.objects(email = u'jeskar@web.de').first().id
        #feature_extractor = EsaFeatureExtractor(prefix = config['prefix'])
        feature_extractor = TfidfFeatureExtractor(prefix = config['prefix'])
        self.trainer = UserModelBayes(self.user_id, extractor = feature_extractor)

    def tearDown(self):
        clear_database()
    
    @unittest.skip("training")
    def test_save_load(self):
        self.trainer.train()
        
        tmp_classifier = self.trainer.clf
        
        self.trainer.save()
        self.trainer.load()
        
        self.assertEqual(tmp_classifier.sigma_.all(),
                         self.trainer.clf.sigma_.all())  
        self.assertEqual(tmp_classifier.theta_.all(),
                         self.trainer.clf.theta_.all()) 
    
    @unittest.skip("training")
    def test_get_unread(self):
        unread_articles = self.trainer._get_unread()
        
        headlines = [a.headline for a in unread_articles]

        self.assertIn(u"Apple = Bad", headlines)
        self.assertNotIn(u"Apple", headlines)
        self.assertEqual(len(headlines), 1)
     
    @unittest.skip("ranking")
    def test_rank(self):
        self.trainer.train()
        
        unread_doc = Article.objects(headline = u"Sony = Bad").first()
        read_doc = Article.objects(headline = u"Apple").first()
        
        rank_unread_doc = self.trainer.rank(unread_doc)
        rank_read_doc = self.trainer.rank(read_doc)
        
        self.assertEqual(rank_unread_doc, UserModelBayes.UNREAD) 
        self.assertEqual(rank_read_doc, UserModelBayes.READ) 
        
class UserModelSVMTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                            level=logging.DEBUG)
            
        
        config = load_config(file_path = ("/media/sdc1/Aptana Studio 3 Workspace"
                                          "/configs/config.yaml"),
                             logger = logger,
                             exit_with_error = True)
        
        #Connect to test database
        connect("nyan_test", port = 20545)
        fill_database()
        #connect(config['database']['db-name'], 
        #        username= config['database']['user'], 
        #        password= config['database']['passwd'], 
        #        port = config['database']['port'])

        self.user_id = User.objects(email = u'jeskar@web.de').first().id
        #feature_extractor = EsaFeatureExtractor(prefix = config['prefix'])
        feature_extractor = TfidfFeatureExtractor(prefix = config['prefix'])
        self.trainer = UserModelSVM(self.user_id, extractor = feature_extractor)

    def tearDown(self):
        clear_database()
        
    def test_mean_std_deviation(self):
        X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [3, 0], [3, 2]])
        
        self.trainer._calculate_mean_and_std_deviation(X)
        
        self.assertAlmostEqual(self.trainer.theta_[0], 0.16666, 4)
        self.assertAlmostEqual(self.trainer.theta_[1], -0.16666, 4)
        self.assertAlmostEqual(self.trainer.sigma_[0], 2.33927, 4)
        self.assertAlmostEqual(self.trainer.sigma_[1], 1.3437, 4)
        
    def test_normalize(self):
        X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [3, 0], [3, 2]])
        
        self.trainer.theta_ = np.array([1, -2], dtype=np.float32)
        self.trainer.sigma_ = np.array([2, 1], dtype=np.float32)
        X = self.trainer._normalize(X)
        
        self.assertEqual(X[1,0], -1.5)
        
    def test_normalize_no_theta(self):
        X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [3, 0], [3, 2]])
        
        self.assertRaises(AttributeError, lambda: self.trainer._normalize(X))
        
        #dummy set theta_ but not sigma_
        self.trainer.theta_ = np.array([1, -2], dtype=np.float32)
        
        self.assertRaises(AttributeError, lambda: self.trainer._normalize(X))
        
    def test_save_load_theta_sigma(self):
        X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [3, 0], [3, 2]])
        
        self.trainer._calculate_mean_and_std_deviation(X)
        
        self.trainer.clf = "dummy"
        
        tmp_theta = self.trainer.theta_
        tmp_sigma = self.trainer.sigma_
        
        self.trainer.save()
        self.trainer.load()
        
        #Check normalization parameters
        self.assertEqual(tmp_theta.all(),
                         self.trainer.theta_.all()) 
        self.assertEqual(tmp_sigma.all(),
                         self.trainer.sigma_.all()) 
        
    @unittest.skip("No ranking implemented yet")
    def test_rank(self):
        self.trainer.train()
        
        unread_doc = Article.objects(headline = u"Sony = Bad").first()
        read_doc = Article.objects(headline = u"Apple").first()
        
        rank_unread_doc = self.trainer.rank(unread_doc)
        rank_read_doc = self.trainer.rank(read_doc)
        
        self.assertEqual(rank_unread_doc, UserModelBayes.UNREAD) 
        self.assertEqual(rank_read_doc, UserModelBayes.READ) 

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()