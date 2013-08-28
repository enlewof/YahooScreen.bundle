# DID NOT ADD SORTS BECAUSE THE SITE SORTS AND A DATE SORT CAN MESS UP THE ORDER SINCE MULTIPLE VIDEOS HAVE THE SAME DATE
TITLE    = 'Yahoo Screen'
PREFIX   = '/video/yahooscreen'
# NOT SURE IF CODE BELOW IS NEEDED ANY LONGER
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

YahooURL = 'http://screen.yahoo.com'
YahooExploreURL = 'http://screen.yahoo.com/explore/'
MostPopularURL = 'http://screen.yahoo.com/_xhr/carousel/bcarousel-mixed-popular/?most_popular=videos&categories=[]&thumb_ratio=16x9&pyoff=0&title_lines_max=4&show_cite=&show_date=&show_provider=&show_author=&show_duration=&show_subtitle=&show_provider_links=&apply_filter=&filters=%255B%255D&template=tile&num_cols=3&num_rows=14'

# This returns json data for the large carousel at the top of each page. And uses the content id
# Currently it returns 32 items. To add more returned results, add the last number plus 5 to pc_starts and ",1u-1u-1u-1u-1u" to pc_layouts for each five entries you want to add
YahooJSON = 'http://screen.yahoo.com/_xhr/slate-data/?list_id=%s&start=0&count=50&pc_starts=1,6,11,16,21,26&pc_layouts=1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u'
# There is an autocomplete for the yahoo search at 'http://screen.yahoo.com/_xhr/search-autocomplete/?query=' though not sure how it would be used
SearchJSON = 'http://video.search.yahoo.com/search//?p=%s&fr=screen&o=js&gs=0&b=%s'
# This is for tabs. The format for this url is YAHOO_TAB_CAROUSEL %(instance_id, content_id, mod_id)
YAHOO_TAB_CAROUSEL = 'http://screen.yahoo.com/_remote/?m_id=MediaRemoteInstance&m_mode=fragment&instance_id=%s&site=ivy&content_id=%s&mod_id=%s&mod_units=30&nolz=1'
# This is for carousels and requires the list_id
CAROUSEL_URL = '%s/_xhr/carousel/bcarousel-mixed-list/?list_id=%%s&thumb_ratio=16x9&num_cols=4&num_rows=4&show_date=1&show_cite=1&show_duration=1' % YahooURL

# This regex pulls the carousel data in the form of a json
REGEX_JSON = '(?P<json>\{"modId":"%s".+\}),Y\.Media\.pageChrome'
# These regex variables pull the list id, content id and tab info from page
RE_LIST_ID = Regex('listId: "(.+?)", pagesConfig: ')
RE_CONTENT_ID = Regex('CONTENT_ID = "(.+?)";')
RE_TAB_LIST_ID = Regex(r'bcarousel-mixed-list\\\\.+/?list_id=(.+?)&thumb_ratio')
RE_TAB_CAROUSEL = Regex(r'tabview_mediatabs_configs=(.+?)<')
RE_TAB_TITLE = Regex(r'yui3-tabview-content\\">(.+?)<\\/div')
###################################################################################################
def Start():

  ObjectContainer.title1 = TITLE
  #HTTP.CacheTime = CACHE_1HOUR 
  #HTTP.CacheTime = 900

###################################################################################################
@handler(PREFIX, TITLE)
def MainMenu():

  oc = ObjectContainer()
  
  # Yahoo Screen By Section
  oc.add(DirectoryObject(key=Callback(YahooDirectory, title='Yahoo Screen by Section', url=YahooExploreURL, thumb=R(ICON)), title='Yahoo Screen by Section'))
  # Most Popular on Yahoo Screens
  oc.add(DirectoryObject(key=Callback(ProduceCarousel, title='Most Popular on Yahoo Screen', url=MostPopularURL), title='Most Popular on Yahoo Screen'))
  # Latest on Yahoo Screens
  oc.add(DirectoryObject(key=Callback(ShowYahoo, title='Latest Videos on Yahoo Screen', url=YahooURL), title='Latest Videos on Yahoo Screen'))
  # Yahoo Search Object
  oc.add(InputDirectoryObject(key=Callback(SearchYahoo, title='Search Yahoo Screen'), title='Search Yahoo Screen', summary="Click here to search Yahoo Screen", prompt="Search for videos in Yahoo Screen"))

  return oc
###################################################################################################
# This function pulls the title and makes a url for each carousel on a page and creates a directory
@route(PREFIX + '/yahoodirectory')
def YahooDirectory(title, url, thumb):
  oc = ObjectContainer(title2=title)
  show_title = title
  try:
    content = HTTP.Request(url).content
  except:
    return ObjectContainer(header=L('Error'), message=L('Unable to access other sections for ths show. Either the show page does not have any additonal videos or they are incompatible with this channel'))
   
  for category in HTML.ElementFromString(content).xpath('//div[contains(@id,"mediabcarousel")]'):
    title = category.xpath('./div/div/div[@class="heading"]/h3//text()')[0]
    if len(title) < 1:
      continue

    car_id = category.xpath('.//@id')[0]
    list_id = GetJSON(url, car_id)
    if not list_id:
      continue

    oc.add(DirectoryObject(key=Callback(ProduceCarousel, title=title, url=CAROUSEL_URL %list_id), title=title, thumb=thumb))

  # This checks to see if a page has tabs and creates directories for them
  if '#mediatabs' in content:
    tab_list = RE_TAB_LIST_ID.findall(content)
    Log('the value of tab_list is %s' %tab_list)
    for list_id in tab_list:
     # This pulls any carousels hidden in a nested tab format with backslashes and creates directories for them
     oc.add(DirectoryObject(key=Callback(ProduceCarousel, title=show_title, url=CAROUSEL_URL %list_id), title=show_title, thumb=thumb))

    # This creates directories for the tabs
    carousel_tabs = TabCarouselList(url, title, thumb)
    for obj in carousel_tabs.objects:
      oc.add(obj)
  else:
    pass
      
  #oc.objects.sort(key = lambda obj: obj.title)

  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This show appears to be empty. There are no sections to display right now.")      
  else:
    return oc
  
####################################################################################################
# This function creates a url for each carousel
def GetJSON(url, id):

  page = HTTP.Request(url).content
  json = Regex(REGEX_JSON % id).search(page)

  if json:
    json_obj = JSON.ObjectFromString(json.group('json'))
    xhr_url = json_obj['xhrUrl']
    if 'list_id' in xhr_url:
      list_id = xhr_url.split('list_id=')[-1].split('&')[0]
    else:
      list_id = xhr_url.split('content_id=')[-1].split('&')[0]
    return list_id

  return None

#########################################################################################################
# This function creates directory objects for the tab style carousels. Finds content_id, instance_ids and mod_ids for YAHOO_TAB_CAROUSEL url
# THESE TABS ARE A DIFFERENT TYPE OF URL THAN CAROUSELS AND I CANNOT FIGURE OUT HOW TO INCREASE RESULTS
# AFTER CLICKING ON A TAB AND CHOOSING PAGE 2 OF RESULTS IT CREATES A XHR CAROUSELS URL BUT CANNOT FIND THE DATA FOR IT ANYWHERE IN THE FILE
@route(PREFIX + '/tabcarousellist')
def TabCarouselList(url, title, thumb):
  oc = ObjectContainer()

  content = HTTP.Request(url).content
  content_id = RE_CONTENT_ID.search(content).group(1)

  # Pulls the tab carousel data from the web page and put it into a json format
  data_list = RE_TAB_CAROUSEL.findall(content)
  json_data = ','.join(data_list)
  json_data = json_data.replace('\\','')
  details = JSON.ObjectFromString(json_data)

  # make as list of tab names which are in a script separate from tab carousel data
  tab_code = RE_TAB_TITLE.search(content).group(1)
  tab_code = tab_code.replace('\\','')
  page = HTML.ElementFromString(tab_code)
  tab_titles = page.xpath('//li/a//text()')

  x=0
  # Put the all data together. SKIP THE FIRST ONE SINCE THE FIRST TAB WILL BE PRODUCED AS A REGULAR CAROUSEL
  for items in details:
    title = tab_titles[x] + ' Tab'
    carousel_url = YAHOO_TAB_CAROUSEL %(items['instanceId'], content_id, items['moduleId'])
    if x > 0:
      oc.add(DirectoryObject(key=Callback(ProduceCarousel, title=title, url=carousel_url), title=title, thumb=thumb))
    x=x+1

  return oc
###################################################################################################
# This function uses the carousel section or tab url to pull the list of shows or videos it lists
@route(PREFIX + '/producecarousel', b=int)
def ProduceCarousel(title, url, b=0):

  oc = ObjectContainer(title2=title)
  # Since each url sent to this function are unique we have to save it for the paging at the bottom
  orig_url = url
  # The tab carousels return errors if you put a page number on then end 
  if '/_remote/' in url:
    page_url = url
  else:
    page_url = url + '&start=' + str(b)
  page = HTML.ElementFromURL(page_url)
  x=0
  for show in page.xpath('//li[@class="bcarousel-item"]'):
    x=x+1
    # li without div gives one extra pull without a url but need it that way to get data provider
    # Results without images have no anchor in //div/a, so we get the title and url from /div/p/a and put image in a try
    try:
      url = show.xpath('./div/div/p/a//@href')[0]
    except:
      continue
    title = show.xpath('./div/div/p/a//text()')[0]
    if not url.startswith('http'):
      url = YahooURL + url
    if '**' in url:
      url = url.split('**')[1]
      url = url.replace('%3A', ':')
    try:
      thumb = show.xpath('./div/a/img//@src')[0]
    except:
      thumb = ''
	  
    # Since this produces videos and shows we split the oc.adds based on whether it is a video file or show folder
    # The only thing that is unique about the results are that video page urls end in .html, .html%3Fvp=1, or ;_ylv=3
    # Videos Object
    if url.endswith('.html%3Fvp=1') or url.endswith(';_ylv=3') or url.endswith('.html'):
      try:
        duration = show.xpath('./div/cite/span/text()')[0]
        duration = Datetime.MillisecondsFromString(duration.replace(' - ',''))
        date = Datetime.ParseDate(show.xpath('./div/cite/span/abbr//@title')[0])
      except:
        duration =  None
        date = None
      # Some videos are produced that are not supported by the Yahoo Screens url service. Ones with a data provider id work
      # except for video.hulu.com and video.cbs.com. 
      data_provider = ''
      try:
        data_provider = show.xpath('.//@data-provider-id')[0]
        Log('the value of data_provider is %s' %data_provider)
      except:
        # If there is not a data provider id, we run a URL Service check for the rest
        if URLTest(url) == 'false':
          continue
        else:
          pass

      # Skip data_provider of hulu or cbs. Also blog urls (fit the URL pattern for the service but give errors when played
      if 'hulu.com' not in data_provider and 'cbstv.com' not in data_provider and '/blogs/' not in url:
        oc.add(VideoClipObject( 
          url=url, 
          title=title, 
          duration = duration, 
          originally_available_at = date, 
          thumb=Resource.ContentsOfURLWithFallback(thumb)))	
    # Show and Section Objects (Electric City now proper page to pull data from)
    else:
      oc.add(DirectoryObject(
        key=Callback(ShowSection, title=title, url=url, thumb=thumb), 
        title=title, 
        thumb=Resource.ContentsOfURLWithFallback(thumb)))	

# Paging code that looks for next page. Each page pulls 30 results so 
# we use the x counter and if it is equal to 30, another page is needed for results
# Added for tab carousels since they do not have pages
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
# This function pulls the ID for the JSON data url. All shows have a content ID but the one for Animal All Stars 
# doesn't produce any results so we use its List ID. So check for List ID first.
# ACTUALLY NOT USING THIS FOR ANIMAL ALL STARS BECAUSE ALL RESULTS ARE BLOGS RIGHT NOW
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
# This produces the top large image carousel and latest videos on most pages
# Sometimes the videos pulled by this function are the same as those pulled from the ProduceCarousel pull but often different
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

  # Several of the json files have nulls at the end that cause errors. So prior to entering the loop, 
  # make sure the data can be pulled and if not, delete the nulls and reproduce the HTML Objects
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
    # here we have to add a thumb if there is none to prevent errors in thumb check at end
    if not thumb:
      thumb = R(ICON)
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
