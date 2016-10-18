TITLE = 'TVLand'
PREFIX = '/video/tvland'
ART = 'art-default.jpg'
ICON = 'icon-default.jpg'

BASE_URL = 'http://www.tvland.com'
RE_MANIFEST_URL = Regex('var triforceManifestURL = "(.+?)";', Regex.DOTALL)
RE_MANIFEST_FEED = Regex('var triforceManifestFeed = (.+?)\n', Regex.DOTALL)

ENT_LIST = ['ent_m100', 'ent_m150', 'ent_m151', 'ent_m112', 'ent_m116']

###################################################################################################
def Start():

    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    HTTP.CacheTime = CACHE_1HOUR

###################################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(FeedMenu, title='Shows', url=BASE_URL+'/shows'), title='Shows'))
    oc.add(DirectoryObject(key=Callback(FeedMenu, title='Full Episodes', url=BASE_URL+'/full-episodes'), title='Full Episodes'))
    return oc

####################################################################################################
# This function pulls the various json feeds for the video sections of a page 
# including those for an individual show's video and full episodes sections
@route(PREFIX + '/feedmenu')
def FeedMenu(title, url, thumb=''):

    oc = ObjectContainer(title2=title)
    feed_title = title
    result_type='shows'
    feed_list = GetFeedList(url)
    if feed_list<1:
        return ObjectContainer(header="Incompatible", message="Unable to find video feeds for %s." %url)
    
    for json_feed in feed_list:
        # Split feed to get ent code
        try: ent_code = json_feed.split('/feeds/')[1].split('/')[0]
        except: ent_code = ''

        ent_code = ent_code.split('_tvland')[0]

        if ent_code not in ENT_LIST:
            continue

        json = JSON.ObjectFromURL(json_feed, cacheTime = CACHE_1DAY)
        try: title = json['result']['promo']['headline'].title()
        except: title = feed_title
        # Create menu for full episodes to produce videos and menu items for full episode feeds by show
        if ent_code in ['ent_m151', 'ent_m112']:
            oc.add(DirectoryObject(key=Callback(ShowVideos, title=title, url=json_feed),
                title=title,
                thumb=Resource.ContentsOfURLWithFallback(url=thumb)
            ))
            # For the main full episodes page also produce the menu items for full episode feeds by show
            if ent_code=='ent_m151':
                for item in json['result']['shows']:
                    oc.add(DirectoryObject(key=Callback(ShowVideos, title=item['title'], url=item['url']),
                        title=item['title']
                    ))
        # Create menu items for all other to go to Produce Sections
        else:
            # For individual show we send the video section (ent_m116) to be broken up by filters
            if ent_code=='ent_m116':
                result_type='filters'
            # For the main shows url we send featured show(ent_m100) and all shows(ent_m150-) to be broken up by shows
            # TVLand does not currently have an all shows/atoz listing but it may be added in the future
            else:
                result_type='shows'
            oc.add(DirectoryObject(key=Callback(ProduceSection, title=title, url=json_feed, result_type=result_type),
                title=title,
                thumb=Resource.ContentsOfURLWithFallback(url=thumb)
            ))
            
    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no results to list.")
    else:
        return oc
#####################################################################################
# For Producing the sections from various json feeds
# This function can produce show lists, AtoZ show lists, and video filter lists
@route(PREFIX + '/producesection')
def ProduceSection(title, url, result_type, thumb='', alpha=''):
    
    oc = ObjectContainer(title2=title)
    (section_title, feed_url) = (title, url)
    try: json = JSON.ObjectFromURL(url)
    except: return ObjectContainer(header="Incompatible", message="Unable to find video sections for feed")

    try: item_list = json['result'][result_type]
    except: item_list = []
    # Create item list for individual sections of alphabet for the All listings
    if '/feeds/ent_m150' in feed_url and alpha:
        item_list = json['result'][result_type][alpha]
    for item in item_list:
        # Create a list of show sections
        if result_type=='shows':
            # Currently TVLand does not have an a to z listing but keeping the code in case it is added later
            if '/feeds/ent_m150' in feed_url and not alpha:
                oc.add(DirectoryObject(
                    key=Callback(ProduceSection, title=item, url=feed_url, result_type=result_type, alpha=item),
                    title=item.replace('hash', '#').title()
                ))
            # TVLand, like CC and Spike, list all of its full episodes and video clips on the show home page
            else:
                try: url = item['url']
                except: url = item['canonicalURL']
                # Skip bad show urls that do not include '/shows/' or events. If '/events/' there is no manifest.
                if '/shows/' not in url:
                    continue
                try: thumb = item['images'][0]['url']
                except: thumb = thumb
                oc.add(DirectoryObject(
                    key=Callback(FeedMenu, title=item['title'], url=url, thumb=thumb),
                    title=item['title'],
                    thumb = Resource.ContentsOfURLWithFallback(url=thumb)
                ))
        # Create season sections for filters
        else:
            # Skip any empty sections
            try: count=item['subFilters'][1]['count']
            except: count=item['count']
            if  count==0:
                continue
            title=item['name']
            try: url=item['subFilters'][1]['url'] 
            except: url=item['url']
            oc.add(DirectoryObject(
                key=Callback(ShowVideos, title=title, url=url),
                title=title,
                thumb=Resource.ContentsOfURLWithFallback(url=thumb)
            ))
    
    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no results to list right now.")
    else:
        return oc
#######################################################################################
# This function produces the videos listed in json feed under items
@route(PREFIX + '/showvideos')
def ShowVideos(title, url):

    oc = ObjectContainer(title2=title)
    json = JSON.ObjectFromURL(url)
    try: videos = json['result']['items']
    except: return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    
    for video in videos:

        vid_url = video['canonicalURL']

        # catch any bad links that get sent here
        if not ('/video-clips/') in vid_url and not ('/full-episodes/') in vid_url:
            continue

        #Log('video for %s' %video['title'])
        try: thumb = video['images'][0]['url']
        except: thumb = ''

        show = video['show']['title']
        try: episode = int(video['season']['episodeNumber'])
        except: episode = 0
        try: season = int(video['season']['seasonNumber'])
        except: season = 0
        
        try: unix_date = video['publishDate']
        except: unix_date = ''
        if unix_date:
            date = Datetime.FromTimestamp(float(unix_date)).strftime('%m/%d/%Y')
            date = Datetime.ParseDate(date)
        else:
            date = Datetime.Now()

        # Durations for clips have decimal points
        duration = video['duration']
        if not isinstance(duration, int):
            duration = int(duration.split('.')[0])
        duration = duration * 1000

        # Everything else has episode and show info now
        oc.add(EpisodeObject(
            url = vid_url, 
            show = show,
            season = season,
            index = episode,
            title = video['title'], 
            thumb = Resource.ContentsOfURLWithFallback(url=thumb),
            originally_available_at = date,
            duration = duration,
            summary = video['description']
        ))

    try: next_page = json['result']['nextPageURL']
    except: next_page = None

    if next_page and len(oc) > 0:

        oc.add(NextPageObject(
            key = Callback(ShowVideos, title=title, url=next_page),
            title = 'Next Page ...'
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no unlocked videos available to watch.")
    else:
        return oc
####################################################################################################
# This function pulls the list of json feeds from a manifest
@route(PREFIX + '/getfeedlist')
def GetFeedList(url):
    
    feed_list = []
    # In case there is an issue with the manifest URL, we then try just pulling the manifest data
    try: content = HTTP.Request(url, cacheTime=CACHE_1DAY).content
    except: content = ''
    if content:
        try: zone_list = JSON.ObjectFromURL(RE_MANIFEST_URL.search(content).group(1))['manifest']['zoness']
        except:
            try:
                zone_data = RE_MANIFEST_FEED.search(content).group(1)
                if zone_data.endswith(';'):
                    zone_data = zone_data[:-1]
                zone_list = JSON.ObjectFromString(zone_data)['manifest']['zones']
            except: zone_list = []
    
        for zone in zone_list:
            if zone in ('header', 'footer', 'ads-reporting', 'ENT_M171'):
                continue
            json_feed = zone_list[zone]['feed']
            #Log('the value of json_feed is %s' %json_feed)
            feed_list.append(json_feed)

    return feed_list
