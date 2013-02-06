#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modified by in 2012 by Karsten Jeschkies <jeskar@web.de>

Some implementations are taken from wikicorpus.py by
Copyright (C) 2010 Radim Rehurek <radimrehurek@seznam.cz>
Copyright (C) 2012 Lars Buitinck <larsmans@gmail.com>

Licensed under the GNU LGPL v2.1 - http://www.gnu.org/licenses/lgpl.html

This is an implementation of a gensim.corpus to work on wikipedia articles where
each article is in one text file. The first line has to be the article's title.
"""

import errno
import exceptions
from gensim import utils, corpora, models
import itertools
import logging

from esamodel import EsaModel, DocumentTitles

from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

import multiprocessing

import os
import sys

# Wiki is first scanned for all distinct word types (~7M). The types that appear
# in more than 10% of articles (supposedly stop words) are removed and 
# from the rest, the DEFAULT_DICT_SIZE most frequent types are kept. 
DEFAULT_DICT_SIZE = 50000

# No word which appear less then NO_BELOW times are kept 
NO_BELOW = 20

#Number of topics to create for lda model
NUM_TOPICS = 500

class CleanDocument(object):
    """
    Takes a document as a string.
    
    Tokenzies documents and stems document words.
    Does not removes stops because all stop words will be removed later when
    the dictionary is filtered.
    
    Resulting document will be a list of tokens.
    
    Needs to be converted with dictionary.
    """
    
    def __init__(self, document):
        '''
        :param document: A string with the content of the document.
        '''
        
        #use pattern lemmatizer. see gensim.utils.lemmatizer. 
        #Note: len(words) < 15 are filtered out
        self.clean_document_ = utils.lemmatize(document)
        
    def get(self):
        return self.clean_document_
    
    def __iter__(self):
        '''
        Iters through words of document.
        '''
        
        for word in self.clean_document_:
            yield word

def process_file_path(file_path):
    with open(file_path, "r") as file:
        #last character is a breaking /n
        article_name = file.readline()[:-1]
        
        #remaining lines is doc
        doc = " ".join(file.readlines())
        
        lemmatized_doc = utils.lemmatize(doc)
        
        return (article_name, lemmatized_doc)

class CleanCorpus(corpora.TextCorpus):
    '''
    Loads all documents in a directory from a file system. Each file in a dir 
    is regarded as a document. It should be a texfile.
    
    The first line is the article name.
    
    Stems all words and removes stop words. Tokenizes each document
    '''

    def __init__(self, fname, no_below=NO_BELOW, keep_words=DEFAULT_DICT_SIZE, 
                 dictionary=None):
        '''
        See gensim.corpora.textcorpus for details.
        
        :param fnam: The path to scan for documents.
        '''
        
        self.fname = fname
        self.article_names = []
        if keep_words is None:
            keep_words = DEFAULT_DICT_SIZE
        if no_below is None:
            no_below = NO_BELOW
              
        self.file_paths = [os.path.join(self.fname, name) for name in os.listdir(self.fname) 
                            if os.path.isfile(os.path.join(self.fname, name))]
        
        self.processes = 2
        
        #each file is considered an article
        self.total_articles = len(self.file_paths)
            
        if dictionary is None:
            self.dictionary = corpora.Dictionary(self.get_texts())
            self.dictionary.filter_extremes(no_below=no_below, no_above=0.1, 
                                            keep_n=keep_words)
        else:
            self.dictionary = dictionary
            
    def get_texts(self):
        '''
        Files are processed parallel.
        
        See wikicorpus.py by Radim Rehurek
        '''
        logger = logging.getLogger("feature_extractor")
        
        logger.info("Scanning %d files." % self.total_articles)
        
        articles_processed = 0

        pool = multiprocessing.Pool(self.processes)
        
        for group in  utils.chunkize_serial(self.file_paths, 
                                            chunksize=10*self.processes):
            for article_name, tokens in pool.imap(process_file_path, group):
                articles_processed += 1
                try:
                    name = article_name.strip("\n").decode("UTF-8")
                except UnicodeDecodeError as e:
                    logger.error("Could not decode %s: %s" % (article_name, e))
                    exit(1) 
                self.article_names.append(name)
                yield tokens
        
        pool.terminate()
        
        logger.info("Processed %d articles." % articles_processed)
                
    def save_article_names(self, file_path):
        logger.info("Saving article names to %s" % file_path)
        with open(file_path, "wb") as fout:
            for name in self.article_names:
                fout.write("%s\n" % name.encode("UTF-8"))
                
    def load_article_names(self, file_path):
        logger.info("Loading article names from %s" % file_path)
        
        #clear old list
        self.article_names[:] = []
        with open(file_path, "r") as file:
            for line in file:
                article_name = line.strip("\n").decode("UTF-8")
                self.article_names.append(article_name)

def save(save_func, path):
    try:
        save_func(path)
    except IOError as e:
        logger.error("Could not save to %s: %s" % (path, e))
        answer = raw_input("Do you want to try with a different path? (yes/no)")
        if answer != "yes":
            raise e
        else: 
            new_path = raw_input("Enter the new path:")
            save(save_func, new_path)
    except Exception as inst:
        logger.error("Unknown error on saving \"%s\" %s: %s" % 
                    (file_path, type(inst), inst))
        raise
            
if __name__ == "__main__":
    from optparse import OptionParser
        
    p = OptionParser()
    p.add_option('-p', '--path', action="store", dest='doc_path',
                     help="specify path of wiki documents")
    p.add_option('-o', '--output-prefix', action="store", dest='prefix',
                     help="specify path prefix where everything should be saved")
    (options, args) = p.parse_args()
    
    logger = logging.getLogger("feature_extractor")
    
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
    logging.root.setLevel(level=logging.INFO)
    logger.info("running %s" % ' '.join(sys.argv))
    
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
    id2token = corpora.Dictionary.load(options.prefix + "_wordids.dict")
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
    #mm_tfidf = corpora.MmCorpus(options.prefix + '_tfidf_corpus.mm')
    
    '''LDA Model creation'''
    
    #build lda model
    #lda = models.LdaModel(corpus=mm_tfidf, id2word=id2token, 
    #                      num_topics=NUM_TOPICS, update_every=1, 
    #                      chunksize=10000, passes=2) 
    
    #save trained model
    #lda.save(options.prefix + '_lda.model')
    
    #save corpus as lda vectors in matrix market format
    #corpora.MmCorpus.serialize(options.prefix + '_lda_corpus.mm', lda[mm_tfidf], 
    #                           progress_cnt=10000)
    
    #init lda-corpus reader
    mm_lda = corpora.MmCorpus(options.prefix + '_lda_corpus.mm')
    
    '''ESA Model creation'''
    
    #document titles
    article_titles = DocumentTitles.load(options.prefix + "_articles.txt")
    
    #build esa model
    esa = EsaModel(mm_lda, num_clusters = 10000, 
                           document_titles = article_titles,
                           num_features = NUM_TOPICS)
    
    esa.save(options.prefix + "_esa_on_lda.model")
    
    logger.info("finished transforming")