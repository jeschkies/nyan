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
@author karsten jeschkies <jeskar@web.de>

This is an implementation of a kMedoids clusterer.

It works memory independent. However, this makes the clusterer very slow!
"""

from collections import defaultdict
from gensim.similarities import Similarity, SparseMatrixSimilarity, MatrixSimilarity
from gensim import matutils
import itertools
import logging
import multiprocessing
import numpy
import random


logger = logging.getLogger('gensim.models.kmedoids')

POOL_SIZE = multiprocessing.cpu_count()
CHUNK_SIZE = 1000

def assign_doc_to_cluster(args):
    id_doc, similarity_index = args
    
    #get similarity of doc to each medoid
    similarities_to_medoids = similarity_index[id_doc[1]]
            
    #get best fit
    best_fit_position = 0
    best_sim = -1
    for pos, sim in enumerate(similarities_to_medoids):
        if sim > best_sim:
            best_sim = sim
            best_fit_position = pos 
            
    return id_doc[0], best_fit_position   
    

class KMedoids(object):
    '''
    Implementation of kmedoids clustering.
    There are two ways to find a medoid:
    - Use the element which is closest to the centroids. 
    This is the "kmeans based" kemdoids.
    - Use the elemen which has the smalles summed distance to the other cluster
    member. This is the "kmedian based" kmedoids.
    
    So far this implementation uses the kmeans based approach.
    '''
    
    def __init__(self, corpus, num_features, num_clusters, max_iterations):
        
        self.similarity_index = Similarity(output_prefix = 'similarities', 
                                           corpus = corpus,
                                           num_features = num_features)
        
        self.num_docs = len(self.similarity_index)
        self.num_clusters = num_clusters
        self.max_iterations = max_iterations
        self.num_features = num_features
        self.corpus = corpus
        
        self.MIN_CLUSTER_SIZE = 2
        
    def get_medoids(self):
        '''
        Retuirns a Matrix containing the medoids
        '''
        return self.medoid_similarity_index.index
        
    def __medoid_generator(self):
        '''
        Yields all medoid documents
        '''
        for medoid_id in self.medoids.iterkeys():
            yield self.similarity_index.vector_by_id(medoid_id)
            
    def __create_medoid_similarity_index(self):
        self.medoid_similarity_index = MatrixSimilarity(
                                           corpus = list(self.__medoid_generator()),
                                           num_features = self.num_features)        
        
    def __random_init_medoids(self):
        #the keys are the indices of the medoids
        #the values are indices list of the elements belonging to medoid
        self.medoids = defaultdict(list)
        
        #init random medoids
        for x in xrange(self.num_clusters):
            medoid_index = random.randrange(self.num_docs)
            self.medoids[medoid_index] = []  
            
        #create similarity index of medoids  
        self.__create_medoid_similarity_index()
            
    def __assign(self):
        #We use cosine-similarity as metric
        #NOTE: the closer the cosine is to 1 the closer the documents are
        
        #the cosine distance is in <-1, 1> where 1 is the closest and -1 the farthest
        #we might convert it to <0, 2> where 0 is the closest and 2 the farthest in the future
        #dis = (dis * -1) +1 

        
        #clear all clusters
        for id, _ in self.medoids.iteritems():
            self.medoids[id] = []
        
        #assign each doc to closest medoid
        args = itertools.izip(enumerate(self.corpus), 
                              itertools.repeat(self.medoid_similarity_index))
        pool = multiprocessing.Pool(POOL_SIZE)
        #for id, pos in pool.imap_unordered(assign_doc_to_cluster, args, 
        #                         chunksize= CHUNK_SIZE):
        for id, pos in pool.imap_unordered(assign_doc_to_cluster, args):
            self.medoids[self.medoids.keys()[pos]].append(id)
            
    def __get_centroid(self, cluster):
        #averages all docs in cluster
        count = 0
        centroid = numpy.zeros(self.num_features, dtype=numpy.float32)
        for doc_id in cluster:
            doc = self.similarity_index.vector_by_id(doc_id).toarray().flatten()
            #full_doc = matutils.sparse2full(doc, self.num_features)
            
            centroid = centroid + doc
            count += 1
            
        if count != 0:
            centroid = centroid / count
            
        return matutils.full2sparse(centroid)
            
    def __recalculate_medoids(self):
        changed = False
        count = 0
        for medoid_id, cluster in self.medoids.items():
            if count % 1000 == 0:
                logger.info("PROGRESS: Recalculate medoid for cluster #%d id%d" 
                            % (count, medoid_id))
            count +=1 
            
            if len(cluster) < self.MIN_CLUSTER_SIZE:
                #cluster is too small, init a new random medoid
                #remove medoid
                del self.medoids[medoid_id]
                
                #add new random medoid. the id could already be used as medoid.
                # for now we just risk our it ;)
                medoid_index = random.randrange(self.num_docs)
                self.medoids[medoid_index] = [] 
                
                changed = True
            else:
                
                logger.debug("Find new centroid for cluster %d." % medoid_id)
                
                #calculate centroid and assign closest doc as new medoid
                centroid = self.__get_centroid(cluster)   
                
                
                old_num_best = self.similarity_index.num_best
                
                #similarity index should only return the best fit
                self.similarity_index.num_best = 1
                try:
                    new_medoid_id, _ = self.similarity_index[centroid][0]
                except IndexError as e:
                    logger.error("Could not find best fit for centroid: %s." % (e))
                    #use random medoid index
                    new_medoid_id = random.randrange(self.num_docs)
                
                self.similarity_index.num_best = old_num_best
                
                if new_medoid_id != medoid_id:
                    changed = True
                    #remove old medoid
                    del self.medoids[medoid_id]
                
                #empty medoid in any case
                self.medoids[new_medoid_id] = []

        if changed:
            self.__create_medoid_similarity_index()
        
        return changed
        
    def cluster(self):
        logger.info("Init random medoids.")
        self.__random_init_medoids()
        
        logger.info("Assign elements to random clusters.")
        self.__assign()
        
        changed = True
        count = 0
        while changed and count < self.max_iterations:
            changed = False
            count += 1
            
            logger.info("Entering iteration #%d." % count)
            
            #recalculate medoids
            logger.info("Recalculate medoids.")
            changed = self.__recalculate_medoids()
            
            #assign all doc to medoids
            logger.info("Assign elements to new clusters.")
            assignment = self.__assign()
            
        if count < self.max_iterations:
            logger.info("Converged in %d iterations." % count)
        else:
            logger.info("May not have converged after %d iterations." % 
                        self.max_iterations)
        return self.medoids