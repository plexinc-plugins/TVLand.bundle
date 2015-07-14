TITLE    = 'TVLand'
PREFIX   = '/video/tvland'
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

BASE_URL = 'http://www.tvland.com'
FULLEP_URL = 'http://www.tvland.com/full-episodes' 
# Using Hot in Cleveland full ep page as url
FULL_SHOW = 'http://www.tvland.com/shows/hot-in-cleveland/full-episodes'
EPISODE_FIND = 'http://www.tvland.com/fragments/search_results/related_episodes_seasons?showId=%s&seasonId=%s'
###################################################################################################
# Set up containers for all possible objects
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
    oc.add(DirectoryObject(key=Callback(Shows, title="Shows", url=FULL_SHOW), title="Shows"))
    oc.add(DirectoryObject(key=Callback(LatestVideos, title="Latest Full Episodes", url=FULLEP_URL), title="Latest Full Episodes")) 
    oc.add(SearchDirectoryObject(identifier="com.plexapp.plugins.tvland", title=L("Search TVLand Videos"), prompt=L("Search for Videos")))
    
    return oc
#########################################################################################################################
# This function produces a directory for All Shows with Full Episodes
# We get the list of full episode from a show's full episode page using Hot In Cleveland right now
# It is the best source to pull the list of shows because this location includes images
@route(PREFIX + '/shows')
def Shows(title, url):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url)
    for show in html.xpath('//div[contains(@class, "showContainer")]'):
        title = show.xpath('.//div[@class="showTitle"]//text()')[0]
        url = show.xpath('.//div[@class="showTitle"]/a/@href')[0]
        thumb = show.xpath('./div[@class="showImage"]//img/@src')[0].split('?')[0]
        summary = show.xpath('.//div[@class="episodeNumber"]/text()')[0]
        show_id = show.xpath('./@id')[0].split('_')[1]
        oc.add(DirectoryObject(key=Callback(Episodes, title=title, url=url, show_id=show_id, thumb=thumb), title=title, summary=summary, thumb=Resource.ContentsOfURLWithFallback(thumb)))
    
    oc.objects.sort(key = lambda obj: obj.title)

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to list right now.")
    else:
        return oc
#########################################################################################################################
# For Checking for season and producing Full Episodes
@route(PREFIX + '/episodes')
def Episodes(title, url, show_id, thumb):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url)
    seasons = html.xpath('//a[@class="season"]')
    if len(seasons)>0:
        for season in seasons:
            title = season.xpath('.//text()')[0].strip()
            seasonid = season.xpath('./@id')[0]
            season_url = EPISODE_FIND % (show_id, seasonid)
            # Checking each season for entries would mean two urls to check here and could cause timeouts, so we are producing all seasons
            oc.add(DirectoryObject(key=Callback(Episodes, title=title, url=season_url, show_id=show_id, thumb=thumb), title=title, thumb=Resource.ContentsOfURLWithFallback(thumb)))
            oc.objects.sort(key = lambda obj: obj.title, reverse=True)

    else:
        for episode in html.xpath('//div[@class="episodeContainer"]'):
            try:
                url = episode.xpath('.//a/@href')[0]
            except:
                # This catches season that do not have episodes but also can prevent other errors
                continue
            if url:
                title = episode.xpath('./div[@class="episodeTitle"]//text()')[0]
                episode_num = episode.xpath('.//div[@class="episodeIdentifier"]/text()')[0].replace('Episode #', '')
                date = Datetime.ParseDate(episode.xpath('.//div[@class="episodeAirDate"]/text()')[0])
                thumb = episode.xpath('.//div[@class="episodeImage"]//img/@src')[0].split('?')[0]
                description = episode.xpath('.//div[@class="episodeDescription"]/text()')[0]
                # because some of the shows do not have a duration, we put it in a try 
                try:
                    duration = episode.xpath('.//span[@class="episodeDuration"]/text()')[0]
                    duration = Datetime.MillisecondsFromString(duration.replace("(", '').replace(")", ''))
                except:
                    duration = None

                oc.add(EpisodeObject(
                    url = url, 
                    title = title,
                    thumb = Resource.ContentsOfURLWithFallback(thumb),
                    summary = description,
                    index = int(episode_num),
                    duration = duration,
                    originally_available_at = date))

        oc.objects.sort(key = lambda obj: obj.index, reverse=True)

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are currently no episodes available for this folder.")
    else:
        return oc
#################################################################################################################
# This pulls the videos from the list of latest videos
@route(PREFIX + '/latestvideos')
def LatestVideos(title, url):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url)
    for video in html.xpath('//div[@class="activity_feed-episodes"]'):
        url = video.xpath('.//div[@class="video_description"]//a/@href')[0]
        thumb = video.xpath('.//div[@class="video_thumbnail"]//img/@src')[0].split('?')[0]
        info_list = video.xpath('.//div[@class="video_description"]/p//text()')
        # This makes sure the list is long enough to not cause errors
        if len(info_list)>2:
            title = '%s: %s' %(info_list[0], info_list[1])
            try: date = Datetime.ParseDate(info_list[len(info_list)])
            except: date = None
      
            oc.add(VideoClipObject(
                url = url, 
                title = title, 
                summary = info_list[2], 
                thumb = thumb, 
                originally_available_at = date
            ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are currently no episodes available for this folder.")
    else:
        return oc
