
TITLE    = 'Yahoo Screen'
PREFIX   = '/video/yahooscreen'
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

RE_LIST_ID = Regex('listId: "(.+?)", pagesConfig: ')
RE_CONTENT_ID = Regex('CONTENT_ID = "(.+?)";')

YahooURL = 'http://screen.yahoo.com'
YahooOrigURL = 'http://screen.yahoo.com/yahoo-originals/'

http = 'http:'

###################################################################################################
# Set up containers for all possible objects
def Start():

  ObjectContainer.title1 = TITLE
  ObjectContainer.art = R(ART)

  DirectoryObject.thumb = R(ICON)
  DirectoryObject.art = R(ART)
  EpisodeObject.thumb = R(ICON)
  EpisodeObject.art = R(ART)
  VideoClipObject.thumb = R(ICON)
  VideoClipObject.art = R(ART)
    
  HTTP.CacheTime = CACHE_1HOUR
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 Firefox/18.0'

###################################################################################################

@handler(PREFIX, TITLE, art=ART, thumb=ICON)

def MainMenu():
# Broke it up into sections like comedy, living, news etc. There are not separate pages for each section and the main page for originals
# has carousels for each section, so in order to get all the shows for each section, I hard coded them in with the id needed to access 
# the carousel for that section
  oc = ObjectContainer()

# Making special menu for Burning Love
  show_url = 'http://screen.yahoo.com/burning-love/'
  page = HTML.ElementFromURL(show_url)
  title = page.xpath("//head//meta[@property='og:title']//@content")[0]
  description = page.xpath("//head//meta[@name='description']//@content")[0]
  thumb = GetThumb(title)	
	
  oc.add(DirectoryObject(
    key=Callback(BurningLove, title=title, url=show_url, thumb=thumb), 
    title=title, 
    thumb=thumb,
    summary=description))

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
# This function uses the carousel file to pull the data needed to produce the different sections
@route(PREFIX + '/sectionyahoo')
def SectionYahoo(title, id):

  oc = ObjectContainer(title2=title)
  list_URL = 'http://screen.yahoo.com/_xhr/carousel/bcarousel-mixed-list/?list_id=' + id + '&thumb_ratio=16x9&pyoff=0&title_lines_max=2&show_cite=&show_date=0&show_provider=0&show_author=&show_duration=0&show_subtitle=&show_provider_links=&apply_filter=&filters=&template=tile&num_cols=4&num_rows=8&start_initial=1&max_items=19&pages_per_batch=1&sec=&module=MediaBCarouselMixedLPCA&spaceid=792884066&mod_units=24&renderer_key='
  page = HTML.ElementFromURL(list_URL)
  for show in page.xpath('//li/ul/li/div'):

      title = show.xpath('./div/p[@class="title"]/a//text()')[0]
      url = show.xpath('./div/p[@class="title"]/a//@href')[0]
      thumb = show.xpath('./a/img//@src')[0]
	  
      if title != 'Burning Love':
      # So Burning Love will not appear twice since it has its own route
        oc.add(DirectoryObject(
          key=Callback(ShowYahoo, title=title, url=url), 
          title=title, 
          thumb=Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON))))	

  return oc

###############################################################################################################
# This is a special section for handling Burning Love so it can have extra videos
@route(PREFIX + '/burninglove')
def BurningLove(title, url, thumb):
# want to create two folders.  One for current episodes and one for other videos that we pull from the MoreVideosYahoo function below
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
# This function pulls the Content ID from each show page for it to be entered into the JSON data url
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
  JSON_url = YahooID(url)
  JSON_url = 'http://screen.yahoo.com/_xhr/slate-data/?list_id=' + JSON_url + '&start=0&count=50&pc_starts=1,6,11,16,21,26&pc_layouts=1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u,1u-1u-1u-1u-1u'

  try:
  # Split this into if type video and if type link to stop errors for missing dates and duration
  # There is a short summary but there is alot of junk around it so for now not pulling summary
    data = JSON.ObjectFromURL(JSON_url)
    for video in data['items']:
      if video['type'] == 'video':
        url = video['link_url'] 
        if url:
          description = video['summary_short']
          desc_data = HTML.ElementFromString(description)
          summary = desc_data.xpath('//text()')[0]
          title = video['title_short'] 
          thumb = video['image_thumb_url']
          duration = video['duration']
          duration = Datetime.MillisecondsFromString(duration)
          date = video['date']
          date = Datetime.ParseDate(date)
          if not url.startswith('http://'):
            url = YahooURL + url

          oc.add(VideoClipObject(
            url = url, 
            title = title, 
            thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)),
            summary = summary,
            duration = duration,
            originally_available_at = date))
	# This section is for type link right now just one show uses the Yahoo Animal Allstars and the URL service is not picking up its videos
      else:
        # The url in the link_url field does not work with the service so we are pulling the url out of summary_short
        description = video['summary_short']
        desc_data = HTML.ElementFromString(description)
        summary = desc_data.xpath('//text()')[0]
        url = desc_data.xpath('//a//@href')[0]
        if url:
          title = video['title_short'] 
          thumb = video['image_thumb_url']
          if not url.startswith('http://'):
            url = YahooURL + url

          oc.add(VideoClipObject(
            url = url, 
            title = title, 
            summary = summary,
            thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)))) 
	
  except:
    html = HTML.ElementFromURL(url)
    # Here is where any alternative code can be put for channels that do not work with JSON
    # This is a basic html pull for channels of the first page of videos on a show that is from Yahoo Screens
    smTitle = title.lower()
    smTitle = smTitle.replace(" ", '')

    for video in html.xpath('//div/ul/li/ul/li[@data-provider-id]'):

      ep_url = video.xpath('./div[@class="item-wrap"]/a//@href')[0]
      ep_url = YahooURL + ep_url
      # There is no description for these videos, just the title and episode number, so not adding the description field
      ep_title = video.xpath('./div[@class="item-wrap"]/div/p[@class="title"]/a//text()')[0]
      # There is no duration for these videos, so not adding the duration field
      ep_thumb = video.xpath('./div[@class="item-wrap"]/a/img//@style') [0]
      ep_thumb = ep_thumb.replace("background-image:url('", '').replace("');", '')
      data_provider =  video.xpath('.//@data-provider-id')[0]
	
      if smTitle in data_provider: 
	
        oc.add(VideoClipObject(
          url = ep_url, 
          title = ep_title, 
          thumb = thumb))
  
  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="Unable to display videos for this show right now.")      
  return oc
   
###############################################################################################################
# This function picks up the second carousel on a page, so it could be used for any show
# Want to use this function to pick up other videos available for Burning Love
@route(PREFIX + '/morevideosyahoo')
def MoreVideosYahoo(title, url):

  oc = ObjectContainer(title2=title)
  html = HTML.ElementFromURL(url)

  for video in html.xpath('//div[@id="mediabcarouselmixedlpca_2"]/div/div/ul/li/ul/li'):
  # need to check if urls need additions and if image is transparent and needs style to access it or any additions to address
    url = video.xpath('./div/a/@href')[0]
    url = YahooURL + url
    thumb = video.xpath('./div/a/img//@style')[0]
    thumb = thumb.replace("background-image:url('", '').replace("');", '')
    title = video.xpath('./div/div/p/a//text()')[0]
				
    oc.add(VideoClipObject(
      url = url, 
      title = title, 
      thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON))))
      
  return oc

#############################################################################################################################
# This is a function to pull the thumb from a the Yahoo Originals page and uses the show title to find the correct image
def GetThumb(title):

  try:
    thumb_page = HTML.ElementFromURL(YahooOrigURL)
    thumb = thumb_page.xpath('//ul/li/ul/li/div/a/img[@alt="%s"]//@style' % title)[0]
    thumb = thumb.replace("background-image:url('", '').replace("');", '')

  except:
    thumb = R(ICON)
  return thumb
