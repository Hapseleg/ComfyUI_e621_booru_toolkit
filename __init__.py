from .nodes.nodes import *
from .pyserver import get_tag_wiki_data

NODE_CLASS_MAPPINGS = {
    "GetBooruPost": GetBooruPost,
    "TagWikiFetch": TagWikiFetch,
    "TagEncode": TagPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetBooruPost": "Fetch e621/Booru Post",
    "TagWikiFetch": "Tag Wiki Lookup (Beta)",  # todo: i really need better names for these
    "TagEncode": "Tag Encode (old)",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
