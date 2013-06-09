# Things to fix
# add separate pages for addtional clips
# look back at adding some of the xpath that was cousing issue
# could combine original and aquired main show pages

TITLE    = 'Tvland'
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
	
  oc.add(DirectoryObject(key=Callback(VideoClipShows, title="Video Clips"), title="Video Clips", thumb=R(ICON)))
	
  return oc

#########################################################################################################################
def FullEpTypes(title):

  oc = ObjectContainer(title2=title)
  
  oc.add(DirectoryObject(key=Callback(OriginalShows, title="Original Shows"), title="Original Shows", thumb=R(ICON)))
	
  oc.add(DirectoryObject(key=Callback(AcquiredShows, title="Acquired Shows"), title="Acquired Shows", thumb=R(ICON)))
	
  return oc


#########################################################################################################################
# For Original Shows with Full Episodes
# STILL NEED TO ADD OLDER SEASON EPISODES
@route(PREFIX + '/originalshows')
def OriginalShows(title):

  oc = ObjectContainer(title2=title)

  html = HTML.ElementFromURL(HIC)
  for show in html.xpath('//div[@class="showContainerOriginal"]'):
    title = show.xpath('./div/div[@class="showTitle"]/a//text()')[0]
    url = show.xpath('./div/div[@class="showTitle"]/a//@href')[0]
    thumb = show.xpath('./div/a/img//@src')[0]
    thumb = thumb.split('?')[0]
	# do not really need total shows, but good to have xpath already
    # total = show.xpath('./div/div[@class="episodeNumber"]//text()')[0]
    # total = int(total.replace(' Full Episodes', ''))

    oc.add(DirectoryObject(key=Callback(PrimeFullEpisodes, title=title, url=url), title=title, thumb=thumb))
	   
  oc.objects.sort(key = lambda obj: obj.title)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no shows to list right now.")
  else:
    return oc
#########################################################################################################################
# For Acquired Shows with Full Episodes
@route(PREFIX + '/acquiredshows')
def AcquiredShows(title):

  oc = ObjectContainer(title2=title)

  html = HTML.ElementFromURL(HIC)
  for show in html.xpath('//div[@class="showContainerAcquired"]'):
    title = show.xpath('./div/div[@class="showTitle"]/a//text()')[0]
    url = show.xpath('./div/div[@class="showTitle"]/a//@href')[0]
    thumb = show.xpath('./div/a/img//@src')[0]
    thumb = thumb.split('?')[0]
	# do not really need total shows, but good to have xpath already
    # total = show.xpath('./div/div[@class="episodeNumber"]//text()')[0]
    # total = int(total.replace(' Full Episodes', ''))

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
    url = episode.xpath('./div[@class="episodeTitle"]/a//@href')[0]
    # Some of the files do not have a url, so need to keep those that do and skip those that do not
    if url:
      title = episode.xpath('./div[@class="episodeTitle"]/a//text()')[0]
      episode_num = episode.xpath('./div/div[@class="episodeIdentifier"]//text()')[0]
      episode_num = episode_num.replace('Episode #', '')
      date = episode.xpath('./div/div[@class="episodeAirDate"]/text()')[0]
      date = Datetime.ParseDate(date)
      thumb = episode.xpath('./div/div[@class="episodeImage"]/a/img//@src')[0]
      thumb = thumb.split('?')[0]
      # for some reason I get out of range erros on description and duration. Will have to look back at these later
      # description = episode.xpath('./div[@class="episodeContentContainer"]/div/div[@class="episodeDescription"]/text')[0]
      # duration = episode.xpath('./div[@class="episodeContentContainer"]/div/div[@class="episodeDescription"]/span//text()')[0]
      # duration = duration.replace("(", '').replace(")", '')
      # duration = Datetime.MillisecondsFromString(duration)
      # season = episode.xpath('./div[@class="tooltip"]/a[@id=%s]', %seasonid)[0].text
      # season = season.replace('Season ', '')

      oc.add(EpisodeObject(
        url = url, 
        title = title,
        # season = int(season),
        thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)),
        # summary = description,
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

#########################################################################################################################
# For Prime video clips
# here is a url for pages 'http://www.tvland.com/shows/the-soul-man/video-clips?page=2&sortBy=date&contentTypes=Video&season=&collectionId='
@route(PREFIX + '/clips', total=int)
def Clips(title, url, total, page = 0):

  oc = ObjectContainer(title2=title)
  pages_list = GetPages(url)
  pages_num = len(pages_list)
  list_num = 0
  while pages_num > page:
    page = pages_list[list_num]
    local_url = url + '?page=' + str(page) + '&sortBy=date&contentTypes=Video'
    list_num = list_num + 1

    html = HTML.ElementFromURL(local_url)
    for episode in html.xpath('//div[@class="search_entry"]'):
      ep_url = episode.xpath('./div/div/div/h3/a//@href')[0]
      # Some of the files do not have a url, so need to keep those that do and skip those that do not
      if ep_url:
        title = episode.xpath('./div/div/div[@class="search_text"]/h3/a//text()')[0]
        title = title.lstrip()
        thumb = episode.xpath('./div/div/div[@class="search_image"]/a/div/div/div/img//@src')[0]
        thumb = thumb.split('?')[0]
        # for some reason I get out of range errors on description. Will have to look back at these later
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
          # summary = description,
          duration = int(duration)))

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

#################################################################################################################################
@route(PREFIX + '/getpages')
def GetPages(url):

  page_list = []
  page_list.append(1)
  page = HTML.ElementFromURL(url)
  for page in page.xpath('//div[@class="search_pagination"]/span/a'):
    num = page.xpath('.//text()')[0]
    num = int(num)
    page_list.append(num)
  return (page_list)

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
