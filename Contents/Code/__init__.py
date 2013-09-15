TITLE    = 'TVLand'
PREFIX   = '/video/tvland'
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

TVLAND_URL = 'http://www.tvland.com'
FULLEP_URL = 'http://www.tvland.com/full-episodes'
SEARCH_URL = 'http://www.tvland.com/search?keywords=%s'
HIC = 'http://www.tvland.com/shows/hot-in-cleveland/full-episodes'
CLIPS = 'http://www.tvland.com/video-clips'
EPISODE_FIND = 'http://www.tvland.com/fragments/search_results/related_episodes_seasons?showId=%s&seasonId=%s'
SHOW_THUMBS = 'http://tvland.mtvnimages.com/images/shows/%s/promos/'
FEED = 'http://www.tvland.com/feeds/mrss?uri=%s'
FIRST_PAGE = '?page=1&sortBy=date&contentTypes=Video'
# This regex gets the show id for the EPISODE_FIND
RE_SHOW_ID = Regex('var showId = "(.+?)";')
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
  oc.add(DirectoryObject(key=Callback(FullEpMain, title="Full Episodes"), title="Full Episodes"))
  oc.add(DirectoryObject(key=Callback(VideoClipMain, title="Video Clips"), title="Video Clips"))
  oc.add(InputDirectoryObject(key=Callback(Clips, title="Search Videos", url=SEARCH_URL), title="Search Videos", summary="Click here to search for Videos on TVLand", prompt="Search for videos in TVLand"))
	
  return oc
#########################################################################################################################
@route(PREFIX + '/fullepmain')
def FullEpMain(title):

  oc = ObjectContainer(title2=title)
  oc.add(DirectoryObject(key=Callback(FullEpType, title="Full Episodes By Show"), title="Full Episodes By Show"))
  oc.add(DirectoryObject(key=Callback(LatestVideos, title="Latest Full Episodes", url=FULLEP_URL, xpath='item'), title="Latest Full Episodes"))
  #oc.add(DirectoryObject(key=Callback(FeaturedVideos, title="Featured Full Episodes", url=FULLEP_URL), title="Featured Full Episodes"))
  oc.add(DirectoryObject(key=Callback(LatestVideos, title="Featured Full Episodes", url=FULLEP_URL, xpath='tvl_off'), title="Featured Full Episodes"))
	
  return oc
#########################################################################################################################
@route(PREFIX + '/fulleptypes')
def FullEpType(title):

  oc = ObjectContainer(title2=title)
  oc.add(DirectoryObject(key=Callback(FullEpShows, title="Original Shows", show_type='Original'), title="Original Shows"))
  oc.add(DirectoryObject(key=Callback(FullEpShows, title="Acquired Shows", show_type='Acquired'), title="Acquired Shows"))
	
  return oc
#########################################################################################################################
@route(PREFIX + '/videoclipmain')
def VideoClipMain(title):

  oc = ObjectContainer(title2=title)
  oc.add(DirectoryObject(key=Callback(VideoClipShows, title="Video Clips By Show"), title="Video Clips By Show"))
  oc.add(DirectoryObject(key=Callback(LatestVideos, title="Latest Video Clips", url=CLIPS, xpath='tvl_off'), title="Latest Video Clips"))
  oc.add(DirectoryObject(key=Callback(FeaturedVideos, title="Featured Video Clips", url=CLIPS), title="Featured Video Clips"))
	
  return oc
#########################################################################################################################
# This function produces a directory for All Shows with Full Episodes
# We get the list of full episode from any show's full episode page. Using Hot in Cleveland full episode page currently
# It is the best source to pull the list of shows because this location includes images
@route(PREFIX + '/fullepshows')
def FullEpShows(title, show_type):

  oc = ObjectContainer(title2=title)
  html = HTML.ElementFromURL(HIC)
  for show in html.xpath('//div[@class="showContainer%s"]'%show_type):
    title = show.xpath('./div/div[@class="showTitle"]/a//text()')[0]
    url = show.xpath('./div/div[@class="showTitle"]/a//@href')[0]
    thumb = show.xpath('./div[@class="showImage"]/a/img//@src')[0].split('?')[0]
    summary = show.xpath('./div/div[@class="episodeNumber"]//text()')[0]

    if show_type == 'Original':
      oc.add(DirectoryObject(key=Callback(PrimeFullSeasons, title=title, url=url, thumb=thumb), title=title, summary=summary, thumb=Resource.ContentsOfURLWithFallback(thumb)))
    else:
      oc.add(DirectoryObject(key=Callback(FullEpisodes, title=title, url=url), title=title, summary=summary, thumb=Resource.ContentsOfURLWithFallback(thumb)))
	
  oc.objects.sort(key = lambda obj: obj.title)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to list right now.")
  else:
    return oc
#########################################################################################################################
# This function produces a directory of shows with video clips
@route(PREFIX + '/videoclipshows')
def VideoClipShows(title):

  oc = ObjectContainer(title2=title)
  html = HTML.ElementFromURL(CLIPS)
  for show in html.xpath('//div[@class="showsList"]/a'):
    title = show.xpath('./text()')[0]
    url = show.xpath('.//@href')[0]
    thumb = GetThumb(url)

    oc.add(DirectoryObject(key=Callback(VideoClipType, title=title, url=url, thumb=thumb), title=title, thumb=Resource.ContentsOfURLWithFallback(thumb)))
	   
  oc.objects.sort(key = lambda obj: obj.title)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to list right now.")
  else:
    return oc
#########################################################################################################################
@route(PREFIX + '/videocliptype')
def VideoClipType(title, url, thumb):

  oc = ObjectContainer(title2=title)
  # Need main show page for featured clips
  show_url = url.replace('/video-clips', '')
  oc.add(DirectoryObject(key=Callback(FeaturedVideos, title="Featured Video Clips", url=show_url), title="Featured Video Clips", thumb=Resource.ContentsOfURLWithFallback(thumb)))
  oc.add(DirectoryObject(key=Callback(Clips, title="All Video Clips", url=url), title="All Video Clips", thumb=Resource.ContentsOfURLWithFallback(thumb)))
	
  return oc
###############################################################################################################
# This function pulls the show and season ID checks to see if there are episodes in that season and if so produces a season folder for it
@route(PREFIX + '/primefullseasons')
def PrimeFullSeasons(url, title, thumb):

  oc = ObjectContainer(title2=title)
  content = HTTP.Request(url).content
  showid = RE_SHOW_ID.search(content).group(1)
  page = HTML.ElementFromString(content)
  for page in page.xpath('//div[@class="tooltip"]/a'):
    title = page.xpath('.//text()')[0]
    seasonid = page.xpath('.//@id')[0]
    season_url = EPISODE_FIND % (showid, seasonid)
    # Here we check to see if the season has episodes in it if not, we do not create a directory for it
    ep_info = HTML.ElementFromURL(season_url).xpath('//div[@class="episodeContainer"]/div//@class')[0]

    if ep_info=='noEpisodesAvailable':
      pass 
    else:
      oc.add(DirectoryObject(key=Callback(FullEpisodes, title=title, url=season_url), title=title, thumb=Resource.ContentsOfURLWithFallback(thumb)))
  
  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to list right now.")
  else:
    return oc
#########################################################################################################################
# For Other Full Episodes
@route(PREFIX + '/fullepisodes')
def FullEpisodes(title, url):

  oc = ObjectContainer(title2=title)
  html = HTML.ElementFromURL(url)
  for episode in html.xpath('//div[@class="episodeContainer"]'):
    url = episode.xpath('./div[@class="episodeTitle"]/a//@href')[0]
    # Some of the files do not have a url, so need to keep those that do and skip those that do not
    if url:
      title = episode.xpath('./div[@class="episodeTitle"]/a//text()')[0]
      episode_num = episode.xpath('./div/div[@class="episodeIdentifier"]//text()')[0].replace('Episode #', '')
      date = Datetime.ParseDate(episode.xpath('./div/div[@class="episodeAirDate"]/text()')[0])
      thumb = episode.xpath('./div/div[@class="episodeImage"]/a/img//@src')[0].split('?')[0]
      # because some of the shows do not have a separate entry for the duration, it messes up my pull for 
      # description and duration, so have to give two options for description and add a try to each
      try:
        description = episode.xpath('./div/div/div[@class="episodeDescription"]/text()')[0]
      except:
        description = episode.xpath('./div/div/div[@class="episodeDescription"]//text()')[0]
      try:
        duration = episode.xpath('./div/div/div[@class="episodeDescription"]/span//text()')[0]
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

    else:
     pass

  oc.objects.sort(key = lambda obj: obj.index, reverse=True)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no episodes to list right now.")
  else:
    return oc
#################################################################################################################
# This pulls the video clip playlist from the top of the a show or section page and uses the mgid to create a list of videos
@route(PREFIX + '/latestvideos')
def LatestVideos(title, url, xpath):

  oc = ObjectContainer(title2=title)
  html = HTML.ElementFromURL(url)
  # the setup for the data is just different enough to make separate xpath lines for each necessary
  # xpath is item for full episodes and tvl_off for clips
  for video in html.xpath('//div[@class="%s"]' %xpath):
    if xpath=='item':
      url = video.xpath('./div[@class="video_description"]/p/a//@href')[0]
      title = video.xpath('./div[@class="video_description"]/p/a//text()')[0]
      date = Datetime.ParseDate(video.xpath('./div[@class="video_description"]/p/span//text()')[0])
      duration = None
      description = video.xpath('./div[@class="video_description"]/p[@class="text"]//text()')[0]
      thumb = video.xpath('./div[@class="video_thumbnail"]/div/div/div/a/img//@src')[0].split('?')[0]
    else:
      url = video.xpath('./div/a//@href')[0]
      try:
        title = video.xpath('./div/div[@class="tooltip_content"]/h2//text()')[0]
      except:
        continue
      duration = video.xpath('./div/div[@class="tooltip_content"]/span//text()')[0]
      duration = Datetime.MillisecondsFromString(duration.replace('(', '').replace(')', ''))
      date = None
      description = video.xpath('./div/div[@class="tooltip_content"]/text()')[1].strip()
      try:
        thumb = video.xpath('./div[@class="video_thumbnail"]/a/div/div/div/img//@src')[0].split('?')[0]
      except:
        thumb = video.xpath('./div/div/div/a/img//@src')[0].split('?')[0]

    oc.add(VideoClipObject(
      url = url, 
      title = title, 
      summary = description, 
      duration = duration, 
      thumb = thumb, 
      originally_available_at = date
      ))

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to list right now.")
  else:
    return oc
#################################################################################################################
# This pulls the video clip playlist or full episodes from the top of the video clips or full episode main page and uses the mgid to create a list of videos
@route(PREFIX + '/featuredvideos')
def FeaturedVideos(title, url):

  oc = ObjectContainer(title2=title)
  xml = GetRSS(url)
  for video in xml.xpath('//item'):
    url = video.xpath('./link//text()')[0]
    title = video.xpath('./title//text()')[0]
    date = Datetime.ParseDate(video.xpath('./pubDate//text()')[0])
    description = video.xpath('./description//text()')[0]
    thumb = video.xpath('./media:group/media:thumbnail//@url', namespaces={'media':'http://search.yahoo.com/mrss/'})[0]

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
#########################################################################################################################
# This function is used for prodicing video clips as well as search results
@route(PREFIX + '/clips')
def Clips(title, url, page_url = '', query=''):

  oc = ObjectContainer(title2=title)
  # If there is not a page_url, then it is the first time through, so need to create proper url
  if query:
    url = SEARCH_URL %String.Quote(query, usePlus = True)
  if page_url:
    if '?keywords' in url:
      local_url = TVLAND_URL + page_url
    else:
      local_url = url + page_url
  else:
    local_url = url
  html = HTML.ElementFromURL(local_url)
  for episode in html.xpath('//div[@class="search_content"]'):
    # Full Episodes search has a slightly different structure to video clip search and video clip by shows, so using try/except where needed
    # Title, show_title, description are in diffferent locations and only full episodes have episode meta needed for episode and date
    try:
      vid_url = episode.xpath('./div[@class="search_image"]/a//@href')[0]
    except:
      continue
    # Some of the files do not have a url, so need to keep those that do and skip those that do not
    if vid_url:
      try:
        vid_title = episode.xpath('./div[@class="search_text"]/h3/a//text()')[0]
      except:
        vid_title = episode.xpath('./h3/a//text()')[0]
      vid_title = vid_title.strip()
      try:
        show_title = episode.xpath('./div[@class="search_text"]/div[@class="search_show"]/b//text()')[0]
      except:
        show_title = episode.xpath('./div[@class="search_show"]/b//text()')[0]
      vid_title = show_title + ' - ' + vid_title
      thumb = episode.xpath('./div[@class="search_image"]/a/div/div/div/img//@src')[0]
      thumb = thumb.split('?')[0]
      # description has four to six entries. For clips the description is the [2] entry. For Episodes, the description is the [0] entry
      # so need to create a list of entries and look for which one has data
      try:
        description = episode.xpath('./div[@class="search_text"]/text()')
        for entry in description:
          entry = entry.strip()
          if entry:
            summary = entry
          else:
            pass
      except:
        summary = ''
      try:
        duration = episode.xpath('./div[@class="search_text"]/span//text()')[0]
        duration = Datetime.MillisecondsFromString(duration.replace("(", '').replace(")", ''))
      except:
        duration = 0
      # For Episode and date, both peices of data as well as a '|' are in /div[@class="episode_meta"]/span/text()
      try:
        episode_data = episode.xpath('./div[@class="episode_meta"]/span/text()')
        episode = episode_data[0].replace('#', '')
        if len(episode)==3:
          season = int(episode[0])
        else:
          season = 0
        date = Datetime.ParseDate(episode_data[2])
      except:
        episode = 0
        season = 0
        date = None

      oc.add(EpisodeObject(
        url = vid_url, 
        title = vid_title,
        thumb = Resource.ContentsOfURLWithFallback(thumb),
        summary = summary,
        index = int(episode),
        season = season,
        originally_available_at = date,
        duration = duration))

    else:
      pass
  
  try:
    page_url = 	html.xpath('//div[@class="search_pagination"]/a[@class="next"]//@href')
    if page_url:
      oc.add(NextPageObject(key = Callback(Clips, title = title, url = url, page_url = page_url), title = L("Next Page ...")))
  except:
      pass

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no episodes to list right now.")
  else:
    return oc

#############################################################################################################################
# This is a function to pull the thumb for shows. Pulling from a side list in the main clip page that only returns title and url 
# This statement works for most is: 'http://tvland.mtvnimages.com/images/shows/' + show_name + '/promos/' + show_name + '_watch_00.jpg'
# Added soul man since I know where it is
@route(PREFIX + '/getthumb')
def GetThumb(url):
  show_name = url.split('/shows/')[1]
  show_name = show_name.replace('/video-clips', '').replace('-', '_')

  if show_name == 'the_soul_man':
    show_name = 'soul_man'
    thumb = SHOW_THUMBS %show_name + 'season1/the_soul_man_watch_00.jpg'
  else:
    thumb = SHOW_THUMBS %show_name + show_name + '_watch_00.jpg'
  return thumb

###############################################################################################################
# This function gets the mgid from a page. Can be use with the feed http://www.tvland.com/feeds/mrss?uri= by adding mgid 
# has title, thumb and description, and date for each video and playlist
@route(PREFIX + '/getmgid', mgid=str)
def GetRSS(url):
  page = HTML.ElementFromURL(url)
  mgid = page.xpath('//div[@id="video_player_box"]//@data-mgid')[0]
  xml = XML.ElementFromURL(FEED %mgid)

  return xml