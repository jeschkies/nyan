'''
Created on 15.10.2012

@author: karsten
'''
from datetime import timedelta
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)
from models.mongodb_models import (Vendor, User, Article, Feedback, RankedArticle, 
                                   ReadArticleFeedback)

class AppUser(UserMixin):
    '''
    '''
    
    def __init__(self, mongodb_user, active=True):
        self.mongodb_user = mongodb_user
        self.active = active

    def is_active(self):
        return self.active
    
    def get_id(self):
        return self.mongodb_user.id
    
    def get_email(self):
        return self.mongodb_user.email
    
    def get_password(self):
        return self.mongodb_user.password
    
    def set_password(self, new_password):
        '''
        Sets the new password. Password should already be hashed etc.
        '''
        #do atomic set
        User.objects(id = self.mongodb_user.id).update_one(set__password = new_password)
    
    #access to models
    def get_user_data(self):
        '''
        Returns mongodb user model
        '''
        return self.mongodb_user
    
    def get_subscriptions(self):
        '''
        Returns iterator to subscriptions of user.
        '''
        return self.mongodb_user.subscriptions
    
    def get_articles(self, date):
        '''
        Returns list of articles between date 0:00 and date 24:00
        '''
        
        #use select_related = 2 to fetch all vendor data
        articles_ = Article.objects(vendor__in=current_user.mongodb_user.subscriptions, 
                                date__gte = date.date(), 
                                date__lt = date.date() + timedelta(days=1)).select_related(2)
        
        #mark articles as read/unread and add id field
        articles_as_dict = []
        for a in articles_:
            #check in database if article has Read Feedback
            feedback = ReadArticleFeedback.objects(user_id = self.mongodb_user.id,
                                                   article = a).first()
            
            tmp_article = a._data
            
            if feedback is None:
                tmp_article['read'] = False
            else:
                tmp_article['read'] = True 
                
            tmp_article['id'] = a.id
            
            articles_as_dict.append(tmp_article)
    
        return articles_as_dict
    
    def get_read_articles(self, date):
        '''
        Returns list of read articles between <date> 0:00 and <date> 24:00
        '''
        all_articles_ = self.get_articles(date)
        
        #filter articles
        #read_articles_ = ReadArticleFeedback.objects(user_id = self.mongodb_user.id,
        #                                             article__in = all_articles_)
        
        #return [a.article._data for a in read_articles_]
        return list()
    
    def get_top_articles(self, date, min_rating):
        '''
        Returns iterator to articles from date and with a rating bigger than
        min_rating.
        '''
        
        #get all articles from specific date
        articles_from_date = Article.objects(date__gte = date.date(), 
                        date__lt = date.date() + timedelta(days=1))
        
        #get all ranked article form loaded articles
        return [a.article for a in RankedArticle.objects(user_id = self.mongodb_user.id, 
                                     rating__gte = min_rating,
                                     article__in = articles_from_date)]
    
    def save_read_article_feedback(self, article, score):
        '''
        Saves a feeback by user: read article.
        
        NOTE: a feedback for one article might be added twice.
        '''
        r = ReadArticleFeedback(user_id = self.mongodb_user.id,
                                article = article, score = score)
        r.save()
        
    def get_trained_profile(self):
        '''
        Return learned user profile.
        '''
        #return self.mongodb_user.learned_profile
        return []
    
    def add_vendor_to_subscriptions(self, vendor):
        '''
        Adds a new vendor to subscriptions.
        vendor should be a mongodb_model object.
        '''
        User.objects(id=self.mongodb_user.id).update_one(add_to_set__subscriptions=vendor)
   
    def remove_vendor_from_subscriptions(self, vendor):
        '''
        Removes vendor form subscriptions.
        vendor should be a mongodb_model object.
        '''
        User.objects(id=self.mongodb_user.id).update_one(pull__subscriptions=vendor)
