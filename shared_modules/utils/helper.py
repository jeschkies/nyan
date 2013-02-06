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
Just some helper functions used quite often
'''
import logging
import sys
import yaml

configs = {}

def load_config(file_path, logger, exit_with_error=False):
    '''
    :param exit_with_error : If set to True the function will call sys.exit(1)
                             thus quitting the program 
                             
    returns config as dict
    '''
    
    #check if config file was loaded already
    if file_path in configs.keys():
        return configs[file_path]
    
    if file_path is None:
        logger.error("Path to config is None.")
        if exit_with_error: sys.exit(1)
    
    with open(file_path, 'r') as config_file:
        try:
            config_ = yaml.load(config_file)
        except Exception as inst:
            logger.error("Unknown error %s: %s" % (type(inst), inst))
            if exit_with_error: sys.exit(1)
        
    if config_ == None:
        logger.error("No config. Exit.")
        if exit_with_error: sys.exit(1)
    
    #add config 
    configs[file_path] = config_    
    
    return config_