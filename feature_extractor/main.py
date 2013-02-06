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
import json
import logging
import socket
import sys
import time
from utils.daemon import Daemon
import stomp #needs to be after daemon for some reason
import yaml

"""
Receives news articles in a STOMP message from the feed crawler. 
Text features are then extracted based on a feature model learned in an offline
process. The articles are then send on to the article ranker.
"""

class StompListener(object):
    
    def __init__(self, config):
        self.config_ = config
        self.logger_ = logging.getLogger("main")
        
        self.extractor = EsaFeatureExtractor(prefix = config['prefix'])
 
    def __extract_features(self, message):
        '''
        Extracts features from clean content and sends it on
        '''

        self.logger_.debug("Got article '%s'" % message['headline'])

        features = self.extractor.get_features(message['clean_content'])
        version = self.extractor.get_version()
        
        #add features to json representation of article
        message['features'] = {'version': version, 
                               'data': features}
        
        #send message on to Article Ranker
        try:
            self.conn_.send(json.dumps(message), destination="queue/features")
        except Exception as inst:
            self.logger_.error("Could not send message to feature queue. "
                               "Unknown Error %s: %s" % (type(inst), inst))
    
    def on_error(self, hears, message):
        self.logger_ .error('received an error %s' % message)
        
    def on_message(self, headers, message):
        received_message = json.loads(message)
        self.__extract_features(received_message)
        
    def set_stomp_connection(self, connection):
        self.conn_ = connection
        
 
class FeatureExtractorDaemon(Daemon):
    
    def __init__(self, pidfile, config_file = None, log_file = None):
        
        logging.basicConfig(format='-' * 80 + '\n' +
                            '%(asctime)s : %(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
                            '%(message)s\n' +
                            '-' * 80,
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
        
        super(FeatureExtractorDaemon, self).__init__(pidfile)
    
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
                
                listener = StompListener(self.config_)
                
                conn = stomp.Connection()
                conn.set_listener('', listener)
                conn.start()
                conn.connect()
                
                conn.subscribe(destination='queue/rawarticles', ack='auto')
                connected = True
                
                listener.set_stomp_connection(conn)
                
            except stomp.exception.ConnectFailedException:
                if trys > 0:
                    pass
                else:
                    logger.error("Could not connect to STOMP broker")
                    sys.exit(1)
            except socket.error:
                pass
        
        if connected:
            logger.info("connected to STOMP broker")
            while True:
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
                 default='/tmp/daemon-feature-extractor.pid',
                 help="store the process id in the given file. Default is "
                 "/tmp/daemon-feature-extractor.pid")
    (options, args) = p.parse_args()
     
    daemon = FeatureExtractorDaemon(options.pidfile, options.config, options.log)
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
