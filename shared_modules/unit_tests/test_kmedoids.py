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
@author: Karsten Jeschkies <jeskar@web.de>

The unittests are not complete.
'''
from kmedoids import KMedoids
from gensim.corpora import Dictionary, MmCorpus
from gensim.models import tfidfmodel
import logging
from profilehooks import profile
import unittest 

logger = logging.getLogger("unittesting")

class TestKMedoids(unittest.TestCase):


    def setUp(self):
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                        level=logging.DEBUG)

    def tearDown(self):
        pass
    
    @profile
    def get_kmedoids(self, corpus, num_features, num_clusters, max_iterations):
        return KMedoids(corpus = corpus, num_features = num_features,
                            num_clusters = num_clusters, 
                            max_iterations = max_iterations)
    
    @profile
    def cluster(self, clusterer):
        return clusterer.cluster()

    def test_cluster(self):
        
        #load tf-idf corpus
        tfidf_corpus = MmCorpus('/media/sdc1/test_dump/result/test_tfidf_corpus.mm')
        
        #load dictionary
        id2token = Dictionary.load("/media/sdc1/test_dump/result/test_wordids.dict")
        
        kmedoids = self.get_kmedoids(tfidf_corpus, len(id2token), 
                                 num_clusters = 15,
                                 max_iterations = 5)
        clusters = self.cluster(kmedoids)

        print clusters
      
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()