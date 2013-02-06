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
Created on 28.11.2012

@author: karsten

Learns the Cosine ESA Model with wikipedia corpus as concept corpus
on news articles or on the Reuters-21578 dataset
'''
from feature_extractor.esa.cosine_esamodel import CosineEsaModel, DocumentTitles
from feature_extractor.extractors import TfidfFeatureExtractor
from gensim import corpora, utils, matutils
import logging
from models.mongodb_models import (Article, RankedArticle, User, 
                                   ReadArticleFeedback)
from mongoengine import *
import numpy as np
from random import sample
from sets import Set
from smote import SMOTE, borderlineSMOTE
import sys
from utils.helper import load_config 

from corpus import R8Split
from database import InMemoryDatabase

UNREAD = 0
READ = 1

################################################################################
####### Helper Function for Article dataset ####################################

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
    
def get_article_samples(config_):
    #Connect to mongo database
    logger.info("Connect to database...")
    connect(config_['database']['db-name'], 
            username= config_['database']['user'], 
            password= config_['database']['passwd'], 
            port = config_['database']['port'])
    
    #get user
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
    
    return X, y

################################################################################
####### Helper Function for Reuters dataset ####################################

def get_features_from_clean_doc(feature_extractor, clean_doc):
    data = feature_extractor.get_features(clean_doc)
    return  matutils.sparse2full(data, feature_extractor.get_feature_number()) 

def get_reuters_samples(reuters_path, feature_extractor):
    
    #Create database
    db = InMemoryDatabase(reuters_path = reuters_path)
    
    samples = R8Split(db)
    
    logger.info("Convert training documents to feature space...")
    training_data = np.array(list(get_features_from_clean_doc(feature_extractor, doc)
                                  for doc
                                  in samples.training_data))
    
    training_target = np.array(list(target
                                    for target
                                    in samples.training_target))
    
    return training_data, training_target

################################################################################
####### Main ###################################################################

if __name__ == '__main__':
    from optparse import OptionParser
        
    p = OptionParser()
    p.add_option('-t', '--path', action="store", dest='tmp_path',
                     help="specify temporary path for shards")
    p.add_option('-o', '--output-prefix', action="store", dest='prefix',
                     help="specify path prefix where everything should be saved")
    p.add_option('-c', '--config', action="store", dest='config',
                 help="specify config file")
    p.add_option('-l', '--log', action="store", dest='log',
                 help="specify log file")
    (options, args) = p.parse_args()
    

    #Setup logging
    logger = logging.getLogger("gensim.models.esamodel")
    logger.setLevel(logging.DEBUG)
    
    # create file handler which logs even debug messages
    fh = logging.FileHandler(options.log)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s : %(levelname)s in %(module)s ' +
                                  '[%(pathname)s:%(lineno)d]: %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)
    
    logger.info("running %s" % ' '.join(sys.argv))
    
    #load config
    logger.info("Load config...")
    
    config_ = load_config(options.config, logger, exit_with_error = True)
    
    #init word -> id map
    id2token = corpora.Dictionary.load(options.prefix + "_wordids.dict")
    
    #init corpus reader
    mm_tfidf = corpora.MmCorpus(options.prefix + '_tfidf_corpus.mm')
    
    #load tfidf feature extractor
    extractor = TfidfFeatureExtractor(prefix = options.prefix)
    
    #document titles
    concept_titles = DocumentTitles.load(options.prefix + "_articles.txt")
    
    #load test articles
    logger.info("Load test articles...")
    
    #Get samples
    #X, y = get_article_samples(config_)
    X, y = get_reuters_samples(config_['reuters_path'], extractor)
    
    logger.info("Create Cosine ESA Model...")
    cesa = CosineEsaModel(mm_tfidf, concept_titles, 
                          X, y, len(y),
                          num_best_features = 1000,
                          num_features = len(id2token),
                          tmp_path = options.tmp_path)
    
    cesa.save(options.prefix + "_cesa.model")
    
    logger.info("...done.")