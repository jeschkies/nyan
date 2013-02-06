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

YOU SHOULD USE THE IMPLEMENTATION OF THE GENSIM
USE THE BRANCH IF IT IS NOT MERGED YET: https://github.com/piskvorky/gensim/tree/reuters_corpus

Some classes which make the access to the Reuters-21578 dataset easier.

'''

from itertools import chain
import numpy as np

class ReutersCorpus(object):
    '''
    Complete Reuters corpus.
    
    Is iterable
    '''


    def __init__(self, database):
        '''
        Constructor
        
        Parameters
        ----------
        database : InMemoryDatabase to use
        '''
        
        self.db = database
        
    def __iter__(self):
        '''
        Iterates over all documents and yields just the text of a document.
        '''
        for doc in self.db.get_documents():
            yield doc[0]
            
class ModLewisSplitCorpus(ReutersCorpus):
    '''
    Get the the Modified Lewis ("ModLewis") Split from Reuters-21578 dataset.
    
    Training Set (13,625 docs): LEWISSPLIT="TRAIN";  TOPICS="YES" or "NO"
    Test Set (6,188 docs):  LEWISSPLIT="TEST"; TOPICS="YES" or "NO"
    Unused (1,765): LEWISSPLIT="NOT-USED" or TOPICS="BYPASS"
    
    See VIII.A. The Modified Lewis ("ModLewis") Split in README of dataset.
    '''
    
    def get_training_set(self):
        '''
        Generator over training set
        '''
        for doc in self.db.get_conn().execute("""SELECT body 
                                        FROM documents 
                                        WHERE (LEWISSPLIT='TRAIN' AND 
                                              TOPICS_Attribute='YES') OR
                                              (LEWISSPLIT='TRAIN' AND 
                                              TOPICS_Attribute='NO')
                                        ORDER BY NEWID"""):
            yield doc[0]
            
    def get_test_set(self):
        '''
        Generator over test set
        '''
        for doc in self.db.get_conn().execute("""SELECT body 
                                        FROM documents 
                                        WHERE (LEWISSPLIT='TEST' AND 
                                              TOPICS_Attribute='YES') OR
                                              (LEWISSPLIT='TEST' AND 
                                              TOPICS_Attribute='NO')
                                        ORDER BY NEWID"""):
            yield doc[0]
    
    def __iter__(self):
        '''
        Iterates over all documents from split and yields just the text of a 
        document.
        
        Just chains training and test sets
        '''
        for doc in chain(self.get_test_set(), self.get_training_set()):
            yield doc
        
        
class ModApteSplitCorpus(ModLewisSplitCorpus):
    '''
    Gets the Modified Apte ("ModApte") Split from Reuters-21578 dataset.
    
    Training Set (9,603 docs): LEWISSPLIT="TRAIN";  TOPICS="YES"
    Test Set (3,299 docs): LEWISSPLIT="TEST"; TOPICS="YES"
    Unused (8,676 docs):   LEWISSPLIT="NOT-USED"; TOPICS="YES"
                     or TOPICS="NO" 
                     or TOPICS="BYPASS"
                     
    See VIII.B. The Modified Apte ("ModApte") Split in README of dataset
    '''
        
    def get_training_set(self):
        '''
        Generator over training set
        '''
        for doc in self.db.get_conn().execute("""SELECT body 
                                        FROM documents 
                                        WHERE (LEWISSPLIT='TRAIN' AND 
                                              TOPICS_Attribute='YES')
                                        ORDER BY NEWID"""):
            yield doc[0]
            
    def get_test_set(self):
        '''
        Generator over test set
        '''
        for doc in self.db.get_conn().execute("""SELECT body 
                                        FROM documents 
                                        WHERE (LEWISSPLIT='TEST' AND 
                                              TOPICS_Attribute='YES')
                                        ORDER BY NEWID"""):
            yield doc[0]
            
class R10Split(ModApteSplitCorpus):
    '''
    Generates the R10 split as described in [1]: 
    "the set of the 10 categories with the highest number of positive training
     examples"
    
    [1] Debole, Franca, and Fabrizio Sebastiani. 
    "An analysis of the relative hardness of Reuters‐21578 subsets." 
    Journal of the American Society for Information Science and Technology 56.6 (2005): 584-596.
    '''
    
    class CategoryMembers(object):
        '''
        The class helps to iterate over documents belonging to one category
        '''
        
        def __init__(self, name, query, db):
            '''
            TODO: make query a function
            '''
            self.name = name
            self.query = query
            self.db = db
            
        def __iter__(self):
            for doc in self.db.get_conn().execute(self.query):
                yield doc[0]
                
        def get_name(self):
            return self.name
   
    def get_training_category_set(self):
        '''
        Generator over training set
        '''
        for topic in self.db.get_conn().execute("""SELECT topics.id, topics.content, COUNT(*)
                                        FROM documents  
                                        JOIN document_to_topic ON document_to_topic.document_id = documents.id
                                        JOIN topics ON document_to_topic.topic_id = topics.id
                                        WHERE (LEWISSPLIT='TRAIN' AND TOPICS_Attribute='YES') 
                                        GROUP BY topics.id
                                        ORDER BY COUNT(*) DESC
                                        LIMIT 10"""):
            yield R10Split.CategoryMembers(name = topic[1],
                                           db = self.db,
                                           query = """
                                                   SELECT documents.title
                                                    FROM documents  
                                                    JOIN document_to_topic ON document_to_topic.document_id = documents.id
                                                    WHERE (LEWISSPLIT='TRAIN' AND 
                                                           TOPICS_Attribute='YES' AND 
                                                           document_to_topic.topic_id= %d)
                                                   """ % topic[0])
            
    def get_test_category_set(self):
        '''
        Generator over test set
        
        TODO: Query is not right yet
        '''
        for topic in self.db.get_conn().execute("""SELECT topics.id, COUNT(*), topics.content
                                        FROM documents  
                                        JOIN document_to_topic ON document_to_topic.document_id = documents.id
                                        JOIN topics ON document_to_topic.topic_id = topics.id
                                        WHERE (LEWISSPLIT='TEST' AND TOPICS_Attribute='YES') 
                                        GROUP BY topics.id
                                        ORDER BY COUNT(*) DESC
                                        LIMIT 10"""):
            yield R10Split.CategoryMembers(name = topic[1],
                                           db = self.db,
                                           query = """
                                                   SELECT documents.title
                                                    FROM documents  
                                                    JOIN document_to_topic ON document_to_topic.document_id = documents.id
                                                    WHERE (LEWISSPLIT='TEST' AND 
                                                           TOPICS_Attribute='YES' AND 
                                                           document_to_topic.topic_id= %d)
                                                   """ % topic[0])
            
class R8Split(R10Split):
    '''
    Suitable for single-label classification
    Generates the R8 [1] split: "documents with a single topic and the classes 
    which still have at least one train and one test example"
    
    [1] See http://web.ist.utl.pt/~acardoso/datasets/
    
    So far the selection if hard coded for topics:
    acq    
    crude    
    earn    
    grain   
    interest 
    money-fx  
    ship
    trade
    '''
    
    target_map = {'acq': 1,
                  'crude': 2,
                  'earn': 3,
                  'grain': 4,
                  'interest': 5,
                  'money-fx': 6,
                  'ship': 7,
                  'trade': 8}   
    
    def get_training_category_set(self):
        '''
        Generator over training set
        
        First get all topics with at least on training and one test sample
        Then yield sample set for each topic where each sample belongs only 
        to one sample. The sets are disjunct.
        '''
        for class_name in self.target_map.keys():
            yield R10Split.CategoryMembers(name = class_name,
                                           db = self.db,
                                           query = """
                                                    SELECT documents.body, documents.title, topics.id, topics.content
                                                        FROM documents  
                                                        JOIN document_to_topic ON document_to_topic.document_id = documents.id
                                                        JOIN topics ON document_to_topic.topic_id = topics.id
                                                        WHERE (LEWISSPLIT='TRAIN' AND TOPICS_Attribute='YES' AND topics.content = '%s') 
                                                        GROUP BY documents.id
                                                        HAVING COUNT(documents.id) = 1
                                                   """ % class_name) #unsafe so far
            
    def get_test_category_set(self):
        '''
        Generator over test set
        '''
        for class_name in self.target_map.keys():
            yield R10Split.CategoryMembers(name = class_name,
                                           db = self.db,
                                           query = """
                                                    SELECT documents.body, documents.title, topics.id, topics.content
                                                        FROM documents  
                                                        JOIN document_to_topic ON document_to_topic.document_id = documents.id
                                                        JOIN topics ON document_to_topic.topic_id = topics.id
                                                        WHERE (LEWISSPLIT='TEST' AND TOPICS_Attribute='YES' AND topics.content = '%s') 
                                                        GROUP BY documents.id
                                                        HAVING COUNT(documents.id) = 1
                                                   """ % class_name) #unsafe so far
    
    def get_target_label(self, target_number):
        for key, value in self.target_map:
            if key == target_number:
                return value
            
    def get_target_labels(self):
        return self.target_map.keys()
            
    def get_target_number(self, target_name):
        return self.target_map[target_name]
    
    @property
    def training_data(self):      
        '''
        Generator over training set
        '''
        for c in self.get_training_category_set():
            for doc in c:
                yield doc
                
    @property
    def training_target(self):
        for c in self.get_training_category_set():
            for _ in c:
                yield self.target_map[c.name]   
            
    @property
    def test_data(self):
        '''
        Generator over test set
        '''
        for c in self.get_test_category_set():
            for doc in c:
                yield doc
                
    @property
    def test_target(self):
        '''
        Returns number for topics
        '''
        for c in self.get_test_category_set():
            for _ in c:
                yield self.target_map[c.name] 
        