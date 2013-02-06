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
Created on 09.12.2012

@author: karsten jeschkies <jeskar@web.de>

A small script which learns the LDA model on the reuters corpus.
'''

from corpus import R8Split
from database import FileDatabase
from gensim import utils, corpora, models

import logging
import sys

logger = logging.getLogger("py21578")

DEFAULT_DICT_SIZE = 50000
# No word which appear less then NO_BELOW times are kept 
NO_BELOW = 5
NO_ABOVE = 0.01
NUM_TOPICS = 50

class CleanCorpus(corpora.TextCorpus):
    '''
    Loads all articles from database.
    
    Stems all words and removes stop words. Tokenizes each document
    '''

    def __init__(self, db, no_below=NO_BELOW, keep_words=DEFAULT_DICT_SIZE, 
                 no_above = NO_ABOVE,
                 dictionary=None):
        '''
        See gensim.corpora.textcorpus for details.
        '''
        
        self.corpus = R8Split(db)
        
        if keep_words is None:
            keep_words = DEFAULT_DICT_SIZE
        if no_below is None:
            no_below = NO_BELOW
        
            
        if dictionary is None:
            self.dictionary = corpora.Dictionary(self.get_texts())
            self.dictionary.filter_extremes(no_below=no_below, 
                                            no_above=no_above, 
                                            keep_n=keep_words)
        else:
            self.dictionary = dictionary
            
    def get_texts(self):
        '''
        Files are processed parallel.
        
        See wikicorpus.py by Radim Rehurek
        '''
        logger = logging.getLogger("feature_extractor")
        
        processed_articles = 0
        for document in  self.corpus:
            if processed_articles % 1000 == 0:
                logger.info("Processing article #%d..." % processed_articles)
                
            processed_articles += 1
            
            try:
                tokens = utils.lemmatize(document)
                yield tokens
            except Exception as e:
                logger.error("Could not process article: %s" % e)
        
        logger.info("Processed %d articles." % processed_articles)

if __name__ == '__main__':
    from optparse import OptionParser
    
    p = OptionParser()
    p.add_option('-p', '--path', action="store", dest='path',
                 help="specify path to Reuters-21579 files")
    p.add_option('-l', '--log', action="store", dest='log',
                 help="specify log file")
    p.add_option('-o', '--output-prefix', action="store", dest='prefix',
                     help="specify path prefix where everything should be saved")
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
    
    #db = FileDatabase.load(database_path =  options.path + "/reuters.db")
    
    #Init clean corpus
    #corpus = CleanCorpus(db = db)
    
    #save dictionary: word <-> token id map
    #corpus.dictionary.save(options.prefix + "_wordids.dict")
    #corpus.dictionary.save_as_text(options.prefix + "_wordids.dict.txt")
    
    #del corpus
    
    '''Bag-of-Words'''
    
    #init corpus reader and word -> id map
    #id2token = corpora.Dictionary.load(options.prefix + "_wordids.dict")
    #new_corpus = CleanCorpus(db = db, dictionary = id2token)
    
    #create and save bow-representation of corpus
    #corpora.MmCorpus.serialize(options.prefix + '_bow_corpus.mm', new_corpus,
    #                           progress_cnt=1000)
    
    #del new_corpus
    
    #init corpus reader and word -> id map
    id2token = corpora.Dictionary.load(options.prefix + "_wordids.dict")
    mm_bow = corpora.MmCorpus(options.prefix + '_bow_corpus.mm')
    
    '''TFIDF Model creation'''
    
    #build tfidf model
    tfidf = models.TfidfModel(mm_bow, id2word=id2token, normalize=True)
    
    #save tfidf model
    tfidf.save(options.prefix + '_tfidf.model')
    
    #save corpus as tfidf vectors in matrix market format
    corpora.MmCorpus.serialize(options.prefix + '_tfidf_corpus.mm', 
                               tfidf[mm_bow], 
                               progress_cnt=1000)

    
    #init tfidf-corpus reader
    mm_tfidf = corpora.MmCorpus(options.prefix + '_tfidf_corpus.mm')
    
    '''LDA Model creation'''
    
    #build lda model
    lda = models.LdaModel(corpus=mm_tfidf, id2word=id2token, 
                          num_topics=NUM_TOPICS, update_every=1, 
                          chunksize=1000, passes=4) 
    
    #save trained model
    lda.save(options.prefix + '_lda_50.model')
    
    logger.info("finished transforming")