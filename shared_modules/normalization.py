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
Created on 10.12.2012

@author: karsten jeschkies <jeskar@web.de>

Methods to normalize vectors.
'''

import logging
import numpy

logger = logging.getLogger('main')

def calculate_mean_and_std_deviation(X):
    '''
    Caluclates mean and standard deviation of sample features.
    
    Parameters
    ----------
    X : array-like, samples, shape = (n_samples, n_features)
    
    Returns
    -------
    theta, sigma
    '''
    
    _, n_features = X.shape
    
    theta = numpy.zeros((n_features))
    sigma = numpy.zeros((n_features))
    epsilon = 1e-9
    
    theta[:] = numpy.mean(X[:,:], axis=0)
    sigma[:] = numpy.std(X[:,:], axis=0) + epsilon
    
    return theta, sigma
    
def normalize(X, theta, sigma):
    '''
    Normalizes sample features.
    
    self.theta_ and self.sigma_ have to be set.
    
    Parameters
    ----------
    X : array-like, samples, shape = (n_samples, n_features)
    
    Returns
    -------
    normalized X
    '''
        
    n_samples, n_features = X.shape
    
    new_X = numpy.zeros(shape=(n_samples, n_features), dtype=numpy.float32)

    new_X[:,:] = (X[:,:] - theta[:]) / sigma[:]
    
    return new_X