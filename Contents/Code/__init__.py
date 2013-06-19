# DID NOT ADD SORTS BECAUSE THE SITE ALREADY SORTS THE SHOWS BY NAME AND BY LATEST EPISODE FIRST 
# IF YOU ADD A DATE SORT TO EACH SHOW, IT CAN MESS UP THE ORDER AND PUT THE EPISODES IN THE WRONG 
# ORDER BECAUSE OFTEN MULTIPLE EPISODE OR VIDEOS ARE UPLOADED ON AND HAVE THE SAME DATE
TITLE    = 'Yahoo Screen'
PREFIX   = '/video/yahooscreen'
# NOT SURE IF CODE BELOW IS NEEDED ANY LONGER
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

YahooURL = 'http://screen.yahoo.com'
YahooOrigURL = 'http://screen.yahoo.com/yahoo-originals/'
http = 'http:'

# These variables pull the list id and content id from page
RE_LIST_ID = Regex('listId: "(.+?)", pagesConfig: ')
RE_CONTENT_ID = Regex('CONTENT_ID = "(.+?)";')
# This is the carousel url and JSON data urls
Carousel = 'http://screen.yahoo.com/_xhr/carousel/bcarousel-mixed-list/?list_id=%s&thumb_ratio=16x9&pyoff=0&title_lines_max=2&show_cite=&show_date=0&show_provider=0&show_author=&show_duration=0&show_subtitle=&show_provider_links=&apply_filter=&filters=&template=tile&num_cols=4&num_rows=8&start_initial=1&max_items=19&pages_per_batch=1&sec=&module=MediaBCarouselMixedLPCA&spaceid=792884066&mod_units=24&renderer_key='
# This is a global variable for the parameters of the Yahoo JSON data file. Currently it returns 32 items. 
# To add more returned results, add the last number plus 5 to pc_starts and ",1u-1u-1u-1u-1u" to pc_layouts for each five entries you want to add
YahooJSON = 'http://screen.yahoo.com/_xhr/slate-data/?list_id=%s&start=0&count=50&pc_starts=1,6,11,16,21,26&pc_layouts=1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u'

###################################################################################################
def Start():

  ObjectContainer.title1 = TITLE
  HTTP.CacheTime = CACHE_1DAY 

###################################################################################################
@handler(PREFIX, TITLE)
# There are not separate pages for each section and the main originals page has carousels, 
# so to get all the shows for each section, sections are hard coded in with a section carousel id
def MainMenu():

  oc = ObjectContainer()

# Made special menu for Burning Love
  url = 'http://screen.yahoo.com/burning-love/'
  page = HTML.ElementFromURL(url)
  title = page.xpath("//head//meta[@property='og:title']//@content")[0]
  summary = page.xpath("//head//meta[@name='description']//@content")[0]
  thumb = GetThumb(title)
	
  oc.add(DirectoryObject(
    key=Callback(BurningLove, title=title, url=url, thumb=thumb), 
    title=title, 
    thumb=thumb,
    summary=summary))

  oc.add(DirectoryObject(
    key=Callback(SectionYahoo, title='Yahoo! Comedy Originals', id='c59ae629-33fc-4bca-977e-604da14af38f'),
    title='Yahoo! Comedy Originals'))

  oc.add(DirectoryObject(
    key=Callback(SectionYahoo, title='Yahoo! Living Originals', id='4b39dfc3-59df-4a8d-b0ca-55380324501c'),
    title='Yahoo! Living Originals'))

  oc.add(DirectoryObject(
    key=Callback(SectionYahoo, title='Yahoo! News Originals', id='ca63a6b9-0e5c-4f61-be53-3803c8461ab9'),
    title='Yahoo! News Originals'))

  oc.add(DirectoryObject(
    key=Callback(SectionYahoo, title='Yahoo! Sports Originals', id='66e3b217-e86f-40d1-a8ff-31902550c962'),
    title='Yahoo! Sports Originals'))

  oc.add(DirectoryObject(
    key=Callback(SectionYahoo, title='Yahoo! Finance Originals', id='e86e7ba3-9f77-4085-8606-b507b6e409e2'),
    title='Yahoo! Finance Originals'))

  oc.add(DirectoryObject(
    key=Callback(SectionYahoo, title='Yahoo! Entertainment Originals', id='94aec3ed-1cf9-41bb-8d59-408a8410fc3a'),
    title='Yahoo! Entertainment Originals'))

  return oc

###################################################################################################
# This function uses the carousel file to pull the the shows for each sections
@route(PREFIX + '/sectionyahoo')
def SectionYahoo(title, id):

  oc = ObjectContainer(title2=title)
  list_URL = Carousel %id
  page = HTML.ElementFromURL(list_URL)
  for show in page.xpath('//div[@class="item-wrap"]'):

      title = show.xpath('./div/p[@class="title"]/a//text()')[0]
      url = show.xpath('./div/p[@class="title"]/a//@href')[0]
      thumb = show.xpath('./a/img//@src')[0]
	  
      # Skipping Burning Love since it has its own route and Electric City since it does not work with URL service
      if title not in ['Electric City', 'Burning Love']:
        oc.add(DirectoryObject(
          key=Callback(ShowYahoo, title=title, url=url), 
          title=title, 
          thumb=Resource.ContentsOfURLWithFallback(thumb)))	

  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to display right now.")      
  else:
    return oc

###############################################################################################################
# This is a special section for handling Burning Love with sections, one for current episodes pulled like other shows
# and one for older episodes that apear in the second section of page
@route(PREFIX + '/burninglove')
def BurningLove(title, url, thumb):

  oc = ObjectContainer(title2=title)

  oc.add(DirectoryObject(
    key=Callback(ShowYahoo, title=title, url=url),
    title='Current Season',
    thumb=thumb))

  oc.add(DirectoryObject(
    key=Callback(MoreVideosYahoo, title=title, url=url),
    title='Older Episodes',
    thumb=thumb))
      
  return oc

###################################################################################################
# This function pulls the ID for the JSON data url
# All shows have a content ID except one (Animal All Stars), so pull List ID for that one
# and check for List ID first.
@route(PREFIX + '/yahooid')
def YahooID(url):

  ID = ''
  content = HTTP.Request(url).content
  try:
    ID = RE_LIST_ID.search(content).group(1)
  except:
    ID = RE_CONTENT_ID.search(content).group(1)
  return ID
 
######################################################################################################
@route(PREFIX + '/showyahoo')
def ShowYahoo(title, url):

  oc = ObjectContainer(title2=title)
  JSON_ID = YahooID(url)
  # could clean this url up with global variables
  JSON_url = YahooJSON %JSON_ID
  try:
    data = JSON.ObjectFromURL(JSON_url)
  except:
    return ObjectContainer(header=L('Error'), message=L('This feed does not contain any video'))

  if data.has_key('items'):
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
		# some entries do not have urls
        if url:
          if not url.startswith('http://'):
            url = YahooURL + url

          oc.add(VideoClipObject(
            url = url, 
            title = title, 
            thumb = Resource.ContentsOfURLWithFallback(thumb),
            summary = summary,
            duration = duration,
            originally_available_at = date))
	# This section is for show with type link in json data that have no dates or duration(just one Yahoo Animal Allstars)
      else:
        # The url in the link_url field does not work with URL service so pull url out of summary_short
        url = desc_data.xpath('//a//@href')[0]
		# some entries do not have urls
        if url:
          if not url.startswith('http://'):
            url = YahooURL + url

          oc.add(VideoClipObject(
            url = url, 
            title = title, 
            summary = summary,
            thumb = Resource.ContentsOfURLWithFallback(thumb))) 
	
  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no videos to display right now.")      
  else:
    return oc
   
###############################################################################################################
# This picks up videos in the second section on a show page with an id="mediabcarouselmixedlpca_2"
# It is only used to pick up older episodes available on the Yahoo Screens website for Burning Love right now
@route(PREFIX + '/morevideosyahoo')
def MoreVideosYahoo(title, url):

  oc = ObjectContainer(title2=title)
  html = HTML.ElementFromURL(url)

  for video in html.xpath('//div[@id="mediabcarouselmixedlpca_2"]/div/div/ul/li/ul/li'):
    url = video.xpath('./div/a/@href')[0]
    url = YahooURL + url
    thumb = video.xpath('./div/a/img//@style')[0]
    thumb = thumb.replace("background-image:url('", '').replace("');", '')
    title = video.xpath('./div/div/p/a//text()')[0]
				
    oc.add(VideoClipObject(
      url = url, 
      title = title, 
      thumb = Resource.ContentsOfURLWithFallback(thumb)))
      
  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no videos to display right now.")      
  else:
    return oc

#############################################################################################################################
# This function pulls the thumb from a the Yahoo Originals main page
# It cannot go through all selections since they are in a carousel, but picks up most.  
# Would require the Yahoo section name and its id to pull the full list from the carousel
@route(PREFIX + '/getthumb')
def GetThumb(title):

  try:
    thumb_page = HTML.ElementFromURL(YahooOrigURL)
    try:
      thumb = thumb_page.xpath('//a[@class="media"]/img[@alt="%s"]//@style' % title)[0]
    except:
      thumb = thumb_page.xpath('//a[@class="img-wrap"]/img[@alt="%s"]//@style' % title)[0]
    thumb = thumb.replace("background-image:url('", '').replace("');", '')
  except:
    thumb = R(ICON)

  return thumb