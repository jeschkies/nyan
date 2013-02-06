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

Implementation of Explicit Semantic Analysis
See: "Computing semantic relatedness using wikipedia-based explicit semantic analysis"
by Gabrilovich, E. and Markovitch, S. in "Proceedings of the 20th international joint conference on artificial intelligence"

Note: It is slightly modified. During the learning process clustering is applied
to reduce the number of concepts. If the number of clusters is the same as the 
number of concepts the implementation is true to the paper.
"""

from collections import defaultdict
import logging
import itertools
from kmedoids import KMedoids 
import math
import numpy

from gensim import interfaces, matutils, utils, similarities


logger = logging.getLogger('gensim.models.esamodel')

class DocumentTitles(object):
    '''
    Loads a list of document titles form a text file.
    Each line is considered to be a title.
    '''
    
    def __init__(self):
        self.document_titles = []
    
    @classmethod
    def load(cls, file_path):
        logger.info("Loading concept titles from %s" % file_path)
        
        result = DocumentTitles()
        with open(file_path, "r") as file:
            for line in file:
                doc_title = line.strip("\n").decode("UTF-8")
                result.document_titles.append(doc_title)
        
        logger.info("Loaded %d concept titles." % len(result.document_titles))
               
        return result
    
    def append(self, value):
        self.document_titles.append(value)
    
    def __iter__(self):
        for title in self.document_titles: yield title
        
    def __getitem__(self, key):
        return self.document_titles[key]
    
    def __len__(self):
        return len(self.document_titles)

class EsaModel(interfaces.TransformationABC):
    """
    Objects of this class realize the transformation between concepts (docs) 
    represented in the TF-IDF (or LDA) model and the ESA model.
    The transformation is done by multiplying the the doc in TF-IDF model by the 
    ESA intepreter matrix. Each column of the ESA matrix is one concept, each row is 
    one token An entry is
    the TF-IDF value of a token and the concept.
    The concepts are usually Wikipedia articles.
    
    The main methods are:
    
    1. constructor, which sets up the interpreter matrix by calculating the TF-IDF 
    value for each token in each concept/doc.
    2. the [] method, which transforms a simple TF-IDF representation into the ESA 
    space.
    
    >>> esa = EsaModel(tfidf_corpus)
    >>> print = esa[some_doc]
    >>> esa.save('/tmp/foo.esa_model', '/tmp/foo.esa_concept_dict')
    
    Model persistency is achieved via its load/save methods.
    """
    def __init__(self, corpus, document_titles, num_clusters = None,
                 num_features = None):
        """
        Computes the interpreter matrix by calculating the TF-IDF value of each
        token in each concept (doc) in corpus.
        
        document_titles give the names of each concept (doc) in corpus.
        num_features gives the number of features of corpus
        
        If num_clusters == None all documents are used as concepts.
        """
        
        if not num_clusters:
            self.num_clusters = len(document_titles)
        else:
            self.num_clusters = num_clusters
        
        if num_features is None:
            logger.info("scanning corpus to determine the number of features")
            num_features = 1 + utils.get_max_id(corpus)
            
        self.num_features = num_features
        
        #reduce column count by k-medoid clustering and using medoid of each cluster
        #TODO: skip clustering when num_clusters == None
        clusterer = KMedoids(corpus = corpus, 
                             num_features = self.num_features,
                             num_clusters = self.num_clusters,
                             max_iterations = 10)
        clusters = clusterer.cluster()
        
        #set the corpus to medoids
        #the corpus is our interpreter matrix. It is not sparse
        #each column is a doc and is seen as a concept
        self.corpus = clusterer.get_medoids().T
        
        
        #reduce document titles
        self.document_titles = DocumentTitles()
        for cluster_id in clusters.iterkeys():
            self.document_titles.append(document_titles[cluster_id] or "no title")
            
        #print clusters with their members
        for cluster_id, members in clusters.iteritems():
            cluster_title = document_titles[cluster_id]
            member_titles = ", ".join(document_titles[member_id] 
                                      for member_id 
                                      in members)
            logger.debug("%s: %s" % (cluster_title, member_titles))
            

    def __str__(self):
        return " \n".join(self.document_titles)
    
    def get_concept_titles(self, doc_vec):
        '''
        Converts ids from document vector to concept titles.
        '''
        return [(self.document_titles[concept_id], weight) 
                for concept_id, weight in doc_vec]

    def __getitem__(self, bow, eps=1e-12):
        """
        Return esa representation of the input vector and/or corpus.
        
        bow should already be weights, e.g. with TF-IDF
        """
        # if the input vector is in fact a corpus, return a transformed corpus 
        # as a result
        is_corpus, bow = utils.is_corpus(bow)
        if is_corpus:
            return self._apply(bow)

        #use corpus as interpreter matrix
        #simply multiply feature vector of input with corpus matrix
        #to get the weight of the concept
        vector = numpy.dot(matutils.sparse2full(bow, self.num_features),
                          self.corpus)


        #normalize
        vector = matutils.unitvec(vector)

        # make sure there are no explicit zeroes in the vector (must be sparse)
        vector = [(concept_id, weight) 
                  for concept_id, weight 
                  in enumerate(vector) 
                  if abs(weight) > eps]
        return vector
    
    def save(self, fname):
        '''
        See MatrixSimilarity.save()
        '''
        logger.info("storing %s object to %s and %s" % (self.__class__.__name__, 
                                                        fname, 
                                                        fname + '.npy'))
        # first, remove the index from self.__dict__, so it doesn't get pickled
        index = self.corpus
        del self.corpus
        try:
            utils.pickle(self, fname) # store index-less object
            numpy.save(fname + '.npy', index) # store index
        finally:
            self.corpus = index


    @classmethod
    def load(cls, fname):
        """
        Load a previously saved object from file (also see `save`).
        """
        logger.info("loading %s object from %s" % (cls.__name__, fname))
        result = utils.unpickle(fname)
        result.corpus = numpy.load(fname + '.npy', mmap_mode='r') # load back as read-only
        return result
#endclass EsaModel