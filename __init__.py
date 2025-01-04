from .nodes.nodes import *

NODE_CLASS_MAPPINGS = {
    "GetBooruPost": GetBooruPost,
    "TagEncode": TagPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetBooruPost": "Fetch e621/Booru Post",
    "TagEncode": "Tag Encode",
}
