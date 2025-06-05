import io
from ..enums import *
import numpy as np
import requests
import torch
import json
from PIL import Image

# booru sites https://sinkaroid.github.io/booru/client/index.html
# class BooruSite(enum.Enum):
#     DANBOORU = "Danbooru"
#     E621 = "e621"
#     E926 = "e926"
#     E6AI = "e6ai"
#     GELBOORU = "Gelbooru"
#     RULE34 = "Rule34"
    
# class BooruSiteURLs(enum.Enum):
#     DANBOORU = "https://danbooru.donmai.us/"
#     E621 = "https://e621.net/"
#     E926 = "https://e926.net/"
#     E6AI = "https://e6ai.net/"
#     GELBOORU = "https://gelbooru.com/index.php/"
#     RULE34 = "https://api.rule34.xxx/"
    
# class ContentRatings(enum.Enum):
#     SAFE = "Safe"
#     QUESTIONABLE = "Questionable"
#     EXPLICIT = "Explicit"

# https://danbooru.donmai.us/posts/random.json?tags=
# https://danbooru.donmai.us/posts/100.json

# https://e6ai.net/posts.json?limit=1&tags=%20order%3Arandom
# https://e621.net/posts/100.json

# https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&tags=sort%3arandom
# https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&id=100

# https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&limit=1&tags=sort%3arandom
# https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&id=100

headers = {"User-Agent": "ComfyUI_e621_booru_toolkit/1.0 (by draconicdragon on github(Hapse fork))"}

# create a blank image tensor to use as a placeholder
blank_img_tensor = torch.from_numpy(np.zeros((512, 512, 3), dtype=np.float32) / 255.0).unsqueeze(0)

#https://danbooru.donmai.us/wiki_pages/help:api
#https://danbooru.donmai.us/wiki_pages/help%3Ausers
#Feature	            No Account	 Member	  Gold	 Platinum	 Builder
#Max tags per search	2	         2	      6	     No Limit	 No Limit
def get_API_key(site, save_file=False, api_login="", api_key=""):
    try:
        with open("./api-secrets.json",'r') as f:
            api_json = json.load(f)
        if save_file:
            api_json[site] = {"API_LOGIN": api_login, "API_KEY": api_key}
            
            # Save the updated JSON back to the file
            with open("./api-secrets.json",'w') as f:
                json.dump(api_json, f, indent=4) # Use indent for readability

        if site in api_json: # Check for the specific site key
            return api_json[site]["API_LOGIN"], api_json[site]["API_KEY"]
        else:
            return "", ""
    except:
        return "", ""

def to_tensor(image: Image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


def calculate_dimensions_for_diffusion(img_width, img_height, scale_target_avg, multiples_of=64):
    # Calculate the average of the original dimensions.
    # This average will be scaled to be near the scale_target_avg.
    original_avg = (img_width + img_height) / 2.0

    # Determine the scaling factor to get the average near the target.
    scale_factor = scale_target_avg / original_avg

    # Scale the dimensions while preserving the aspect ratio.
    new_width = round(img_width * scale_factor)  # rounding because output can be 1023.9999999999
    new_height = round(img_height * scale_factor)

    # Adjust the scaled dimensions to be multiples of
    new_width = (new_width // multiples_of) * multiples_of
    new_height = (new_height // multiples_of) * multiples_of

    return (
        int(new_width),
        int(new_height),
    )

#https://danbooru.donmai.us/posts/random.json?tags=1girl
def get_e621_post_data(post, img_size):
    print(post.get("id", ""))
    # post = response.get("post", {})
    # post = response
    # print(post)
    # NOTE: e621 has contributor key in tags since 18th dec., not useful for image gen
    # Get tags, e6 tags are in a list instead of space separated string like dbr
    tags = post.get("tags", {})
    tags_dict = {
        "general_tags": ", ".join(tags.get("general", [])),
        "character_tags": ", ".join(tags.get("character", [])),
        "copyright_tags": ", ".join(tags.get("copyright", [])),
        "artist_tags": ", ".join(tags.get("artist", [])),
        "species_tags": ", ".join(tags.get("species", [])),
    }

    # Get image size of original image | "file" key in json response
    img_width = post.get("file", {}).get("width", 0)
    img_height = post.get("file", {}).get("height", 0)

    if img_size == "none - don't download image":
        img_tensor = blank_img_tensor
    else:
        if img_size not in ["original", "sample"]:
            img_size = "preview"
        if img_size == "original":
            img_size = "file"

        image_url = post.get(img_size, {}).get("url")

        if not image_url:  # fallback
            image_url = post.get("file", {}).get("url")

        if image_url != None:
            img_data = requests.get(image_url).content
            img_stream = io.BytesIO(img_data)
            image_ = Image.open(img_stream)
            img_tensor = to_tensor(image_)
        else:
            img_tensor = blank_img_tensor

    return (
        img_tensor,
        tags_dict,
        img_width,
        img_height,
    )

def get_rule34_post_data(post, img_size):
    print(post["id"])
    # post = response.get(""])
    img_tensor = blank_img_tensor
    tags_dict = {
        "general_tags": post["tags"].replace(" ", ", "),
        "character_tags": "",
        "copyright_tags": "",
        "artist_tags": "",
        "species_tags": "",
    }
    # Get image size of original image | "file" key in json response
    img_width = post["width"]
    img_height = post["height"]

    if img_size == "none - don't download image":
        img_tensor = blank_img_tensor
    else:
        image_url = post["sample_url"]
        if img_size == "original" or post["sample_url"] == "":
            image_url = post["file_url"]

        if image_url != None:
            img_data = requests.get(image_url).content
            img_stream = io.BytesIO(img_data)
            image_ = Image.open(img_stream)
            img_tensor = to_tensor(image_)
            
    return (
        img_tensor,
        tags_dict,
        img_width,
        img_height,
    )
    

def get_danbooru_post_data(response, img_size):
    # print(response)
    # Get tags
    print(response.get("id", ""))
    tags_dict = {
        "general_tags": response.get("tag_string_general", "").replace(" ", ", "),
        "character_tags": response.get("tag_string_character", "").replace(" ", ", "),
        "copyright_tags": response.get("tag_string_copyright", "").replace(" ", ", "),
        "artist_tags": response.get("tag_string_artist", "").replace(" ", ", "),
        "species_tags": "",  # danbooru doesn't have this
    }

    # Get image size and dimensions of original image
    original_img_width = response.get("image_width", 0)
    original_img_height = response.get("image_height", 0)

    if img_size == "none - don't download image":
        img_tensor = blank_img_tensor

    else:
        # Get image size variant for selected variant and output desired image size
        variants = response.get("media_asset", {}).get("variants", [])
        selected_variant = next((variant for variant in variants if variant["type"] == img_size), None)

        # print(selected_variant)
        if selected_variant:
            image_url = selected_variant["url"]
        else:  # fallback to original image
            image_url = response.get("file_url")
        # print(image_url)

        img_data = requests.get(image_url).content
        img_stream = io.BytesIO(img_data)
        image_ = Image.open(img_stream)
        img_tensor = to_tensor(image_)

    return (
        img_tensor,
        tags_dict,
        original_img_width,
        original_img_height,
    )


class GetBooruPost:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {"multiline": False, "tooltip": "Enter the URL of the Danbooru/e621 post"}),
                "scale_target_avg": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 16384,
                        "step": 64,  # add multiples_of option and then allow different step sizes although usually not needed
                        "tooltip": "[BETA] Calculates the image's width and height so it's average is close to the scale_target_avg value while keeping the aspect ratio as close to original as possible. Use 1024 for SDXL",
                    },
                ),
                "img_size": (
                    [
                        "none - don't download image",
                        "180x180",
                        "360x360",
                        "720x720",
                        "sample",
                        "original",
                    ],
                    {
                        "default": "sample",
                        "tooltip": "Select the image size variant to output through 'IMAGE'. Choose 'none' to output a blank image. For e6, anything below sample will be 'preview'",
                    },
                ),
                "format_tags": (
                    "BOOLEAN",
                    {"default": True, "tooltip": "Removes underscores and adds backslashes to brackets if set to True"},
                ),
                "exclude_tags": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Removes tags before output based on textbox content below",
                    },
                ),
                "user_excluded_tags": (
                    "STRING",
                    {  # todo: load defaults from file maybe
                        "default": "conditional dnp, sound_warning, unknown_artist, third-party_edit, anonymous_artist, e621, e621 post recursion, e621_comment, patreon, patreon logo, patreon username, instagram username, text, dialogue",
                        "multiline": True,
                        "tooltip": "Enter tags you don't want outputted. Input should be comma separated like prompts (they can include underscore or spaces, with or without backslashes)",
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "STRING", "INT", "INT", "INT", "INT",)
    RETURN_NAMES = (
        "IMAGE",
        "GENERAL_TAGS",
        "CHARACTER_TAGS",
        "COPYRIGHT_TAGS",
        "ARTIST_TAGS",
        "E6_SPECIES_TAGS",
        "SCALED_WIDTH",
        "SCALED_HEIGHT",
        "ORIGINAL_WIDTH",
        "ORIGINAL_HEIGHT",
    )
    FUNCTION = "get_data"
    CATEGORY = "E621 Booru Toolkit"

    def get_data(self, url, scale_target_avg, img_size, format_tags, exclude_tags, user_excluded_tags):
        # Check if URL already ends with .json
        # todo: doesnt work for gelbooru, safebooru, similar
        # NOTE: these sites are cringe, the tags are in a singular string. Char/artist/general tags, all merged. WHY?
        # gelbooru api url https://gelbooru.com/index.php?page=dapi&s=post&q=index&id=1&json=1
        if ".json" not in url:
            # Split URL into base and query parts if it contains a query
            if "?" in url:
                base_url, sep, query = url.partition("?")  # sep = "?"
            else:
                base_url = url
                sep = ""
                query = ""

            json_url = base_url + ".json"

            # Remake full URL with query part, if any, maybe not needed
            if query:
                json_url = json_url + sep + query
        else:
            json_url = url


        match json_url:
            case "e621" | "e926" | "e6ai":
                response = requests.get(json_url, headers=headers).json()
                post = response.get("post", {})
                img_tensor, tags_dict, og_img_width, og_img_height = get_e621_post_data(post, img_size)
            case _:
                response = requests.get(json_url, headers=headers).json()
                img_tensor, tags_dict, og_img_width, og_img_height = get_danbooru_post_data(response, img_size)
                

        # todo: check if e6 api format or dbr, or other, needs to get api response first
        # if any(keyword in json_url for keyword in ["e621", "e926", "e6ai"]):
        #     response = requests.get(json_url, headers=headers).json()
        #     post = response.get("post", {})
        #     img_tensor, tags_dict, og_img_width, og_img_height = get_e621_post_data(post, img_size)

        # # elif: # for other sites

        # else:  # danbooru used / used as fallback for now
        #     response = requests.get(json_url, headers=headers).json()
        #     img_tensor, tags_dict, og_img_width, og_img_height = get_danbooru_post_data(response, img_size)

        # print(f"E621 Booru Toolkit DEBUG - Possibly unsupported site? Using danbooru as fallback. URL: {json_url}")

        # scale image to diffusion-compatible size
        scaled_img_width, scaled_img_height = calculate_dimensions_for_diffusion(
            og_img_width, og_img_height, scale_target_avg
        )

        if exclude_tags:
            # convert user_excluded_tags to a list and format it properly to match tags_dict
            user_excluded_tags = user_excluded_tags.replace(", ", ",").split(",")
            exclude_tags_list = [
                tag.replace(" ", "_").replace("\\(", "(").replace("\\)", ")") for tag in user_excluded_tags
            ]

            # remove tags in tags_dict that match the exclude_tags_list
            for key in tags_dict:
                tags_dict[key] = ", ".join([tag for tag in tags_dict[key].split(", ") if tag not in exclude_tags_list])

        if format_tags:  # should run last
            for key in tags_dict:
                tags_dict[key] = tags_dict[key].replace("_", " ").replace("(", "\\(").replace(")", "\\)")

        return (
            img_tensor,
            tags_dict["general_tags"],
            tags_dict["character_tags"],
            tags_dict["copyright_tags"],
            tags_dict["artist_tags"],
            tags_dict["species_tags"],
            scaled_img_width,
            scaled_img_height,
            og_img_width,
            og_img_height,
        )


class GetRandomBooruPost:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "site": (
                    [site.value for site in BooruSite],
                    {
                        "default": BooruSite.DANBOORU.value,
                        "tooltip": "The booru site it should get a random post from"
                    },
                ),
                "scale_target_avg": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 16384,
                        "step": 64,  # add multiples_of option and then allow different step sizes although usually not needed
                        "tooltip": "[BETA] Calculates the image's width and height so it's average is close to the scale_target_avg value while keeping the aspect ratio as close to original as possible. Use 1024 for SDXL",
                    },
                ),
                "img_size": (
                    [
                        "none - don't download image",
                        "180x180",
                        "360x360",
                        "720x720",
                        "sample",
                        "original",
                    ],
                    {
                        "default": "sample",
                        "tooltip": "Select the image size variant to output through 'IMAGE'. Choose 'none' to output a blank image. For e6, anything below sample will be 'preview'",
                    },
                ),
                "include_tags": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Removes tags before output based on textbox content below",
                    },
                ),
                "user_included_tags": (
                    "STRING",
                    {  # todo: load defaults from file maybe
                        "default": "",
                        "multiline": True,
                        "tooltip": "Enter tags you don't want outputted. Input should be comma separated like prompts (they can include underscore or spaces, with or without backslashes)",
                    },
                ),
                "exclude_tags": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Excludes the tags from the search",
                    },
                ),
                "user_excluded_tags": (
                    "STRING",
                    {  # todo: load defaults from file maybe
                        "default": "conditional dnp, sound_warning, unknown_artist, third-party_edit, anonymous_artist, e621, e621 post recursion, e621_comment, patreon, patreon logo, patreon username, instagram username, text, dialogue",
                        "multiline": True,
                        "tooltip": "Enter tags want to exclude from the search query. Input should be comma separated like prompts (they can include underscore or spaces, with or without backslashes)",
                    },
                ),
                "seed":( "INT",{"default": 0 }),
            },
            "hidden": {"unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO", "prompt": "PROMPT"},
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "STRING", "INT", "INT", "INT", "INT", "STRING",)
    RETURN_NAMES = (
        "IMAGE",
        "GENERAL_TAGS",
        "CHARACTER_TAGS",
        "COPYRIGHT_TAGS",
        "ARTIST_TAGS",
        "E6_SPECIES_TAGS",
        "SCALED_WIDTH",
        "SCALED_HEIGHT",
        "ORIGINAL_WIDTH",
        "ORIGINAL_HEIGHT",
        "URL"
    )
    FUNCTION = "get_random_data"
    CATEGORY = "E621 Booru Toolkit"

    def get_random_data(self, site, scale_target_avg, img_size, include_tags, user_included_tags, exclude_tags, user_excluded_tags, **kwargs):
        # todo: doesnt work for gelbooru, safebooru, similar
        # NOTE: these sites are cringe, the tags are in a singular string. Char/artist/general tags, all merged. WHY?
        
        # https://danbooru.donmai.us/posts/random.json?tags=
        # https://e6ai.net/posts.json?limit=1&tags=%20order%3Arandom
        # https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&tags=sort%3arandom
        # https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&limit=1&tags=sort%3arandom
        match site:
            case BooruSite.DANBOORU.value:
                base_url = f"{BooruSiteURLs.DANBOORU.value}posts/random.json?"
                #check for api key in json
                API_LOGIN, API_KEY = get_API_key(BooruSite.DANBOORU)
                if API_LOGIN != "":
                    base_url += "login=" + API_LOGIN + "&"
                    base_url += "api_key=" + API_KEY + "&"
                base_url += "tags="
            case BooruSite.E621.value:
                base_url = f"{BooruSiteURLs.E621.value}posts.json?limit=1&tags=%20order%3Arandom"
            case BooruSite.E926.value:
                base_url = f"{BooruSiteURLs.E926.value}posts.json?limit=1&tags=%20order%3Arandom"
            case BooruSite.E6AI.value:
                base_url = f"{BooruSiteURLs.E6AI.value}posts.json?limit=1&tags=%20order%3Arandom"
            case BooruSite.GELBOORU.value:
                base_url = f"{BooruSiteURLs.GELBOORU.value}index.php?page=dapi&s=post&q=index&json=1&limit=1&tags=sort%3arandom"
            case BooruSite.RULE34.value:
                base_url = f"{BooruSiteURLs.RULE34.value}index.php?page=dapi&s=post&q=index&json=1&limit=1&tags=sort%3arandom"
            case _:
                print("Unsupported site")
                raise Exception("Unsupported site")
        
        #animated stuff will break it all
        tag_str = "-animated+"
        tag_str = ""
            
        if include_tags:
            user_included_tags = user_included_tags.replace(", ", ",").split(",")
            for tag in user_included_tags:
                tag_str += tag.replace(" ", "_").replace("\\(", "(").replace("\\)", ")") + '+'
            
            
        if exclude_tags:
            user_excluded_tags = user_excluded_tags.replace(", ", ",").split(",")
            for tag in user_excluded_tags:
                tag_str += '-' + tag.replace(" ", "_").replace("\\(", "(").replace("\\)", ")") + '+'

        #remove the extra + at the end
        if len(tag_str) > 0:
            tag_str = tag_str[:-1]

        full_url = base_url + tag_str
        print(full_url)
        response = requests.get(full_url, headers=headers)
        try:
            response = response.json()
        except:
            raise Exception("No posts found")
        
        # Check for success
        if site != BooruSite.RULE34.value and response.get("success", "") == False:
            raise Exception(response.get("message", ""))
        
        match site:
            case BooruSite.DANBOORU.value:
                img_tensor, tags_dict, og_img_width, og_img_height = get_danbooru_post_data(response, img_size)
                
            case BooruSite.E621.value | BooruSite.E926.value | BooruSite.E6AI.value:
                post = response.get("posts", [])
                img_tensor, tags_dict, og_img_width, og_img_height = get_e621_post_data(post[0] if post else {}, img_size)
                
            case BooruSite.GELBOORU.value:
                post = response.get("post", [])
                img_tensor, tags_dict, og_img_width, og_img_height = get_rule34_post_data(post[0] if post else {}, img_size)
                
            case BooruSite.RULE34.value:
                # post = response[0]
                img_tensor, tags_dict, og_img_width, og_img_height = get_rule34_post_data(response[0] if response else {}, img_size)
                
            case _:
                print("Unsupported site")
                raise Exception("Unsupported site")
        

        # scale image to diffusion-compatible size
        scaled_img_width, scaled_img_height = calculate_dimensions_for_diffusion(
            og_img_width, og_img_height, scale_target_avg
        )

        
        return (
            img_tensor,
            tags_dict["general_tags"],
            tags_dict["character_tags"],
            tags_dict["copyright_tags"],
            tags_dict["artist_tags"],
            tags_dict["species_tags"],
            scaled_img_width,
            scaled_img_height,
            og_img_width,
            og_img_height,
            full_url,
        )


class TagWikiFetch:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tags": (
                    "STRING",
                    {
                        "multiline": False,
                        "tooltip": "Enter the tags to search for, separated by commas."
                        + "Input tags are normalized meaning you don't need to pay attention to using underscores or backslashes or having to worry about too many spaces."
                        + "(Important: currently only supports a single tag. If multiple are supplied then one before first comma is chosen.)",
                    },
                ),
                "booru": (
                    ["danbooru", "e621, e6ai, e926"],
                    {"default": "danbooru", "tooltip": "Select the booru to search for the tag wiki page."},
                ),
                "extended_info": (
                    ["yes", "no", "only_extended"],
                    {
                        "default": "no",
                        "tooltip": "Include extended info of the wiki page response, mostly useless for now.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_wiki_data"
    OUTPUT_NODE = True

    CATEGORY = "E621 Booru Toolkit"

    def get_wiki_data(self, tags, booru, extended_info):

        import asyncio

        from ..pyserver import get_tag_wiki_data

        response = asyncio.run(get_tag_wiki_data.fetch_wiki_data(tags, booru, extended_info))

        data = response.get("data", "")
        return {"ui": {"text": data}, "result": (data,)}
