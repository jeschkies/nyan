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
Created on 22.11.2012

@author: karsten jeschkies <jeskar@web.de>
'''
from feature_extractor.extractors import (EsaFeatureExtractor, 
                                          TfidfFeatureExtractor, 
                                          LdaFeatureExtractor)
import logging
import unittest
from utils.helper import load_config

logger = logging.getLogger("unittesting")

class LDAFeatureExtractorTest(unittest.TestCase):


    def setUp(self):
        self.config = load_config(file_path = "/home/karten/Programmierung/frontend/config.yaml",
                             logger = logger,
                             exit_with_error = True)


    def tearDown(self):
        pass


    def test_get_feature_number(self):
        feature_extractor = LdaFeatureExtractor(prefix = self.config['prefix'])
        
        num_topics = feature_extractor.get_feature_number()
        self.assertEqual(500, num_topics)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()