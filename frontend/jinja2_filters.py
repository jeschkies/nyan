# -*- coding: utf-8 -*-
'''
Created on 02.10.2012

@author: karsten
'''
from datetime import datetime, timedelta
from nltk.tokenize import sent_tokenize
import time



#jinja2 filter to format date and time for links
def datetimeformat(value, format=u'%d-%m-%Y'):
    return value.strftime(format)

#jinja2 filter to format date and time for nice readability
def datetimeformat_read(value, format=u'%d-%m-%Y'):
    if is_today(value):
        return "Today"
    if(datetime.now()-value-timedelta(days=1) < timedelta(days=1)):
        return "Yesterday"
    return value.strftime(format)

#jinja2 filter to to get first two sentences of article
def firstparagraph(value):
    sentences = sent_tokenize(value)
    return " ".join(sentences[0:2])

#jinja2 filter to get pervious day of datetime
def prevdate(value):
    d = value-timedelta(days=1)
    return d

#jinja2 filter to get next day of datetime
def nextdate(value):
    d = value+timedelta(days=1)
    return d

#jinja2 filter returns true if date (value) is today
def is_today(value):
    if datetime.now()-value < timedelta(days=1):
        return True
    return False

#jinja2 filter to measure performance
START_TIME = 0
def start_timer(value):
    global START_TIME
    START_TIME = time.time()
    
    return value

def end_timer(value, timer_name):
    elapsed_time = time.time() - START_TIME
    #cherrypy.log.error("%s took %.3f s" % (timer_name, elapsed_time))
    
    return value