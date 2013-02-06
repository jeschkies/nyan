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

Unittests for the implementation of the ESA model.

The tests are not complete and were used for debugging.
'''

from esamodel import EsaModel, DocumentTitles
from gensim.corpora import Dictionary, MmCorpus
from gensim.models import tfidfmodel
import logging
import unittest 

logger = logging.getLogger("unittesting")

# set up vars used in testing ("Deerwester" from the web tutorial)
texts = [['human', 'interface', 'computer'], #human interface
 ['survey', 'user', 'computer', 'system', 'response', 'time'], #computer systems
 ['eps', 'user', 'interface', 'system'], #eps
 ['system', 'human', 'system', 'eps'], #human systems
 ['user', 'response', 'time'], #response time
 ['trees'], #trees
 ['graph', 'trees'], #graph
 ['graph', 'minors', 'trees'], #minor tress
 ['graph', 'minors', 'survey']] #minors survey
dictionary = Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]
concepts = ['human interface', 'computer systems', 'eps', 'human systems',
            'response time', 'tress', 'graph', 'minors tress', 'minors survey']

class TestESAModel(unittest.TestCase):


    def setUp(self):
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                        level=logging.DEBUG)

    def tearDown(self):
        pass


    @unittest.skip("Skip small test")
    def test_constructor(self):
        #create tf-idf model
        tfidf_model = tfidfmodel.TfidfModel(corpus, normalize=True)
        
        #transform corpus
        tfidf_corpus = tfidf_model[corpus]
        
        #train esa model
        esa_model = EsaModel(tfidf_corpus, num_clusters = 9, 
                             document_titles = concepts,
                             num_features = len(dictionary))
        
        print "%s\n" % str(esa_model)
        
        test_doc = ['user', 'computer', 'time']
        tfidf_test_doc = tfidf_model[dictionary.doc2bow(test_doc)]
        
        #transform test doc to esa
        esa_test_doc = esa_model[tfidf_test_doc]
        
        for concept_id, weight in sorted(esa_test_doc, key=lambda item: -item[1]):
            print "%s %.3f" % (esa_model.document_titles[concept_id], weight)
         
    #@unittest.skip("Skip bigger test") 
    def test_constructor_with_file_wikicorpus(self):
        
        #load tf-idf corpus
        tfidf_corpus = MmCorpus('/media/sdc1/test_dump/result/test_tfidf_corpus.mm')
        
        #load lda corpus
        #lda_corpus = MmCorpus('/media/sdc1/test_dump/result/test_lda_corpus.mm')
        
        #load dictionary
        id2token = Dictionary.load("/media/sdc1/test_dump/result/test_wordids.dict")
        
        #load article titles
        document_titles = DocumentTitles.load("/media/sdc1/test_dump/result/test_articles.txt")

        #train esa model
        esa_model = EsaModel(tfidf_corpus, num_clusters = 15, 
                             document_titles = document_titles,
                             num_features = len(id2token))
        
        print esa_model
        
        esa_model.save('/media/sdc1/test_dump/result/wiki_esa.model')
        
        tmp_esa = EsaModel.load('/media/sdc1/test_dump/result/wiki_esa.model') 
        print tmp_esa  
        
    @unittest.skip("too big")
    def test_constructor_with_big_file_wikicorpus(self):
        
        #load tf-idf corpus
        tfidf_corpus = MmCorpus('/media/sdc1/test_dump/result/wiki_tfidf_corpus.mm')
        
        #load lda corpus
        #lda_corpus = MmCorpus('/media/sdc1/test_dump/result/test_lda_corpus.mm')
        
        #load dictionary
        id2token = Dictionary.load("/media/sdc1/test_dump/result/wiki_wordids.dict")
        
        #load article titles
        document_titles = DocumentTitles.load("/media/sdc1/test_dump/result/wiki_articles.txt")

        #train esa model
        esa_model = EsaModel(tfidf_corpus, num_clusters = 15, 
                             document_titles = document_titles,
                             num_features = len(id2token))
        
        print esa_model
        
        esa_model.save('/media/sdc1/test_dump/result/wiki_esa.model')
        
        tmp_esa = EsaModel.load('/media/sdc1/test_dump/result/wiki_esa.model') 
        print tmp_esa  
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()