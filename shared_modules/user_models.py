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
Created on 29.10.2012

@author: karsten jeschkies <jeskar@web.de>

Several different user models for capturing a user's interests.
'''
import cPickle
from gensim import interfaces, utils, matutils, similarities
from itertools import chain, izip
import logging
from models.mongodb_models import (Article, User, UserModel, Feedback, Features, 
                                   ReadArticleFeedback, RankedArticle)
from mongoengine import queryset
import numpy
from random import sample
import scipy.sparse
from sets import Set
#from naive_bayes import GaussianNB #iterative GaussainNB
from sklearn.naive_bayes import GaussianNB
from sklearn import svm, tree
from smote import SMOTE, borderlineSMOTE

logger = logging.getLogger("main")

class UserModelBase(object):
    
    def __init__(self, user_id, extractor):
        self.user  = User.objects(id = user_id).first()
        
        self.extractor = extractor
        
        self.num_features_ = self.extractor.get_feature_number()
    
    def train(self):
        logger.debug("train() not implemented!")
        raise NotImplementedError()
    
    def save(self):
        logger.debug("save() not implemented!")
        raise NotImplementedError()
    
    def load(self):
        logger.debug("load() not implemented!")
        raise NotImplementedError()       
    
    def rank(self, doc):
        '''
        Ranks a document with learnt model
        '''
        logger.debug("rank() not implemented!")
        raise NotImplementedError()
    
    @classmethod
    def get_version(cls):
        logger.debug("get_version not implemented!")
        raise NotImplementedError()
    
    def get_features(self, article):
        '''
        Reaturns full features vector from article.
        Article should be a mongodb model
        '''
        #check if features of article are current version
        try:
            feature_version = article.features.version
        except AttributeError as e:
            if str(e) == 'features':
                logger.error("Article %s does not have any features." % 
                             article.id)
                #article seems not to exist anymore go on
                raise 
             
        if feature_version != self.extractor.get_version():
            clean_content = article.clean_content
                
            #get new features
            new_features = self.extractor.get_features(clean_content)
                
            #save new features
            features = Features(version = self.extractor.get_version(), 
                                data = new_features)
            article.features = features
            try:
                article.save()
            except queryset.OperationError as e:
                logger.error("Could not save article with id %s: %s" %
                             (article.id, e))
        
        #sparse2full converts list of 2-tuples to numpy array
        article_features_as_full_vec = matutils.sparse2full(article.features.data, 
                                                            self.num_features_)
        
        return article_features_as_full_vec
        

class UserModelCentroid(UserModelBase):
    '''
    Trains a user model base on user feedback.
    
    It uses the centroid based user model described in:
    Han und Karypis "Centroid-Based Document Classification: 
    Analysis & Experimental Results" ,2000
    '''

    READ = 2
    UNREAD = 1

    @classmethod
    def get_version(cls):
        return "UserModelCentroid-1.0"
     
    def train(self, read_article_ids = None, unread_article_ids = None):
        #Load user feedback if needed
        if read_article_ids is None:
            read_article_ids = (r.article.id for r in ReadArticleFeedback.objects(user_id = self.user.id).only("article"))
            
        user_feedback = Article.objects(id__in = read_article_ids)
        
        #TODO: cluster feedback articles and save more than one profile
        
        num_loaded_articles = 0
        centroid = numpy.zeros(self.num_features_, dtype=numpy.float32)
        
        for article in user_feedback:
            try:
                article_features_as_full_vec = self.get_features(article)
            except Exception as inst:
                logger.error("Could not get features for article %s: %s" %
                             (article.id, inst))
                continue
            
            #do we need this?
            tmp_doc = matutils.unitvec(article_features_as_full_vec)
            
            #add up tmp_doc
            centroid = numpy.add(centroid, tmp_doc)
            num_loaded_articles += 1 
            
        #average each element
        if num_loaded_articles != 0:
            centroid = centroid / num_loaded_articles
            
        centroid = matutils.full2sparse(centroid)
        
        #set user model data
        self.user_model_features = [centroid]
        
    def save(self): 
        #replace old user model with new
        try:
            #replace profile
            UserModel.objects(user_id = self.user.id).update(upsert = True,
                                                             set__user_id = self.user.id,
                                                             set__data = self.user_model_features,
                                                             set__version = self.get_version())
        except Exception as inst:
            logger.error("Could not save learned user model due to unknown"
                         " error %s: %s" % (type(inst), inst))
            
    def load(self):
        '''
        Loads user model from self.user. Not yet from UserModel
        
        NOTE: No feature conversion is done!
        '''
        
        #learned_user_model = UserModel.objects(user_id = self.user.id).first()
        
        #if learned_user_model is None:
        #    self.user_model_features = []
        #    return
        
        #get learned profile/model
        #convert features to list of tuples. 
        #we make a double list because we will have more than one model soon.
        self.user_model_features = [[tuple(a) for a in learned_user_model.data] 
                                   for profile in self.user.learned_profile]
            
    def rank(self, doc):
        '''
        Returns a ranking of the document to learnt model.
        
        doc should be instance of mongodb_models.Article
        '''
        
        #self.load()
        
        if len(self.user_model_features) == 0:
            logger.error("Learned user model seems to be empty.")
            return None
                
        index = similarities.SparseMatrixSimilarity(self.user_model_features,
                                        num_terms=self.num_features_,
                                        num_best = 1,
                                        num_features = self.num_features_,
                                        num_docs= len(self.user_model_features))
            
        #convert features to list of tuples
        news_article_features = list(tuple(a) for a in 
                                     doc.features.data)
            
        logger.debug("converted news article features")
            
        #calculate similarities of article to each user model
        #will return best fit
        sim = index[news_article_features]
            
        logger.debug("created similarities")
        
        #convert sim from numpy.float32 to native float
        try:
            native_sim = numpy.asscalar(sim[0][1])
        except IndexError as e:
            logger.error("Could not access similarity: %s. Similarity: %s. User model: %s"
                         % (e, sim, self.user_model_features))
            return None

        if native_sim > 0.3:
            return self.READ

        return self.UNREAD        
    
class NoClassifier(Exception):
    pass
            
class UserModelBayes(UserModelBase):
    '''
    Trains a user model base on user feedback.
    
    A Naive Bayes classifier is trained to decide if an article belongs to the
    "read" articles or not.
    
    Does not use SMOTE
    '''
    
    READ = 2
    UNREAD = 1

    @classmethod
    def get_version(cls):
        return "UserModelBayes-1.0"
    
    class AllArticles(object):
        
        def __init__(self, 
                     read_articles, 
                     unread_articles, 
                     get_features_function):
            '''
            Parameters:
            read_articles : Article Queryset
            unread_article : Article Queryset
            get_features_function : should be a function that takes an article
                                    as Article instance and returns the full 
                                    features vector
            '''
            self.read_articles = read_articles
            self.unread_articles = unread_articles
            self.get_features = get_features_function
            
        def _iter_features_and_marks(self):
            marked_read_articles = ((article, UserModelBayes.READ) 
                                    for article 
                                    in self.read_articles) 
            marked_unread_articles = ((article, UserModelBayes.UNREAD) 
                                      for 
                                      article 
                                      in self.unread_articles) 
            
            all_articles = chain(marked_read_articles, marked_unread_articles)
            
            for article, mark in all_articles:
                try:
                    article_features_as_full_vec = self.get_features(article)
                    yield article_features_as_full_vec, mark
                except AttributeError as e:
                    logger.error("Article %s does not have attribute: %s." 
                                  % (article.id, e))
                    
        def __iter__(self):
            for a, _ in self._iter_features_and_marks():
                yield a
                
        def get_marks(self):
            for _, mark in self._iter_features_and_marks():
                yield mark 

    def train(self, read_article_ids = None, unread_article_ids = None):
        '''
        Trains the Bayes Classifier.
        read_article_ids should be an iterable over read article ids
        unread_article_ids should be an iterable over unread article ids
        
        If one is None it will be loaded from database.
        '''
        
        #Load user feedback if needed
        if read_article_ids is None:
            read_article_ids = Set(r.article.id 
                                for r 
                                in ReadArticleFeedback.objects(user_id = self.user.id).only("article"))
        else:
            read_article_ids = Set(read_article_ids)
        
        logger.info("Use %d read articles for learning." % len(read_article_ids))
        read_articles = Article.objects(id__in = read_article_ids)

        #Get all articles the user did not read.
        if unread_article_ids is None:
            ranked_article_ids = (a.article.id 
                               for a 
                               in RankedArticle.objects(user_id = self.user.id).only("article"))
            all_article_ids = Set(a.id 
                                  for a 
                                  in Article.objects(id__in = ranked_article_ids).only("id"))
            unread_article_ids = all_article_ids - read_article_ids
            
        #undersample unreads
        logger.info("Use %d unread articles for learning." % (len(unread_article_ids)))
        
        unread_articles = Article.objects(id__in = unread_article_ids)
        
        #convert all article features
        all_articles = UserModelBayes.AllArticles(read_articles, 
                                                  unread_articles,
                                                  self.get_features)
            
        self.clf = GaussianNB()
        self.clf.fit(numpy.array(list(all_articles)), numpy.array(list(all_articles.get_marks())))
        
    def save(self):
        #replace old user model with new
        try:
            #pickle classifier and decode it to utf-8
            pickled_classifier = cPickle.dumps(self.clf).decode('utf-8')
            
            #replace profile
            UserModel.objects(user_id = self.user.id).update(upsert = True,
                                                             set__user_id = self.user.id,
                                                             set__data = pickled_classifier,
                                                             set__version = self.get_version())
            
        except Exception as inst:
            logger.error("Could not save learned user model due to unknown"
                         " error %s: %s" % (type(inst), inst)) 
            
    def load(self):
        try:
            if self.clf is not None:
                return
            
            user_model = UserModel.objects(user_id = self.user.id).first()
            
            if user_model is None:
                logger.debug("UserModel for user %s is empty." % self.user.id)
                self.clf = None
                return
            
            #ensure right version
            if user_model.version != self.get_version():
                logger.debug("UserModel for user %s has wrong version." %
                             self.user.id)
                self.clf = None
                return
            
            #unpickle classifier. it was saved as a utf-8 string.
            #get the str object by encoding it.
            pickled_classifier = user_model.data.encode('utf-8')
            self.clf = cPickle.loads(pickled_classifier)
                
        except Exception as inst:
            logger.error("Could not load learned user model due to unknown"
                         " error %s: %s" % (type(inst), inst))
    def rank(self, doc):
        '''
        doc should be instance of mongodb_models.Article
        '''
        
        self.load()
        
        if self.clf is None:
            logger.error("No classifier for user %s." % self.user.id)
            raise NoClassifier("Bayes Classifier for user %s seems to be None."
                               % self.user.id)

        data = numpy.empty(shape=(1,self.num_features_), 
                           dtype=numpy.float32)
        
        data[0] = self.get_features(doc)
        prediction = self.clf.predict(data)
        
        return prediction[0]
    
class UserModelSVM(UserModelBayes):
    
    READ = 2
    UNREAD = 1

    @classmethod
    def get_version(cls):
        return "UserModelSVM-1.0"
    
    def __init__(self, user_id, extractor):
        self.set_samples_sizes()
        
        super(UserModelSVM, self).__init__(user_id, extractor)  
        
    def _calculate_mean_and_std_deviation(self, X):
        '''
        Caluclates mean and standard deviation of sample features.
        
        Parameters
        ----------
        X : array-like, samples, shape = (n_samples, n_features)
        '''
        
        _, n_features = X.shape
        
        self.theta_ = numpy.zeros((n_features))
        self.sigma_ = numpy.zeros((n_features))
        epsilon = 1e-9
        
        self.theta_[:] = numpy.mean(X[:,:], axis=0)
        self.sigma_[:] = numpy.std(X[:,:], axis=0) + epsilon
        
    def _normalize(self, X):
        '''
        Normalizes sample features.
        
        self.theta_ and self.sigma_ have to be set.
        
        Parameters
        ----------
        X : array-like, samples, shape = (n_samples, n_features)
        '''
            
        n_samples, n_features = X.shape
        
        new_X = numpy.zeros(shape=(n_samples, n_features), dtype=numpy.float32)
        
        try:
            new_X[:,:] = (X[:,:] - self.theta_[:]) / self.sigma_[:]
        except AttributeError as e:
            logger.error(("theta_ or sigma_ are not set. "
                          "Call _calculate_mean_and_std_deviation. Error: %s")
                         % e)
            raise AttributeError()
        
        return new_X
    
    def _get_samples(self, 
                     read_article_ids, 
                     unread_article_ids,
                     p_synthetic_samples = 300,
                     p_majority_samples = 500,
                     k = 5):
        '''
        read_article_ids : Set
        unread_article_ids : Set
        p_synthetic_samples : Percentage of snythetic samples, 300 for 300% 
                              If None no are created 
        p_majority_samples : Size of majority sample = p_majority_samples/n_minority_sample, 
                             500 for 500%
                             If None under sampling ist not done
        k : neighbourhood for k nearest neighbour, standard 5

        Returns
        -------
        array-like full vector samples, shape = [n_features, n_samples]
        array-like marks, shape = [n_samples]
        '''
        
        #Under-sample unread ids
        if p_majority_samples is not None:
            unread_article_ids = Set(sample(unread_article_ids, 
                                            min(p_majority_samples/100 * len(read_article_ids), 
                                                len(unread_article_ids))
                                            )
                                     )
        
        #Create unread article vectors
        unread_marks = numpy.empty(len(unread_article_ids))
        unread_marks.fill(UserModelSVM.UNREAD)
        unread_articles = numpy.empty(shape=(len(unread_article_ids), 
                                             self.num_features_))
        
        
        for i, article in enumerate(Article.objects(id__in = unread_article_ids)):
            try:
                article_features_as_full_vec = self.get_features(article)
                unread_articles[i,:] = article_features_as_full_vec[:]
            except AttributeError as e:
                logger.error("Article %s does not have attribute: %s." 
                             % (article.id, e))  
                
        #Create read article vectors
        read_marks = numpy.empty(len(read_article_ids))
        read_marks.fill(UserModelSVM.READ)  
        read_articles = numpy.empty(shape=(len(read_article_ids), 
                                             self.num_features_))
        
        for i, article in enumerate(Article.objects(id__in = read_article_ids)):
            try:
                article_features_as_full_vec = self.get_features(article)
                read_articles[i,:] = article_features_as_full_vec[:]
            except AttributeError as e:
                logger.error("Article %s does not have attribute: %s." 
                             % (article.id, e))           
        
        #SMOTE sample minorities
        #synthetic_read_articles = SMOTE(read_articles, p_synthetic_samples, k) 
        
        #borderlineSMOTE sample minorites if p_synthetic_samples not None
        X = numpy.concatenate((read_articles, unread_articles)) 
        
        self._calculate_mean_and_std_deviation(X)
        X = self._normalize(X)
        
        y = numpy.concatenate((read_marks, unread_marks))
        if p_synthetic_samples is None:
            return X, y
        else:
            new_read_articles, synthetic_read_articles, danger_read_articles = borderlineSMOTE(X = X,
                                                                                               y = y,
                                                                                               minority_target = UserModelSVM.READ,
                                                                                               N = p_synthetic_samples, k = k)
            
            #Create synthetic read samples
            synthetic_marks = numpy.zeros(len(synthetic_read_articles))
            synthetic_marks.fill(UserModelSVM.READ)  
            
            read_marks = numpy.empty(len(new_read_articles))
            read_marks.fill(UserModelSVM.READ)  
            
            danger_read_marks = numpy.empty(len(danger_read_articles))
            danger_read_marks.fill(UserModelSVM.READ)   
            
            logger.info("Use %d read, %d unread, %d danger reads and %d synthetic samples." %
                        (len(read_marks), len(unread_marks), 
                         len(danger_read_marks), len(synthetic_marks)))
        
            return (numpy.concatenate((new_read_articles, 
                                       synthetic_read_articles, 
                                       danger_read_articles,
                                       unread_articles)),
                    numpy.concatenate((read_marks, 
                                      synthetic_marks, 
                                      danger_read_marks,
                                      unread_marks))
                    )  
        
    def set_samples_sizes(self, 
                          p_synthetic_samples = 300,
                          p_majority_samples = 500):
        self.p_synthetic_samples = p_synthetic_samples
        self.p_majority_samples = p_majority_samples
    
    def train(self, read_article_ids = None, unread_article_ids = None):
        '''
        Trains the SVM Classifier.
        read_article_ids should be an iterable over read article ids
        unread_article_ids should be an iterable over unread article ids
        
        If one is None it will be loaded from database.
        '''
        
        #Load user feedback if needed
        if read_article_ids is None:
            read_article_ids = Set(r.article.id 
                                for r 
                                in ReadArticleFeedback.objects(user_id = self.user.id).only("article"))
        else:
            read_article_ids = Set(read_article_ids)

        #Get all articles the user did not read.
        if unread_article_ids is None:
            ranked_article_ids = (a.article.id 
                               for a 
                               in RankedArticle.objects(user_id = self.user.id).only("article"))
            all_article_ids = Set(a.id 
                                  for a 
                                  in Article.objects(id__in = ranked_article_ids).only("id"))
            unread_article_ids = all_article_ids - read_article_ids
        
        #convert all article features
        all_articles, marks = self._get_samples(read_article_ids, 
                                                unread_article_ids,
                                                p_synthetic_samples = self.p_synthetic_samples,
                                                p_majority_samples = self.p_majority_samples)

        logger.debug("Learn on %d samples." % len(marks))            

        self.clf = svm.SVC(kernel='linear')
        self.clf.fit(all_articles, marks)
        
    def save(self):
        #replace old user model with new
        try:
            #pickle classifier and decode it to utf-8
            pickled_classifier = cPickle.dumps(self.clf).decode('utf-8')
            
            pickled_theta = cPickle.dumps(self.theta_).decode('utf-8')
            pickled_sigma = cPickle.dumps(self.sigma_).decode('utf-8')
            
            data = {'clf': pickled_classifier, 
                    'theta': pickled_theta,
                    'sigma': pickled_sigma}
            
            #replace profile
            UserModel.objects(user_id = self.user.id).update(upsert = True,
                                                             set__user_id = self.user.id,
                                                             set__data = data,
                                                             set__version = self.get_version())
            
        except Exception as inst:
            logger.error("Could not save learned user model due to unknown"
                         " error %s: %s" % (type(inst), inst)) 
            
    def load(self):
        try:
            if self.clf is not None:
                return
            
            user_model = UserModel.objects(user_id = self.user.id).first()
            
            if user_model is None:
                logger.debug("UserModel for user %s is empty." % self.user.id)
                self.clf = None
                return
            
            #ensure right version
            if user_model.version != self.get_version():
                logger.debug("UserModel for user %s has wrong version." %
                             self.user.id)
                self.clf = None
                return
            
            #unpickle classifier. it was saved as a utf-8 string.
            #get the str object by encoding it.
            pickled_classifier = user_model.data.clf.encode('utf-8')
            pickled_theta = user_model.data.theta.encode('utf-8')
            pickled_sigma = user_model.data.sigma.encode('utf-8')
            
            self.clf = cPickle.loads(pickled_classifier)
            self.theta_ = cPickle.loads(pickled_theta)
            self.sigma_ = cPickle.loads(pickled_sigma)
                
        except Exception as inst:
            logger.error("Could not load learned user model due to unknown"
                         " error %s: %s" % (type(inst), inst))
        
    def rank(self, doc):
        '''
        doc should be instance of mongodb_models.Article
        '''
        
        self.load()
        
        if self.clf is None:
            logger.error("No classifier for user %s." % self.user.id)
            raise NoClassifier("SVM Classifier for user %s seems to be None."
                               % self.user.id)

        data = numpy.empty(shape=(1,self.num_features_), 
                           dtype=numpy.float32)
        
        data[0] = self.get_features(doc)
        data = self._normalize(data)
        prediction = self.clf.predict(data)
        
        return prediction[0]
        
class UserModelTree(UserModelSVM):
    
    READ = 2
    UNREAD = 1

    @classmethod
    def get_version(cls):
        return "UserModelMeta-1.0"
    
    def train(self, read_article_ids = None, unread_article_ids = None):
        '''
        Trains the DecisionTree Classifier.
        read_article_ids should be an iterable over read article ids
        unread_article_ids should be an iterable over unread article ids
        
        If one is None it will be loaded from database.
        '''
        
        #Load user feedback if needed
        if read_article_ids is None:
            read_article_ids = Set(r.article.id 
                                for r 
                                in ReadArticleFeedback.objects(user_id = self.user.id).only("article"))
        else:
            read_article_ids = Set(read_article_ids)

        #Get all articles the user did not read.
        if unread_article_ids is None:
            ranked_article_ids = (a.article.id 
                               for a 
                               in RankedArticle.objects(user_id = self.user.id).only("article"))
            all_article_ids = Set(a.id 
                                  for a 
                                  in Article.objects(id__in = ranked_article_ids).only("id"))
            unread_article_ids = all_article_ids - read_article_ids
        
        #convert all article features
        all_articles, marks = self._get_samples(read_article_ids, 
                                                unread_article_ids,
                                                p_synthetic_samples = self.p_synthetic_samples,
                                                p_majority_samples = self.p_majority_samples)

        logger.debug("Learn on %d samples." % len(marks))            

        self.clf = tree.DecisionTreeClassifier()
        self.clf.fit(all_articles, marks)
        
        
class UserModelMeta(UserModelSVM):
    
    READ = 2
    UNREAD = 1

    @classmethod
    def get_version(cls):
        return "UserModelMeta-1.0"
    
    def _call_classifiers(self, classifiers, parameters):
        '''
        Calls
        
        articles, marks = self._get_samples(read_article_ids, 
                                            unread_article_ids,
                                            p_synthetic_samples = 300,
                                            p_majority_samples = 500,
                                            k = 10)
        clf = classifier(kernel='rbf')
        clf.fit(articles, marks)
        
        for each classifier and parameter set
        
        Parameters
        ----------
        classifiers : iterable of classifier classes (not instances)
        parameters : an iterable of dictionaries of 
                     form {read_article_ids, 
                           unread_article_ids,
                           p_synthetic_samples = 300,
                           p_majority_samples = 500,
                           k = 10}
        '''
        self.classifiers_ = list()
        for classifier, param_dict in izip(classifiers, parameters):
                articles, marks = self._get_samples(**param_dict)
                clf = classifier()
                clf.fit(articles, marks)
                self.classifiers_.append(clf)
    
    def train(self, read_article_ids = None, unread_article_ids = None):
        '''
        Trains the several SVM and Naive Bayes Classifiers.
        read_article_ids should be an iterable over read article ids
        unread_article_ids should be an iterable over unread article ids
        
        If one is None it will be loaded from database.
        '''
        
        #Load user feedback if needed
        if read_article_ids is None:
            read_article_ids = Set(r.article.id 
                                for r 
                                in ReadArticleFeedback.objects(user_id = self.user.id).only("article"))
        else:
            read_article_ids = Set(read_article_ids)

        #Get all articles the user did not read.
        if unread_article_ids is None:
            ranked_article_ids = (a.article.id 
                               for a 
                               in RankedArticle.objects(user_id = self.user.id).only("article"))
            all_article_ids = Set(a.id 
                                  for a 
                                  in Article.objects(id__in = ranked_article_ids).only("id"))
            unread_article_ids = all_article_ids - read_article_ids
        
        classifiers = [lambda: svm.SVC(kernel='rbf'), 
                       lambda: svm.SVC(kernel='rbf'),
                       lambda: svm.SVC(kernel='rbf'),
                       lambda: svm.SVC(kernel='rbf'),
                       lambda: svm.SVC(kernel='rbf'),
                       GaussianNB, 
                       GaussianNB, 
                       GaussianNB, 
                       GaussianNB]
        
        parameters = [#SVM
                      {'read_article_ids': read_article_ids, 
                       'unread_article_ids': unread_article_ids,
                       'p_synthetic_samples': 100,
                       'p_majority_samples': 200,
                       'k': 10},
                      {'read_article_ids': read_article_ids, 
                       'unread_article_ids': unread_article_ids,
                       'p_synthetic_samples': 200,
                       'p_majority_samples': 300,
                       'k': 10},
                      {'read_article_ids': read_article_ids, 
                       'unread_article_ids': unread_article_ids,
                       'p_synthetic_samples': 300,
                       'p_majority_samples': 400,
                       'k': 10},
                      {'read_article_ids': read_article_ids, 
                       'unread_article_ids': unread_article_ids,
                       'p_synthetic_samples': 400,
                       'p_majority_samples': 500,
                       'k': 10},
                      {'read_article_ids': read_article_ids, 
                       'unread_article_ids': unread_article_ids,
                       'p_synthetic_samples': 500,
                       'p_majority_samples': 600,
                       'k': 10},
                      #Naive Bayes
                      {'read_article_ids': read_article_ids, 
                       'unread_article_ids': unread_article_ids,
                       'p_synthetic_samples': 100,
                       'p_majority_samples': 100,
                       'k': 10},
                      {'read_article_ids': read_article_ids, 
                       'unread_article_ids': unread_article_ids,
                       'p_synthetic_samples': 100,
                       'p_majority_samples': 200,
                       'k': 10},
                      {'read_article_ids': read_article_ids, 
                       'unread_article_ids': unread_article_ids,
                       'p_synthetic_samples': 300,
                       'p_majority_samples': 500,
                       'k': 10},
                      {'read_article_ids': read_article_ids, 
                       'unread_article_ids': unread_article_ids,
                       'p_synthetic_samples': 600,
                       'p_majority_samples': 600,
                       'k': 10}]
        
        self._call_classifiers(classifiers, parameters)
        
    def rank(self, doc):
        '''
        doc should be instance of mongodb_models.Article
        '''
        
        #self.load()
        
        #check if classifiers were loaded

        data = numpy.empty(shape=(1,self.num_features_), 
                           dtype=numpy.float32)
        
        data[0] = self.get_features(doc)
        predictions = numpy.empty(shape=(len(self.classifiers_)))
        for i, clf in enumerate(self.classifiers_):
            predictions[i] = clf.predict(data)

        #Evaluate votes
        uniques = numpy.unique(predictions)
        
        if len(uniques) == 1:
            return uniques[0]
        else: #So far all classifiers have to vote for READ to have it READ
            return self.UNREAD
