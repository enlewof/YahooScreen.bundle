# DID NOT ADD SORTS BECAUSE THE SITE ALREADY SORTS THE SHOWS BEST AND A DATE SORT CAN MESS UP THE ORDER 
# SINCE OFTEN MULTIPLE VIDEOS ARE UPLOADED ON OR HAVE THE SAME DATE
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
# This is a global variable for the parameters of the Yahoo JSON data file. Currently it returns 32 items. 
# To add more returned results, add the last number plus 5 to pc_starts and ",1u-1u-1u-1u-1u" to pc_layouts for each five entries you want to add
YahooJSON = 'http://screen.yahoo.com/_xhr/slate-data/?list_id=%s&start=0&count=50&pc_starts=1,6,11,16,21,26&pc_layouts=1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u'
RE_CAROUSEL = Regex('Y.Media.BCarousel(.+?),Y.Media.pageChrome')

###################################################################################################
def Start():

  ObjectContainer.title1 = TITLE
  HTTP.CacheTime = CACHE_1HOUR 

###################################################################################################
# There are not separate pages for each section and the main originals page has carousels, 
# so we pull the carousel info into JSON format and use that to pull sections and urls
@handler(PREFIX, TITLE)
def MainMenu():

  oc = ObjectContainer()

# Made special menu for Burning Love since it is the most popular show on the site
  url = 'http://screen.yahoo.com/burning-love/'
  page = HTML.ElementFromURL(url, cacheTime = CACHE_1DAY)
  title = page.xpath("//head//meta[@property='og:title']//@content")[0]
  summary = page.xpath("//head//meta[@name='description']//@content")[0]
  thumb = page.xpath('//img[@alt="Burning Love"]//@style')[0]
  thumb = thumb = thumb.replace("background-image:url('", '').replace("');", '')
	
  oc.add(DirectoryObject(key=Callback(BurningLove, title=title, url=url, thumb=thumb), title=title, thumb=Resource.ContentsOfURLWithFallback(thumb), summary=summary))

  # Here we start the pulls for the other sections
  content = HTTP.Request(YahooOrigURL).content
  details = GetYahooJson(content)
  #Log('the value of details is %s' %details)

  i=0
  for items in details:
    i=i+1
    carousel_type = items[i]['modId']
    carousel_url = items[i]['xhrUrl']
    carousel_url = YahooURL + carousel_url
    # To make sure it produces all the results we have to increase the &num_rows=. (changing the &num_cols decreases image size)
    # deleting data after num_rows= does not seem to affect results so we increase num_rows to 10 with
    carousel_url = carousel_url.split('&num_rows=')[0] + '&num_rows=10'
    # Once we pull the type and url from the json, we need to compare it to carousel id on the page
    page = HTML.ElementFromString(content)
    # XPATH ON YAHOO ORIGINALS PAGE IS NOT SPECIFIC ENOUGH TO ONLY PULL THE SECTIONS INFO
    # THE CODE BELOW NARROWS IT DOWN AS MUCH AS POSSIBLE
    for section in page.xpath('//div[contains(@class,"yom-stage")]/div/div/div'):
      # NOT ALL SECTIONS HAVE CAROUSEL INFO SO HAD TO PUT IT IN A TRY
      try:
        carousel_id = section.xpath('./div[contains(@id,"mediabcarouselmixedlpca")]//@id')[0]
      except:
        continue
      if carousel_id == carousel_type:
        title = section.xpath('./div[contains(@id,"categoryHeader")]/div/div/h1//text()')[0]
        oc.add(DirectoryObject(key=Callback(SectionYahoo, title=title, url=carousel_url), title=title))

  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to display right now.")      
  else:
    return oc

#########################################################################################################
# This function pulls carousel data from the Yahoo Originals page using regex and puts it in json format for easier pulls of info
@route(PREFIX + '/getyahoojson')
def GetYahooJson(content):

  data_list = RE_CAROUSEL.findall(content)
  data_list_new = []
  x = 1
  for data in data_list:
    data = str(x) + ':' + data.lstrip('(')
    data_list_new.append(data)
    x=x+1
  data_json = '[{' + ('},{'.join(data_list_new)) + '}]'
  details = JSON.ObjectFromString(data_json)

  return details
 
###################################################################################################
# This function uses the carousel file to pull the the shows for each sections
@route(PREFIX + '/sectionyahoo')
def SectionYahoo(title, url):

  oc = ObjectContainer(title2=title)
  page = HTML.ElementFromURL(url)
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
# This function pulls the ID for the JSON data url. All shows have a content ID except Animal All Stars that has a List ID
# So check for List ID first.
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

