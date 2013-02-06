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
Created on 18.12.2012

@author: karsten jeschkies <jeskar@web.de>

Evaluates SMOTE on the Reuters corpus and creates a nice Latex table.
'''
from centroid import CentroidClassifier
from collections import defaultdict
from py21578.corpus import R8Split
from py21578.database import FileDatabase
from gensim import utils, corpora, models, matutils
from itertools import izip
import logging
import numpy as np
from normalization import normalize, calculate_mean_and_std_deviation
from sklearn import svm, metrics, naive_bayes
from smote import SMOTE, borderlineSMOTE
import sys

logger = logging.getLogger("py21578")  

def evaluate(minority_label,
             majority_label,
             training_data, training_target,
             test_data, test_true_target,
             clf,
             p_synthetic_samples = None,
             p_majority_samples = None):
    '''
    Parameters
    ----------
    minor_label : 
    minor_label : 
    p_synthetic_samples : Sets parameter N for SMOTE. Tells how many synthetic samples are 
                          supposed to be generated.
                          If not None SMOTE is done.
    p_majority_samples : Sets how many majority samples should be used. 
                         n_majority_samples = p_majority_samples/100 * n_minority_samples.
                         If None no under sampling is done.
    '''

    #Normalize training data
    theta, sigma = calculate_mean_and_std_deviation(training_data)
    training_data = normalize(training_data, theta, sigma)
            
    #just train and test on labels
    minor_mask = (training_target == samples.get_target_number(minority_label))
    major_mask = (training_target == samples.get_target_number(majority_label))
    minority_samples = training_data[minor_mask]
    majority_samples = training_data[major_mask]
    
    minority_target = training_target[minor_mask]
    majority_target = training_target[major_mask]
    
    training_sizes = {minority_label: minority_samples.shape[0], 
                    majority_label: majority_samples.shape[0]}
    
    #Under-sampling
    if p_majority_samples is not None:
        logger.info("Under-sample majority class...")    
        n_majority_samples = p_majority_samples / 100 * minority_samples.shape[0]
        np.random.shuffle(majority_samples)
        majority_samples = majority_samples[:n_majority_samples]
        
        logger.info("Selected %d random majority samples." 
                    % majority_samples.shape[0])
        majority_target = np.empty(shape=(majority_samples.shape[0]))
        majority_target[:] = samples.get_target_number(majority_label)
    
    #SMOTE
    if p_synthetic_samples is not None:
        logger.info("SMOTE minority class...")
        
        #Create synthetic data and target
        synthetic_minor_samples = SMOTE(minority_samples, p_synthetic_samples, k = 5)
        synthetic_targets = np.empty(shape=(synthetic_minor_samples.shape[0]))
        synthetic_targets[:] = samples.get_target_number(minority_label)
        
        logger.info("Created %d synthetic minority samples from %d samples with N = %d." 
                    % (synthetic_minor_samples.shape[0], minority_samples.shape[0],
                       p_synthetic_samples))
        
        #Add synthetic data and target
        minority_samples = np.concatenate((minority_samples, synthetic_minor_samples))
        minority_target = np.concatenate((minority_target, synthetic_targets))
        
    #Put minorities and majorities together
    training_data = np.concatenate((minority_samples,majority_samples))
    training_target = np.concatenate((minority_target,majority_target))
    
    #Train
    logger.info("Train classifier...")
    clf.fit(training_data, training_target)

    #Just use targets for labels
    mask = (test_true_target == samples.get_target_number(minority_label))
    neg_mask = (test_true_target == samples.get_target_number(majority_label))
    
    evaluation_sizes = {minority_label: np.sum(mask), 
                        majority_label: np.sum(neg_mask)}
    
    test_data = np.concatenate((test_data[mask],test_data[neg_mask]))
    test_true_target = np.concatenate((test_true_target[mask],test_true_target[neg_mask]))
    
    #Normalize test data
    test_data = normalize(test_data, theta, sigma)
    
    test_predicted_target = clf.predict(test_data)
                
    logger.debug("Predicted classes: %s" % unicode(np.unique(test_predicted_target)))
    logger.debug("%d, %d" % (np.sum(test_predicted_target == samples.get_target_number(minority_label)), 
                             np.sum(test_predicted_target == samples.get_target_number(majority_label))))
                
    #Score test data, target
    logger.info("Calculate F1 Score...")
    precisions, recalls, f1_scores, _ = metrics.precision_recall_fscore_support(test_true_target, 
                                                                                test_predicted_target,
                                                                                pos_label = None)
    
    for precision, recall, f1_score, label \
    in izip(precisions, recalls, f1_scores, [minority_label, majority_label]):
        logger.info("%s: Recall = %.5f, Precision = %.5f, F1 Score = %.5f" % 
                    (label, recall, precision, f1_score))
        
    return precisions, recalls, f1_scores, evaluation_sizes, training_sizes

def build_latex_table(minority_label, majority_label,
                      training_sizes, 
                      evaluation_sizes, 
                      clf_results):
    latex_table = """\\begin{table}[h]
                     \\begin{adjustwidth}{-5cm}{-5cm}
                     \\begin{center}
                     \\begin{tabular}{c | c || c|c|c || c|c|c || c}
                     """
    latex_table += "& & \\multicolumn{3}{c||}{'%s' (%d/%d)}" % (minority_label, training_sizes[minority_label], evaluation_sizes[minority_label])
    latex_table += " & \\multicolumn{3}{c||}{'%s' (%d/%d)}" % (majority_label, training_sizes[majority_label], evaluation_sizes[majority_label]) 
    latex_table += " &  \\\\ "
    latex_table += """\\hline
                       Classifier & Features & Precision & Recall & F1 Score & Precision & Recall & F1 Score & Average \\\\
                        \\hline
                        \\hline \n
                    """
        
    for clf_name, results in clf_results.iteritems():
        latex_table +=  "%" + clf_name + " results% \n"
        latex_table +=  "\\hline"
        latex_table +=  "\\multirow{%d}{*}{%s}" % (len(results), clf_name)
    
        for feature_name, precisions, recalls, f1_scores, average in results:
            latex_table += """
                            & %s & %.5f & %.5f & \\cellcolor{gray!25}%.5f & %.5f & %.5f & \\cellcolor{gray!25}%.5f & %.5f \\\\
                            \\cline{2-9}
                           """ % (feature_name, precisions[0], recalls[0], f1_scores[0],
                                  precisions[1], recalls[1], f1_scores[1],
                                  average)
                       
        latex_table += """\\hline \n"""
        
    latex_table += """\\end{tabular}
                        \\caption{Imbalanced training data \\textit{with} SMOTE (N = %d) }
                      \\end{center}
                      \\end{adjustwidth}
                      \\end{table}
                   """ % (SMOTE_N or 0)
    
    return latex_table

def build_smote_latex_table(minority_label, majority_label, results):

    latex_table = """\\begin{table}[h]
                     \\begin{adjustwidth}{-5cm}{-5cm}
                     \\begin{center}
                     \\begin{tabular}{c || c|c|c || c|c|c || c}
                     """
    latex_table += "& \\multicolumn{3}{c||}{'%s'} & \\multicolumn{3}{c||}{'%s'} &  \\\\ \\hline" % (majority_label, minority_label)
    latex_table += """ Features & Precision & Recall & F1 Score & Precision & Recall & F1 Score & N/P \\\\
                        \\hline
                        \\hline \n
                    """

    for feature_name, precisions, recalls, f1_scores, N, P in results:
        latex_table += """
                            %s & %.5f & %.5f & \\cellcolor{gray!25}%.5f & %.5f & %.5f & \\cellcolor{gray!25}%.5f & %d / %d \\\\
                       """ % (feature_name, precisions[0], recalls[0], f1_scores[0],
                                  precisions[1], recalls[1], f1_scores[1],
                                  N, P)
                    
    latex_table += """\\end{tabular}
                        \\caption{Imbalanced training data \\textit{with} SMOTE and SVM classifier}
                      \\end{center}
                      \\end{adjustwidth}
                      \\end{table}
                   """
    
    return latex_table
                        
if __name__ == '__main__':
    from optparse import OptionParser
    
    p = OptionParser()
    p.add_option('-p', '--path', action="store", dest='path',
                 help="specify path to Reuters-21579 files")
    p.add_option('-l', '--log', action="store", dest='log',
                 help="specify log file")
    p.add_option('-o', '--output-prefix', action="store", dest='prefix',
                     help="specify path prefix where everything should be saved")
    (options, args) = p.parse_args()
    
    logger.setLevel(logging.DEBUG)
    
    # create file handler which logs even debug messages
    fh = logging.FileHandler(options.log)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s : %(levelname)s in %(module)s ' +
                                  '[%(pathname)s:%(lineno)d]: %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)
    
    logger.info("running %s" % ' '.join(sys.argv))
    
    #Load Reuters-21578 dataset
    if options.path is None:
        logger.error("Path to Reuters-21578 dataset not set.")
        sys.exit(1) 
    
    db = FileDatabase(reuters_path = None, 
                      database_path =  options.path + "/reuters.db")
    
    #Set corpus
    labels = ['earn', 'interest']
    samples = R8Split(db)
    
    N_MAX = 500
    P_MAX = 500
    
    clf = svm.SVC(kernel='linear')
    
    #results = [('TFIDF', list([ 0.9491018 ,  0.53296703]), list([ 0.88178025,  0.74045802]), list([ 0.91420332,  0.61980831]), 600, 600), ('LDA-20', list([ 0.96616541,  0.20890411]), list([ 0.35744089,  0.93129771]), list([ 0.52182741,  0.34125874]), 600, 600), ('LDA-50', list([ 0.96498906,  0.29262087]), list([ 0.61335188,  0.8778626 ]), list([ 0.75     ,  0.4389313]), 600, 600), ('LDA-BOW-20', list([ 0.96810934,  0.28467153]), list([ 0.59109875,  0.89312977]), list([ 0.73402418,  0.43173432]), 600, 600), ('LDA-BOW-30', list([ 0.97807018,  0.3071066 ]), list([ 0.62030598,  0.92366412]), list([ 0.75914894,  0.46095238]), 600, 600), ('LDA-BOW-50', list([ 0.9826087 ,  0.31538462]), list([ 0.6286509,  0.9389313]), list([ 0.76675148,  0.47216891]), 600, 600), ('mESA-1000', list([ 0.99843994,  0.62200957]), list([ 0.89012517,  0.99236641]), list([ 0.94117647,  0.76470588]), 600, 600)]    
    
    #Load target data
    training_target = np.load(options.path + '/training_target.npy', mmap_mode="r")
    test_true_target = np.load(options.path + '/test_target.npy', mmap_mode="r")
    
    #Setup for each Feature set
    setup = [("TFIDF", 
               np.load(options.path + '/training_data_tfidf.npy', mmap_mode="r"),
               np.load(options.path + '/test_data_tfidf.npy', mmap_mode="r"),
               ),
             ("LDA-20",
               np.load(options.path + '/training_data_lda_20.npy', mmap_mode="r"),
               np.load(options.path + '/test_data_lda_20.npy', mmap_mode="r")
               ),
             ("LDA-50",
               np.load(options.path + '/training_data_lda_50.npy', mmap_mode="r"),
               np.load(options.path + '/test_data_lda_50.npy', mmap_mode="r")
               ),
             ("LDA-BOW-20",
               np.load(options.path + "/training_data_lda_bow_20.npy", mmap_mode="r"),
               np.load(options.path + "/test_data_lda_bow_20.npy", mmap_mode="r")
              ),
             ("LDA-BOW-30",
               np.load(options.path + "/training_data_lda_bow_30.npy", mmap_mode="r"),
               np.load(options.path + "/test_data_lda_bow_30.npy", mmap_mode="r")
              ),
             ("LDA-BOW-50",
               np.load(options.path + "/training_data_lda_bow_50.npy", mmap_mode="r"),
               np.load(options.path + "/test_data_lda_bow_50.npy", mmap_mode="r")
              ),
             ("mESA-1000",
               np.load(options.path + "/training_data_cesa.npy", mmap_mode="r"),
               np.load(options.path + "/test_data_cesa.npy", mmap_mode="r")
              )]
    
    results = list()
    
    for feature_name, training_data, test_data in setup:
        
        current_best_precision = 0.0
        
        for SMOTE_N in xrange(100, N_MAX, 100):
            for P in xrange(100, P_MAX, 100):
                precisions, recalls, f1_scores, evaluation_sizes, _ = evaluate(minority_label = labels[1], 
                                                                                          majority_label = labels[0],
                                                                                          training_data = training_data, 
                                                                                          training_target = training_target,
                                                                                          test_data = test_data, 
                                                                                          test_true_target = test_true_target,
                                                                                          clf = clf,
                                                                                          p_synthetic_samples = SMOTE_N,
                                                                                          p_majority_samples = P)
                
                if precisions[1] > current_best_precision:
                    current_best_precision = precisions[1]
                    best_results = (feature_name, 
                                    precisions, recalls, f1_scores, 
                                    SMOTE_N, P)
                
        results.append(best_results)
    
    #Create and Print table
    latex_table = build_smote_latex_table(minority_label = labels[1], 
                                          majority_label = labels[0],
                                          results = results)
    
    print latex_table
    