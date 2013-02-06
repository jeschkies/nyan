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
Created on 19.10.2012

@author: karsten jeschkies <jeskar@web.de>

Converts features of article from TFIDF to ESA Model
'''
from feature_extractor.extractors import EsaFeatureExtractor
from gensim import utils, corpora, models 
import logging
from models.mongodb_models import (Article, Features)
from mongoengine import *
from mongoengine import connection, queryset
import sys
from utils.helper import load_config

if __name__ == '__main__':
    from optparse import OptionParser
        
    p = OptionParser()
    p.add_option('-c', '--config', action="store", dest='config',
                     help="specify path to config file")
    (options, args) = p.parse_args()
    
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
    logging.root.setLevel(level=logging.INFO)
    
    logger = logging.getLogger("main")
    
    logger.info("Load config from %s" % options.config)
    config = load_config(options.config, logger, exit_with_error = True)
    
    #Connect to mongo database
    try:
        connect(config['database']['db-name'], 
                username= config['database']['user'], 
                password= config['database']['passwd'], 
                port = config['database']['port'])
    except connection.ConnectionError as e:
        logger.error("Could not connect to mongodb: %s" % e)
        sys.exit(1)
    
    
    feature_extractor = EsaFeatureExtractor(prefix = config['prefix'] )
    
    #go through each article and convert features
    count = 0
    for article in Article.objects(features__version__ne = feature_extractor.get_version()):
        if count % 10 == 0:
            logger.info("PROGRESS: processing article #%d" % count)
        count += 1
        
        if article.features.version == EsaFeatureExtractor.get_version():
            continue
        
        clean_content = article.clean_content
        
        #get new features
        new_features = feature_extractor.get_features(clean_content)
        
        #save new features
        features = Features(version = feature_extractor.get_version(), data = new_features)
        article.features = features
        try:
            article.save()
        except queryset.OperationError as e:
            logger.error("Could not save article #%d: %s" % (count, e))