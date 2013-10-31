TITLE    = 'Yahoo Screen'
PREFIX   = '/video/yahooscreen'
# NOT SURE IF CODE BELOW IS NEEDED ANY LONGER
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

YahooURL = 'http://screen.yahoo.com'
# could possibly use type = user below to pull user preferred channels
YahooSectionJSON = 'http://screen.yahoo.com/ajax/resource/channels;videocount=0;count=%s;type=%s'
YahooShowJSON = 'http://screen.yahoo.com/ajax/resource/channel/id/%s;count=20;start=%s'
YahooShowURL = 'http://screen.yahoo.com/%s/%s.html'

###################################################################################################
def Start():

  ObjectContainer.title1 = TITLE
  HTTP.CacheTime = CACHE_1HOUR 

###################################################################################################
@handler(PREFIX, TITLE)
def MainMenu():

  oc = ObjectContainer()
  
  # Yahoo Screen Featured Sections
  oc.add(DirectoryObject(key=Callback(SectionJSON, title='Featured Channels', ch='feat'), title='Featured Channels'))
  # Yahoo Screen All sections but featured
  oc.add(DirectoryObject(key=Callback(SectionJSON, title='More Channels', ch='orig'), title='More Channels'))
  # Yahoo Screen SNL sections
  oc.add(DirectoryObject(key=Callback(SectionJSON, title='Saturday Night Live Channels', ch='snl'), title='Saturday Night Live Channels'))
  # Yahoo Screen By A to Z
  oc.add(DirectoryObject(key=Callback(Alphabet, title='All Channels A to Z'), title='All Channels A to Z'))
  # Most Popular on Yahoo Screens
  oc.add(DirectoryObject(key=Callback(VideoJSON, title='Most Popular Videos', url='popular'), title='Most Popular Videos'))
  # Yahoo Search Object
  oc.add(SearchDirectoryObject(identifier="com.plexapp.plugins.yahooscreen", title=L("Search Yahoo Screen Videos"), prompt=L("Search for Videos")))

  return oc
####################################################################################################
# A to Z pull for VH1. But could be used with different sites. The # portion has bad links so removed it
@route(PREFIX + '/alphabet')
def Alphabet(title):
    oc = ObjectContainer(title2=title)
    for ch in list('#ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
        oc.add(DirectoryObject(key=Callback(SectionJSON, title=ch, ch=ch), title=ch))
    return oc
######################################################################################################
# This is a JSON to produce sections on Yahoo
# Using ch to showsection type or letter of alphabet to determine which objects to add
@route(PREFIX + '/sectionjson')
def SectionJSON(title, ch):

  oc = ObjectContainer(title2=title)
  # You have to determine and include a total count in the json url, otherwise it will only return the first 20 results or featured channels
  # So setting it to the top 200 shows

  try:
    data = JSON.ObjectFromURL(YahooSectionJSON %('200', 'common'), cacheTime = CACHE_1HOUR)
  except:
    return ObjectContainer(header=L('Error'), message=L('This feed does not contain any video'))

  for video in data:
    url_name = video['url_alias'] 
    title = video['name'] 
    
    if ch=='snl':
      if 'snl' in url_name:
        oc.add(DirectoryObject(key=Callback(VideoJSON, title=title, url=url_name), title=title))
      else:
        pass
    elif ch=='orig' or ch=='feat':
      # The first featured sections have a value for dock logo
      test=video['dock_logo']
      if test and ch=='feat':
        oc.add(DirectoryObject(key=Callback(VideoJSON, title=title, url=url_name), title=title))
      elif ch=='orig' and 'snl' not in url_name and not test:
        oc.add(DirectoryObject(key=Callback(VideoJSON, title=title, url=url_name), title=title))
      else:
        pass
    else:
      if title.startswith(ch):
        oc.add(DirectoryObject(key=Callback(VideoJSON, title=title, url=url_name), title=title))
      elif title[0].isalpha()==False and ch=='#':
        oc.add(DirectoryObject(key=Callback(VideoJSON, title=title, url=url_name), title=title))
      else:
        pass

  # Prefer the websites ordering of sections. Only use this for a to z
  if len(ch)==1:
    oc.objects.sort(key = lambda obj: obj.title)
	
  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This directory appears to be empty or contains videos that are not compatible with this channel.")      
  else:
    return oc
######################################################################################################
# This is a JSON to produce videos on Yahoo
# They have taken the total out of this page so may have some with a next that has no results
@route(PREFIX + '/videojson', start=int)
def VideoJSON(title, url, start=0):

  oc = ObjectContainer(title2=title)
  try:
    data = JSON.ObjectFromURL(YahooShowJSON %(url, start))
  except:
    return ObjectContainer(header=L('Error'), message=L('This feed does not contain any video'))

  x=0
  for video in data['videos']:
    x=x+1 
    url_show = video['channel_url_alias']
    url_name = video['url_alias'] 
    video_url = YahooShowURL %(url_show, url_name)
    duration = int(video['duration']) * 1000
    date = Datetime.ParseDate(video['publish_time'])
    summary = video['description']
    title = video['title'] 
    if '[' in title:
      ep_info = title.split('[')[1].replace(']', '')
      if 'S' in ep_info:
        season = int(ep_info.split(':')[0].replace('S', ''))
        episode = ep_info.split(':')[1]
      else:
        season = 0
        episode = ep_info
      episode = int(episode.replace('Ep.', ''))
      title = title.split('[')[0]
    else:
      season = 0
      episode = 0
    try:
      thumb = video['thumbnails'][1]['url']
    except:
      thumb = R(ICON)
    # May need this for excluding videos that may not work with URL service
    provider_name = video['provider_name']

    oc.add(EpisodeObject(
      url = video_url, 
      title = title, 
      thumb = Resource.ContentsOfURLWithFallback(thumb),
      index = episode,
      season = season,
      summary = summary,
      duration = duration,
      originally_available_at = date))

# Paging code. Each page pulls 20 results use x counter for need of next page
  if x >= 20:
    start = start + 20
    oc.add(NextPageObject(key = Callback(VideoJSON, title = title, url=url, start=start), title = L("Next Page ...")))
          
  if len(oc) < 1:
    return ObjectContainer(header="Empty", message="This directory appears to be empty or contains videos that are not compatible with this channel.")      
  else:
    return oc
