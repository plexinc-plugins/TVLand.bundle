TITLE    = 'TVLand'
PREFIX   = '/video/tvland'
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

BASE_URL = 'http://www.tvland.com'
FULLEP_URL = 'http://www.tvland.com/full-episodes'
EPISODE_FIND = 'http://www.tvland.com/fragments/search_results/related_episodes_seasons?showId=%s&seasonId=%s'
SHOW_THUMBS = 'http://tvland.mtvnimages.com/images/shows/%s/promos/'
###################################################################################################
# Set up containers for all possible objects
def Start():

    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)

    DirectoryObject.thumb = R(ICON)
    HTTP.CacheTime = CACHE_1DAY 

###################################################################################################
@handler(PREFIX, TITLE)
def MainMenu():

    oc = ObjectContainer()
    # This picks up the first url of a show listed under the fullepisode pull sown menu to use for producing a show list
    full_show = HTML.ElementFromURL(FULLEP_URL).xpath('//li[@class="first full_ep"]/a/@href')[0]
    oc.add(DirectoryObject(key=Callback(FullEpShows, title="Shows", url=full_show), title="Shows"))
    oc.add(DirectoryObject(key=Callback(Videos, title="Latest Full Episodes", url=FULLEP_URL), title="Latest Full Episodes")) 
    oc.add(SearchDirectoryObject(identifier="com.plexapp.plugins.tvland", title=L("Search TVLand Videos"), prompt=L("Search for Videos")))
    
    return oc
#########################################################################################################################
# This function produces a directory for All Shows with Full Episodes
# We get the list of full episode from any show's full episode page using first show listed under full episodes
# It is the best source to pull the list of shows because this location includes images
@route(PREFIX + '/fullepshows')
def FullEpShows(title, url):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url)
    for show in html.xpath('//div[contains(@class, "showContainer")]'):
        show_type = show.xpath('./@class')[0]
        title = show.xpath('.//div[@class="showTitle"]/a//text()')[0]
        url = show.xpath('.//div[@class="showTitle"]/a//@href')[0]
        thumb = show.xpath('./div[@class="showImage"]/a/img//@src')[0].split('?')[0]
        summary = show.xpath('.//div[@class="episodeNumber"]//text()')[0]
        show_id = show.xpath('./@id')[0].split('_')[1]
        oc.add(DirectoryObject(key=Callback(FullEpisodes, title=title, url=url, show_id=show_id, thumb=thumb), title=title, summary=summary, thumb=Resource.ContentsOfURLWithFallback(thumb)))
    
    oc.objects.sort(key = lambda obj: obj.title)

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to list right now.")
    else:
        return oc
#########################################################################################################################
# For Checking for season and producing Full Episodes
@route(PREFIX + '/fullepisodes')
def FullEpisodes(title, url, show_id, thumb):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url)
    seasons = html.xpath('//div[@class="tooltip"]/a')
    if len(seasons)>0:
        for season in seasons:
            title = season.xpath('.//text()')[0]
            seasonid = season.xpath('.//@id')[0]
            season_url = EPISODE_FIND % (show_id, seasonid)
            # Here we check to see if the season has episodes in it if not, we do not create a directory for it
            ep_info = HTML.ElementFromURL(season_url).xpath('//div[@class="episodeContainer"]/div//@class')[0]
            if ep_info!='noEpisodesAvailable':
                oc.add(DirectoryObject(key=Callback(FullEpisodes, title=title, url=season_url, show_id=show_id, thumb=thumb), title=title, thumb=Resource.ContentsOfURLWithFallback(thumb)))

    else:
        for episode in html.xpath('//div[@class="episodeContainer"]'):
            url = episode.xpath('./div[@class="episodeTitle"]/a//@href')[0]
            # Some of the files do not have a url, so need to keep those that do and skip those that do not
            if url:
                title = episode.xpath('./div[@class="episodeTitle"]/a//text()')[0]
                episode_num = episode.xpath('.//div[@class="episodeIdentifier"]//text()')[0].replace('Episode #', '')
                date = Datetime.ParseDate(episode.xpath('.//div[@class="episodeAirDate"]/text()')[0])
                thumb = episode.xpath('.//div[@class="episodeImage"]/a/img//@src')[0].split('?')[0]
                # because some of the shows do not have a separate entry for the duration, it messes up my pull for 
                # description and duration, so have to give two options for description and add a try to each
                try:
                    description = episode.xpath('.//div[@class="episodeDescription"]/text()')[0]
                except:
                    description = episode.xpath('.//div[@class="episodeDescription"]//text()')[0]
                try:
                    duration = episode.xpath('.//div[@class="episodeDescription"]/span//text()')[0]
                    duration = Datetime.MillisecondsFromString(duration.replace("(", '').replace(")", ''))
                except:
                    duration = 0

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
        return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no episodes to list right now.")
    else:
        return oc
#################################################################################################################
# This pulls the videos from the list of latest videos
@route(PREFIX + '/videos')
def Videos(title, url):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url)
    for video in html.xpath('//div[contains(@class,"activity_feed") and contains(@id,"frag_")]'):
        url = video.xpath('.//div[@class="video_description"]//a/@href')[0]
        thumb = video.xpath('.//div[@class="video_thumbnail"]//img/@src')[0].split('?')[0]
        info_list = video.xpath('.//div[@class="video_description"]/p//text()')
        title = '%s: %s' %(info_list[0], info_list[1])
        description = info_list[2]
        date = Datetime.ParseDate(info_list[4])
      
        oc.add(VideoClipObject(
            url = url, 
            title = title, 
            summary = description, 
            thumb = thumb, 
            originally_available_at = date
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to list right now.")
    else:
        return oc
