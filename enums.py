import enum

class BooruSite(enum.Enum):
    DANBOORU = "Danbooru"
    E621 = "e621"
    E926 = "e926"
    E6AI = "e6ai"
    GELBOORU = "Gelbooru"
    RULE34 = "Rule34"
    
class BooruSiteURLs(enum.Enum):
    DANBOORU = "https://danbooru.donmai.us"
    E621 = "https://e621.net"
    E926 = "https://e926.net"
    E6AI = "https://e6ai.net"
    GELBOORU = "https://gelbooru.com/index.php"
    RULE34 = "https://api.rule34.xxx"
    
class ContentRatings(enum.Enum):
    ANY = "Any rating"
    GENERAL = "General"
    SENSITIVE = "Sensitive"
    QUESTIONABLE = "Questionable"
    EXPLICIT = "Explicit"
    SAFE = "Safe"
    SFW = "SFW"
    NSFW = "NSFW"
    