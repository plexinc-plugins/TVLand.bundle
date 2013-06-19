TITLE    = 'TVLand'
PREFIX   = '/video/tvland'
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

# We get the list of full episode shows from any pages with a watch more full episode section.
# here we are using Hot in Cleveland full episode page
HIC = 'http://www.tvland.com/shows/hot-in-cleveland/full-episodes'
CLIPS = 'http://www.tvland.com/video-clips'
EPISODE_FIND = 'http://www.tvland.com/fragments/search_results/related_episodes_seasons?showId=%s&seasonId=%s'
SHOW_THUMBS = 'http://tvland.mtvnimages.com/images/shows/%s/promos/'
FEED = 'http://www.tvland.com/feeds/mrss?uri=%s'
FIRST_PAGE = '?page=1&sortBy=date&contentTypes=Video&season=&collectionId='
# This regex gets the show id for the EPISODE_FIND
RE_SHOW_ID = Regex('var showId = "(.+?)";')

###################################################################################################
# Set up containers for all possible objects
def Start():

  ObjectContainer.title1 = TITLE
  HTTP.CacheTime = CACHE_1DAY 

###################################################################################################
@handler(PREFIX, TITLE)
def MainMenu():

  oc = ObjectContainer()
  
  oc.add(DirectoryObject(key=Callback(FullEpTypes, title="Full Episodes"), title="Full Episodes"))
	
  oc.add(DirectoryObject(key=Callback(VideoClipTypes, title="Video Clips"), title="Video Clips"))
	
  return oc

#########################################################################################################################
@route(PREFIX + '/fulleptypes')
def FullEpTypes(title):

  oc = ObjectContainer(title2=title)
  
  oc.add(DirectoryObject(key=Callback(FullEpShows, title="Original Shows", show_type='Original'), title="Original Shows"))
	
  oc.add(DirectoryObject(key=Callback(FullEpShows, title="Acquired Shows", show_type='Acquired'), title="Acquired Shows"))
	
  return oc

#########################################################################################################################
@route(PREFIX + '/videocliptypes')
def VideoClipTypes(title):

  oc = ObjectContainer(title2=title)
  
  oc.add(DirectoryObject(key=Callback(VideoClipLatest, title="Video Clips"), title="Latest Video Clips"))
	
  oc.add(DirectoryObject(key=Callback(VideoClipShows, title="Video Clips"), title="Video Clips By Show"))
	
  return oc


#########################################################################################################################
# For All Shows with Full Episodes
@route(PREFIX + '/fullepshows')
def FullEpShows(title, show_type):

  oc = ObjectContainer(title2=title)

  html = HTML.ElementFromURL(HIC)
  for show in html.xpath('//div[@class="showContainer%s"]'%show_type):
    title = show.xpath('./div/div[@class="showTitle"]/a//text()')[0]
    url = show.xpath('./div/div[@class="showTitle"]/a//@href')[0]
    thumb = show.xpath('./div/a/img//@src')[0]
    thumb = thumb.split('?')[0]

    if show_type == 'Original':
      oc.add(DirectoryObject(key=Callback(PrimeFullEpisodes, title=title, url=url), title=title, thumb=Resource.ContentsOfURLWithFallback(thumb)))
    else:
      oc.add(DirectoryObject(key=Callback(FullEpisodes, title=title, url=url), title=title, thumb=Resource.ContentsOfURLWithFallback(thumb)))
	
  oc.objects.sort(key = lambda obj: obj.title)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to list right now.")
  else:
    return oc

#########################################################################################################################
# For Video Clips
@route(PREFIX + '/videoclipshows')
def VideoClipShows(title):

  oc = ObjectContainer(title2=title)

  html = HTML.ElementFromURL(CLIPS)
  for show in html.xpath('//div[@class="showsList"]/a'):
    title = show.xpath('./text()')[0]
    url = show.xpath('.//@href')[0]
    thumb = GetThumb(url)

    oc.add(DirectoryObject(key=Callback(Clips, title=title, url=url), title=title, thumb=Resource.ContentsOfURLWithFallback(thumb)))
	   
  oc.objects.sort(key = lambda obj: obj.title)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no shows to list right now.")
  else:
    return oc

#########################################################################################################################
# For Full Episodes
# found this URL that gives shows and episodes with descriptions and thumbs for original show full episodes
# http://www.tvland.com/fragments/search_results/related_episodes_seasons?showId=25573&seasonId=63748
@route(PREFIX + '/primefullepisodes')
def PrimeFullEpisodes(title, url):

  oc = ObjectContainer(title2=title)
  showid = ShowID(url)
  # they usually only make the current season and a couple episodes from the last season available on the site
  # but based on the time of the year, the newest season folder may be empty on the site, so you would
  # have to go back three season. So the only way to make sure we were getting all episodes was to 
  # pull and go through the page with all the seasons
  season_list = GetSeasonIDs(url)
  seasons = len(season_list)
  while seasons > 0:
    list_num = seasons - 1
    seasonid = season_list[list_num]
    show_url = EPISODE_FIND % (showid, seasonid)
    html = HTML.ElementFromURL(show_url)
    try:
      for episode in html.xpath('//div[@class="episodeContainer"]'):
        url = episode.xpath('./div[@class="episodeTitle"]/a//@href')[0]
        if url:
          title = episode.xpath('./div[@class="episodeTitle"]/a//text()')[0]
          episode_num = episode.xpath('./div/div[@class="episodeIdentifier"]//text()')[0]
          episode_num = episode_num.replace('Episode #', '')
          date = episode.xpath('./div/div[@class="episodeAirDate"]/text()')[0]
          thumb = episode.xpath('./div/div[@class="episodeImage"]/a/img//@src')[0]
          thumb = thumb.split('?')[0]
          description = episode.xpath('./div/div/div[@class="episodeDescription"]/text()')[0]
          duration = episode.xpath('./div/div/div[@class="episodeDescription"]/span//text()')[0]
          duration = Datetime.MillisecondsFromString(duration.replace("(", '').replace(")", ''))

          oc.add(EpisodeObject(
            url = url, 
            title = title,
            season = int(seasons),
            thumb = Resource.ContentsOfURLWithFallback(thumb),
            summary = description,
            index = int(episode_num),
            duration = duration,
            originally_available_at = Datetime.ParseDate(date)))

        else:
          pass

    except:
      pass

    seasons = seasons - 1

  oc.objects.sort(key = lambda obj: obj.index, reverse=True)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no episodes to list right now.")
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
      episode_num = episode.xpath('./div/div[@class="episodeIdentifier"]//text()')[0]
      episode_num = episode_num.replace('Episode #', '')
      date = episode.xpath('./div/div[@class="episodeAirDate"]/text()')[0]
      thumb = episode.xpath('./div/div[@class="episodeImage"]/a/img//@src')[0]
      thumb = thumb.split('?')[0]
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
        originally_available_at = Datetime.ParseDate(date)))

    else:
     pass

  oc.objects.sort(key = lambda obj: obj.index, reverse=True)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no episodes to list right now.")
  else:
    return oc

#################################################################################################################
# This pulls a latest video playlist mgid from the video clips main page
@route(PREFIX + '/latestclips')
def VideoClipLatest(title):

  oc = ObjectContainer(title2=title)
  xml = GetRSS(CLIPS)
  for video in xml.xpath('//item'):
    url = video.xpath('./link//text()')[0]
    title = video.xpath('./title//text()')[0]
    date = video.xpath('./pubDate//text()')[0]
    description = video.xpath('./description//text()')[0]
    thumb = video.xpath('./media:group/media:thumbnail//@url', namespaces={'media':'http://search.yahoo.com/mrss/'})[0]

    oc.add(VideoClipObject(
      url = url, 
      title = title, 
      summary = description, 
      thumb = thumb, 
      originally_available_at = Datetime.ParseDate(date)
      ))

  return oc
  
#########################################################################################################################
# here is a sample url for adding pages
# 'http://www.tvland.com/shows/the-soul-man/video-clips?page=2&sortBy=date&contentTypes=Video&season=&collectionId='
@route(PREFIX + '/clips', total=int)
def Clips(title, url, page_url = ''):

  oc = ObjectContainer(title2=title)
  if not page_url:
    local_url = url + FIRST_PAGE
  else:
    local_url = url + page_url
  Log('the value of local_url is %s' %local_url)
  html = HTML.ElementFromURL(local_url)
  for episode in html.xpath('//div[@class="search_entry"]'):
    vid_url = episode.xpath('./div/div/div/h3/a//@href')[0]
    # Some of the files do not have a url, so need to keep those that do and skip those that do not
    if vid_url:
      vid_title = episode.xpath('./div/div/div[@class="search_text"]/h3/a//text()')[0]
      vid_title = title.lstrip()
      thumb = episode.xpath('./div/div/div[@class="search_image"]/a/div/div/div/img//@src')[0]
      thumb = thumb.split('?')[0]
      # all of the clips appear to include a separate entry for the duration, but just to be safe
      # I am still keeping the two options and adding a try for description and duration
      try:
        description = episode.xpath('./div/div/div[@class="search_text"]/text()')[2]
      except:
        description = episode.xpath('./div/div/div[@class="search_text"]//text()')[2]
      description = description.strip()
      Log('the value of description is %s' %description)
      try:
        duration = episode.xpath('./div/div/div[@class="search_text"]/span//text()')[0]
        duration = Datetime.MillisecondsFromString(duration.replace("(", '').replace(")", ''))
      except:
        duration = 0

      oc.add(VideoClipObject(
        url = vid_url, 
        title = vid_title,
        thumb = Resource.ContentsOfURLWithFallback(thumb),
        summary = description.strip(),
        duration = duration))

    else:
      pass
  
  try:
    page_url = 	html.xpath('//div[@class="search_pagination"]/a[@class="next"]//@href')
    Log('the value of page_url is %s' %page_url)
    if page_url:
      oc.add(NextPageObject(key = Callback(Clips, title = title, url = url, page_url = page_url), title = L("Next Page ...")))
  except:
      pass

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="This directory appears to be empty. There are no episodes to list right now.")
  else:
    return oc

###############################################################################################################
# This function pulls the show ID 
@route(PREFIX + '/showid')
def ShowID(url):
  ID = ''
  content = HTTP.Request(url).content
  ID = RE_SHOW_ID.search(content).group(1)
  return ID

#################################################################################################################################
def GetSeasonIDs(url):
# To get all season IDS, we need to create a list
  season_list = []
  page = HTML.ElementFromURL(url)
  for page in page.xpath('//div[@class="tooltip"]/a'):
    id = page.xpath('.//@id')[0]
    season_list.append(id)
  return (season_list)

#############################################################################################################################
# This is a function to pull the thumb for shows. Pulling from a side list in the main clip page that only returns title and url 
# This statement works for most is: 'http://tvland.mtvnimages.com/images/shows/' + show_name + '/promos/' + show_name + '_watch_00.jpg'
# Added shoul man since I know where it is
@route(PREFIX + '/getthumb')
def GetThumb(url):
  show_name = url.split('/shows/')[1]
  show_name = show_name.replace('/video-clips', '')
  show_name = show_name.replace('-', '_')

  if show_name == 'the_soul_man':
    show_name = 'soul_man'
    thumb = SHOW_THUMBS %show_name + 'season1/the_soul_man_watch_00.jpg'
  else:
    thumb = SHOW_THUMBS %show_name + show_name + '_watch_00.jpg'
  return thumb

###############################################################################################################
# this gets the mgid from a page. Can be use with the feed http://www.tvland.com/feeds/mrss?uri= by adding mgid 
# has title, thumb and description, and date for each video and playlist

@route(PREFIX + '/getmgid', mgid=str)
def GetRSS(url):
  page = HTML.ElementFromURL(url)
  mgid = page.xpath('//div[@id="video_player_box"]//@data-mgid')[0]
  xml = XML.ElementFromURL(FEED %mgid)

  return xml


# Notes

# url service test
# I love lucy full episodes have issues - The Gossip played only the first block and then gave error. Fred and Ethel Fight
# played first two sections and then played credits twice
# found a cosby episode that is playing the last section double. Roseanne and Curb Your Enthusiasm work fine

# Could not find any jsons for the site. Did find the html with images and links for Original Full Episodes
# Found that there is are mgids in most pages that can be used with the feed used to find video files (see FEED variable)
# Episode or video pages as well as the full episode main pages contain the mgid for the video or episode currently
# playing. These are used below to get extra info needed for videos
# Show pages and the main video clips page contain a playlist mgid that gives the latest video clips
# You can also add the show id from the shows main page found in the 'http://repo.comedycentral.com/feeds' url
# to 'http://www.tvland.com/feeds/mrss?uri=mgid:cms:playlist:tvland.com:' + show_id and get the latest 25 videos from each show
# Not sure how this could be used other than replacing the existing viceo clip sections or adding a latest videos section to 
# each show's video clip section. Maybe later the site will add more playlists options
# thought the playlist could give links to thumbs for shows but all give the main thumb as 
# 'http://www.tvland.com/sitewide/img/sprites/TVLand_bug2.png'

