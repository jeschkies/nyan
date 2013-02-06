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

#Crawls content from articles linked in RSS feeds.

$: << File.expand_path(File.dirname(__FILE__))

require 'rubygems'
require 'feedzirra'
require 'log4r'
require 'optparse'
require 'ostruct'
require 'psych'
require 'processor'
require 'storage'

class OptionParser
  
  #
  # Return a structure describing the options.
  #
  def self.parse(args)
    options = OpenStruct.new
    
    opts = OptionParser.new do |opts|
      opts.banner = "Usage: feed_crawler.rb [options]"

      opts.separator ""
      opts.separator "Feed_Crawler options:"
    
      #Add log path option
      opts.on("-l", "--log PATH",
              "Log to PATH") do |log|
        options.log_path = log
      end
      
      #Add config path option
      opts.on("-c", "--config PATH",
              "Load config from PATH") do |config|
        options.config_path = config
      end 
      
      #Add state path option   
      opts.on("-s", "--state PATH",
              "Load and save state from/to PATH") do |state|
        options.state_path = state
      end  
      
      #Show Help
      opts.on_tail("-h", "--help", "Show this message") do
        puts opts
        exit
      end
    end
    
    opts.parse!(args)
    
    #if log, config and state are not given
    if options.log_path == nil or options.config_path == nil or
      options.state_path == nil then
      puts "Some options are missing."
      puts opts.help
      exit
    end
    
    options   
    
  end #end parse()
  
end #end class def

def save_state(vendor_names, newest_entry_url, state_path)
  feed_to_yaml = {}
  
  vendor_names.each do |vendor_name|
    feed_to_yaml[vendor_name] = {
      'last_entry' => newest_entry_url[vendor_name]
    }
  end
  
  file = File.new(state_path, "w")
  Psych.dump(feed_to_yaml, file)
end

#main
if __FILE__ == $0
  
  #parse options
  options = OptionParser.parse(ARGV)
  
  #setup logger
  logger = Log4r::Logger.new('main')
  logger.outputters << Log4r::StdoutOutputter.new('stdout')
  logger.outputters << Log4r::FileOutputter.new('filelog', 
    :filename => options.log_path)
  
  #load config
  config_path = options.config_path
  feed_state_path = options.state_path
  
  Log4r::Logger['main'].info "Load config."
  begin
    news_feed_config = Psych.load_file(config_path)
  rescue
    Log4r::Logger['main'].error "Could not load config."
    abort("ABORT: Could not load config.")
  end
  
  #load old state
  old_entry_urls = Psych.load_file(feed_state_path)
  
  #all feed which should be crawled are under feeds
  feeds_to_crawl = news_feed_config['feeds']
  
  #create array of links to feeds
  feed_links = []
  feeds_to_crawl.each do |vendor_name|
    feed_links << news_feed_config['vendors'][vendor_name]['feed-url']
  end
  
  #create storage object
  begin
    st_json = Storage::SimpleJSON.new
  rescue Exception => e
    Log4r::Logger['main'].error "Could not connect to stomp broker:" + e.inspect
    abort("ABORT: Could not connect to stomp broker:" + e.inspect)
  end
  
  Log4r::Logger['main'].info "Crawl feeds..."
  Log4r::Logger['main'].debug feed_links
  feeds = Feedzirra::Feed.fetch_and_parse(feed_links)
  
  newest_entry_urls = {}

  #save entries for each feed
  feeds_to_crawl.each do |vendor_name|
    
    Log4r::Logger['main'].debug "Entries for #{vendor_name}"
    
    #get feed link as for ahs key
    feed_url = news_feed_config['vendors'][vendor_name]['feed-url']
    
    begin
      newest_entry_urls[vendor_name] = feeds[feed_url].entries.first.url
    rescue Exception => e
      Log4r::Logger['main'].error "Could not get newest url for #{vendor_name} feed:" + e.inspect
      newest_entry_urls[vendor_name] = ""
      next    
    end
    
    feeds[feed_url].entries.each do |entry|
      
      if old_entry_urls[vendor_name] != nil then
        break if old_entry_urls[vendor_name]['last_entry'] == entry.url
      end
      
      #workaround: name is not saved in config anymore
      news_feed_config['vendors'][vendor_name]['scraping']['name'] = vendor_name
      
      #crawl page
      page_content = Processor::PageContent.new(entry.url,
        news_feed_config['vendors'][vendor_name]['scraping'],
        entry.author, entry.title)
      
      #save/send page
      Log4r::Logger['main'].debug page_content.dump
      page_content.store st_json
    end
  end
  
  st_json.close()
  save_state(feeds_to_crawl, newest_entry_urls, options.state_path)
end