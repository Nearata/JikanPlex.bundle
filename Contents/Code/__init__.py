from time import sleep

AGENT_NAME = "JikanPlex"

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

SLEEP_TIME = 4

def Start():
    pass

class JikanPlex(Agent.TV_Shows):
    name = AGENT_NAME
    languages = LANGUAGES
    primary_provider = PRIMARY_PROVIDER
    accepts_from = ACCEPTS_FROM

    def search(self, results, media, lang):
        if str(media.year) == "None":
            data = get_json(url=JIKAN_URL + JIKAN_ANIME_SEARCH.format(title=String.Quote(media.show)))
        else:
            data = get_json(url=JIKAN_URL + JIKAN_ANIME_SEARCH.format(title=String.Quote(media.show)) + "&start_date=" + str(media.year) + "-01-01")
        
        for index, data in enumerate(reversed(data["results"]), 1):
            results.Append(MetadataSearchResult(
                id=str(data["mal_id"]),
                name=data["title"],
                year=str(data["start_date"]).split("T")[0],
                score=index + 90,
                lang=lang
            ))

    def update(self, metadata, media, lang):
        search_result = get_json(JIKAN_URL + JIKAN_ANIME_DETAILS.format(id=metadata.id))

        metadata.title = search_result["title"]
        metadata.originally_available_at = Datetime.ParseDate(str(search_result["aired"]["from"]).split("T")[0]).date()
        metadata.rating = float(search_result["score"])
        metadata.content_rating = search_result["rating"]
        metadata.original_title = metadata.title

        for studio in search_result["studios"]:
            metadata.studio = studio["name"]

        metadata.summary = search_result["synopsis"]
        
        metadata.genres.clear()
        for genre in search_result["genres"]:
            metadata.genres.add(genre["name"])

        metadata.duration = int(str(search_result["duration"]).split(" ")[0])

        if EXTRA_POSTERS == "Small and Large":
            posters_data = get_json(JIKAN_URL + JIKAN_ANIME_PICTURES.format(id=metadata.id))
            for i in posters_data["pictures"]:
                if i["small"] not in metadata.posters:
                    try:
                        metadata.posters[i["small"]] = Proxy.Preview(HTTP.Request(i["small"]).content)
                    except:
                        pass
                        
            for i in posters_data["pictures"]:
                if i["large"] not in metadata.posters:
                    try:
                        metadata.posters[i["large"]] = Proxy.Preview(HTTP.Request(i["large"]).content)
                    except:
                        pass
                        
        elif EXTRA_POSTERS == "Only Small":
            posters_data = get_json(JIKAN_URL + JIKAN_ANIME_PICTURES.format(id=metadata.id))
            for i in posters_data["pictures"]:
                if i["small"] not in metadata.posters:
                    try:
                        metadata.posters[i["small"]] = Proxy.Preview(HTTP.Request(i["small"]).content)
                    except:
                        pass
                        
        elif EXTRA_POSTERS == "Only Large":
            posters_data = get_json(JIKAN_URL + JIKAN_ANIME_PICTURES.format(id=metadata.id))
            for i in posters_data["pictures"]:
                if i["large"] not in metadata.posters:
                    try:
                        metadata.posters[i["large"]] = Proxy.Preview(HTTP.Request(i["large"]).content)
                    except:
                        pass
        elif search_result["image_url"] not in metadata.posters:
                try:
                    metadata.posters[search_result["image_url"]] = Proxy.Preview(HTTP.Request(search_result["image_url"]).content)
                except:
                    pass

        if CAST_DATA == "Characters":
            characters_data = get_json(JIKAN_URL + JIKAN_ANIME_CHARACTERS.format(id=metadata.id))
            metadata.roles.clear()
            for i in characters_data["characters"]:
                role = metadata.roles.new()
                role.name = i["name"]
                role.role = i["role"]
                role.photo = i["image_url"]
        
        elif CAST_DATA == "Voice Actors":
            characters_data = get_json(JIKAN_URL + JIKAN_ANIME_CHARACTERS.format(id=metadata.id))
            metadata.roles.clear()
            for i in characters_data["characters"]:
                for actor in i["voice_actors"]:
                    if actor["language"] == "Japanese":
                        actor_image = get_html(url="https://myanimelist.net/people/" + str(actor["mal_id"]), par1="//td[@class='borderClass']/div/a/img//@src")
                        role = metadata.roles.new()
                        role.name = actor["name"]
                        role.role = i["name"]
                        role.photo = actor_image[0]
            
        episodes_data = get_json(JIKAN_URL + JIKAN_ANIME_EPISODES.format(id=metadata.id))
        for episode in episodes_data["episodes"]:
            episodeSeason1 = metadata.seasons[1].episodes[int(episode["episode_id"])]
            episodeSeason1.title = episode["title"]
            try:
                episodeSeason1.originally_available_at = Datetime.ParseDate(str(episode["aired"]["from"]).split("T")[0]).date()
            except:
                pass

        if len(media.seasons) > 1:
            if "Sequel" in search_result["related"]:
                media.seasons.pop("1")
                sequel_id = None
                for data in search_result["related"]["Sequel"]:
                    sequel_id = data["mal_id"]

                for s in sorted(media.seasons):
                    season = metadata.seasons[s]
                    search_data = get_json(JIKAN_URL + JIKAN_ANIME_DETAILS.format(id=sequel_id))
                    if EXTRA_POSTERS == "Small and Large":
                        posters_data = get_json(JIKAN_URL + JIKAN_ANIME_PICTURES.format(id=sequel_id))
                        for i in posters_data["pictures"]:
                            if i["small"] not in season.posters:
                                try:
                                    season.posters[i["small"]] = Proxy.Preview(HTTP.Request(i["small"]).content)
                                except:
                                    pass

                        for posterLarge in posters_data["pictures"]:
                            if posterLarge["large"] not in season.posters:
                                try:
                                    season.posters[posterLarge["large"]] = Proxy.Preview(HTTP.Request(posterLarge["large"]).content)
                                except:
                                    pass
                        
                    elif EXTRA_POSTERS == "Only Small":
                        posters_data = get_json(JIKAN_URL + JIKAN_ANIME_PICTURES.format(id=sequel_id))
                        for i in posters_data["pictures"]:
                            if i["small"] not in season.posters:
                                try:
                                    season.posters[i["small"]] = Proxy.Preview(HTTP.Request(i["small"]).content)
                                except:
                                    pass
                        
                    elif EXTRA_POSTERS == "Only Large":
                        posters_data = get_json(JIKAN_URL + JIKAN_ANIME_PICTURES.format(id=sequel_id))
                        for i in posters_data["pictures"]:
                            if i["large"] not in season.posters:
                                try:
                                    season.posters[i["large"]] = Proxy.Preview(HTTP.Request(i["large"]).content)
                                except:
                                    pass
                                
                    elif search_data["image_url"] not in season.posters:
                            season.posters[search_data["image_url"]] = Proxy.Preview(HTTP.Request(search_data["image_url"]).content)
                    
                    posters_data = get_json(JIKAN_URL + JIKAN_ANIME_EPISODES.format(id=sequel_id))
                    for i in posters_data["episodes"]:
                        season_episode = metadata.seasons[s].episodes[int(i["episode_id"])]
                        season_episode.title = i["title"]
                        try:
                            season_episode.originally_available_at = Datetime.ParseDate(str(i["aired"]["from"]).split("T")[0]).date()
                        except:
                            pass

                    if "Sequel" in search_data["related"]:
                        for data in search_data["related"]["Sequel"]:
                            sequel_id = data["mal_id"]


class JikanPlex(Agent.Movies):
    name = AGENT_NAME
    languages = LANGUAGES
    primary_provider = PRIMARY_PROVIDER
    accepts_from = ACCEPTS_FROM

    def search(self, results, media, lang):
        if str(media.year) == "None":
            search_data = get_json(JIKAN_URL + JIKAN_ANIME_SEARCH.format(title=String.Quote(media.name)) + "&type=Movie")
        else:
            search_data = get_json(JIKAN_URL + JIKAN_ANIME_SEARCH.format(title=String.Quote(media.name)) + "&type=Movie&start_date=" + str(media.year) + "-01-01")
        
        for index, data in enumerate(reversed(search_data["results"]), 1):
            results.Append(MetadataSearchResult(
                id=str(data["mal_id"]),
                name=data["title"],
                year=str(data["start_date"]).split("T")[0],
                score=index + 90,
                lang=lang
            ))

    def update(self, metadata, media, lang):
        search_data = get_json(JIKAN_URL + JIKAN_ANIME_DETAILS.format(id=metadata.id))

        metadata.title = search_data["title"]
        metadata.originally_available_at = Datetime.ParseDate(str(search_data["aired"]["from"]).split("T")[0]).date()
        metadata.rating = float(search_data["score"])
        metadata.content_rating = search_data["rating"]
        metadata.original_title = metadata.title

        if search_data["studios"]:
            for i in search_data["studios"]:
                metadata.studio = i["name"]

        metadata.summary = search_data["synopsis"]

        metadata.genres.clear()
        for i in search_data["genres"]:
            metadata.genres.add(i["name"])

        metadata.duration = int(str(search_data["duration"]).split(" ")[0])
        
        if EXTRA_POSTERS == "Small and Large":
            posters_data = get_json(JIKAN_URL + JIKAN_ANIME_PICTURES.format(id=metadata.id))
            for i in posters_data["pictures"]:
                if i["small"] not in metadata.posters:
                    try:
                        metadata.posters[i["small"]] = Proxy.Preview(HTTP.Request(i["small"]).content)
                    except:
                        pass
                        
            for i in posters_data["pictures"]:
                if i["large"] not in metadata.posters:
                    try:
                        metadata.posters[i["large"]] = Proxy.Preview(HTTP.Request(i["large"]).content)
                    except:
                        pass
                        
        elif EXTRA_POSTERS == "Only Small":
            posters_data = get_json(JIKAN_URL + JIKAN_ANIME_PICTURES.format(id=metadata.id))
            for i in posters_data["pictures"]:
                if i["small"] not in metadata.posters:
                    try:
                        metadata.posters[i["small"]] = Proxy.Preview(HTTP.Request(i["small"]).content)
                    except:
                        pass
                        
        elif EXTRA_POSTERS == "Only Large":
            posters_data = get_json(JIKAN_URL + JIKAN_ANIME_PICTURES.format(id=metadata.id))
            for i in posters_data["pictures"]:
                if i["large"] not in metadata.posters:
                    try:
                        metadata.posters[i["large"]] = Proxy.Preview(HTTP.Request(i["large"]).content)
                    except:
                        pass
                        
        elif search_data["image_url"] not in metadata.posters:
            try:
                metadata.posters[search_data["image_url"]] = Proxy.Preview(HTTP.Request(search_data["image_url"]).content)
            except:
                pass

        if CAST_DATA == "Characters":
            characters_data = get_json(JIKAN_URL + JIKAN_ANIME_CHARACTERS.format(id=metadata.id))
            metadata.roles.clear()
            for i in characters_data["characters"]:
                role = metadata.roles.new()
                role.name = i["name"]
                role.role = i["role"]
                role.photo = i["image_url"]
        
        elif CAST_DATA == "Voice Actors":
            characters_data = get_json(JIKAN_URL + JIKAN_ANIME_CHARACTERS.format(id=metadata.id))
            metadata.roles.clear()
            for i in characters_data["characters"]:
                for actor in i["voice_actors"]:
                    if actor["language"] == "Japanese":
                        actorImage = get_html(url="https://myanimelist.net/people/" + str(actor["mal_id"]), par1="//td[ @class='borderClass' ]/div/a/img//@src")
                        role = metadata.roles.new()
                        role.name = actor["name"]
                        role.role = i["role"]
                        role.photo = actorImage[0]


def get_json(url):
    sleep(SLEEP_TIME)
    
    result = None
    try:
        result = JSON.ObjectFromURL(url, sleep=2, headers={"Accept": "application/json"}, method="GET")
    except Exception as e:
        Log(AGENT_NAME + " Error fetching data from: " + url + " - Error: " + str(e))
    return result
    
def get_html(url, par1):
    sleep(SLEEP_TIME)
    
    result = None
    try:
        result = HTML.ElementFromURL(url).xpath(par1)
    except Exception as e:
        Log(AGENT_NAME + " Error fetching data from: " + url + " - Error: " + str(e))
    return result