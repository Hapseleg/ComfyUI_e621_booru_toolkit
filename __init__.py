from .nodes.nodes import *

NODE_CLASS_MAPPINGS = {
    "GetBooruImageInfo": GetBooruImageInfo,
    "TagEncode": TagPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetBooruImageInfo": "Fetch Booru Tags + Image",
    "TagEncode": "Tag Encode",
}
