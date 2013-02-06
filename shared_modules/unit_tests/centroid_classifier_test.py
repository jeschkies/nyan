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
'''
from centroid import CentroidClassifier
import numpy as np
import unittest

class CentroidClassifierTest(unittest.TestCase):


    def setUp(self):
        self.X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])
        self.Y = np.array([2, 2, 2, 1, 1, 1])

    def tearDown(self):
        pass


    def test_fit(self):
        clf = CentroidClassifier()
        clf.fit(self.X, self.Y)
        
        np.testing.assert_almost_equal(clf.similarity_index.index[1], 
                                      [-2, -1.33333], 
                                      decimal = 5)
    
    def test_predict(self):
        clf = CentroidClassifier()
        clf.fit(self.X, self.Y)
        result = clf.predict([[-0.8, -1]])
        
        self.assertEqual(result, [2])

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()