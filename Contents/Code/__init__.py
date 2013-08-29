# DID NOT ADD SORTS BECAUSE THE SITE SORTS AND A DATE SORT CAN MESS UP THE ORDER SINCE MULTIPLE VIDEOS HAVE THE SAME DATE
TITLE    = 'Yahoo Screen'
PREFIX   = '/video/yahooscreen'
# NOT SURE IF CODE BELOW IS NEEDED ANY LONGER
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

YahooURL = 'http://screen.yahoo.com'
YahooExploreURL = 'http://screen.yahoo.com/explore/'
MostPopularURL = 'http://screen.yahoo.com/_xhr/carousel/bcarousel-mixed-popular/?most_popular=videos&categories=[]&thumb_ratio=16x9&pyoff=0&title_lines_max=4&show_cite=&show_date=&show_provider=&show_author=&show_duration=&show_subtitle=&show_provider_links=&apply_filter=&filters=%255B%255D&template=tile&num_cols=3&num_rows=14'

# There is an autocomplete for the yahoo search at 'http://screen.yahoo.com/_xhr/search-autocomplete/?query=' though not sure how it would be used
SearchJSON = 'http://video.search.yahoo.com/search//?p=%s&fr=screen&o=js&gs=0&b=%s'
# This is for tabs. The format for this url is YAHOO_TAB_CAROUSEL %(instance_id, content_id, mod_id)
YAHOO_TAB_CAROUSEL = 'http://screen.yahoo.com/_remote/?m_id=MediaRemoteInstance&m_mode=fragment&instance_id=%s&site=ivy&content_id=%s&mod_id=%s&mod_units=30&nolz=1'
# This is for carousels and requires the list_id
CAROUSEL_URL = '%s/_xhr/carousel/bcarousel-mixed-list/?list_id=%%s&thumb_ratio=16x9&num_cols=1&num_rows=25&show_date=1&show_cite=1&show_duration=1' % YahooURL

# This regex pulls the carousel data 
RE_CAROUSEL_FULL = Regex('Y.Media.BCarousel\((.+?),Y.Media.pageChrome')
RE_CAROUSEL_PART = Regex('Y.Media.BCarousel\((.+?)&renderer_key=')
# These regex variables pull the tab info from page
RE_LIST_ID = Regex('listId: "(.+?)", pagesConfig: ')
RE_CONTENT_ID = Regex('CONTENT_ID = "(.+?)";')
RE_TAB_CAROUSEL = Regex(r'tabview_mediatabs_configs=(.+?)<')
RE_TAB_TITLE = Regex(r'yui3-tabview-content\\">(.+?)<\\/div')
# These regex variables pull the list id, content id and tab info from page
RE_LIST_ID = Regex('listId: "(.+?)", pagesConfig: ')
#RE_LIST_ID = Regex('"#mediaslate", listId: "(.+?)", pagesConfig: ')
RE_CONTENT_ID = Regex('CONTENT_ID = "(.+?)";')
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
   
  # It is much faster to pull all carousel data on a page then use that to match to carousel id
  # Use a partial regex match and add ending json to avoid data at end of each carousel entry that cause errors when fixing backslashes in tabbed carousel json in GetJSON function
  json_data = '[' + ('"},'.join(RE_CAROUSEL_PART.findall(content))) + '"}]'

  # If 'nested_mediatabs' in the the carousel json data, there is an extra carousel and there are tabs associated with that carousel
  # Since the tabbed carousels have completely different xpath, easier to just add a pull here than try alter carousel id xpath pull below
  # Create the list_id for the tabbed carousel from the GetJSON function and add directory for it
  if 'nested_mediatabs' in json_data:
    car_id = 'nested_mediatabs_'
    list_id = GetJSON(json_data, car_id)
    oc.add(DirectoryObject(key=Callback(ProduceCarousel, title=title, url=CAROUSEL_URL %list_id), title=title, thumb=thumb))
    # Create separate directories for its associated tabs
    carousel_tabs = TabCarouselList(url, title, thumb)
    for obj in carousel_tabs.objects:
      oc.add(obj)
  else:
    pass
  # If there is a content_id in the json_ data, then there is a carousel for the latest videos, if not we need to create a directory
  # for the latest videos.
  if '?content_id=' not in json_data and '/explore/' not in url:
    content_id = YahooID(url)
    if content_id:
      oc.add(DirectoryObject(key=Callback(ProduceCarousel, title='Latest Videos', url=CAROUSEL_URL %content_id), title='Latest Videos', thumb=thumb))
  else:
    pass
  
  for category in HTML.ElementFromString(content).xpath('//div[contains(@id,"mediabcarousel")]'):
    title = category.xpath('./div/div/div[@class="heading"]/h3//text()')[0]
    if len(title) < 1:
      continue

    car_id = category.xpath('.//@id')[0]
    # Skip the Most Popular Now on Screen section in each show
    if car_id == 'mediabcarouselmixedmostpopularca':
      continue

    else:
      list_id = GetJSON(json_data, car_id)
      if not list_id:
        continue
      oc.add(DirectoryObject(key=Callback(ProduceCarousel, title=title, url=CAROUSEL_URL %list_id), title=title, thumb=thumb))
      
  #oc.objects.sort(key = lambda obj: obj.title)

  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This show appears to be empty. There are no sections to display right now.")      
  else:
    return oc

####################################################################################################
# This function creates a url for each carousel based on the carousel identifier used for each section 
# and the associated carousel json data pulled from the bottom of each page 
def GetJSON(json_data, car_id):

  try:
    json = JSON.ObjectFromString(json_data)
  except:
    # The json data for pages with tabs have backslashes in the data and give errors here so 
    # if the JSON parse fails, we replace the backslashes and try the pull again
    try:
      json_data = json_data.replace('\\','')
      json = JSON.ObjectFromString(json_data)
    except:
      return None

  for item in json:
    mod_id = item['modId']
    # Made this an "in" instead of "==" so it will work with the mediatab modId
    # the ModId appears to be 'nested_mediatabs_nmid_1_' but just pull 'nested_mediatabs_' to be sure we catch all
    if car_id in mod_id:
      xhr_url = item['xhrUrl']
      if 'list_id' in xhr_url:
        list_id = xhr_url.split('list_id=')[-1].split('&')[0]
      else:
        list_id = xhr_url.split('content_id=')[-1].split('&')[0]
      return list_id
    else:
      pass

  return None
#########################################################################################################
# This function creates directory objects for the tab style carousels. Finds content_id, instance_ids and mod_ids for YAHOO_TAB_CAROUSEL url
# TABS ARE A DIFFERENT TYPE OF URL THAN CAROUSELS ('/_remote/' instead of '/_xhr/') AND CANNOT FIGURE OUT HOW TO INCREASE RESULTS IN THEM
# AFTER CLICKING ON A TAB AND CHOOSING PAGE 2 OF THE RESULTS IT CREATES A XHR TYPE CAROUSELS URL BUT CANNOT FIND THE LIST ID FOR IT ANYWHERE
@route(PREFIX + '/tabcarousellist')
def TabCarouselList(url, title, thumb):
  oc = ObjectContainer()

  content = HTTP.Request(url).content
  content_id = RE_CONTENT_ID.search(content).group(1)

  # Pulls the tab data from the web page and put it into a json format
  data_list = RE_TAB_CAROUSEL.findall(content)
  json_data = ','.join(data_list)
  json_data = json_data.replace('\\','')
  details = JSON.ObjectFromString(json_data)

  # make as list of tab names which are in a script separate from tab data above
  # There is no actual HTML code on the page to pull xpath data from
  tab_code = RE_TAB_TITLE.search(content).group(1)
  tab_code = tab_code.replace('\\','')
  page = HTML.ElementFromString(tab_code)
  tab_titles = page.xpath('//li/a//text()')

  x=0
  # Put the all data together. 
  for items in details:
    title = tab_titles[x] + ' Tab'
    carousel_url = YAHOO_TAB_CAROUSEL %(items['instanceId'], content_id, items['moduleId'])
    # Skip the first tab since there is a regular carousel for it
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
    if not url.startswith('http'):
      url = YahooURL + url
    if '**' in url:
      url = url.split('**')[1]
      url = url.replace('%3A', ':')
    # Found  http://yhoo.it/ in a link that resolves to another url and is not supported by URL service 
    # but when you put a check in for it, Burning Love no longer produces
    title = show.xpath('./div/div/p/a//text()')[0]
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
        #Log('the value of data_provider is %s' %data_provider)
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
      oc.add(DirectoryObject(key=Callback(YahooDirectory, title=title, url=url, thumb=thumb), title=title, thumb=Resource.ContentsOfURLWithFallback(thumb)))	

# SINCE SOME RESULTS DO NOT WORK, IT MAY GO THROUGH ALL THE ENTRIES ON A PAGE AND STILL PUT NOTHING BUT A NEXT PAGE ON IT
# SINCE BLOCKING OF PAGE MUST BE SET IN ADVANCE, JUST SET TOTAL PER PAGE TO 25
# Paging code. Each page pulls 16 results max and use x counter to determine need for more results
# Added remote check for tab carousels since they do not have pages
  if  '/_remote/' not in url:
    if x >= 16:
      b = b + 16
      oc.add(NextPageObject(
        key = Callback(ProduceCarousel, title = title, url=orig_url, b=b), 
        title = L("Next Page ...")))
	

  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This section does not contain any videos that are compatible with this channel.")      
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
  #Log('the value of url test is %s' %url_good)
  return url_good

###################################################################################################
# This function pulls the ID to be added to the YahooJSON url. All shows have a content ID that when added to the URL 
# will produce the latest videos. But main sections and some shows also have a list ID that will produce the top carousel if one exists
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

# Paging code. Each page pulls 30 results use x counter for need of next page
  if x >= 30:
    b = b + 30
    oc.add(NextPageObject(
      key = Callback(SearchYahoo, title = title, b=b, query = query), 
      title = L("Next Page ...")))
	
  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no videos to display right now.")      
  else:
    return oc
