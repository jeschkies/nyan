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


Creates an (in-memory) SQLite database from Reuters-21578 corpus

See "VI.B. Document-Internal Tags" of Readme

So far TYPTE and COMPANIES are ignored.

Document Table:
---------------
id, Date, MKNote, Companies, Unknown, Author, Dateline, Title, Body,
LEWISSPLIT, TOPICS-Attribute, CGISPLIT, OLDID, NEWID


Topic-To-Document-Table:
------------------------
id, document_id, topic_id

Topics Table:
-------------
id, Topic

Places-To-Document-Table:
------------------------
id, document_id, place_id

Places Table:
-------------
id, Place

People-To-Document-Table:
------------------------
id, document_id, people_id

People Table:
-------------
id, Person

Orgs-To-Document-Table:
------------------------
id, document_id, org_id

Orgs Table:
-------------
id, Org

Exchanges-To-Document-Table:
------------------------
id, document_id, exchange_id

Exchanges Table:
-------------
id, Exchange
'''
from bs4 import BeautifulSoup
import logging
import os
from sets import ImmutableSet
import sqlite3

logger = logging.getLogger("py21578")

class FileDatabase(object):
    
    reuters_21578_files = ['reut2-000.sgm',
                            'reut2-001.sgm',
                            'reut2-002.sgm',
                            'reut2-003.sgm',
                            'reut2-004.sgm',
                            'reut2-005.sgm',
                            'reut2-006.sgm',
                            'reut2-007.sgm',
                            'reut2-008.sgm',
                            'reut2-009.sgm',
                            'reut2-010.sgm',
                            'reut2-011.sgm',
                            'reut2-012.sgm',
                            'reut2-013.sgm',
                            'reut2-014.sgm',
                            'reut2-015.sgm',
                            'reut2-016.sgm',
                            'reut2-017.sgm',
                            'reut2-018.sgm',
                            'reut2-019.sgm',
                            'reut2-020.sgm',
                            'reut2-021.sgm']
    
    # Public Methods ##########################################################
    
    def get_documents(self):
        for row in self.conn.execute("SELECT body FROM documents"):
            yield row

    def get_conn(self):
        return self.conn

    # Private Methods #########################################################
    
    def _create_tables(self):
        c = self.conn.cursor()
                
        #Drop all table if they exist
        c.execute('''DROP TABLE IF EXISTS documents''')
        c.execute('''DROP TABLE IF EXISTS document_to_topic''')
        c.execute('''DROP TABLE IF EXISTS topics''')
        c.execute('''DROP TABLE IF EXISTS document_to_exchange''')
        c.execute('''DROP TABLE IF EXISTS exchanges''')
        c.execute('''DROP TABLE IF EXISTS document_to_place''')
        c.execute('''DROP TABLE IF EXISTS places''')
        c.execute('''DROP TABLE IF EXISTS document_to_org''')
        c.execute('''DROP TABLE IF EXISTS orgs''')
        c.execute('''DROP TABLE IF EXISTS document_to_person''')
        c.execute('''DROP TABLE IF EXISTS people''')
        
        #Create document table
        c.execute('''CREATE TABLE documents
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      date TEXT, 
                      MKNote TEXT, 
                      unknown TEXT, 
                      author TEXT, 
                      dateline TEXT, 
                      title TEXT, 
                      body TEXT,
                      LEWISSPLIT TEXT, 
                      TOPICS_Attribute TEXT, 
                      CGISPLIT TEXT, 
                      OLDID INTEGER, 
                      NEWID INTEGER)''')
        
        #Create many-to-many document to topic
        c.execute('''CREATE TABLE document_to_topic
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     document_id INTEGER, 
                     topic_id INTEGER)''')
        
        #Create topics table
        c.execute('''CREATE TABLE topics 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     content TEXT)''')
        
        #Create many-to-many document to exchange
        c.execute('''CREATE TABLE document_to_exchange
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     document_id INTEGER, 
                     exchange_id INTEGER)''')
        
        #Create exchanges table
        c.execute('''CREATE TABLE exchanges 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     content TEXT)''')
        
        #Create many-to-many document to place
        c.execute('''CREATE TABLE document_to_place
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     document_id INTEGER, 
                     place_id INTEGER)''')
        
        #Create places table
        c.execute('''CREATE TABLE places 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     content TEXT)''')
        
        #Create many-to-many document to org
        c.execute('''CREATE TABLE document_to_org
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     document_id INTEGER, 
                     org_id INTEGER)''')
        
        #Create orgs table
        c.execute('''CREATE TABLE orgs 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     content TEXT)''')
        
        #Create many-to-many document to person
        c.execute('''CREATE TABLE document_to_person
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     document_id INTEGER, 
                     people_id INTEGER)''')
        
        #Create people table
        c.execute('''CREATE TABLE people 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     content TEXT)''')
        
        self.conn.commit()
        
    def _add_document_category_relation(self, relation_table_name,
                                        category_table_name, column_name,
                                        document_id, category_values):
        '''
        Adds many-to-many relation of a document and many category calues.
        
        Only legal category values are connected. 
        
        Parameters
        ----------
        relation_table_name : E.g. document_to_topic
        category_table_name : E.g. topics
        column_name : E.g. topic_id
        document_id : Id of the document in the table documents
        topic_list : A list of category values as string
        '''
        c = self.conn.cursor()
        
        query = """INSERT INTO %s (document_id, %s)   
                   SELECT ?,id 
                   FROM %s 
                   WHERE content = ?;""" % (relation_table_name, 
                                            column_name,
                                            category_table_name)#unsafe
        for value in category_values:
            c.execute(query, (document_id, value,))
            
        self.conn.commit()
        
        
    def _load_legal_set(self, path):
        with open(path, 'r') as legal_list_file:
            legal_set = ImmutableSet(legal.strip("\n") for legal in legal_list_file) 
        return legal_set
    
    def _add_legal_category_to_table(self, legal_set, table_name):
        c = self.conn.cursor()
        
        query = 'INSERT INTO %s (content) VALUES (?)' % table_name
        for legal_category in legal_set:
            c.execute(query, (legal_category,))
            
        self.conn.commit()
        
    def _add_document(self, date, MKNote, unknown, author, dateline, title, 
                      body, LEWISSPLIT, TOPICS_Attribute, CGISPLIT, 
                      OLDID, NEWID):
        '''
        Adds a new document to database
        
        Returns
        -------
        id of row inserted
        '''
        c = self.conn.cursor()
        
        query = '''INSERT INTO documents 
                        (date, MKNote, unknown, author, dateline, title, 
                         body, LEWISSPLIT, TOPICS_Attribute, CGISPLIT, 
                         OLDID, NEWID) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        c.execute(query, (date, MKNote, unknown, author, dateline, title, 
                          body, LEWISSPLIT, TOPICS_Attribute, CGISPLIT, 
                          OLDID, NEWID,)
                  )
        
        last_id = c.lastrowid
            
        self.conn.commit()
        
        return last_id
        
    def _get_safe_content(self, tag, default = u''):
        '''
        Trys to get content from tag. If this fails default is returned
        
        tag should be a BeautifulSoup Node
        '''
        try:
            if tag is None:
                return default
            return unicode(tag.string)
        except Exception as e:
            logger.error("Could not get content: %s" % e)
            return default
        
    def _get_safe_attribute(self, tag, attribute_name, default = ''):
        '''
        Trys to get attribute value from tag. If this fails default is returned
        
        tag should be a BeautifulSoup Node
        attribute_name is a string
        '''
        try:
            if tag is None:
                return default
            return tag[attribute_name]
        except Exception as e:
            logger.error("Could not get attribute: %s" % e)
            return default
              
    def _get_safe_categories(self, tag, category_name):
        '''
        Trys to get categories from tag by category_name
        
        Returns
        -------
        list of categories as string
        '''
        try:
            category = tag.find(category_name)
            return [c for c in category.strings]
        except Exception as e:
            logger.error("Could not get categories: %s" % e)
            
    def _get_next_reuters(self, file):
            #go to first <Reuters
            line = file.readline()
            if not line:
                raise StopIteration()
            while not line.startswith("<REUTERS"):
                file.readline()
                
            #line should start with <REUTERS now
            #append next lines until </RETUERS> is read.
            next_line = file.readline()
            while not next_line.startswith("</REUTERS"):
                line += next_line
                next_line = file.readline()

            #we did not append <REUTERS
            raw = line + "</REUTERS>"
            
            #Parse everthing else
            soup = BeautifulSoup(raw, "xml")
            
            return soup
        
    def _get_all_reuters(self, path):
        #Since the format is somewhat screwed 
        # we look for <REUTERS ...>...</REUTERS> sets and parse them individually
        with open(os.path.join(path), 'r') as file:
            #skip <!DOCTYPE ../>
            file.readline()
            
            try:
                while 1:
                    yield self._get_next_reuters(file)
            except StopIteration as e:
                logger.info("Read all reuters: %s" % e)
            
    def _load_and_add_documents(self, path):
        '''
        Adds all documents from reut2-0XX.sgm to database
        '''
        #Load documents
        logger.info("Process file %s..." % path)

        #Add each document to database
        for reuters in self._get_all_reuters(path):
            try:
                logger.debug("Add document %s." % reuters.find('TITLE'))
                did = self._add_document(date = self._get_safe_content(reuters.find('DATE')),
                                   MKNote = self._get_safe_content(reuters.find('MKNote')), 
                                   unknown = self._get_safe_content(reuters.find('UNKNOWN')), 
                                   author = self._get_safe_content(reuters.find('AUTHOR')), 
                                   dateline = self._get_safe_content(reuters.find('DATELINE')), 
                                   title = self._get_safe_content(reuters.find('TITLE')), 
                                   body = self._get_safe_content(reuters.find('BODY')), 
                                   LEWISSPLIT = self._get_safe_attribute(reuters.find('REUTERS'), 'LEWISSPLIT'), 
                                   TOPICS_Attribute  = self._get_safe_attribute(reuters.find('REUTERS'), 'TOPICS'), 
                                   CGISPLIT = self._get_safe_attribute(reuters.find('REUTERS'), 'CGISPLIT'), 
                                   OLDID = int(self._get_safe_attribute(reuters.find('REUTERS'), 'OLDID', default = -1)), 
                                   NEWID = int(self._get_safe_attribute(reuters.find('REUTERS'), 'NEWID', default = -1)))
                
                #Add relations to database
                topics = self._get_safe_categories(reuters, 'TOPICS')
                self._add_document_category_relation('document_to_topic',  
                                                     'topics',
                                                     'topic_id',
                                                     did,
                                                     topics)
                
                exchanges = self._get_safe_categories(reuters, 'EXCHANGES')
                self._add_document_category_relation('document_to_exchange', 
                                                     'exchanges',
                                                     'exchange_id', 
                                                     did,
                                                     exchanges)
                
                people = self._get_safe_categories(reuters, 'PEOPLE')
                self._add_document_category_relation('document_to_person', 
                                                     'people',
                                                     'people_id', 
                                                     did,
                                                     people)
                
                places = self._get_safe_categories(reuters, 'PLACES')
                self._add_document_category_relation('document_to_place', 
                                                     'places',
                                                     'place_id', 
                                                     did,
                                                     places)
                
                orgs = self._get_safe_categories(reuters, 'ORGS')
                self._add_document_category_relation('document_to_org', 
                                                     'orgs',
                                                     'org_id', 
                                                     did,
                                                     orgs)
            except Exception as e:
                print e
        
    def __init__(self, reuters_path, database_path):
        '''
        Creates SQLite Database from Reuters-21578 dataset.
        
        Parameters
        ----------
        reuters_path : If not None a new database will be created
        database_path : Path for database
        '''
  
        if reuters_path is None:
            self.conn = sqlite3.connect(database_path)
            return
        
        #Create new database
        logger.info("Reuters path: %s" % reuters_path)
        self.conn = sqlite3.connect(database_path)
        self._create_tables()
        
        #Leagal category lists
        legal_topics = self._load_legal_set(os.path.join(reuters_path, 
                                                         "all-topics-strings.lc.txt"))
        self._add_legal_category_to_table(legal_topics, "topics")
        
        legal_exchanges = self._load_legal_set(os.path.join(reuters_path, 
                                                         "all-exchanges-strings.lc.txt"))
        self._add_legal_category_to_table(legal_exchanges, "exchanges")
        
        legal_places = self._load_legal_set(os.path.join(reuters_path, 
                                                         "all-places-strings.lc.txt"))
        self._add_legal_category_to_table(legal_places, "places")
        
        legal_orgs = self._load_legal_set(os.path.join(reuters_path, 
                                                         "all-orgs-strings.lc.txt"))
        self._add_legal_category_to_table(legal_orgs, "orgs")
        
        legal_people = self._load_legal_set(os.path.join(reuters_path, 
                                                         "all-people-strings.lc.txt"))
        self._add_legal_category_to_table(legal_people, "people")
        
        #Load and add documents
        for file_name in self.reuters_21578_files:
            self._load_and_add_documents(os.path.join(reuters_path, file_name))
        #self._load_and_add_documents(os.path.join(reuters_path, "test.sgm"))
        
    @classmethod
    def load(cls, database_path):
        logger.info("Load database from %s" % database_path)
        return FileDatabase(reuters_path = None, 
                            database_path = database_path)
        
class InMemoryDatabase(FileDatabase):
    '''
    Creates new database in memory
    '''
    
    def __init__(self, reuters_path):
        super(InMemoryDatabase, self).__init__(reuters_path = reuters_path,
                                               database_path = ":memory:")  
    
                