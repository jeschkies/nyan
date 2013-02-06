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

Some evaluation on reuters dataset.
'''
from centroid import CentroidClassifier
from collections import defaultdict
from corpus import R8Split
from database import FileDatabase
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
        
        logger.info("Created %d synthetic minority samples." 
                    % synthetic_minor_samples.shape[0])
        
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
        latex_table +=  "\hline"
        latex_table +=  "\multirow{%d}{*}{%s}" % (len(results), clf_name)
    
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

def build_smote_latex_table(results):
    
    N_Samples = results.shape[0]
    P_Samples = results.shape[1]
    
    latex_table = """\\begin{table}[h]
                     \\begin{adjustwidth}{-5cm}{-5cm}
                     \\begin{center}
                  """
    latex_table += "\\begin{tabular}{%s}" % ("c|" * (N_Samples +1) )
    latex_table += """\\hline
                       P \\ N 
                   """
    for N in xrange(N_Samples * 100, step = 100):
        latex_table += "& %d" % N
                       
    latex_table += """
                        \\\\
                        \\hline
                        \\hline \n
                    """
        
    for row_i in xrange(P_Samples):
        latex_table += "%d" % (row_i * 100)
        for col_i in xrange(N_Samples):
            latex_table += " & %.5f" % results[row_i, col_i]
        
    latex_table += """\\end{tabular}
                        \\caption{Precision for SMOTE}
                      \\end{center}
                      \\end{adjustwidth}
                      \\end{table}
                   """ % (SMOTE_N or 0)
    
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
    labels = ['earn', 'trade']
    samples = R8Split(db)
    
    SMOTE_N = None
    
    #Setup for classifiers
    classifier_setup = [(CentroidClassifier(), "Centroid"),
                        (svm.SVC(kernel='linear'), "SVM"), 
                        (naive_bayes.GaussianNB(),"Bayes")]
    
    #Load target data
    training_target = np.load(options.path + '/training_target.npy', mmap_mode="r")
    test_true_target = np.load(options.path + '/test_target.npy', mmap_mode="r")
    
    clf_results = defaultdict(lambda: list())
    
    for clf, clf_name in classifier_setup:
    
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

        for feature_name, training_data, test_data in setup:
            precisions, recalls, f1_scores, evaluation_sizes, training_sizes = evaluate(minority_label = labels[0], 
                                                                                      majority_label = labels[1],
                                                                                      training_data = training_data, 
                                                                                      training_target = training_target,
                                                                                      test_data = test_data, 
                                                                                      test_true_target = test_true_target,
                                                                                      clf = clf,
                                                                                      p_synthetic_samples = SMOTE_N,
                                                                                      p_majority_samples = None)#500)
            #transform from dictionary to array
            evaluation_sizes_tmp = [evaluation_sizes[labels[0]], evaluation_sizes[labels[1]]]
            
            clf_results[clf_name].append((feature_name,
                                          precisions,
                                          recalls,
                                          f1_scores,
                                          np.average(f1_scores, weights = evaluation_sizes_tmp)
                                          ))
    
    latex_table = build_latex_table(labels[0], labels[1],
                                    training_sizes, 
                                    evaluation_sizes, 
                                    clf_results)
    
    print latex_table
    
