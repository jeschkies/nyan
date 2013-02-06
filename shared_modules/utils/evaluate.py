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
Created on 12.11.2012

@author: karsten jeschkies <jeskar@web.de>

Evaluates different feature and user model combinations using precision, recall
and f1-score.

                 predicted as
             
               |   unread   |   read
        -------------------------------
        read   |            |
reality unread |            |
'''
from __future__ import division
from feature_extractor.extractors import (EsaFeatureExtractor, 
                                          TfidfFeatureExtractor,
                                          LdaFeatureExtractor,
                                          LdaBowFeatureExtractor,
                                          cEsaFeatureExtractor)
import logging
from models.mongodb_models import (Article, Features, User, UserModel, 
                                   RankedArticle, ReadArticleFeedback)
from mongoengine import *
import numpy as np
from random import sample
from sets import Set
from sklearn import metrics
import sys
from user_models import (UserModelBayes, UserModelCentroid, 
                         UserModelSVM, UserModelMeta, UserModelTree)
from utils.helper import load_config

logger = logging.getLogger("main")

#-------------------------------------------------------------------------------
#Helper Functions
#-------------------------------------------------------------------------------

    
if __name__ == '__main__':
    from optparse import OptionParser
    
    p = OptionParser()
    p.add_option('-c', '--config', action="store", dest='config',
                 help="specify config file")
    p.add_option('-l', '--log', action="store", dest='log',
                 help="specify log file")
    
    (options, args) = p.parse_args()

    logging.basicConfig(format='%(asctime)s : %(levelname)s in %(module)s ' +
                               '[%(pathname)s:%(lineno)d]:%(message)s', 
                        level=logging.DEBUG,
                        filename=options.log)
    
    #load config
    logger.info('#' * 80 + '\nStart evaluation')
    logger.info("Load config...")
    
    config_ = load_config(options.config, logger, exit_with_error = True)
    N_ITERATIONS = 10
        
    if config_ == None:
        logger.error("No config. Exit.")
        sys.exit(1)
        
    #Connect to mongo database
    connect(config_['database']['db-name'], 
            username= config_['database']['user'], 
            password= config_['database']['passwd'], 
            port = config_['database']['port'])
    
    #Load feature extractor
    #feature_extractor = EsaFeatureExtractor(prefix = config_['prefix'])
    #feature_extractor = TfidfFeatureExtractor(prefix = config_['prefix'])
    #feature_extractor = LdaFeatureExtractor(prefix = config_['prefix'])
    #feature_extractor = LdaBowFeatureExtractor(prefix = config_['prefix'])
    feature_extractor = cEsaFeatureExtractor(prefix = config_['prefix'])
    
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

    for p_synthetic in xrange(100, 700, 100):
        for p_majority in xrange(100, 700, 100): 
            
            logger.info("Synthetic over-sampling %d and majority undersampling %d" %
                        (p_synthetic, p_majority))
            
            #run test N_ITERATIONS
            precisions_read = np.zeros((N_ITERATIONS))
            recalls_read = np.zeros((N_ITERATIONS))
            f1_scores_read = np.zeros((N_ITERATIONS))
            precisions_unread = np.zeros((N_ITERATIONS))
            recalls_unread = np.zeros((N_ITERATIONS))
            f1_scores_unread = np.zeros((N_ITERATIONS))
            
            predicted_interesting = np.zeros((N_ITERATIONS))
            actual_of_predicted_interesting = np.zeros((N_ITERATIONS))
            for iteration in xrange(N_ITERATIONS):
                #undersample unread articles
                #unread_article_ids = Set(sample(unread_article_ids, len(read_article_ids)))
        
                #get ids for evaluation
                evaluation_set_unread = Set(sample(unread_article_ids,200))
                evaluation_set_read = Set(sample(read_article_ids, 10))
                
                #get rest for training
                training_set_unread = unread_article_ids - evaluation_set_unread    
                training_set_read = read_article_ids - evaluation_set_read
                
                #Print trainings read articles
                #read_article_headlines = list()
                #for article_id in training_set_read:
                #    article = Article.objects(id = article_id).first()
                #    if article is None: continue
                #    read_article_headlines.append(article.headline)

                #logger.info("Training articles: %s" 
                #            % " | ".join(read_article_headlines))
                
                #logger.info(("Trainingset: %d (read: %d, unread: %d)." 
                #             "Evaluationset: %d (read: %d, unread: %d).") %
                #            (len(training_set_read)+len(training_set_unread), 
                #             len(training_set_read), 
                #             len(training_set_unread),
                #             len(evaluation_set_read)+len(evaluation_set_unread), 
                #             len(evaluation_set_read), 
                #             len(evaluation_set_unread)))
                
                #learn on subset
                #user_model = UserModelBayes(user_id = user.id,
                #                            extractor = feature_extractor)
                
                #user_model = UserModelCentroid(user_id = user.id,
                #                               extractor = feature_extractor)
                
                user_model = UserModelSVM(user_id = user.id,
                                          extractor = feature_extractor)
                
                #user_model = UserModelTree(user_id = user.id,
                #                           extractor = feature_extractor)
                user_model.set_samples_sizes(p_synthetic, p_majority)
                #user_model.set_samples_sizes(p_synthetic_samples = None, 
                #                             p_majority_samples = None)
                
                #user_model = UserModelMeta(user_id = user.id,
                #                           extractor = feature_extractor)
                
                user_model.train(read_article_ids = training_set_read, 
                                 unread_article_ids = training_set_unread)
                
                #Set y_true
                y_true = np.empty(shape=(len(evaluation_set_read) + len(evaluation_set_unread)))
                y_true[:len(evaluation_set_read)] = user_model.READ
                y_true[len(evaluation_set_read):] = user_model.UNREAD
                
                #Set y_pred
                y_pred = np.empty(shape=(y_true.shape[0]))
                predicted_insteresting_headlines = list()
                actual_interesting_headlines = list()
                
                #predict with other subset and record measures
                for i, article_id in enumerate(evaluation_set_read):
                    article = Article.objects(id = article_id).first()
                    if article is None: continue
                    
                    #Predict and record result
                    result = user_model.rank(doc = article)
                    y_pred[i] = result
                    
                    #Redcord headline
                    if result == user_model.READ:
                        actual_interesting_headlines.append(article.headline)
                        
                    actual_interesting_headlines.append(article.headline)
            
                for i, article_id in enumerate(evaluation_set_unread, start = len(evaluation_set_read)):
                    article = Article.objects(id = article_id).first()
                    if article is None: continue
                    
                    #Predict and record result
                    result = user_model.rank(doc = article)
                    y_pred[i] = result
                
                    
                #calculate precision, recall and f1 score
                precisions, recalls, f1_scores, _ = metrics.precision_recall_fscore_support(y_true, 
                                                                                            y_pred, 
                                                                                            pos_label = user_model.READ)
                    
                #add score etc.
                predicted_interesting[iteration] = np.sum(y_pred == user_model.READ)
                actual_of_predicted_interesting[iteration] = np.sum(y_pred[y_true == user_model.READ] == user_model.READ)
                
                precisions_read[iteration] = precisions[0]
                recalls_read[iteration] = recalls[0]
                f1_scores_read[iteration] = f1_scores[0]
                
                precisions_unread[iteration] = precisions[1]
                recalls_unread[iteration] = recalls[1]
                f1_scores_unread[iteration] = f1_scores[1]
                
                #logger.debug("Predicted interesting headlines: %s." %
                #             " | ".join(predicted_insteresting_headlines))
                #logger.debug("Predicted and actual interesting headlines: %s." %
                #             " | ".join(actual_interesting_headlines))
                
            #Average scores
            precision_read = np.mean(precisions_read)
            recall_read = np.mean(recalls_read)
            f1_score_read = np.mean(f1_scores_read)
            
            precision_unread = np.mean(precisions_unread)
            recall_unread = np.mean(recalls_unread)
            f1_score_unread = np.mean(f1_scores_unread)
            
            interesting = np.mean(predicted_interesting)
            actual_of_predicted = np.mean(actual_of_predicted_interesting) 
            
            #Output
            logger.info(("An average of %d articles were predicted as interesting." 
                         "\nAn average of %d are actual interesting.") % 
                        (interesting, actual_of_predicted))
            logger.info("Read: Precision %.5f, Recall %.5f, F1-Score: %.5f" % 
                        (precision_read, recall_read, f1_score_read))
            logger.info("Unread: Precision %.5f, Recall %.5f, F1-Score: %.5f" % 
                        (precision_unread, recall_unread, f1_score_unread))
