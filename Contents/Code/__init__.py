TITLE = 'TVLand'
PREFIX = '/video/tvland'
ART = 'art-default.jpg'
ICON = 'icon-default.jpg'

BASE_URL = 'http://www.tvland.com'
RE_MANIFEST_URL = Regex('var triforceManifestURL = "(.+?)";', Regex.DOTALL)
RE_MANIFEST = Regex('var triforceManifestFeed = (.+?);\n', Regex.DOTALL)

EXCLUSIONS = []
SEARCH ='http://relaunch-search.tvland.com/solr/tvland/select?q=%s&wt=json&defType=edismax&start='
SEARCH_TYPE = ['Video', 'Episode', 'Series']
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
    oc.add(InputDirectoryObject(key = Callback(SearchSections, title="Search"), title = "Search"))
    return oc

####################################################################################################
# This function pulls the various json feeds for video sections of a page 
@route(PREFIX + '/feedmenu')
def FeedMenu(title, url, thumb=''):
    
    oc = ObjectContainer(title2=title)
    feed_title = title
    try:
        content = HTTP.Request(url, cacheTime=CACHE_1DAY).content
        try: 
            zone_list = JSON.ObjectFromString(RE_MANIFEST.search(content).group(1))['manifest']['zones']
        except: 
            zone_list = JSON.ObjectFromURL(RE_MANIFEST_URL.search(content).group(1))['manifest']['zones']
    except:
        return ObjectContainer(header="Incompatible", message="Unable to find video feeds for %s." % (url))

    if not thumb:
        try: thumb = HTML.ElementFromString(content).xpath('//meta[@property="og:image"]/@content')[0].strip()
        except: thumb = ''

    for zone in zone_list:

        if zone in ('header', 'footer', 'ads-reporting', 'ENT_M171'):
            continue

        json_feed = zone_list[zone]['feed']

        # Split feed to get ent code
        try: ent_code = json_feed.split('/feeds/')[1].split('/')[0]
        except:  ent_code = ''

        ent_code = ent_code.split('_tvland')[0]

        if ent_code not in ENT_LIST:
            continue

        json = JSON.ObjectFromURL(json_feed, cacheTime = CACHE_1DAY)

        try: title = json['result']['promo']['headline'].title()
        except: 
            try: title = json['result']['data']['headerText'].title()
            except: 
                title = feed_title
        # Create menu for the ent_m151 - full episodes to produce videos and menu items for full episode feeds by show
        if ent_code=='ent_m151':
            oc.add(DirectoryObject(key=Callback(ShowVideos, title=title, url=json_feed),
                title=title,
                thumb=Resource.ContentsOfURLWithFallback(url=thumb)
            ))
            for item in json['result']['shows']:
                oc.add(DirectoryObject(key=Callback(ShowVideos, title=item['title'], url=item['url']),
                    title=item['title']
                ))
        # Create menu for each show's full episodes - ent_m112
        elif ent_code == 'ent_m112':

            oc.add(DirectoryObject(
                key = Callback(ShowVideos, title=title, url=json_feed),
                title = title,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb)
            ))

        # Create menu items for those that need to go to Produce Sections
        # ent_m100-featured show and ent_m150-all shows and ent_m112 - video clips by season
        # ent_m116 result type filters otherwise the result type is items
        else:
            if ent_code == 'ent_m116':
                result_type = 'filters'
            else:
                result_type = 'items'
            oc.add(DirectoryObject(key=Callback(ProduceSection, title=title, url=json_feed, result_type=result_type),
                title=title,
                thumb=Resource.ContentsOfURLWithFallback(url=thumb)
            ))
            
    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no results to list.")
    else:
        return oc
####################################################################################################
# For Producing the sections from various json feeds
# This function can produce show lists, AtoZ show lists, and video filter lists
# Even though TVLand just has featured shows, we are keeping the alpha code if it is added later
@route(PREFIX + '/producesection', alpha=int)
def ProduceSection(title, url, result_type, thumb='', alpha=None):

    oc = ObjectContainer(title2=title)
    (section_title, feed_url) = (title, url)
    counter=0
    json = JSON.ObjectFromURL(url)

    try: item_list = json['result']['data']['items']
    except: 
        try: item_list = json['result'][result_type]
        except: item_list = []

    # Create item list for individual sections of alphabet for the All listings
    if '/ent_m150/' in feed_url and alpha:
        item_list = json['result']['data']['items'][alpha]['sortedItems']
    for item in item_list:
        # Create a list of show sections
        if '/ent_m150/' in feed_url or '/ent_m100/' in feed_url:
            if '/ent_m150/' in feed_url and not alpha:
                oc.add(DirectoryObject(
                    key=Callback(ProduceSection, title=item['letter'], url=feed_url, result_type=result_type, alpha=counter),
                    title=item['letter']
                ))
                counter=counter+1
            else:
                try: url = item['canonicalURL']
                except:
                    try: url = item['url']
                    except: continue
                # Skip bad show urls that do not include '/shows/' or events. If '/events/' there is no manifest.
                if '/shows/' not in url:
                    continue
                if item['title'] in EXCLUSIONS:
                    continue
                try: thumb = item['image']['url']
                except: 
                    try: thumb = item['image'][0]['url']
                    except: thumb = thumb
                if thumb.startswith('//'):
                    thumb = 'https:' + thumb
                oc.add(DirectoryObject(
                    key=Callback(FeedMenu, title=item['title'], url=url, thumb=thumb),
                    title=item['title'],
                    thumb = Resource.ContentsOfURLWithFallback(url=thumb)
                ))

        # Create season sections for filters
        else:
            # Skip any empty sections
            count=item['count']
            if  count==0:
                continue
            oc.add(DirectoryObject(
                key=Callback(ShowVideos, title=item['name'], url=item['url']),
                title=item['name'],
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
    except:
        try: videos = json['result']['data']['items']
        except: return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    
    for video in videos:

        vid_url = video['canonicalURL']

        # catch any bad links that get sent here
        if not ('/video-clips/') in vid_url and not ('/video-playlists/') in vid_url and not ('/full-episodes/') in vid_url and not ('/episodes/') in vid_url:
            continue
        if 'bellator.spike.com' in vid_url:
            continue

        thumb = video['images'][0]['url']

        show = video['show']['title']
        try: episode = int(video['season']['episodeNumber'])
        except: episode = 0
        try: season = int(video['season']['seasonNumber'])
        except: season = 0
        
        try: unix_date = video['airDate']
        except:
            try: unix_date = video['publishDate']
            except: unix_date = unix_date = video['date']['originalPublishDate']['timestamp']
        date = Datetime.FromTimestamp(float(unix_date)).strftime('%m/%d/%Y')
        date = Datetime.ParseDate(date)

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
            thumb = Resource.ContentsOfURLWithFallback(url=thumb ),
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
@route(PREFIX + '/searchsections')
def SearchSections(title, query):
    
    oc = ObjectContainer(title2=title)
    json_url = SEARCH %String.Quote(query, usePlus = False)
    local_url = json_url + '0&facet=on&facet.field=bucketName_s'
    json = JSON.ObjectFromURL(local_url)
    i = 0
    search_list = json['facet_counts']['facet_fields']['bucketName_s']
    for item in search_list:
        if item in SEARCH_TYPE and search_list[i+1]!=0:
            oc.add(DirectoryObject(key = Callback(Search, title=item, url=json_url, search_type=item), title = item))
        i=i+1

    return oc
####################################################################################################
@route(PREFIX + '/search', start=int)
def Search(title, url, start=0, search_type=''):

    oc = ObjectContainer(title2=title)
    local_url = '%s%s&fq=bucketName_s:%s' %(url, start, search_type)
    json = JSON.ObjectFromURL(local_url)

    for item in json['response']['docs']:

        result_type = item['bucketName_s']
        title = item['title_t']
        full_title = '%s: %s' % (result_type, title)

        try: item_url = item['url_s']
        except: continue
        # Skip bellator url that are not part of the URL service
        if not item_url.startswith(BASE_URL):
            continue

        # For Shows
        if result_type == 'Series':

            oc.add(DirectoryObject(
                key = Callback(FeedMenu, title=item['title_t'], url=item_url, thumb=item['imageUrl_s']),
                title = full_title,
                thumb = Resource.ContentsOfURLWithFallback(url=item['imageUrl_s'])
            ))

        # For Episodes and ShowVideo(video clips)
        else:
            try: season = int(item['seasonNumber_s'].split(':')[0])
            except: season = None

            try: episode = int(item['episodeNumber_s'])
            except: episode = None

            try: show = item['seriesTitle_t']
            except: show = None

            try: summary = item['description_t']
            except: summary = None

            try: duration = Datetime.MillisecondsFromString(item['duration_s'])
            except: duration = None

            oc.add(EpisodeObject(
                url = item_url, 
                show = show, 
                title = full_title, 
                thumb = Resource.ContentsOfURLWithFallback(url=item['imageUrl_s']),
                summary = summary, 
                season = season, 
                index = episode, 
                duration = duration, 
                originally_available_at = Datetime.ParseDate(item['contentDate_dt'])
            ))

    if json['response']['start']+10 < json['response']['numFound']:

        oc.add(NextPageObject(
            key = Callback(Search, title='Search', url=url, search_type=search_type, start=start+10),
            title = 'Next Page ...'
        ))

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no results to list.")
    else:
        return oc
