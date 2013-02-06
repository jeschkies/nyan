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
Created on 23.11.2012

@author: karsten jeschkies <jeskar@web.de>
'''

from cosine_esamodel import CosineEsaModel, DocumentTitles
from feature_extractor.extractors import (EsaFeatureExtractor, 
                                          TfidfFeatureExtractor,
                                          LdaFeatureExtractor)
from gensim import utils, matutils
from gensim.corpora import Dictionary, MmCorpus
from gensim.models import tfidfmodel
import itertools
import logging
from models.mongodb_models import (Article, Features, User, UserModel, 
                                   RankedArticle, ReadArticleFeedback)
from mongoengine import *
import numpy as np
import unittest 
from utils.helper import load_config
from random import sample
from sets import Set
from smote import SMOTE, borderlineSMOTE
import sys

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

test_corpus_texts = [['graph', 'minors', 'eps'],
               ['human', 'system', 'computer'],
               ['user', 'system', 'human']
               ]
test_corpus = [dictionary.doc2bow(text) for text in test_corpus_texts]

UNREAD = 0
READ = 1

def get_features(article, extractor):
    '''
    Reaturns full features vector from article.
    Article should be a mongodb model
    '''
    #check if features of article are current version
    try:
        feature_version = article.features.version
    except AttributeError as e:
        if str(e) == 'features':
            logger.error("Article %s does not have any features." % 
                         article.id)
            #article seems not to exist anymore go on
            raise 
         
    if feature_version != extractor.get_version():
        clean_content = article.clean_content
            
        #get new features
        features = extractor.get_features(clean_content)
    else:
        features = article.features.data
    
    #sparse2full converts list of 2-tuples to numpy array
    article_features_as_full_vec = matutils.sparse2full(features, 
                                                        extractor.get_feature_number())
    
    return article_features_as_full_vec

def get_samples(extractor,
                read_article_ids, 
                unread_article_ids,
                p_synthetic_samples = 300,
                p_majority_samples = 500,
                k = 5):
    '''
    read_article_ids : Set
    unread_article_ids : Set
    n_synthetic_samples : Percentage of snythetic samples, 300 for 300%
    k : neighbourhood for k nearest neighbour, standard 5

    Returns
    -------
    array-like full vector samples, shape = [n_features, n_samples]
    array-like marks, shape = [n_samples]
    '''
    
    #Under-sample unread ids
    unread_article_ids = Set(sample(unread_article_ids, 
                                    min(p_majority_samples/100 * len(read_article_ids), 
                                        len(unread_article_ids))
                                    )
                             )
    
    #Create unread article vectors
    unread_marks = np.empty(len(unread_article_ids))
    unread_marks.fill(UNREAD)
    unread_articles = np.empty(shape=(len(unread_article_ids), 
                                         extractor.get_feature_number()))
    
    
    for i, article in enumerate(Article.objects(id__in = unread_article_ids)):
        try:
            article_features_as_full_vec = get_features(article, extractor)
            unread_articles[i,:] = article_features_as_full_vec[:]
        except AttributeError as e:
            logger.error("Article %s does not have attribute: %s." 
                         % (article.id, e))  
            
    #Create read article vectors
    read_marks = np.empty(len(read_article_ids))
    read_marks.fill(READ)  
    read_articles = np.empty(shape=(len(read_article_ids), 
                                         extractor.get_feature_number()))
    
    for i, article in enumerate(Article.objects(id__in = read_article_ids)):
        try:
            article_features_as_full_vec = get_features(article, extractor)
            read_articles[i,:] = article_features_as_full_vec[:]
        except AttributeError as e:
            logger.error("Article %s does not have attribute: %s." 
                         % (article.id, e))           
    
    #SMOTE sample minorities
    #synthetic_read_articles = SMOTE(read_articles, p_synthetic_samples, k) 
    
    #borderlineSMOTE sample minorites
    X = np.concatenate((read_articles, unread_articles)) 
    y = np.concatenate((read_marks, unread_marks))
    new_read_articles, synthetic_read_articles, danger_read_articles = borderlineSMOTE(X = X,
                                                                                    y = y,
                                                                                    minority_target = READ,
                                                                                    N = p_synthetic_samples, k = k)
    
    #Create synthetic read samples
    synthetic_marks = np.zeros(len(synthetic_read_articles))
    synthetic_marks.fill(READ)  
    
    read_marks = np.empty(len(new_read_articles))
    read_marks.fill(READ)  
    
    danger_read_marks = np.empty(len(danger_read_articles))
    danger_read_marks.fill(READ)   
    
    logger.info("Use %d read, %d unread, %d danger reads and %d synthetic samples." %
                (len(read_marks), len(unread_marks), 
                 len(danger_read_marks), len(synthetic_marks)))
    
    return (np.concatenate((new_read_articles, 
                              synthetic_read_articles, 
                              danger_read_articles,
                              unread_articles)),
            np.concatenate((read_marks, 
                              synthetic_marks, 
                              danger_read_marks,
                              unread_marks))
            )

class TestCosineESAModel(unittest.TestCase):


    def setUp(self):
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                        level=logging.DEBUG)
        
        self.config_ = load_config(("/media/sdc1/Aptana Studio 3 Workspace/"
                                    "configs/config.yaml"), 
                                   logger, 
                                   exit_with_error = True)
        
        if self.config_ == None:
            logger.error("No config. Exit.")
            sys.exit(1)

    def tearDown(self):
        pass


    @unittest.skip("Skip small test")
    def test_constructor(self):
        #create tf-idf model
        tfidf_model = tfidfmodel.TfidfModel(corpus, normalize=True)
        
        #transform corpus
        tfidf_corpus = tfidf_model[corpus]
        
        #train esa model
        esa_model = CosineEsaModel(tfidf_corpus,
                                   document_titles = concepts,
                                   test_corpus = test_corpus, 
                                   test_corpus_targets = [1,2,2],
                                   num_test_corpus = 3,
                                   num_best_features = 2, 
                                   num_features = len(dictionary))
        
        test_doc = ['graph', 'minors', 'trees']#['user', 'computer', 'time']#
        tfidf_test_doc = tfidf_model[dictionary.doc2bow(test_doc)]
        
        #transform test doc to esa
        esa_test_doc = esa_model[tfidf_test_doc]
        
        print esa_test_doc
        #for concept_id, weight in sorted(esa_test_doc, key=lambda item: -item[1]):
        #    print "%s %.3f" % (esa_model.document_titles[concept_id], weight)
         
    #@unittest.skip("Skip bigger test") 
    def test_constructor_with_file_wikicorpus(self):
        
        #load tf-idf model
        tfidf_model = tfidfmodel.TfidfModel.load("/media/sdc1/test_dump/result/test_tfidf.model")
        extractor = TfidfFeatureExtractor("/media/sdc1/test_dump/result/test")
        
        #load tf-idf corpus
        tfidf_corpus = MmCorpus('/media/sdc1/test_dump/result/test_tfidf_corpus.mm')
        
        #load lda corpus
        #lda_corpus = MmCorpus('/media/sdc1/test_dump/result/test_lda_corpus.mm')
        
        #load dictionary
        id2token = Dictionary.load("/media/sdc1/test_dump/result/test_wordids.dict")
        
        #load article titles
        document_titles = DocumentTitles.load("/media/sdc1/test_dump/result/test_articles.txt")
        
        #Connect to mongo database
        connect(self.config_['database']['db-name'], 
                username= self.config_['database']['user'], 
                password= self.config_['database']['passwd'], 
                port = self.config_['database']['port'])
        
        #Load articles as test corpus
        user = User.objects(email=u"jeskar@web.de").first()
        
        ranked_article_ids = (a.article.id 
                              for a 
                              in RankedArticle.objects(user_id = user.id).only("article"))
        all_article_ids = Set(a.id 
                              for a 
                              in Article.objects(id__in = ranked_article_ids).only("id"))
        
        read_article_ids = Set(a.article.id 
                               for a 
                               in ReadArticleFeedback.objects(user_id = user.id).only("article"))
        
        unread_article_ids = all_article_ids - read_article_ids

        #sample test articles
        X, y = get_samples(extractor, read_article_ids, unread_article_ids)
        
        s,f = X.shape
        logger.debug("Traning with %d samples, %d features, %d marks" % 
                     (s,f, len(y)))

        #train esa model
        esa_model = CosineEsaModel(tfidf_corpus, 
                                   document_titles = document_titles,
                                   test_corpus = X, 
                                   test_corpus_targets = y, 
                                   num_test_corpus = len(y),
                                   num_best_features = 15,
                                   num_features = len(id2token))
        
        print esa_model
        
        esa_model.save('/media/sdc1/test_dump/result/test_cesa.model')
        
        tmp_esa = CosineEsaModel.load('/media/sdc1/test_dump/result/test_cesa.model') 
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
        
        esa_model.save('/media/sdc1/test_dump/result/wiki_cesa.model')
        
        tmp_esa = EsaModel.load('/media/sdc1/test_dump/result/wiki_cesa.model') 
        print tmp_esa  
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()