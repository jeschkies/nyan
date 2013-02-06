#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Karsten Jeschkies <jeskar@web.de>

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
from feature_extractor.extractors import EsaFeatureExtractor
import logging
from models.mongodb_models import User
from mongoengine import *
import sys
from user_models import UserModelCentroid
from utils.helper import load_config
import yaml

"""
Learns a new user model when called.
"""

if __name__ == '__main__':
    from optparse import OptionParser
    
    p = OptionParser()
    p.add_option('-c', '--config', action="store", dest='config',
                 help="specify config file")
    p.add_option('-l', '--log', action="store", dest='log',
                 help="specify log file")
    
    (options, args) = p.parse_args()

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                            level=logging.DEBUG,
                            filename=options.log)
    
    #load config
    logger = logging.getLogger("main")
    logging.info("Load config")
    
    config_ = load_config(options.config, logger, exit_with_error = True)
        
    if config_ == None:
        logger.error("No config. Exit.")
        sys.exit(1)
        
    #Connect to mongo database
    connect(config_['database']['db-name'], 
            username= config_['database']['user'], 
            password= config_['database']['passwd'], 
            port = config_['database']['port'])
    
    feature_extractor = EsaFeatureExtractor(prefix = config_['prefix'])
    
    logger.info("Learn user model...")
    users = User.objects()
    for u in users:
        logger.info("for %s" % u.name)
        trainer = UserModelCentroid(user_id = u.id,
                                    extractor = feature_extractor)
        trainer.train()
        trainer.save()
    logger.info("...done.")
