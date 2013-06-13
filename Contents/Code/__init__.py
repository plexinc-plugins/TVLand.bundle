
TITLE    = 'TVLand'
PREFIX   = '/video/tvland'
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

BASE_URL = 'http://www.tvland.com'
FULL_EPISODES = 'http://www.tvland.com/full-episodes'
# or get them from any pages watch more full episode section
HIC = 'http://www.tvland.com/shows/hot-in-cleveland/full-episodes'
CLIPS = 'http://www.tvland.com/video-clips'
EPISODE_FIND = 'http://www.tvland.com/fragments/search_results/related_episodes_seasons?'
SHOW_THUMBS = 'http://tvland.mtvnimages.com/images/shows/'
FEED = 'http://www.tvland.com/feeds/mrss?uri='

RE_SHOW_ID = Regex('var showId = "(.+?)";')

http = 'http:'
COUNTER = 0

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

###################################################################################################
# This Main Menu provides a section for each type of show. It is hardcoded in since the types of show have to be set and preprogrammed in
@handler(PREFIX, TITLE, art=ART, thumb=ICON)

def MainMenu():

  oc = ObjectContainer()
  
  oc.add(DirectoryObject(key=Callback(FullEpTypes, title="Full Episodes"), title="Full Episodes", thumb=R(ICON)))
	
  oc.add(DirectoryObject(key=Callback(VideoClipTypes, title="Video Clips"), title="Video Clips", thumb=R(ICON)))
	
  return oc

#########################################################################################################################
def FullEpTypes(title):

  oc = ObjectContainer(title2=title)
  
  oc.add(DirectoryObject(key=Callback(FullEpShows, title="Original Shows", show_type='Original'), title="Original Shows", thumb=R(ICON)))
	
  oc.add(DirectoryObject(key=Callback(FullEpShows, title="Acquired Shows", show_type='Acquired'), title="Acquired Shows", thumb=R(ICON)))
	
  return oc

#########################################################################################################################
def VideoClipTypes(title):

  oc = ObjectContainer(title2=title)
  
  oc.add(DirectoryObject(key=Callback(VideoClipLatest, title="Video Clips"), title="Latest Video Clips", thumb=R(ICON)))
	
  oc.add(DirectoryObject(key=Callback(VideoClipShows, title="Video Clips"), title="Video Clips By Show", thumb=R(ICON)))
	
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
    # do not really need total shows, but good to have xpath already
    # total = show.xpath('./div/div[@class="episodeNumber"]//text()')[0]
    # total = int(total.replace(' Full Episodes', ''))

    if show_type == 'Original':
      oc.add(DirectoryObject(key=Callback(PrimeFullEpisodes, title=title, url=url), title=title, thumb=thumb))
    else:
      oc.add(DirectoryObject(key=Callback(FullEpisodes, title=title, url=url), title=title, thumb=thumb))
	
  oc.objects.sort(key = lambda obj: obj.title)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no shows to list right now.")
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
    total = show.xpath('./span//text()')[0]
    total = total.replace("(", '').replace(")", '')
    icon = show.xpath('.//@class')[0]
    if icon.find('prime') > -1:
      prime = True
    else:
      prime = False
    thumb = GetThumb(title)

    oc.add(DirectoryObject(key=Callback(Clips, title=title, url=url, total=total), title=title, thumb=thumb))
	   
  oc.objects.sort(key = lambda obj: obj.title)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no shows to list right now.")
  else:
    return oc

#########################################################################################################################
# For Full Episodes
# found this that gives shows and episodes with descriptions and thumbs
# http://www.tvland.com/fragments/search_results/related_episodes_seasons?showId=25573&seasonId=63748
@route(PREFIX + '/primefullepisodes')
def PrimeFullEpisodes(title, url):

  oc = ObjectContainer(title2=title)
  showid = ShowID(url)
  season_list = GetSeasonIDs(url)
  seasons = len(season_list)
  while seasons > 0:
    list_num = seasons - 1
    seasonid = season_list[list_num]
    show_url = EPISODE_FIND + 'showId=' + showid + '&seasonId=' + seasonid
    html = HTML.ElementFromURL(show_url)
    try:
      for episode in html.xpath('//div[@class="episodeContainer"]'):
        ep_url = episode.xpath('./div[@class="episodeTitle"]/a//@href')[0]
        if ep_url:
          title = episode.xpath('./div[@class="episodeTitle"]/a//text()')[0]
          episode_num = episode.xpath('./div/div[@class="episodeIdentifier"]//text()')[0]
          episode_num = episode_num.replace('Episode #', '')
          date = episode.xpath('./div/div[@class="episodeAirDate"]/text()')[0]
          date = Datetime.ParseDate(date)
          thumb = episode.xpath('./div/div[@class="episodeImage"]/a/img//@src')[0]
          thumb = thumb.split('?')[0]
          description = episode.xpath('./div/div/div[@class="episodeDescription"]/text()')[0]
          duration = episode.xpath('./div/div/div[@class="episodeDescription"]/span//text()')[0]
          duration = duration.replace("(", '').replace(")", '')
          duration = Datetime.MillisecondsFromString(duration)
          page = HTML.ElementFromURL(url)
          oc.add(EpisodeObject(
            url = ep_url, 
            title = title,
            season = int(seasons),
            thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)),
            summary = description,
            index = int(episode_num),
            duration = int(duration),
            originally_available_at = date))

        else:
          pass

    except:
      pass

    seasons = seasons - 1

  oc.objects.sort(key = lambda obj: obj.index, reverse=True)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no episodes to list right now.")
  else:
    return oc
#########################################################################################################################
# For Other Full Episodes
@route(PREFIX + '/fullepisodes')
def FullEpisodes(title, url):

  oc = ObjectContainer(title2=title)
  html = HTML.ElementFromURL(url)
  for episode in html.xpath('//div[@class="episodeContainer"]'):
    ep_url = episode.xpath('./div[@class="episodeTitle"]/a//@href')[0]
    # Some of the files do not have a url, so need to keep those that do and skip those that do not
    if ep_url:
      title = episode.xpath('./div[@class="episodeTitle"]/a//text()')[0]
      episode_num = episode.xpath('./div/div[@class="episodeIdentifier"]//text()')[0]
      episode_num = episode_num.replace('Episode #', '')
      date = episode.xpath('./div/div[@class="episodeAirDate"]/text()')[0]
      date = Datetime.ParseDate(date)
      thumb = episode.xpath('./div/div[@class="episodeImage"]/a/img//@src')[0]
      thumb = thumb.split('?')[0]
      # for some reason I get out of range erros on description and duration. So using mgid for description
      try:
        description = GetDesc(ep_url)
      except:
        description = 'No Description'
      # below is the xpath from the page that gave out of range errors
      # description = episode.xpath('./div[@class="episodeContentContainer"]/div/div[@class="episodeDescription"]/text')[0]
      # duration = episode.xpath('./div[@class="episodeContentContainer"]/div/div[@class="episodeDescription"]/span//text()')[0]
      # duration = duration.replace("(", '').replace(")", '')
      # duration = Datetime.MillisecondsFromString(duration)

      oc.add(EpisodeObject(
        url = ep_url, 
        title = title,
        thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)),
        summary = description,
        index = int(episode_num),
        # duration = int(duration),
        originally_available_at = date))

    else:
     pass

  oc.objects.sort(key = lambda obj: obj.index, reverse=True)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no episodes to list right now.")
  else:
    return oc

#################################################################################################################
# This pulls a latest video playlist mgid from the video clips main page
@route(PREFIX + '/latestclips')
def VideoClipLatest(title):

  oc = ObjectContainer(title2=title)
  mgid = GetMGID(CLIPS)
  xml_url = FEED + mgid
  xml = XML.ElementFromURL(xml_url)
  for video in xml.xpath('//item'):
    epUrl = video.xpath('./link//text()')[0]
    epTitle = video.xpath('./title//text()')[0]
    epDate = video.xpath('./pubDate//text()')[0]
    epDate = Datetime.ParseDate(epDate)
    description = video.xpath('./description//text()')[0]
    epThumb = video.xpath('./media:group/media:thumbnail//@url', namespaces={'media':'http://search.yahoo.com/mrss/'})[0]

    oc.add(VideoClipObject(
      url = epUrl, 
      title = epTitle, 
      summary = description, 
      thumb = epThumb, 
      originally_available_at = epDate
      ))

  return oc
  
#########################################################################################################################
# For video clips
# here is a url for adding pages
# 'http://www.tvland.com/shows/the-soul-man/video-clips?page=2&sortBy=date&contentTypes=Video&season=&collectionId='
@route(PREFIX + '/clips', total=int, page=int)
def Clips(title, url, total, page = 1):

  oc = ObjectContainer(title2=title)
  # we want this number to reflect the total number of pages so we are using the base url
  pages_num = GetNumPages(total)
  local_url = url + '?page=' + str(page) + '&sortBy=date&contentTypes=Video'

  html = HTML.ElementFromURL(local_url)
  for episode in html.xpath('//div[@class="search_entry"]'):
    ep_url = episode.xpath('./div/div/div/h3/a//@href')[0]
    # Some of the files do not have a url, so need to keep those that do and skip those that do not
    if ep_url:
      title = episode.xpath('./div/div/div[@class="search_text"]/h3/a//text()')[0]
      title = title.lstrip()
      thumb = episode.xpath('./div/div/div[@class="search_image"]/a/div/div/div/img//@src')[0]
      thumb = thumb.split('?')[0]
      # for some reason I get out of range errors on description. so using mgid and xml instead
      try:
        description = GetDesc(ep_url)
      except:
        description = 'No Description'
      # below is the xpath from the page that gave out of range errors
      # description = episode.xpath('./div/div/div[@class="search_text"]/text')[0]
      # description = description.strip()
      try:
        duration = episode.xpath('./div/div/div[@class="search_text"]/span//text()')[0]
        duration = duration.replace("(", '').replace(")", '')
        duration = Datetime.MillisecondsFromString(duration)
      except:
        duration = 0

      oc.add(VideoClipObject(
        url = ep_url, 
        title = title,
        thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)),
        summary = description,
        duration = int(duration)))

    else:
      pass

# here we would add pages and use the YouTube as example
#  for some reason I can only go as high as nine. I think the pages_num cannot pick up any more because it does not show 
# higher than nine with the base url
  if pages_num > 1:
    page = html.xpath('//div[@class="search_pagination"]/span[@class="pageOn"]//text()')[1]
    Log('the value of page is %s' %page)
    page = int(page)
    page = page + 1 
    if page <= pages_num: 
      oc.add(NextPageObject(
      key = Callback(Clips, title = title, url = url, total= total, page = page), 
      title = L("Next Page ...")))
    else:
      pass
  else:
    pass

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no episodes to list right now.")
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

##################################################################################################################################
# this pulls the numbers from the pagination code at the bottom of each page
# it only works to page nine, so may need to add a check for more pages
@route(PREFIX + '/getnumpages', total=int)
def GetNumPages(total):

  pages = float(total) / 20
  Log('the value of pages is %s' %pages)
  total_pages = int(total) / 20
  Log('the value of total_pages is %s' %total_pages)
  if  pages > total_pages:
    total_pages = total_pages +1
    Log('the value of total_pages is %s' %total_pages)
  return (total_pages)

#############################################################################################################################
# This is a function to pull the thumb for shows
# cannot get the thumbs for video clip shows so this is a way to try to find them
# the statement below works for most
# http://tvland.mtvnimages.com/images/shows/ + show_name + /promos/ + show_name + _watch_00.jpg
@route(PREFIX + '/getthumb')
def GetThumb(title):
  show_name = title.lower()
  show_name = show_name.rstrip()
  show_name = show_name.replace(' ', '_')
  show_name = show_name.replace(',', '')
  show_name = show_name.replace("'", '')
  show_name = show_name.replace('the_andy_griffith_show', 'andy_griffith_show')
  show_name = show_name.replace('the_cosby_show', 'bill_cosby_show')
  show_name = show_name.replace('_-_starring_fran_drescher', '')

  if show_name == 'hot_in_cleveland':
    thumb = SHOW_THUMBS + 'hot_in_cleveland/hot_in_cleveland_watch_background_4f5d00.jpg'
  elif show_name == 'the_soul_man':
    thumb = SHOW_THUMBS + 'soul_man/promos/season1/the_soul_man_watch_00.jpg'
  elif show_name == 'happily_divorced':
    thumb = SHOW_THUMBS + 'happily_divorced/promos/season2/happily_divorced_watch_00.jpg'
  else:
    thumb = SHOW_THUMBS + show_name + '/promos/' + show_name + '_watch_00.jpg'

  return thumb

###############################################################################################################
# this gets the mgid from a page. For individual video pages, it returns the mgid for that episode or video
# for show pages, it returns the mgid for a video clip playlist, and for full episode pages, it returns the mgid for 
# the episode currently playing and there is also a latest video playlist mgid on the video main page
# Can be use with the feed http://www.tvland.com/feeds/mrss?uri= by adding mgid 
# has title, thumb and description, and date for each video and playlist

@route(PREFIX + '/getmgid', mgid=str)
def GetMGID(url):
  page = HTML.ElementFromURL(url)
  mgid = page.xpath('//div[@id="video_player_box"]//@data-mgid')[0]
  return mgid

#################################################################################################################
# this pulls the description from the feeds when unable to easily get them from the url
@route(PREFIX + '/getdesc', desc=str)
def GetDesc(url):
  mgid = GetMGID(url)
  xml_url = FEED + mgid
  xml = XML.ElementFromURL(xml_url)
  desc = xml.xpath('//channel/description//text()')[0]
  return desc

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

