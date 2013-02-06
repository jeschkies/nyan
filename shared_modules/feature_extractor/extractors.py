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
@author: karsten jeschkies <jeskar@web.de>

An extractor creates a feature vector from a text. This implementation relies
heavily on gensim. Som additions were made to gensim. See esamodel.

All extractors have to load at least one feature model.
'''

from esa.esamodel import EsaModel
from esa.cosine_esamodel import CosineEsaModel
from gensim import corpora, models, utils
import logging

logger = logging.getLogger("extractor")

class Extractor:
    '''
    Extractor interface
    '''
    
    def get_features(self, document):
        logger.debug("get_features not implemented!")
        raise NotImplementedError()
    
    def get_feature_number(self):
        logger.debug("get_feature_number not implemented!")
        raise NotImplementedError()
    
    @classmethod
    def get_version(self, document):
        logger.debug("get_version not implemented!")
        raise NotImplementedError()
    
class TfidfFeatureExtractor(Extractor):
    
    def __init__(self, prefix):
        logger.info("Load dictionary and tfidf model with prefix %s" 
                    % prefix)
        self.dictionary = corpora.Dictionary.load(prefix + "_wordids.dict")
        self.tfidf_model = models.TfidfModel.load(prefix + "_tfidf.model")
        
    def get_features(self, document):
        #create list of tokens from doc
        logger.debug("Lemmatize document.")
        tokens = utils.lemmatize(document)
        
        #create bow of doc from token list
        logger.debug("Create bag-of-words representation from article.")
        doc_bow = self.dictionary.doc2bow(tokens)
        
        #create tfidf representation from bag-of-words
        logger.debug("Transform to tfidf.")
        doc_tfidf = self.tfidf_model[doc_bow]
        
        return doc_tfidf
    
    def get_feature_number(self):
        return len(self.dictionary)
    
    @classmethod
    def get_version(self):
        return u"TF-IDF-1.1"
    
class LdaFeatureExtractor(Extractor):
    
    def __init__(self, prefix):
        logger.info("Load dictionary and tfidf and lda model with prefix %s" 
                    % prefix)
        self.dictionary = corpora.Dictionary.load(prefix + "_wordids.dict")
        self.tfidf_model = models.TfidfModel.load(prefix + "_tfidf.model")
        self.lda_model = models.LdaModel.load(prefix+ "_lda.model")
        
    def get_features(self, document):
        #create list of tokens from doc
        logger.debug("Lemmatize document.")
        tokens = utils.lemmatize(document)
        
        #create bow of doc from token list
        logger.debug("Create bag-of-words representation from article.")
        doc_bow = self.dictionary.doc2bow(tokens)
        
        #create tfidf representation from bag-of-words
        logger.debug("Transform to tfidf.")
        doc_tfidf = self.tfidf_model[doc_bow]
        
        #create lda representation from tfidf
        logger.debug("Transform to lda")
        doc_lda = self.lda_model[doc_tfidf]
        
        return doc_lda
    
    def get_feature_number(self):
        return self.lda_model.num_topics
    
    @classmethod
    def get_version(self):
        return u"LDA-0.3"
    
class LdaBowFeatureExtractor(Extractor):
    
    def __init__(self, prefix):
        logger.info("Load dictionary and lda model with prefix %s" 
                    % prefix)
        self.dictionary = corpora.Dictionary.load(prefix + "_wordids.dict")
        self.lda_model = models.LdaModel.load(prefix+ "_lda_on_bow.model")
        
    def get_features(self, document):
        #create list of tokens from doc
        logger.debug("Lemmatize document.")
        tokens = utils.lemmatize(document)
        
        #create bow of doc from token list
        logger.debug("Create bag-of-words representation from article.")
        doc_bow = self.dictionary.doc2bow(tokens)
        
        #create lda representation from tfidf
        logger.debug("Transform to lda")
        doc_lda = self.lda_model[doc_bow]
        
        return doc_lda
    
    def get_feature_number(self):
        return self.lda_model.num_topics
    
    @classmethod
    def get_version(self):
        return u"LDA-on-BOW-50"
    
class EsaFeatureExtractor(Extractor):
    
    def __init__(self, prefix):
        '''
        prefix is the prefix path to tfidf, lda and esa model.
        '''
        logger.info("Load dictionary, tfidf model, lda model and esa model with prefix %s" 
                    % prefix)
        self.dictionary = corpora.Dictionary.load(prefix + "_wordids.dict")
        self.tfidf_model = models.TfidfModel.load(prefix + "_tfidf.model")
        self.lda_model = models.LdaModel.load(prefix+ "_lda.model")
        self.esa_model = EsaModel.load(prefix + "_esa_on_lda.model")
            
    def get_features(self, document):
        #create list of tokens from doc
        logger.debug("Lemmatize document.")
        tokens = utils.lemmatize(document)
        
        #create bow of doc from token list
        logger.debug("Create bag-of-words representation from article.")
        doc_bow = self.dictionary.doc2bow(tokens)
        
        #create tfidf representation from bag-of-words
        logger.debug("Transform to tfidf.")
        doc_tfidf = self.tfidf_model[doc_bow]
        
        #create lda representation from tfidf
        logger.debug("Transform to lda")
        doc_lda = self.lda_model[doc_tfidf]
        
        #create esa representation from lda
        logger.debug("Transform to esa")
        doc_esa = self.esa_model[doc_lda]
        
        return doc_esa
    
    def get_feature_number(self):
        return len(self.esa_model.document_titles)
    
    @classmethod
    def get_version(self):
        return u"ESA-1.0"
    
class cEsaFeatureExtractor(Extractor):
    
    def __init__(self, prefix):
        '''
        prefix is the prefix path to tfidf, lda and esa model.
        '''
        logger.info("Load dictionary, tfidf model, lda model and cosine esa model with prefix %s" 
                    % prefix)
        self.dictionary = corpora.Dictionary.load(prefix + "_wordids.dict")
        self.tfidf_model = models.TfidfModel.load(prefix + "_tfidf.model")
        self.cesa_model = CosineEsaModel.load(prefix + "_cesa.model")
            
    def get_features(self, document):
        #create list of tokens from doc
        logger.debug("Lemmatize document.")
        tokens = utils.lemmatize(document)
        
        #create bow of doc from token list
        logger.debug("Create bag-of-words representation from article.")
        doc_bow = self.dictionary.doc2bow(tokens)
        
        #create tfidf representation from bag-of-words
        logger.debug("Transform to tfidf.")
        doc_tfidf = self.tfidf_model[doc_bow]
        
        #create cosine esa representation from lda
        logger.debug("Transform to cesa")
        doc_cesa = self.cesa_model[doc_tfidf]
        
        return doc_cesa
    
    def get_feature_number(self):
        return len(self.cesa_model.document_titles)
    
    @classmethod
    def get_version(self):
        return u"cESA-1.1"
