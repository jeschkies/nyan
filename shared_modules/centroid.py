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
Created on 12.12.2012

@author: karsten jeschkies <jeskar@web.de>

Implementation of a centroid classifier
'''
from gensim.similarities import MatrixSimilarity
import numpy as np
from sklearn.utils import array2d

class CentroidClassifier(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        
    def fit(self, X, y):
        '''
        Parameters
        ----------
        """Fit Centroid classifier according to X, y

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]
            Training vectors, where n_samples is the number of samples
            and n_features is the number of features.

        y : array-like, shape = [n_samples]
            Target values.
        '''
        
        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y have incompatible shapes")
        
        n_features = X.shape[1]
        self.classes = unique_y = np.unique(y)
        n_classes = unique_y.shape[0]
        centroids = np.zeros(shape=(n_classes, n_features))
        
        #Calculate mean for each class
        for i, y_i in enumerate(unique_y):
            centroids[i, :] = np.mean(X[y == y_i, :], axis=0)
            
        #Build similarity index from centroids
        self.similarity_index = MatrixSimilarity(corpus = centroids,
                                                 num_features = n_features)
        
    def predict(self, X):
        """
        Perform classification on an array of test vectors X.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]

        Returns
        -------
        C : array, shape = [n_samples]
            Predicted target values for X
        """
        X = array2d(X)
        
        n_samples = X.shape[0]
        predictions = np.empty(shape=(n_samples))
        for i, sample in enumerate(X):
            similarities = self.similarity_index[sample]
            class_id = np.argmax(similarities)
            predictions[i] = self.classes[class_id]
        
        return predictions