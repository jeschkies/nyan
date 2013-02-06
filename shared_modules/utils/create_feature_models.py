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
Created on 22.11.2012

@author: karsten jeschkies <jeskar@web.de>
'''

from gensim import utils, corpora, models
import logging

#from esamodel import EsaModel, DocumentTitles
from utils.daemon import Daemon 
import sys

# Wiki is first scanned for all distinct word types (~7M). The types that appear
# in more than 10% of articles (supposedly stop words) are removed and 
# from the rest, the DEFAULT_DICT_SIZE most frequent types are kept. 
DEFAULT_DICT_SIZE = 50000

# No word which appear less then NO_BELOW times are kept 
NO_BELOW = 20

#Number of topics to create for lda model
NUM_TOPICS = 100
    
class ModelLearningDaemon(Daemon):

    def __init__(self, pidfile, log_file = None, prefix = None):
        
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                            level=logging.INFO,
                            filename= log_file)
        
        self.logger = logging.getLogger("feature_extractor")
        
        super(ModelLearningDaemon, self).__init__(pidfile) 
        
        self.prefix = prefix           
            

    def run(self):
        self.logger.info("Starting...")
        #corpus = CleanCorpus(options.doc_path)
        
        #save dictionary: word <-> token id map
        #corpus.dictionary.save(options.prefix + "_wordids.dict")
        #save(lambda path: corpus.dictionary.save(path), 
        #     options.prefix + "_wordids.dict")
        #corpus.dictionary.save_as_text(options.prefix + "_wordids.dict.txt")
        
        #del corpus
        
        '''Bag-of-Words'''
        
        #init corpus reader and word -> id map
        #id2token = corpora.Dictionary.load(options.prefix + "_wordids.dict")
        #new_corpus = CleanCorpus(options.doc_path, dictionary = id2token)
        
        #create and save bow-representation of corpus
        #corpora.MmCorpus.serialize(options.prefix + '_bow_corpus.mm', new_corpus,
        #                         progress_cnt=10000)
        
        #save article names
        #new_corpus.save_article_names(options.prefix + "_articles.txt")
        
        #new_corpus.load_article_names(options.prefix + "_articles.txt")
        
        #del new_corpus
        
        #init corpus reader and word -> id map
        id2token = corpora.Dictionary.load(self.prefix + "_wordids.dict")
        #mm_bow = corpora.MmCorpus(options.prefix + '_bow_corpus.mm')
        
        '''TFIDF Model creation'''
        
        #build tfidf model
        #tfidf = models.TfidfModel(mm_bow, id2word=id2token, normalize=True)
        
        #save tfidf model
        #tfidf.save(options.prefix + '_tfidf.model')
        
        #save corpus as tfidf vectors in matrix market format
        #corpora.MmCorpus.serialize(options.prefix + '_tfidf_corpus.mm', tfidf[mm_bow], 
        #                           progress_cnt=10000)
    
        
        #init tfidf-corpus reader
        mm_tfidf = corpora.MmCorpus(self.prefix + '_tfidf_corpus.mm')
        
        '''LDA Model creation'''
        
        #build lda model
        lda = models.LdaModel(corpus=mm_tfidf, id2word=id2token, 
                              num_topics=NUM_TOPICS, update_every=1, 
                              chunksize=10000, passes=2) 
        
        #save trained model
        lda.save(self.prefix + '_lda.model')
        
        #save corpus as lda vectors in matrix market format
        #corpora.MmCorpus.serialize(options.prefix + '_lda_corpus.mm', lda[mm_tfidf], 
        #                           progress_cnt=10000)
        
        #init lda-corpus reader
        #mm_lda = corpora.MmCorpus(options.prefix + '_lda_corpus.mm')
        
        '''ESA Model creation'''
        
        #document titles
        #article_titles = DocumentTitles.load(options.prefix + "_articles.txt")
        
        #build esa model
        #esa = EsaModel(mm_lda, num_clusters = 10000, 
        #                       document_titles = article_titles,
        #                       num_features = NUM_TOPICS)
        
        #esa.save(options.prefix + "_esa_on_lda.model")
        
        self.logger.info("finished transforming")

if __name__ == "__main__":
    from optparse import OptionParser
    
    p = OptionParser()
    p.add_option('-o', '--output-prefix', action="store", dest='prefix',
                     help="specify path prefix where everything should be saved")
    p.add_option('-d', action="store_true", dest='daemonize',
                 help="run the server as a daemon")
    p.add_option('-l', '--log', action="store", dest='log',
                 help="specify log file")
    p.add_option('-p', '--pidfile', dest='pidfile', 
                 default='/tmp/daemon-article-ranker.pid',
                 help="store the process id in the given file. Default is "
                 "/tmp/daemon-article-ranker.pid")
    (options, args) = p.parse_args()
     
    daemon = ModelLearningDaemon(options.pidfile, 
                                 options.log,
                                 options.prefix)
    if len(sys.argv) >= 2:
            if 'start' == sys.argv[1]:
                if not options.log:
                    print "No logfile set."
                    sys.exit(2)
                elif options.daemonize:
                    daemon.start()
                else:
                    daemon.run()
            elif 'stop' == sys.argv[1]:
                    daemon.stop()
            elif 'restart' == sys.argv[1]:
                if not options.log:
                    print "No logfile set."
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
