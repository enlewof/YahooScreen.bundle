TITLE = 'Yahoo Screen'
PREFIX = '/video/yahooscreen'

YAHOO_URL = 'http://screen.yahoo.com'
# We break the section results up into pages of 20 since SNL returns 120 channels or shows.
YAHOO_SECTION_JSON = 'https://screen.yahoo.com/ajax/resource/channels;channel_alias=%s;channel_group=common;count=20;hasSubchannels=true;start=%s;videocount=0'
# could use type = user above to pull user preferred channels
YAHOO_SHOW_JSON = 'http://screen.yahoo.com/ajax/resource/channel/id/%s;count=20;start=%d'
YAHOO_SHOW_URL = 'http://screen.yahoo.com/%s/%s.html'

YAHOO_Category_URL = 'https://screen.yahoo.com/ajax/resource/channels;count=100;hasSubchannels=true;start=0;type=category;videocount=0'

# Season and Episode are always in the title and can be in brackets
RE_SEASON = Regex('(SEASON|Season|\[S) ?(\d+)')
RE_EPISODE = Regex('(Episode|Ep.) ?(\d+)')

# Need to create a list of Featured pages that we know have multiple categories
MORE_FEATURE = ["SNL", "VEVO", "Comedy Central"]
# This could be used to search for shows
CHANNEL_SEARCH_JSON = 'https://screen.yahoo.com/_screen_api/resource/videosearch;query=%s;type=suggestions'

###################################################################################################
def Start():

    ObjectContainer.title1 = TITLE
    HTTP.CacheTime = CACHE_1HOUR

###################################################################################################
@handler(PREFIX, TITLE)
def MainMenu():

    oc = ObjectContainer()

    # Yahoo Screen Featured Sections
    oc.add(DirectoryObject(key=Callback(Featured, title='Featured'), title='Featured'))

    # Yahoo Screen By Categories
    oc.add(DirectoryObject(key=Callback(Categories, title='Categories'), title='Channels by Category'))

    # Yahoo Search Object
    oc.add(SearchDirectoryObject(identifier='com.plexapp.plugins.yahooscreen', title='Search Yahoo Screen Videos', prompt='Search for Videos'))

    # THE MENU ITEM BELOW CONNECTS TO A FUNCTION WITHIN THIS CHANNEL CODE THAT PRODUCES A LIST OF CHANNELS FOR YAHOO SCREENS
    # IT DOES NOT USE OR INTERACT WITH THE SEARCH SERVICES FOR VIDEOS ABOVE
    # LISTED THIS AFTER THE VIDEO SEARCH TO MAKE SURE THE VIDEO SEARCH IS ACCESIBLE TO PLEX WEB CLIENTS
    #To get the InputDirectoryObject to produce a search input in Roku, prompt value must start with the word "search"
    oc.add(InputDirectoryObject(key=Callback(ChannelFinder), title='Find Yahoo Screen Channels', summary="You can enter a word or first letter and the first 25 results will be returned", prompt="Search for the channels you would like to find"))

    return oc

####################################################################################################
# featured are pulled from html while all others are pulled from json
@route(PREFIX + '/featured')
def Featured(title):

    oc = ObjectContainer(title2=title)
    page = HTML.ElementFromURL(YAHOO_URL)
    section = title

    # Adding the [1] to the ul tag makes sure only the ul that immediately follows the title is picked up instead of all
    for category in page.xpath('//*[text()="%s"]/following-sibling::ul[1]/li/span/a' %title):
        title = category.xpath('.//text()')[0]
        url = category.xpath('./@href')[0]
        cat = url.replace('/', '')

        # This catches any listed in the featured section that would just produce a lists of all the featured
        # and category sections again and sends those on to produce the videos listed at the top of that page
        if title in MORE_FEATURE:
            oc.add(DirectoryObject(key=Callback(SectionJSON, title=title, cat=cat), title=title))
        else:
            oc.add(DirectoryObject(key=Callback(SectionJSON, title=title, cat=cat), title=title))

    return oc

####################################################################################################
@route(PREFIX + '/categories')
def Categories(title):

    oc = ObjectContainer(title2=title)

    try:
        data = JSON.ObjectFromURL(YAHOO_Category_URL)
    except:
        return ObjectContainer(header='Error', message='This feed does not contain any video')

    for item in data:
        cat_title = item['name']
        cat = item['url_alias']
        oc.add(DirectoryObject(key=Callback(SectionJSON, title=cat_title, cat=cat), title=cat_title))

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no channels for %s.' % title)
    else:
        return oc

######################################################################################################
# This is a JSON to produce sections or categories of shows using the parent alias
@route(PREFIX + '/sectionjson', start=int)
def SectionJSON(title, cat, start=0):

    oc = ObjectContainer(title2=title)
    local_url = YAHOO_SECTION_JSON % (cat, start)

    if start == 0:
        # This is to pick up the videos that are listed at the top of each category page
        title = 'Top %s Videos' %title
        oc.add(DirectoryObject(key=Callback(VideoJSON, title=title, url=cat), title=title))

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
    json_url = YAHOO_SECTION_JSON % (cat, start)

    if TestNext(json_url, 'section'):
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

    if TestNext(json_url, 'videos'):
        oc.add(NextPageObject(key = Callback(VideoJSON, title=title, url=url, start=start), title='Next Page ...'))

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no videos for this channel.')
    else:
        return oc

####################################################################################################
# Test to see if there is any data on the next page
@route(PREFIX + '/testnext')
def TestNext(json_url, json_type):

    data = JSON.ObjectFromURL(json_url)

    if json_type == 'section':
        if len(data) > 0:
            return True
    else:
        if 'videos' in data and len(data['videos']) > 0:
            return True

    return False

####################################################################################################
# This function searches for channels on the Yahoo Screen website
# then it sends any results to the VideoJSON() function to produce any videos listed for that channel
@route(PREFIX + '/channelfinder')
def ChannelFinder(query, title='Channel Finder'):

    oc = ObjectContainer(title2='Channel Finder')

    # the QUERY URL can use %20 or plus for spaces
    json_url = CHANNEL_SEARCH_JSON % String.Quote(query, usePlus=True)
    try:
        data = JSON.ObjectFromURL(json_url)
    except:
        return ObjectContainer(header='Error', message='Unable to find results for this query')

    for entry in data['channelResults']:
        title = entry['title']
        alias = entry['alias']
        #Log(' the value of alias is %s' %alias)
        alias = alias.replace('wf-channel=', '')
        oc.add(DirectoryObject(key=Callback(VideoJSON, title=title, url=alias), title=title))

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no videos for this channel.')
    else:
        return oc
