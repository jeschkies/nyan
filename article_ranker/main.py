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

from article_ranker import ArticleRanker
from datetime import datetime
from feature_extractor.extractors import EsaFeatureExtractor
import json
import logging
from models.mongodb_models import Vendor, User, Article
from mongoengine import *
import socket
import stomp
import sys
import time
from daemon import Daemon
import yaml

"""
The Article Ranker receives messages via STOMP from the Feature Extractor.

The messages include article details, the content and the extracted features.
Articles will be saved to database and ranked for each user. They will be marked
as top articles if their rank is high enough.
"""

logger = logging.getLogger("main")

class StompListener(object):
    
    def __init__(self, config):
        self.config_ = config
        
        #Connect to mongo database
        try:
            connect(config['database']['db-name'], 
                    username= config['database']['user'], 
                    password= config['database']['passwd'], 
                    port = config['database']['port'])
        except ConnectionError as e:
            logger.error("Could not connect to mongodb: %s" % e)
            sys.exit(1)
        
        logger.info("Load feature extractor.")
        try:
            self.feature_extractor_ = EsaFeatureExtractor(prefix = self.config_["prefix"])
        except Exception as inst:
            logger.error("Could not load feature extractor."
                         "Unknown error %s: %s" % (type(inst), inst))
            sys.exit(1)
        
        self.ranker = ArticleRanker(extractor = self.feature_extractor_)        
            
    def rank_article(self, article_as_dict):
        self.ranker.rank_article(article_as_dict)
            
    def on_error(self, hears, message):
        logger.error('received an error %s' % message)
        
    def on_message(self, headers, message):        
        received_message = json.loads(message)
        
        #save and rank article
        self.rank_article(received_message)
        
class ArticleRankerDaemon(Daemon):
    
    def __init__(self, pidfile, config_file = None, log_file = None):
        
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                            level=logging.DEBUG,
                            filename= log_file)
        try:
            if config_file != None:
                stream = file(config_file, 'r')
                self.config_ = yaml.load(stream)
                stream.close()
            else:
                self.config_ = None
        except IOError as e:
            print "Could not open %s: %s" % (config_file, e)
            sys.exit(1)
        except Exception as inst:
            print "Unknown error %s: %s" % (type(inst), inst)
            sys.exit(1)
        
        super(ArticleRankerDaemon, self).__init__(pidfile)            
            
    def run(self):

        logger = logging.getLogger("main")
        
        if self.config_ == None:
            logger.error("No config.")
            sys.exit(1)
        
        hosts = [('localhost', 61613)]
        
        connected = False
        trys = 5
        while not connected:
            try:
                trys = trys-1
                
                conn = stomp.Connection()
                conn.set_listener('', StompListener(self.config_))
                conn.start()
                conn.connect()
                
                conn.subscribe(destination='queue/features', ack='auto')
                connected = True
            except stomp.exception.ConnectFailedException:
                if trys > 0:
                    pass
                else:
                    logger.error("Could not connect to STOMP broker")
                    sys.exit(1)
            except socket.error:
                pass
        
        if connected:
            logger.info("Connected to STOMP broker")
            while 1:
                time.sleep(20)
        
if __name__ == "__main__":
    from optparse import OptionParser
    
    p = OptionParser()
    p.add_option('-c', '--config', action="store", dest='config',
                 help="specify config file")
    p.add_option('-d', action="store_true", dest='daemonize',
                 help="run the server as a daemon")
    p.add_option('-l', '--log', action="store", dest='log',
                 help="specify log file")
    p.add_option('-p', '--pidfile', dest='pidfile', 
                 default='/tmp/daemon-article-ranker.pid',
                 help="store the process id in the given file. Default is "
                 "/tmp/daemon-article-ranker.pid")
    (options, args) = p.parse_args()
     
    daemon = ArticleRankerDaemon(options.pidfile, options.config, options.log)
    if len(sys.argv) >= 2:
            if 'start' == sys.argv[1]:
                if not options.config or not options.log:
                    print "No config or logfile set."
                    sys.exit(2)
                elif options.daemonize:
                    daemon.start()
                else:
                    daemon.run()
            elif 'stop' == sys.argv[1]:
                    daemon.stop()
            elif 'restart' == sys.argv[1]:
                if not options.config or not options.log:
                    print "No config or logfile set."
                    sys.exit(2)
                else:
                    daemon.restart()
            else:
                print "Unknown command"
                sys.exit(2)
            sys.exit(0)
    else:
            print "usage: %s start|stop|restart options" % sys.argv[0]
            sys.exit(2)
