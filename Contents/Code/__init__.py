# DID NOT ADD SORTS BECAUSE THE SITE ALREADY SORTS THE SHOWS BEST AND A DATE SORT CAN MESS UP THE ORDER 
# SINCE OFTEN MULTIPLE VIDEOS ARE UPLOADED ON OR HAVE THE SAME DATE

TITLE    = 'Yahoo Screen'
PREFIX   = '/video/yahooscreen'
# NOT SURE IF CODE BELOW IS NEEDED ANY LONGER
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

YahooURL = 'http://screen.yahoo.com'
YahooExploreURL = 'http://screen.yahoo.com/explore/'
YahooOrigURL = 'http://screen.yahoo.com/yahoo-originals/'
BurningLoveURL = 'http://screen.yahoo.com/burning-love/'
MostPopularURL = 'http://screen.yahoo.com/_xhr/carousel/bcarousel-mixed-popular/?most_popular=videos&categories=[]&thumb_ratio=16x9&pyoff=0&title_lines_max=4&show_cite=&show_date=&show_provider=&show_author=&show_duration=&show_subtitle=&show_provider_links=&apply_filter=&filters=%255B%255D&template=tile&num_cols=3&num_rows=14'
http = 'http:'

# These variables pull the list id and content id from page
RE_LIST_ID = Regex('listId: "(.+?)", pagesConfig: ')
RE_CONTENT_ID = Regex('CONTENT_ID = "(.+?)";')
# This is a global variable for the parameters of the Yahoo JSON data file. Currently it returns 32 items. 
# To add more returned results, add the last number plus 5 to pc_starts and ",1u-1u-1u-1u-1u" to pc_layouts for each five entries you want to add
YahooJSON = 'http://screen.yahoo.com/_xhr/slate-data/?list_id=%s&start=0&count=50&pc_starts=1,6,11,16,21,26&pc_layouts=1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u'
# There is an autocomplete for the yahoo search at 'http://screen.yahoo.com/_xhr/search-autocomplete/?query=' though not sure how it would be used
SearchJSON = 'http://video.search.yahoo.com/search//?p=%s&fr=screen&o=js&gs=0&b=%s'
# The format for this url is YAHOO_TAB_CAROUSEL %(instance_id, content_id, mod_id)
YAHOO_TAB_CAROUSEL = 'http://screen.yahoo.com/_remote/?m_id=MediaRemoteInstance&m_mode=fragment&instance_id=%s&site=ivy&content_id=%s&mod_id=%s&mod_units=30&nolz=1'
RE_TAB_CAROUSEL = Regex('tabview_mediatabs_configs=(.+?)<')
RE_TAB_TITLE = Regex('yui3-tabview-list clearfix(.+?)ul')
RE_CAROUSEL_FULL = Regex('Y.Media.BCarousel(.+?),Y.Media.pageChrome')
RE_CAROUSEL_PART = Regex('Y.Media.BCarousel(.+?),"paginationTemplate":')
RE_CAROUSEL_TYPE = Regex('{"modId":"(.+?)","uuid"')
RE_CAROUSEL_URL = Regex(',"xhrUrl":"(.+?)","paginationTemplate":')
###################################################################################################
def Start():

  ObjectContainer.title1 = TITLE
  #HTTP.CacheTime = CACHE_1HOUR 

###################################################################################################
# NEED TO LOOK AT LIMITING SECTION PULL
@handler(PREFIX, TITLE)
def MainMenu():

  oc = ObjectContainer()
  
  # Yahoo Screen By Section
  oc.add(DirectoryObject(key=Callback(SectionsMain, title='Yahoo Screen by Section', url=YahooExploreURL), title='Yahoo Screen by Section'))
  # Most Popular on Yahoo Screens
  oc.add(DirectoryObject(key=Callback(ProduceCarousel, title='Most Popular on Yahoo Screen', url=MostPopularURL), title='Most Popular on Yahoo Screen'))
  # Latest on Yahoo Screens
  oc.add(DirectoryObject(key=Callback(ShowYahoo, title='Latest Videos on Yahoo Screen', url=YahooURL), title='Latest Videos on Yahoo Screen'))
  
  # Made special menu for Burning Love since it is the most popular show on the site
  # There is also content pull for the Content ID for JSON pull of latest videos and carousel list
  #page = HTML.ElementFromURL(BurningLoveURL, cacheTime = CACHE_1DAY)
  page = HTML.ElementFromURL(BurningLoveURL)
  summary = page.xpath("//head//meta[@name='description']//@content")[0]
  thumb = page.xpath('//img[@alt="Burning Love"]//@style')[0]
  thumb = thumb = thumb.replace("background-image:url('", '').replace("');", '')
  oc.add(DirectoryObject(key=Callback(ShowSection, title='Burning Love', url=BurningLoveURL, thumb=thumb), title='Burning Love', thumb=Resource.ContentsOfURLWithFallback(thumb), summary=summary))

  # Yahoo Search Object
  oc.add(InputDirectoryObject(key=Callback(SearchYahoo, title='Search Yahoo Screen'), title='Search Yahoo Screen', summary="Click here to search Yahoo Screen", prompt="Search for videos in Yahoo Screen"))

  return oc
###################################################################################################
# This is a function that will pull the urls for each of the main sections from the Explore pull down menu
# IT GIVES ALL SECTIONS INCLUDING NEWS AND GAMES THAT ISN'T AVAILABLE ELSWHERE
@route(PREFIX + '/sectionsmain')
def SectionsMain(title, url):

  oc = ObjectContainer(title2=title)

  page = HTML.ElementFromURL(url)
  #HAVING HARD TIME WITH CODE BELOW, SOMETIMES IT GIVES RESULTS OTHER TIME IT DOESN'T
  for section in page.xpath('//div[contains(@class,"nav-1")]/ul/li/a[contains(@data-ylk,"_Explore")]'):
    url = section.xpath('.//@href')[0]
    if not url.startswith('http'):
      url = YahooURL + url
    title = section.xpath('./span//text()')[0]

    # Skip TV shows since none produce videos
    if 'TV Shows' not in title:
      if 'yahoo-originals' in url:
        oc.add(DirectoryObject(key=Callback(YahooOrig, title=title, url=url), title=title))
      else:
        oc.add(DirectoryObject(key=Callback(ShowSection, title=title, url=url, thumb = R(ICON)), title=title))

  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to display right now.")      
  else:
    return oc
 
#########################################################################################################
# This function creates a list of the carousel ids and properly formatted urls from a page 
# This list is used in later functions to produce all the videos or shows in that particular carousel 
@route(PREFIX + '/carousellist')
def CarouselList(url):

  # Here we pulls the carousel data from the web page and put it into a json format
  content = HTTP.Request(url).content
  data_list = RE_CAROUSEL_FULL.findall(content)
  carousel_list = []
  for data in data_list:
    # Add an exception for any data that does not work with regex. This tells us that the page has tabs
    try:
      carousel_type = RE_CAROUSEL_TYPE.search(data).group(1)
    except:
      # The data for ANIMAL ALLSTARS has extra slashes in it, due to having tabs, so we have to remove that
      data = data.replace('\\','')
      carousel_type = RE_CAROUSEL_TYPE.search(data).group(1)
      # if it has backslashes in data, then it has tabs so add a tabs entry to list
      carousel_list.append({'type':'tab', 'url':url})
    carousel_url = RE_CAROUSEL_URL.search(data).group(1)
    carousel_url = YahooURL + carousel_url.replace("\/", '/')
    # To make sure it produces the results properly we need to set the &num_rows= and &num_cols to a set number for paging
    # deleting data after num_rows= does not seem to affect url
    carousel_url = carousel_url.split('&num_cols=')[0] + '&num_cols=4&num_rows=4'
    carousel_list.append({'type':carousel_type, 'url':carousel_url})

  return carousel_list
#########################################################################################################
# This function creates a list for the tab style carousel of instance_ids and mod_ids to be used with YAHOO_TAB_CAROUSEL
# to produce videos for shows that use tabs
# THESE TABS ARE A DIFFERENT TYPE OF URL THAN CAROUSELS AND I CANNOT FIGURE OUT HOW TO INCREASE RESULTS
# AFTER CLICKING ON A TAB AND CHOOSING PAGE 2 OF RESULTS IT CREATES A XHR CAROUSELS URL BUT CANNOT FIND THE DATA FOR IT ANYWHERE IN THE FILE
@route(PREFIX + '/tabcarousellist')
def TabCarouselList(url, title, thumb):
  oc = ObjectContainer()

  # Here we pulls the carousel data from the web page and put it into a json format
  content = HTTP.Request(url).content
  content_id = YahooID(url)
  data_list = RE_TAB_CAROUSEL.findall(content)
  json_list = []
  for data in data_list:
    data = data.replace('\\','')
    json_list.append(data)
  Log('the value of json_list is %s' %json_list)
  json_data = ','.join(json_list)
  Log('the value of json_data is %s' %json_data)
  details = JSON.ObjectFromString(json_data)

  # make as list of tab names
  # but they are not in the code of the page in a script, so have to use regex
  tab_code = RE_TAB_TITLE.search(content).group(1)
  tab_code = tab_code.lstrip('>"')
  tab_code = tab_code.rstrip('<')
  tab_code = tab_code.replace('\\','')
  page = HTML.ElementFromString(tab_code)
  tab_titles = page.xpath('//li/a//text()')

  x=0
  # below is how we pull the data from the json object
  for items in details:
    title = tab_titles[x]
    carousel_url = YAHOO_TAB_CAROUSEL %(items['instanceId'], content_id, items['moduleId'])
    oc.add(DirectoryObject(key=Callback(ProduceCarousel, title=title, url=carousel_url), title=title, thumb=thumb))
    x=x+1

  return oc
###################################################################################################
# This function uses the carousel url lists to get a title from the source page and creates a directories for each carousel url
# WANT TO REORDER TABBED RESULTS TO BRING UP CAROUSELS THEN TABS
@route(PREFIX + '/yahoodirectory')
def YahooDirectory(title, url, thumb):
  oc = ObjectContainer(title2=title)
  # Once we pull the type and url from the json, we need to compare it to carousel id on the page
  try:
    content = HTTP.Request(url).content
  except:
    return ObjectContainer(header=L('Error'), message=L('Unable to access other sections for ths show. Either the show page does not have any additonal videos or they are incompatible with this channel'))
  carousel_list = CarouselList(url)
  page = HTML.ElementFromString(content)
  for ids in carousel_list:
    carousel_type = ids['type']
    # this goes through all the carousel sections in the list and gets the title for each by using the carousel id in the xpath
    if carousel_type == 'tab':
    # if this page has tabs in addition to or instead of carousels, this creates directories for them
      carousel_tabs = TabCarouselList(ids['url'], title, thumb)
      for obj in carousel_tabs.objects:
        oc.add(obj)
    else:
      try:
        title = page.xpath('//div[contains(@id,"%s")]/div/div/div[@class="heading"]/h3//text()' %carousel_type)[0]
      except:
        pass
      oc.add(DirectoryObject(key=Callback(ProduceCarousel, title=title, url=ids['url']), title=title, thumb=thumb))
      
  oc.objects.sort(key = lambda obj: obj.title, reverse=True)

  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This show appears to be empty. There are no sections to display right now.")      
  else:
    return oc
  
###################################################################################################
# This function uses the url of a carousel or tab to pull the the shows or videos within that carousel section
# SEE IF WE CAN ADD PAGING TO THIS &start=30 gives you the next 30 results
@route(PREFIX + '/producecarousel', b=int)
def ProduceCarousel(title, url, b=1):

  oc = ObjectContainer(title2=title)
  # Since each url sent to this function are unique we have to save it for the paging at the bottom
  orig_url = url
  #The tab carousels return errors if you put a page number on then end 
  if '/_remote/' in url:
    page_url = url
  else:
    page_url = url + '&start=' + str(b)
  page = HTML.ElementFromURL(page_url)
  x=0
  for show in page.xpath('//li/div'):
    x=x+1
    # Results without images have no anchor in //div/a, so we get the title and url from /div/p/a and put image in a try
    url = show.xpath('./div/p/a//@href')[0]
    title = show.xpath('./div/p/a//text()')[0]
    if not url.startswith('http'):
      url = YahooURL + url
    if '**' in url:
      url = url.split('**')[1]
      url = url.replace('%3A', ':')
    try:
      thumb = show.xpath('./a/img//@src')[0]
    except:
      thumb = ''
	  
    # Since this produces videos and shows we split the oc.adds based on whether it is a video file or show folder
    # The only thing that is unique about the results are that video page urls end in .html, .html%3Fvp=1, or ;_ylv=3
    # Videos Object
    if url.endswith('.html%3Fvp=1') or url.endswith(';_ylv=3') or url.endswith('.html'):
      # Some videos are produced that are not supported by the Yahoo Screens url service.
      # Ones with a data provider id work except for video.hulu.com and video.cbs.com 
      # If there is not a data provider id, we run a URL Service check.
      data_provider = ''
      try:
        data_provider = show.xpath('.//@data-provider-id')[0]
        #Log('the value of data_provider is %s' %data_provider)
      except:
        # Url service check for the rest
        if URLTest(url) == 'false':
          continue
        else:
          pass

      # Skip data_provider of hulu or cbs. Also blog urls ( contian '/blogs/') fit the URL pattern for the service but give errors when played
      if 'hulu.com' not in data_provider and 'cbstv.com' not in data_provider and '/blogs/' not in url:
        oc.add(VideoClipObject( 
          url=url, 
          title=title, 
          thumb=Resource.ContentsOfURLWithFallback(thumb)))	
    # Show and Section Objects
    # Electric City now proper page to pull data from now so no restrictions
    else:
      oc.add(DirectoryObject(
        key=Callback(ShowSection, title=title, url=url, thumb=thumb), 
        title=title, 
        thumb=Resource.ContentsOfURLWithFallback(thumb)))	

# Paging code that looks for next page. Each page pulls 30 results so 
# we use the x counter and if it is equal to 30, another page is needed for results
# Also put exception for tab carousels since they do not have pages
  if  '/_remote/' not in url:
    if x >= 16:
      b = b + 16
      oc.add(NextPageObject(
        key = Callback(ProduceCarousel, title = title, url=orig_url, b=b), 
        title = L("Next Page ...")))
	

  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This section does not contain any videos that are not compatible with this channel.")      
  else:
    return oc

############################################################################################################################
# This is to test if there is a Plex URL service for  given url.  
#       if URLTest(url) == "true":
@route(PREFIX + '/urltest')
def URLTest(url):
  url_good = ''
  if URLService.ServiceIdentifierForURL(url) is not None:
    url_good = 'true'
  else:
    url_good = 'false'
  return url_good

###############################################################################################################
# This breaks the shows into two sections one for the json pull and one for the list of carousels
@route(PREFIX + '/showsection')
def ShowSection(title, url, thumb):

  oc = ObjectContainer(title2=title)

  # Do not produce json for Animal All Stars since all results are blogs
  if 'Animal All Stars' not in title:
    oc.add(DirectoryObject(
      key=Callback(ShowYahoo, title=title, url=url),
      title='Latest Videos',
      thumb=thumb))

  oc.add(DirectoryObject(
    key=Callback(YahooDirectory, title=title, url=url, thumb=thumb),
    title='All Videos',
    thumb=thumb))
    
  return oc

###################################################################################################
# This function pulls the ID for the JSON data url. All shows have a content ID except Animal All Stars that has a List ID
# So check for List ID first.
@route(PREFIX + '/yahooid')
def YahooID(url):

  content = HTTP.Request(url).content
  ID = ''
  try:
    ID = RE_LIST_ID.search(content).group(1)
  except:
    ID = RE_CONTENT_ID.search(content).group(1)
  return ID
 
######################################################################################################
# This produces the latest videos and the top large image carousel on most pages
# Some of the videos pulled by this function are the same as those pulled from the ProduceCarousel pull
# But the additional videos and data it produces as well as its ability to produce main sections large image 
# carousels make it worth keeping
@route(PREFIX + '/showyahoo')
def ShowYahoo(title, url):

  oc = ObjectContainer(title2=title)
  JSON_ID = YahooID(url)
  JSON_url = YahooJSON %JSON_ID
  content = HTTP.Request(JSON_url).content
  try:
    data = JSON.ObjectFromString(content)
  except:
    return ObjectContainer(header=L('Error'), message=L('This feed does not contain any video'))

  # Several of the json files have nulls at the end of the page that cause errors when pulling the data
  # So prior to entering the loop to pull data we use this code to makes sure the data can be pulled and
  # if not, we deletes the nulls at the end of the data and reproduce the HTML Objects
  for item in data['items']:
    try:
      description = item['summary_short']
    except:
      content = content.replace(',null', '')
      data = JSON.ObjectFromString(content)

  for video in data['items']:
    description = video['summary_short']
    desc_data = HTML.ElementFromString(description)
    summary = desc_data.xpath('//text()')[0]
    title = video['title_short'] 
    thumb = video['image_thumb_url']
    if video['type'] == 'video':
      url = video['link_url'] 
      duration = Datetime.MillisecondsFromString(video['duration'])
      date = Datetime.ParseDate(video['date'])
    else:
      # This section is for show or sections with a type of link in json data. They have no dates or duration
      # and the url in the link_url field does not work with URL service so we pull the url out of summary_short
      url = desc_data.xpath('//a//@href')[0]
      duration = None
      date = None

    # a few entries have no urls
    if url:
      if not url.startswith('http://'):
        url = YahooURL + url
      # This checks for unsupported videos. JSON does not list a data_provider but does include video.provider.com as part of image source
      # As stated earlier, the data providers video.hulu.com and video.cbstv.com as well as blogs fail in the url service 
      if 'hulu.com' not in thumb and 'cbstv.com' not in thumb and '/blogs/' not in url:

        oc.add(VideoClipObject(
          url = url, 
          title = title, 
          thumb = Resource.ContentsOfURLWithFallback(thumb),
          summary = summary,
          duration = duration,
          originally_available_at = date))
	
  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This directory appears to be empty or contains videos that are not compatible with this channel.")      
  else:
    return oc
######################################################################################################
# This functions searches Yahoo Screens at 'http://video.search.yahoo.com/search//?fr=screen&q=love'
# HOW CAN WE DETERMINE WHEN TO STOP ADDING A PAGE? Need to put a count on page
@route(PREFIX + '/searchyahoo', b=int)
def SearchYahoo(title, query, b=1):

  oc = ObjectContainer(title2=title)
  JSON_url = SearchJSON %(query, b)
  try:
    data = JSON.ObjectFromURL(JSON_url)
  except:
    return ObjectContainer(header=L('Error'), message=L('This feed does not contain any video'))

  x=0
  if data.has_key('results'):
    for entry in data['results']:
      x=x+1
      search_data = HTML.ElementFromString(entry)
      url = search_data.xpath('//a//@data-rurl')[0]
      thumb = search_data.xpath('//a/img//@src')[0]
      title = search_data.xpath('//a/div/div/h3//text()')[0]
      duration = Datetime.MillisecondsFromString(search_data.xpath('//a/div/span//text()')[0])
      summary_info = search_data.xpath('//a//@data')[0]
      summary_data = JSON.ObjectFromString(summary_info)
      summary = summary_data['d']
        
      if not url.startswith('http://'):
        url = YahooURL + url

      # had one give no service error with cbs in url
      if 'cbs.html' not in url:
        oc.add(VideoClipObject(
          url = url, 
          title = title, 
          thumb = Resource.ContentsOfURLWithFallback(thumb),
          summary = summary,
          duration = duration))

# Paging code that looks for next page. Each page pulls 30 results so 
# we use the x counter and if it is equal to 30, another page is needed for results
  if x >= 30:
    b = b + 30
    oc.add(NextPageObject(
      key = Callback(SearchYahoo, title = title, b=b, query = query), 
      title = L("Next Page ...")))
	
  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no videos to display right now.")      
  else:
    return oc
###################################################################################################
# This is a function that pulls from the Yahoo Originals page to make sections from carousels 
# This page has a different format so it does not work in the YahooDirectory function and must go directly to ProduceCarousel function
@route(PREFIX + '/maindirectory')
def YahooOrig(title, url):

  oc = ObjectContainer(title2=title)

  content = HTTP.Request(url).content
  carousel_list = CarouselList(url)
  page = HTML.ElementFromString(content)
    # Xpath on Yahoo Originals page is not specific enough to only pull the sections
    # So below is best option with try/except continue
  for section in page.xpath('//div[contains(@class,"yom-stage")]/div/div/div'):
    try:
      carousel_id = section.xpath('./div[contains(@id,"mediabcarouselmixedlpca")]//@id')[0]
    except:
      continue
    for ids in carousel_list:
      carousel_type = ids['type']
      if carousel_id == carousel_type:
        title = section.xpath('./div[contains(@id,"categoryHeader")]/div/div/h1//text()')[0]
        oc.add(DirectoryObject(key=Callback(ProduceCarousel, title=title, url=ids['url']), title=title))

  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to display right now.")      
  else:
    return oc
 
#########################################################################################################
# This function creates a json formatted string from the carousel on a page 
# This is used in later functions to produce all the videos or shows in that particular carousel 
# WANT TO KEEP THIS VERSION OF THE FUNCTION IN THE CODE IN CASE WE WOULD RATHER USE A JSON STRING INSTEAD OF A LIST
@route(PREFIX + '/carousellistalt')
def CarouselListAlt(url):

  # Here we pulls the carousel data from the web page, fix the url data, and create a list of the carousel info and put it into a json formated string
  content = HTTP.Request(url).content
  data_list = RE_CAROUSEL_PART.findall(content)
  json_list = []
  for data in data_list:
    data = data.lstrip('(')
    data = data.replace('"xhrUrl":"', '"xhrUrl":"' + YahooURL)
    # To make sure it produces all the results we have to increase the &num_rows=. (changing the &num_cols decreases image size)
    # deleting data after num_rows= does not seem to affect results so we increase num_rows to 14 with
    data = data.split('&num_rows=')[0] + '&num_rows=14"}'
    json_list.append(data)
  json_data = '[' + (','.join(json_list)) + ']'
  details = JSON.ObjectFromString(json_data)

  # below is the code to pull the necessary data entries from the json object
  #for items in details:
    #carousel_type = items['modId']
    #carousel_url = items['xhrUrl']

  return details
