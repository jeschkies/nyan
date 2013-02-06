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
Created on 04.12.2012

@author: karsten jeschkies <jeskar@web.de>
'''
import unittest

from itertools import izip
import numpy as np
from sklearn.feature_selection import SelectKBest, f_classif
from selectkbest import iSelectKBest, if_classif

class TestiSelectKBest(unittest.TestCase):


    def setUp(self):
        self.X = np.array([[5,   3.5, 8  ],
                      [4.5, 7,   4  ],
                      [4,   2,   3.5],
                      [3,   4.5, 2  ]]) 
        
        self.y = np.array([2, 1, 1, 2])


    def tearDown(self):
        pass


    def test_original(self):

        selector = SelectKBest(f_classif, k=1)
        selector.fit(self.X, self.y)
        r = selector.transform(self.X)
        print r
        
    def test_iter(self):
        
        #Calculate original
        selector_original = SelectKBest(f_classif, k=1)
        selector_original.fit(self.X, self.y)        
        
        #Calculate custom
        X_y = izip(self.X, self.y)

        selector = iSelectKBest(if_classif, k=1)
        selector.fit(X_y, self.X.shape[1])
        
        #Asserts
        np.testing.assert_array_almost_equal([0.05882353, 0.03846154, 0.17241379], 
                                             selector.scores_, 8)
        np.testing.assert_array_almost_equal([0.83096915, 0.86263944, 0.71828192], 
                                             selector.pvalues_, 8)
        
        #Asserts
        np.testing.assert_array_equal(selector_original.scores_, 
                                      selector.scores_)
        np.testing.assert_array_equal(selector_original.pvalues_, 
                                      selector.pvalues_)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()