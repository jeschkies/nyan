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

"""
@author: karsten jeschkies <jeskar@web.de>

An example on how to use the ESA model.

Note: ESA can be trained on an TFIDF or LDA corpus. If it is only trained on a
TFIDF corpus not LDA model is needed.
"""

from esamodel import EsaModel
from gensim import utils, corpora, models 
import logging
import sys

if __name__ == "__main__":
    from optparse import OptionParser
        
    p = OptionParser()
    p.add_option('-t', '--textfile', action="store", dest='text',
                     help="specify path to text file")
    p.add_option('-p', '--input-prefix', action="store", dest='prefix',
                     help="specify path prefix")
    (options, args) = p.parse_args()
    
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
    logging.root.setLevel(level=logging.INFO)
    
    logger = logging.getLogger("main")
    
    logger.info("Load text file %s" % options.text)
    
    try:
        with open(options.text, "r") as file:
            doc = " ".join(file.readlines())
    except Exception as e:
        logger.error("Could not load document from %s" % options.text)
        sys.exit(1)
        
    #load dictionary, tfidf model, lda model, esa model
    logger.info("Load dictionary, tfidf model, lda model and esa model with prefix %s" 
                % options.prefix)
    dictionary = corpora.Dictionary.load(options.prefix + "_wordids.dict")
    tfidf_model = models.TfidfModel.load(options.prefix + "_tfidf.model")
    lda_model = models.LdaModel.load(options.prefix + "_lda.model")
    esa_model = EsaModel.load(options.prefix + "_esa_on_lda.model")
    
    #create list of tokens from doc
    logger.info("Lemmatize document.")
    tokens = utils.lemmatize(doc)
    
    #create bow of doc from token list
    logger.info("Create bag-of-words representation from document.")
    doc_bow = dictionary.doc2bow(tokens)
    
    #create tfidf representation from bag-of-words
    logger.info("Transform to tfidf.")
    doc_tfidf = tfidf_model[doc_bow]
    
    #create lda representation from tfidf
    logger.info("Transform to lda")
    doc_lda = lda_model[doc_tfidf]
    
    #create esa representation from lda
    logger.info("Transform to esa")
    doc_esa = esa_model[doc_lda]
    
    #print
    doc_esa_sorted = sorted(doc_esa, key=lambda item: -item[1])
    doc_esa_printable = esa_model.get_concept_titles(doc_esa_sorted)[0:100]
    
    for concept, weight in doc_esa_printable:
        print "%s: %f" % (concept, weight) 
        
    
    
    