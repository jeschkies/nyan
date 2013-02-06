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

require 'nokogiri'
require 'open-uri'
require 'sqlite3'
require 'cgi'
require 'thread'
require 'psych'
require 'log4r'

require 'storage'

module Processor

  CRAWL_WORKERS = 5
  ARTICLE_WORKERS = 10
  PAGES_COUNT = 1000
  class PageContent
    
    @@lock = Mutex.new
    @author, @content, @headline, @name = nil, nil, nil, nil
    
    def initialize(url, config, author = nil, headline = nil)
      
      begin
        html = open(url)
      rescue Exception => ex
        Log4r::Logger['main'].error "Could not open #{url}: #{ex.message}"
        @author, @content, @headline, @name = nil, nil, nil, nil
        return
      end
      
      begin
        doc = Nokogiri::HTML(html.read)
      rescue Exception => ex
        Log4r::Logger['main'].error "Could not read html from #{url}: #{ex.message}"
        return
      end

      #get headline
      if headline != nil
        @headline = headline
      else
        begin
          headline_path = config['headline']['path']
          if config['headline']['type'] == 'CSS'
            @headline = doc.css(headline_path).first
          elsif config['headline']['type'] == 'XPath'
            @headline = doc.xpath(headline_path).first    
          end
    
          @headline = @headline.content.strip
        rescue
          @headline = ""
        end       
      end

      #get author
      if author != nil
        @author = author
      else
        begin
          author_path = config['author']['path']
          if config['author']['type'] == 'CSS'
            @author = doc.css(author_path).first
          elsif config['author']['type'] == 'XPath'
            @author = doc.xpath(author_path).first
          end
          
          @author = @author.content.strip
        rescue
          @author = ""
        end       
      end

      #get content
      begin
        content_path = config['content']['path']
        if config['content']['type'] == 'CSS'
          @content = doc.css(content_path)
        elsif config['content']['type'] == 'XPath'
          @content = doc.xpath(content_path)
        end
      rescue
        @content = nil
      end

      @url = url
      begin
        @name = config['name']
      rescue
        @name = ""
      end
    end

    def store(storage)
        begin
          if @url != nil and @content != nil and @headline != nil and @name != nil and @author != nil
            clean_content = clean_content(@content)
            storage.store_article(@author, @url, @headline, 
              @content.to_s, clean_content, @name)
          end
        rescue Exception => ex
          Log4r::Logger['main'].error "Could not save to storage: #{ex.message}"
        end
    end

    def dump
      "'#{@headline}' by #{@author} on #{@name}"
    end
    
    private
    
    def clean_content(content)
      
      if content.respond_to?('search')
        
         #remove unwanted HTML objects such as scripts, iframes amd images
        content.search(".//script").remove
        content.search(".//iframe").remove
        content.search(".//img").remove
        content.search(".//form").remove
        
        #Remove breaks, tabs and whitespaces
        content.inner_text.gsub(/[ \s]+/, " ")    
      else
        "" 
      end
      
    end

  end

  class UrlProcessor
    
    @config = nil
    
    def initialize(news_service_config)
      @config = news_service_config
    end
    
    def parallel
      
      if @config == nil
        return
      end
      
      batch = GirlFriday::Batch.new(nil, :size => CRAWL_WORKERS) do |url|
        process_list(url)
      end
      
      (1..@config['archive-links']['max']).each do |page_num|
        page = "#{page_num}"
        archive_link = @config['archive-links']['archive-url'].gsub('page_num', page) 
        batch.push(archive_link) do |result|
          Log4r::Logger['main'].info "Finished processing #{archive_link}"
        end
      end
      #batch.results
    end
    
    def serial
      if @config == nil
        return
      end
      
      (1..@config['archive-links']['max']).each do |page_num|
        page = "#{page_num}"
        process_list @config['archive-links']['archive-url'].gsub('page_num', page)
      end
    end

    #process an url list
    def process_list(url)

      begin
        html = open(url)
      rescue Exception => ex
        #TODO make true rescue
        Log4r::Logger['main'].error "Could not open #{url}: #{ex.message}"
        return
      end
      
      Log4r::Logger['main'].info "Crawl #{url}"
      
      doc = Nokogiri::HTML(html.read)
      
      batch = GirlFriday::Batch.new(nil, :size => ARTICLE_WORKERS) do |link|
        process_article(link)
      end
      
      if @config['archive-links']['type'] == 'CSS'
        article_links = doc.css(@config['archive-links']['path'])
      elsif @config['archive-links']['type'] == 'XPath'
        article_links = doc.xpath(@config['archive-links']['path'])
      end

      if article_links == nil
        return  
      end

      # get page content from each article link
      article_links.each do|l|
        batch << l
      end
      batch.results
    end

    #process an article page
    def process_article(l)     
      url = l.attribute("href").value
      if (url =~ URI::regexp).nil?
        #we don't have a correct url try something before giving up
        unless url.start_with?(@config['url'])
          url = URI::join(@config['url'], url).to_s()
        end
        
        #give up
        if (url =~ URI::regexp).nil?
          Log4r::Logger['main'].error "Url is not well formed: #{url}"
          return
        end
      end
      
      page = Processor::PageContent.new url, @config
    
      page.store
    end

  end

end
