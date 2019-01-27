import time

AGENT_NAME = "[JikanPlex]"

LANGUAGES = [Locale.Language.English]
PRIMARY_PROVIDER = True
ACCEPTS_FROM = ["com.plexapp.agents.localmedia"]

EXTRA_POSTERS = Prefs["extraPosters"]
CAST_DATA = Prefs["getCast"]

JIKAN_URL = "https://api.jikan.moe/v3"
JIKAN_ANIME_SEARCH = "/search/anime?q={title}&limit=10"
JIKAN_ANIME_DETAILS = "/anime/{id}"
JIKAN_ANIME_PICTURES = "/anime/{id}/pictures"
JIKAN_ANIME_CHARACTERS = "/anime/{id}/characters_staff"
JIKAN_ANIME_EPISODES = "/anime/{id}/episodes"

def Start(): pass

class JikanPlex(Agent.TV_Shows):
    name = "JikanPlex"
    languages = LANGUAGES
    primary_provider = PRIMARY_PROVIDER
    accepts_from = ACCEPTS_FROM

    def search(self, results, media, lang):
        if str( media.year ) == "None":
            searchData = GetData( url=JIKAN_URL + JIKAN_ANIME_SEARCH.format( title=String.Quote(media.show) ) )
        else:
            searchData = GetData( url=JIKAN_URL + JIKAN_ANIME_SEARCH.format( title=String.Quote(media.show) ) + "&start_date=" + str( media.year ) + "-01-01" )
        
        for idx,data in enumerate( reversed( searchData["results"] ), 1 ):
            results.Append(MetadataSearchResult(
                id = str( data["mal_id"] ),
                name = data["title"],
                year = str( data["start_date"] ).split("T")[0],
                score = idx + 90,
                lang = lang
            ))

    def update(self, metadata, media, lang):
        searchData = GetData( JIKAN_URL + JIKAN_ANIME_DETAILS.format( id=metadata.id ) )

        # Title
        metadata.title = searchData["title"]

        # Start airing
        metadata.originally_available_at = Datetime.ParseDate( str( searchData["aired"]["from"] ).split("T")[0] ).date()

        # Members score
        metadata.rating = float( searchData["score"] )

        # Content rating
        metadata.content_rating = searchData["rating"]

        # Original title
        metadata.original_title = metadata.title

        # Studios
        for studio in searchData["studios"]:
            metadata.studio = studio["name"]

        # Synopsis
        metadata.summary = searchData["synopsis"]

        # Genres
        metadata.genres.clear()
        for genre in searchData["genres"]:
            metadata.genres.add( genre["name"] )

        # Duration
        metadata.duration = int( str(searchData["duration"]).split(" ")[0] )
        
        # Check user choice for posters
        if EXTRA_POSTERS == "small and large":
            postersData = GetData( JIKAN_URL + JIKAN_ANIME_PICTURES.format( id=metadata.id ) )
                
            # Small Posters
            for posterSmall in postersData["pictures"]:
                if posterSmall["small"] not in metadata.posters:
                    try: metadata.posters[ posterSmall["small"] ] = Proxy.Preview(HTTP.Request( posterSmall["small"] ).content)
                    except: pass
                        
            # Large Posters
            for posterLarge in postersData["pictures"]:
                if posterLarge["large"] not in metadata.posters:
                    try: metadata.posters[ posterLarge["large"] ] = Proxy.Preview(HTTP.Request( posterLarge["large"] ).content)
                    except: pass
                        
        elif EXTRA_POSTERS == "only small":
            postersData = GetData( JIKAN_URL + JIKAN_ANIME_PICTURES.format( id=metadata.id ) )
                
            # Small Posters
            for posterSmall in postersData["pictures"]:
                if posterSmall["small"] not in metadata.posters:
                    try: metadata.posters[ posterSmall["small"] ] = Proxy.Preview(HTTP.Request( posterSmall["small"] ).content)
                    except: pass
                        
        elif EXTRA_POSTERS == "only large":
            postersData = GetData( JIKAN_URL + JIKAN_ANIME_PICTURES.format( id=metadata.id ) )
                
            # Large Posters
            for posterLarge in postersData["pictures"]:
                if posterLarge["large"] not in metadata.posters:
                    try: metadata.posters[ posterLarge["large"] ] = Proxy.Preview(HTTP.Request( posterLarge["large"] ).content)
                    except: pass
        else:
            if searchData["image_url"] not in metadata.posters:
                try: metadata.posters[ searchData["image_url"] ] = Proxy.Preview(HTTP.Request( searchData["image_url"] ).content)
                except: pass

        # Cast
        if CAST_DATA == "Characters":
            charactersData = GetData( JIKAN_URL + JIKAN_ANIME_CHARACTERS.format( id=metadata.id ) )
            
            metadata.roles.clear()
            for character in charactersData["characters"]:
                role = metadata.roles.new()
                
                role.name = character["name"]
                role.role = character["role"]
                role.photo = character["image_url"]
        
        elif CAST_DATA == "Voice Actors":
            charactersData = GetData( JIKAN_URL + JIKAN_ANIME_CHARACTERS.format( id=metadata.id ) )
            
            metadata.roles.clear()
            for character in charactersData["characters"]:
                for actor in character["voice_actors"]:
                    if actor["language"] == "Japanese":
                        actorImage = GetHtmlData( url="https://myanimelist.net/people/" + str( actor["mal_id"] ), par1="//td[ @class='borderClass' ]/div/a/img//@src" )
                        
                        role = metadata.roles.new()
                        role.name = actor["name"]
                        role.role = character["name"] #data["role"]
                        role.photo = actorImage[0]
            
        episodesData = GetData( JIKAN_URL + JIKAN_ANIME_EPISODES.format( id=metadata.id ) )
        
        # Updating season 1 episodes
        for episode in episodesData["episodes"]:
            episodeSeason1 = metadata.seasons[1].episodes[ int( episode["episode_id"] ) ]
                    
            episodeSeason1.title = episode["title"]
                    
            try: episodeSeason1.originally_available_at = Datetime.ParseDate( str( episode["aired"]["from"] ).split("T")[0] ).date()
            except: pass
            
        # Check if there are more seasons in this serie
        if len( media.seasons ) > 1:
            
            # Check if actually exists a sequel
            if "Sequel" in searchData["related"]:
            
                # We don't need season 1 here
                media.seasons.pop("1")
            
                # Store current anime sequel ID
                animeSequelId = None
                
                # Get sequel ID
                for data in searchData["related"]["Sequel"]:
                    animeSequelId = data["mal_id"]
                
                # Sort season by ascending and loop over it
                for s in sorted( media.seasons ):
                    season = metadata.seasons[s]
                    
                    searchData = GetData( JIKAN_URL + JIKAN_ANIME_DETAILS.format( id=animeSequelId ) )
                    
                    # Check user choice for posters
                    if EXTRA_POSTERS == "small and large":
                        postersData = GetData( JIKAN_URL + JIKAN_ANIME_PICTURES.format( id=animeSequelId ) )
                            
                        # Small Posters
                        for posterSmall in postersData["pictures"]:
                            if posterSmall["small"] not in metadata.posters:
                                try: metadata.posters[ posterSmall["small"] ] = Proxy.Preview(HTTP.Request( posterSmall["small"] ).content)
                                except: pass
                        
                        # Large Posters
                        for posterLarge in postersData["pictures"]:
                            if posterLarge["large"] not in metadata.posters:
                                try: metadata.posters[ posterLarge["large"] ] = Proxy.Preview(HTTP.Request( posterLarge["large"] ).content)
                                except: pass
                        
                    elif EXTRA_POSTERS == "only small":
                        postersData = GetData( JIKAN_URL + JIKAN_ANIME_PICTURES.format( id=animeSequelId ) )
                        
                        # Small Posters
                        for posterSmall in postersData["pictures"]:
                            if posterSmall["small"] not in metadata.posters:
                                try: metadata.posters[ posterSmall["small"] ] = Proxy.Preview(HTTP.Request( posterSmall["small"] ).content)
                                except: pass
                        
                    elif EXTRA_POSTERS == "only large":
                        postersData = GetData( JIKAN_URL + JIKAN_ANIME_PICTURES.format( id=animeSequelId ) )
                            
                        # Large Posters
                        for posterLarge in postersData["pictures"]:
                            if posterLarge["large"] not in metadata.posters:
                                try: metadata.posters[ posterLarge["large"] ] = Proxy.Preview(HTTP.Request( posterLarge["large"] ).content)
                                except: pass
                    else:
                        if searchData["image_url"] not in metadata.posters:
                            metadata.posters[ searchData["image_url"] ] = Proxy.Preview(HTTP.Request( searchData["image_url"] ).content)
                    
                    episodesData = GetData( JIKAN_URL + JIKAN_ANIME_EPISODES.format( id=animeSequelId ) )
                    # Season episodes
                    for episode in episodesData["episodes"]:
                        seasonEpisode = metadata.seasons[s].episodes[ int( episode["episode_id"] ) ]
                        
                        seasonEpisode.title = episode["title"]
                        
                        try: seasonEpisode.originally_available_at = Datetime.ParseDate( str( episode["aired"]["from"] ).split("T")[0] ).date()
                        except: pass
                    
                    # Check if there is another season after this one
                    if "Sequel" in searchData["related"]:
                        for data in searchData["related"]["Sequel"]:
                            animeSequelId = data["mal_id"]
                    else: pass
                    
            else: pass
            
#################################################################
           
class JikanPlex(Agent.Movies):
    name = "JikanPlex"
    languages = LANGUAGES
    primary_provider = PRIMARY_PROVIDER
    accepts_from = ACCEPTS_FROM

    def search(self, results, media, lang):
        if str( media.year ) == "None":
            searchData = GetData( JIKAN_URL + JIKAN_ANIME_SEARCH.format( title=String.Quote(media.name) ) + "&type=Movie" )
        else:
            searchData = GetData( JIKAN_URL + JIKAN_ANIME_SEARCH.format( title=String.Quote(media.name) ) + "&type=Movie&start_date=" + str( media.year ) + "-01-01" )
        
        for idx,data in enumerate( reversed( searchData["results"] ), 1 ):
            results.Append(MetadataSearchResult(
                id = str( data["mal_id"] ),
                name = data["title"],
                year = str( data["start_date"] ).split("T")[0],
                score = idx + 90,
                lang = lang
            ))

    def update(self, metadata, media, lang):
        searchData = GetData( JIKAN_URL + JIKAN_ANIME_DETAILS.format( id=metadata.id ) )

        # Title
        metadata.title = searchData["title"]

        # Start airing
        metadata.originally_available_at = Datetime.ParseDate( str( searchData["aired"]["from"] ).split("T")[0] ).date()

        # Members score
        metadata.rating = float( searchData["score"] )

        # Content rating
        metadata.content_rating = searchData["rating"]

        # Original title
        metadata.original_title = metadata.title

        # Studios
        if searchData["studios"] is not None:
            for studio in searchData["studios"]:
                metadata.studio = studio["name"]

        # Synopsis
        metadata.summary = searchData["synopsis"]

        # Genres
        metadata.genres.clear()
        for genre in searchData["genres"]:
            metadata.genres.add( genre["name"] )

        # Duration
        metadata.duration = int( str(searchData["duration"]).split(" ")[0] )
        
        # Check user choice for posters
        if EXTRA_POSTERS == "Small and Large":
            postersData = GetData( JIKAN_URL + JIKAN_ANIME_PICTURES.format( id=metadata.id ) )
                
            # Small Posters
            for posterSmall in postersData["pictures"]:
                if posterSmall["small"] not in metadata.posters:
                    try: metadata.posters[ posterSmall["small"] ] = Proxy.Preview(HTTP.Request( posterSmall["small"] ).content)
                    except: pass
                        
            # Large Posters
            for posterLarge in postersData["pictures"]:
                if posterLarge["large"] not in metadata.posters:
                    try: metadata.posters[ posterLarge["large"] ] = Proxy.Preview(HTTP.Request( posterLarge["large"] ).content)
                    except: pass
                        
        elif EXTRA_POSTERS == "Only Small":
            postersData = GetData( JIKAN_URL + JIKAN_ANIME_PICTURES.format( id=metadata.id ) )
                
            # Small Posters
            for posterSmall in postersData["pictures"]:
                if posterSmall["small"] not in metadata.posters:
                    try: metadata.posters[ posterSmall["small"] ] = Proxy.Preview(HTTP.Request( posterSmall["small"] ).content)
                    except: pass
                        
        elif EXTRA_POSTERS == "Only Large":
            postersData = GetData( JIKAN_URL + JIKAN_ANIME_PICTURES.format( id=metadata.id ) )
                
            # Large Posters
            for posterLarge in postersData["pictures"]:
                if posterLarge["large"] not in metadata.posters:
                    try: metadata.posters[ posterLarge["large"] ] = Proxy.Preview(HTTP.Request( posterLarge["large"] ).content)
                    except: pass
                        
        else:
            if searchData["image_url"] not in metadata.posters:
                try: metadata.posters[ searchData["image_url"] ] = Proxy.Preview(HTTP.Request( searchData["image_url"] ).content)
                except: pass

        # Cast
        if CAST_DATA == "Characters":
            charactersData = GetData( JIKAN_URL + JIKAN_ANIME_CHARACTERS.format( id=metadata.id ) )
            
            metadata.roles.clear()
            for character in charactersData["characters"]:
                role = metadata.roles.new()
                
                role.name = character["name"]
                role.role = character["role"]
                role.photo = character["image_url"]
        
        elif CAST_DATA == "Voice Actors":
            charactersData = GetData( JIKAN_URL + JIKAN_ANIME_CHARACTERS.format( id=metadata.id ) )
            
            metadata.roles.clear()
            for data in charactersData["characters"]:
                for actor in data["voice_actors"]:
                    if actor["language"] == "Japanese":
                        actorImage = GetHtmlData( url="https://myanimelist.net/people/" + str( actor["mal_id"] ), par1="//td[ @class='borderClass' ]/div/a/img//@src" )
                        
                        role = metadata.roles.new()
                        role.name = actor["name"]
                        role.role = data["role"]
                        role.photo = actorImage[0]
            
        else: pass

#################################################################

SLEEP_TIME = 4
JSON_SLEEP_TIME = 2.0

def GetData(url):
    time.sleep( SLEEP_TIME )
    
    result = None
    try: result = JSON.ObjectFromURL( url, sleep=JSON_SLEEP_TIME, headers={ "Accept": "application/json" }, method="GET" )
    except Exception as ex: Log( AGENT_NAME + " Error fetching data from: " + url + " - Error: " + str( ex ) )
    return result
    
def GetHtmlData(url, par1):
    time.sleep( SLEEP_TIME )
    
    result = None
    try: result = HTML.ElementFromURL( url ).xpath( par1 )
    except Exception as ex: Log( AGENT_NAME + " Error fetching data from: " + url + " - Error: " + str( ex ) )
    return result