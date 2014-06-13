TITLE = 'Yahoo Screen'
PREFIX = '/video/yahooscreen'

YAHOO_URL = 'http://screen.yahoo.com'
# You have to determine and include a total count in the json url, otherwise it will only return the first 20 results
# Since this json is used to return all shows or channels to be ordered A to Z, we need all shows returned
# There is no code in the pages or json that gives a total count. There are currently 258 channels or shows, so setting it to the 300 for now
YAHOO_ALL_JSON = 'http://screen.yahoo.com/ajax/resource/channels;count=300;type=common;videocount=0'
# We break the section results up into pages of 20 since SNL returns 120 channels or shows. For popular, parent alias must be blank
YAHOO_SECTION_JSON = 'http://screen.yahoo.com/ajax/resource/channels;count=20;start=%d;type=common;parent_alias=%s;videocount=0'
# could use type = user above to pull user preferred channels
YAHOO_SHOW_JSON = 'http://screen.yahoo.com/ajax/resource/channel/id/%s;count=20;start=%d'
YAHOO_SHOW_URL = 'http://screen.yahoo.com/%s/%s.html'

# Season and Episode are always in the title and can be in brackets
RE_SEASON = Regex('(SEASON|Season|\[S) ?(\d+)')
RE_EPISODE = Regex('(Episode|Ep.) ?(\d+)')

###################################################################################################
def Start():

  ObjectContainer.title1 = TITLE
  HTTP.CacheTime = CACHE_1HOUR

###################################################################################################
@handler(PREFIX, TITLE)
def MainMenu():

  oc = ObjectContainer()

  # Yahoo Screen Featured Sections
  oc.add(DirectoryObject(key=Callback(Categories, title='Featured'), title='Featured Channels'))
  # Yahoo Screen By Categories
  oc.add(DirectoryObject(key=Callback(Categories, title='Categories'), title='Channels by Category'))
  # Yahoo Screen By A to Z
  # The channel code could be much shorter if we removed this section, but this is very helpful for finding a particular show or channel
  oc.add(DirectoryObject(key=Callback(Alphabet, title='All Channels A to Z'), title='All Channels A to Z'))
  # Yahoo Search Object
  oc.add(SearchDirectoryObject(identifier='com.plexapp.plugins.yahooscreen', title='Search Yahoo Screen Videos', prompt='Search for Videos'))

  return oc

####################################################################################################
@route(PREFIX + '/alphabet')
def Alphabet(title):

  oc = ObjectContainer(title2=title)

  for ch in list('#ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    oc.add(DirectoryObject(key=Callback(AllJSON, title=ch, ch=ch), title=ch))

  return oc

####################################################################################################
@route(PREFIX + '/categories')
def Categories(title):

  oc = ObjectContainer(title2=title)
  page = HTML.ElementFromURL(YAHOO_URL)

  # Adding the [1] to the ul tag makes sure only the ul that immediately follows the title is picked up instead of all
  for category in page.xpath('//*[text()="%s"]/following-sibling::ul[1]/li/span/a' % title):
    title = category.xpath('.//text()')[0]
    url = category.xpath('./@href')[0]
    cat = url.replace('/', '')

    oc.add(DirectoryObject(key=Callback(SectionJSON, title=title, cat=cat), title=title))

  return oc

######################################################################################################
# This is a JSON to produce sections by letter. We pull all channels or shows and compare to letter
@route(PREFIX + '/alljson')
def AllJSON(title, ch):

  oc = ObjectContainer(title2=title)

  try:
    data = JSON.ObjectFromURL(YAHOO_ALL_JSON)
  except:
    return ObjectContainer(header='Error', message='This feed does not contain any video')

  for video in data:
    url_name = video['url_alias']
    title = String.DecodeHTMLEntities(video['name'])

    if title.startswith(ch) or (title[0].isalpha()==False and ch=='#'):
      oc.add(DirectoryObject(key=Callback(VideoJSON, title=title, url=url_name), title=title))

  if len(oc) < 1:
    return ObjectContainer(header='Empty', message='This directory appears to be empty or contains videos that are not compatible with this channel.')
  else:
    oc.objects.sort(key = lambda obj: obj.title)
    return oc

######################################################################################################
# This is a JSON to produce sections or categories of shows using the parent alias
@route(PREFIX + '/sectionjson', start=int)
def SectionJSON(title, cat, start=0):

  oc = ObjectContainer(title2=title)
  local_url = YAHOO_SECTION_JSON % (start, cat)

  # The popular section does not produce results when popular is put in the ';parent_alias=' portion of the section json url
  if cat == 'popular':
    local_url = local_url.replace(';parent_alias=popular', '')

  try:
    data = JSON.ObjectFromURL(local_url)
  except:
    return ObjectContainer(header='Error', message='This feed does not contain any video')

  for video in data:
    url_name = video['url_alias'] 
    cat_title = String.DecodeHTMLEntities(video['name'])

    oc.add(DirectoryObject(key=Callback(VideoJSON, title=cat_title, url=url_name), title=cat_title))

  # Paging code. Each page pulls 20 results
  # There is not a total number of videos to check against so we use a test to make sure the next page has results
  start = start + 20
  json_url = YAHOO_SECTION_JSON % (start, cat)

  # The popular section does not produce results when popular is put in the ';parent_alias=' portion of the section json url
  if cat == 'popular':
    json_url = json_url.replace(';parent_alias=popular', '')

  if TestNext(json_url):
    oc.add(NextPageObject(key=Callback(SectionJSON, title=title, cat=cat, start=start), title='Next ...'))

  if len(oc) < 1:
    return ObjectContainer(header='Empty', message='There are no channels for %s.' % title)
  else:
    return oc

######################################################################################################
# This function processes JSON to produce videos on Yahoo
@route(PREFIX + '/videojson', start=int)
def VideoJSON(title, url, start=0):

  oc = ObjectContainer(title2=title)

  try:
    data = JSON.ObjectFromURL(YAHOO_SHOW_JSON % (url, start))
  except:
    return ObjectContainer(header='Error', message='This feed does not contain any video')

  for video in data['videos']:
    url_show = video['channel_url_alias']
    url_name = video['url_alias']
    video_url = YAHOO_SHOW_URL % (url_show, url_name)
    duration = int(video['duration']) * 1000
    date = Datetime.ParseDate(video['publish_time'])
    summary = String.DecodeHTMLEntities(video['description'])
    title = String.DecodeHTMLEntities(video['title'])
    # check for episode and season in title
    try: season = int(RE_SEASON.search(title).group(2))
    except: season = None
    try: episode = int(RE_EPISODE.search(title).group(2))
    except: episode = None

    if '[' in title:
      title = title.split('[')[0]

    try:
      thumb = video['thumbnails'][1]['url']
    except:
      thumb = ''

    if episode or season:
      oc.add(EpisodeObject(
        url = video_url, 
        title = title, 
        thumb = Resource.ContentsOfURLWithFallback(thumb),
        index = episode,
        season = season,
        summary = summary,
        duration = duration,
        originally_available_at = date
      ))
    else:
      oc.add(VideoClipObject(
        url = video_url,
        title = title,
        thumb = Resource.ContentsOfURLWithFallback(thumb),
        summary = summary,
        duration = duration,
        originally_available_at = date
      ))

  # Paging code. Each page pulls 20 results
  # There is not a total number of videos to check against so we use a test to make sure the next page has results
  start = start + 20
  json_url = YAHOO_SHOW_JSON % (url, start)

  if TestNext(json_url):
    oc.add(NextPageObject(key = Callback(VideoJSON, title=title, url=url, start=start), title='Next Page ...'))

  if len(oc) < 1:
    return ObjectContainer(header='Empty', message='There are no videos for this channel.')
  else:
    return oc

####################################################################################################
# Test to see if there is any data on the next page
@route(PREFIX + '/testnext')
def TestNext(json_url):

  data = JSON.ObjectFromURL(json_url)

  if not 'videos' in data or len(data['videos']) < 1:
    return False

  return True
