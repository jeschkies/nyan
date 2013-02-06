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

require '../processor.rb'
require 'psych'
require 'girl_friday'
gem 'test-unit'
require 'test/unit'

#Tests for UrlProcessor and configs for different sites

class TestUrlProcessor < Test::Unit::TestCase
  
  def setup  
    
    #GirlFriday::Queue.immediate! 
    
    @news_service_config = Psych.load_file("../articles-config.yaml")
    
    #change store in pagecontent to just output and not save to db
    Processor::PageContent.class_eval do
      def store
        Log4r::Logger['main'].debug "'#{@headline}' by #{@author}"
      end      
    end
    
    #setup logger
    logger = Log4r::Logger.new('main')
    logger.outputters << Log4r::FileOutputter.new('filelog', 
      :filename => 'testing.log')

  end
  
  def teardown
    #nothing yet
  end
   
  def test_processor_techcrunch_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][0]
    processor.process_list "http://techcrunch.com/page/1/"
  end
  
  def test_processor_techcrunch_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][0]
    processor.serial
  end
  
  def test_processor_allthingsd_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][1]
    processor.process_list "http://allthingsd.com/page/3/"
  end
  
  def test_processor_allthingsd_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][1]
    processor.serial
  end
  
  def test_processor_engadget_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][2]
    processor.process_list "http://www.engadget.com/page/3/"
  end
  
  def test_processor_engadget_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][2]
    processor.serial   
  end
  
  def test_processor_mashable_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][3]
    processor.process_list "http://mashable.com/page/3/"
  end
  
  def test_processor_mashable_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][3]
    processor.serial   
  end
  
  def test_processor_theverge_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][4]
    processor.process_list "http://www.theverge.com/archives/3"      
  end
  
  def test_processor_theverge_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][4]
    processor.serial     
  end
  
  def test_processor_venturebeat_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][5]
    processor.process_list "http://venturebeat.com/page/3/"        
  end
  
  def test_processor_venturebeat_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][5]
    processor.serial       
  end
  
  def test_processor_macrumors_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][6]
    processor.process_list "http://www.macrumors.com/3/"
  end
  
  def test_processor_macrumors_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][6]
    processor.serial       
  end
  
  def test_processor_readwriteweb_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][7]
    processor.process_list "http://www.readwriteweb.com/indexpage2.php"    
  end
  
  def test_processor_readwriteweb_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][7]
    processor.serial     
  end
  
  def test_processor_anandtech_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][8]
    processor.process_list "http://www.anandtech.com/Page/2"        
  end
  
  def test_processor_anandtech_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][8]
    processor.serial     
  end
  
  def test_processor_businessinsider_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][9]
    processor.process_list "http://www.businessinsider.com/?page=2"        
  end
  
  def test_processor_businessinsider_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][9]
    processor.serial         
  end
  
  def test_processor_androidandme_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][10]
    processor.process_list "http://androidandme.com/page/2/"     
  end
  
  def test_processor_androidandme_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][10]
    processor.serial      
  end
  
  def test_processor_bgr_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][11]
    processor.process_list "http://www.bgr.com/page/2/"       
  end
  
  def test_processor_bgr_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][11]
    processor.serial   
  end
  
  def test_processor_allfacebook_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][12]
    processor.process_list "http://allfacebook.com/page/2/"      
  end
  
  def test_processor_allfacebook_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][12]
    processor.serial       
  end
  
  #test_torrentfreak missing
  
  def test_processor_thenextweb_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][14]
    processor.process_list "http://thenextweb.com/page/2/"      
  end
  
  def test_processor_thenextweb_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][14]
    processor.serial     
  end
  
  def test_processor_gigaom_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][15]
    processor.process_list "http://gigaom.com/page/2/"         
  end
  
  def test_processor_gigaom_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][15]
    processor.serial       
  end
  
  def test_processor_slashgear_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][16]
    processor.process_list "http://www.slashgear.com/page/4/"     
  end
  
  def test_processor_slashgear_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][16]
    processor.serial      
  end
  
  def test_processor_boingboing_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][17]
    processor.process_list "http://www.boingboing.net/page/4/"     
  end
  
  def test_processor_boingboing_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][17]
    processor.serial    
  end
  
  def test_processor_gizmodo_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][18]
    processor.process_list "http://blog.gizmodo.com/?p=2"        
  end
  
  def test_processor_gizmodo_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][18]
    processor.serial    
  end
  
  def test_processor_joystiq_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][19]
    processor.process_list "http://www.joystiq.com/page/2/"       
  end
  
  def test_processor_joystiq_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][19]
    processor.serial     
  end
  
  def test_processor_eurogamer_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][20]
    processor.process_list "http://www.eurogamer.net/ajax.php?action=frontpage&page=3&"     
  end
  
  def test_processor_eurogamer_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][20]
    processor.serial     
  end
  
  def test_processor_gamefront_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][22]
    processor.process_list "http://www.gamefront.com/news/page/3/"      
  end
  
  def test_processor_gamefront_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][22]
    processor.serial   
  end
  
  def test_processor_shacknews_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][23]
    processor.process_list "http://www.shacknews.com/news?page=3"    
  end
  
  def test_processor_shacknews_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][23]
    processor.serial      
  end
  
  def test_processor_ubergizmo_list
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][24]
    processor.process_list "http://www.ubergizmo.com/page/3/"    
  end
  
  def test_processor_ubergizmo_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][24]
    processor.serial     
  end
  
  def test_rockpapershotgun_init
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][25]
    processor.process_list "http://www.rockpapershotgun.com/page/3/"       
  end
  
  def test_rockpapershotgun_serial
    omit()
    processor = Processor::UrlProcessor.new @news_service_config['articles'][25]
    processor.serial       
  end
end