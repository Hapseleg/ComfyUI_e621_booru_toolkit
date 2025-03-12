from .nodes.nodes import *
from .pyserver import get_tag_wiki_data

NODE_CLASS_MAPPINGS = {
    "GetBooruPost": GetBooruPost,
    "TagWikiFetch": TagWikiFetch,
    "GetRandomBooruPost": GetRandomBooruPost,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetBooruPost": "Fetch e621/Booru Post",
    "TagWikiFetch": "Tag Wiki Lookup",  # todo: i really need better names for these
    "GetRandomBooruPost": "Fetch random e621/Booru Post"
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
