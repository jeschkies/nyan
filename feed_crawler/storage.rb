#!/usr/bin/env ruby
# encoding: utf-8 

# @author: Karsten Jeschkies <jeskar@web.de>
# 
# The MIT License (MIT)
# Copyright (c) 2012-2013 Karsten Jeschkies <jeskar@web.de>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of 
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to use, 
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
# Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


require "dbi"
require 'erb'
require 'json'
require 'log4r'
require 'psych'
require 'stomp'

module Storage
  
  #Different adapters to store crawled news articles.
  
  class Database
    
    #Stores a news article in a mysql database
    
    @@db_user = nil
    @@db_password = nil
    @@db_table =
    @@dbh = nil
    @@stmt = nil
    @@lock = Mutex.new
    
    def initialize(config)
      
      @@db_user = config['user']
      @@db_password = config['passwd']
      @@db_table = config['article-table']
      
      begin
        @@dbh = DBI.connect("DBI:Mysql:masterthesis:localhost", @@db_user, @@db_password)
      rescue DBI::DatabaseError => e
        Log4r::Logger['main'].error "Could not connect to Database."
        Log4r::Logger['main'].error "Error code: #{e.err}"
        Log4r::Logger['main'].error "Error message: #{e.errstr}"
      end
      
      if @@dbh
        @@stmt = @@dbh.prepare("INSERT INTO #{@@db_table} (author, link, headline, 
          content, clean_content, newsservice) VALUES (?, ?, ?, ?, ?, ?)")
      end
    end
    
    def store_article(author, link, headline, content, clean_content, newsservice)
      begin
        @@lock.synchronize do
          @@stmt.execute(author.encode('UTF-8'), link.encode('UTF-8'), 
            headline.encode('UTF-8'), content.encode('UTF-8'), 
            clean_content.encode('UTF-8'), newsservice.encode('UTF-8'))
        end
      rescue Exception => ex
        Log4r::Logger['main'].error "Could not save to database: #{ex.message}"
      end
    end
    
    def close()
      @@dbh.disconnect
    end
    
  end #end class database
  
  class SimpleJSON
    
    #News articles are saved in JSON and then send over a STOMP message queue.
    @client = nil
    
    def initialize()
     @client = Stomp::Client.new("", "", "localhost", 61613)     
    end
    
    def store_article(author, link, headline, content, clean_content, newsservice)
      begin
        document = JSON.generate({
          'author' => author,
          'link' => link,
          'headline' => headline,
          'content' => content,
          'clean_content' => clean_content,
          'news_vendor' => newsservice
        })
        
        @client.publish('queue/rawarticles', document)
        Log4r::Logger['main'].info "Send '#{headline}'"
        
      rescue Exception => ex
        Log4r::Logger['main'].error "Could not send article: #{ex.message}"
      end
    end
    
    def close()
      @client.close()
    end
    
  end #end class simplejson
  
  class HTML
    
    def initialize()
      begin
        @template = ERB.new File.new("article.erb").read, nil, "%"
      rescue Exception => ex
        Log4r::Logger['main'].error "Could not load template: #{ex.message}"
      end
    end
    
    #simple output to an html file
    def store_article(author, link, headline, content, clean_content, newsservice)
      begin        
        fh = File.new("#{newsservice}.html", "w")
        fh.write( @template.result(binding) )
        fh.close()
      rescue Exception => ex
        Log4r::Logger['main'].error "Could not save article: #{ex.message}"
      end
    end
  end #end class HTML
  
end