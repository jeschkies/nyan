#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Karsten Jeschkies <jeskar@web.de>

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

from datetime import datetime
from gensim import similarities
import logging
from models.mongodb_models import *
from mongoengine import *
import numpy
from user_models import UserModelCentroid

logger = logging.getLogger("main")

class ArticleRanker(object):
    
    def __init__(self, extractor):
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                            level=logging.DEBUG)
                
        self.feature_extractor_ = extractor
        
    def get_vendor(self, article_as_dict):
        #get vendor for article
        try:
            article_vendor = Vendor.objects(name = article_as_dict['news_vendor']).first()
        except Exception as e:
            logger.error("Could not get vender due to error %s: %s" % (type(e), e))
            return None
        return article_vendor
        
    def save_article(self, article_vendor, article_as_dict):
        #save news article with to database
        try:
            features = Features(version = article_as_dict['features']['version'], 
                            data = article_as_dict['features']['data'])
        except KeyError as e:
            logger.error("Could not create features. Features are malformed. Key %s is missing in: %s" %
                        (e, article_as_dict))
            return None
        except Exception as e:
            logger.error("Could not create features due to error %s: %s" % (type(e), e))
            return None
        
        try:
            stored_article = Article(vendor = article_vendor, 
                                     url = article_as_dict['link'],
                                     author = article_as_dict['author'],
                                     headline = article_as_dict['headline'],
                                     clean_content = article_as_dict['clean_content'],
                                     content = article_as_dict['content'],
                                     features = features,
                                     date = datetime.now())
            stored_article.save(safe=True)
        except KeyError as e:
            logger.error("Could not save article. Data is malformed. Key %s is missing in %s."
                         % (e, article_as_dict))
            return None
        except Exception as e:
            logger.error("Could not save article due to error %s: %s" % (type(e), e))
            return None
        
        return stored_article
    
    def save_rating(self, user, article, rating):
        ranked_article = RankedArticle(user_id = user.id,
                                       article = article,
                                       rating = rating)
        ranked_article.save()

        logger.debug("Saved article rating")

    def rank_article(self, article_as_dict):           
        article_vendor = self.get_vendor(article_as_dict)
                
        if article_vendor == None:
            logger.error("No vendor for '%s'" % article_as_dict['news_vendor'])
            return
        
        stored_article = self.save_article(article_vendor, article_as_dict)
        
        if stored_article == None:
            logger.error("Could not save article")
            return
        
        #get users for vendor
        users = User.objects(subscriptions = article_vendor)
        
        #rank article for each user to her profile
        for u in users:            
            user_model = UserModelCentroid(user_id = u.id, 
                                           extractor = self.feature_extractor_)
            
            ranking = user_model.rank(stored_article)
            
            self.save_rating(u, stored_article, ranking) 
