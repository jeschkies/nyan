#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The :mod:`sklearn.naive_bayes` module implements Naive Bayes algorithms. These
are supervised learning methods based on applying Bayes' theorem with strong
(naive) feature independence assumptions.

"""

# Author: Vincent Michel <vincent.michel@inria.fr>
#         Minor fixes by Fabian Pedregosa
#         Amit Aides <amitibo@tx.technion.ac.il>
#         Yehuda Finkelstein <yehudaf@tx.technion.ac.il>
#         Lars Buitinck <L.J.Buitinck@uva.nl>
#         (parts based on earlier work by Mathieu Blondel)
#
# License: BSD Style.

from abc import ABCMeta, abstractmethod
from collections import defaultdict
from itertools import izip

import numpy as np
from scipy.sparse import issparse

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import binarize, LabelBinarizer
from sklearn.utils import array2d, atleast2d_or_csr
from sklearn.utils.extmath import safe_sparse_dot, logsumexp
from sklearn.utils import check_arrays

__all__ = ['BernoulliNB', 'GaussianNB', 'MultinomialNB']


class BaseNB(BaseEstimator, ClassifierMixin):
    """Abstract base class for naive Bayes estimators"""

    __metaclass__ = ABCMeta

    @abstractmethod
    def _joint_log_likelihood(self, X):
        """Compute the unnormalized posterior log probability of X

        I.e. ``log P(c) + log P(x|c)`` for all rows x of X, as an array-like of
        shape [n_classes, n_samples].

        Input is passed to _joint_log_likelihood as-is by predict,
        predict_proba and predict_log_proba.
        """

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
        jll = self._joint_log_likelihood(X)
        return self.classes_[np.argmax(jll, axis=1)]

    def predict_log_proba(self, X):
        """
        Return log-probability estimates for the test vector X.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]

        Returns
        -------
        C : array-like, shape = [n_samples, n_classes]
            Returns the log-probability of the sample for each class
            in the model, where classes are ordered arithmetically.
        """
        jll = self._joint_log_likelihood(X)
        # normalize by P(x) = P(f_1, ..., f_n)
        log_prob_x = logsumexp(jll, axis=1)
        return jll - np.atleast_2d(log_prob_x).T

    def predict_proba(self, X):
        """
        Return probability estimates for the test vector X.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]

        Returns
        -------
        C : array-like, shape = [n_samples, n_classes]
            Returns the probability of the sample for each class in
            the model, where classes are ordered arithmetically.
        """
        return np.exp(self.predict_log_proba(X))


class GaussianNB(BaseNB):
    """
    Gaussian Naive Bayes (GaussianNB)

    Parameters
    ----------
    X : iterable array-like, shape = [n_features]
        Training vector, n_features is the number of features.

    y : array, shape = [n_samples]
        Target vector relative to X

    Attributes
    ----------
    `class_prior_` : array, shape = [n_classes]
        probability of each class.

    `theta_` : array, shape = [n_classes, n_features]
        mean of each feature per class

    `sigma_` : array, shape = [n_classes, n_features]
        variance of each feature per class

    Examples
    --------
    >>> import numpy as np
    >>> X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])
    >>> Y = np.array([1, 1, 1, 2, 2, 2])
    >>> from sklearn.naive_bayes import GaussianNB
    >>> clf = GaussianNB()
    >>> clf.fit(X, Y)
    GaussianNB()
    >>> print(clf.predict([[-0.8, -1]]))
    [1]
    """

    def fit(self, X, y):
        """Fit Gaussian Naive Bayes according to X, y
        
        Mean and variance are calculated using an online algorithm described here: 
        http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Online_algorithm

        Parameters
        ----------
        X : iterable of array-like, shape = [n_features]
            Training vectors, where n_features is the number of features.

        y : array-like, shape = [n_samples]
            Target values.

        Returns
        -------
        self : object
            Returns self.
        """
        
        self.classes_ = unique_y = np.unique(y)
        n_classes = unique_y.shape[0]

        #n_samples, n_features = X.shape

        #if n_samples != y.shape[0]:
        #    raise ValueError("X and y have incompatible shapes")

        first_sample = None
        for one in X:
            first_sample = one
            break
        n_features = first_sample.shape[0]


        self.theta_ = np.zeros((n_classes, n_features))
        self.sigma_ = np.zeros((n_classes, n_features))
        self.class_prior_ = np.zeros(n_classes)
        
        mapping = defaultdict()
        for i, y_i in enumerate(unique_y):
            mapping[y_i] = i
        
        epsilon = 1e-9
        
        #calculate mean (theta_) and variance (sigma_) online in one pass
        n_samples = 0
        M2 = np.zeros((n_classes, n_features))
        for sample, y_i in izip(X, y):
            n_samples += 1
            i = mapping[y_i]
            
            delta = sample[:] - self.theta_[i, :]
            self.theta_[i, :] += delta[:]/n_samples
            M2[i, :] += delta[:]*(sample[:]-self.theta_[i, :])
            
        self.sigma_[:, :] = M2[:, :]/(n_samples -1) + epsilon

        #calculate prior
        for i, y_i in enumerate(unique_y):
            self.class_prior_[i] = np.float(np.sum(y == y_i)) / n_samples
        return self            

    def _joint_log_likelihood(self, X):
        X = array2d(X)
        joint_log_likelihood = []
        for i in xrange(np.size(self.classes_)):
            jointi = np.log(self.class_prior_[i])
            n_ij = - 0.5 * np.sum(np.log(np.pi * self.sigma_[i, :]))
            n_ij -= 0.5 * np.sum(((X - self.theta_[i, :]) ** 2) / \
                                 (self.sigma_[i, :]), 1)
            joint_log_likelihood.append(jointi + n_ij)

        joint_log_likelihood = np.array(joint_log_likelihood).T
        return joint_log_likelihood