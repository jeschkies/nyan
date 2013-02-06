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
Created on 12.12.2012

@author: karsten jeschkies <jeskar@web.de>

Converts R8 split of Reuters-21578 corpus and saves it to numpy array
'''
from corpus import R8Split
from database import FileDatabase
from feature_extractor.extractors import (LdaFeatureExtractor,
                                          LdaBowFeatureExtractor,
                                          TfidfFeatureExtractor,
                                          cEsaFeatureExtractor)
from feature_extractor.esa.cosine_esamodel import CosineEsaModel
from gensim import utils, corpora, models, matutils
import logging
import numpy as np
import sys

logger = logging.getLogger("py21578")

def get_features(feature_extractor, doc):
    data = feature_extractor.get_features(doc)
    return  matutils.sparse2full(data, feature_extractor.get_feature_number()) 

def train_data(feature_extractor, samples):
    logger.info("Convert training documents to feature space...")
    training_data = np.array(list(get_features(feature_extractor, doc)
                                  for doc
                                  in samples.training_data))
    
    return training_data

def test_data(feature_extractor, samples):
    logger.info("Convert test documents to feature space and predict...")
    test_data = np.array(list(get_features(feature_extractor, doc)
                              for doc
                              in samples.test_data))
    
    return test_data

if __name__ == '__main__':
    from optparse import OptionParser
    
    p = OptionParser()
    p.add_option('-p', '--path', action="store", dest='path',
                 help="specify path to Reuters-21579 files")
    p.add_option('-l', '--log', action="store", dest='log',
                 help="specify log file")
    p.add_option('-o', '--prefix', action="store", dest='prefix',
                     help="specify path prefix to find models etc.")
    (options, args) = p.parse_args()
    
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
    
    #Load Reuters-21578 dataset
    if options.path is None:
        logger.error("Path to Reuters-21578 dataset not set.")
        sys.exit(1) 
        
    #Load feature models and extractor
    #feature_extractor = LdaBowFeatureExtractor(prefix = options.prefix)
    #feature_extractor = LdaFeatureExtractor(prefix = options.prefix)
    feature_extractor = cEsaFeatureExtractor(prefix = options.path + '/models/cesa_on_reuters/wiki')
    
    #Load database, training and test data
    db = FileDatabase.load(options.path + '/reuters.db')
    split = R8Split(db)
    
    training_data = train_data(feature_extractor, split)
    test_data = test_data(feature_extractor, split)
        
    # store training and test data
    np.save(options.path + '/training_data_cesa.npy', training_data)
    np.save(options.path + '/test_data_cesa.npy', test_data)
    
    logger.info("done.")