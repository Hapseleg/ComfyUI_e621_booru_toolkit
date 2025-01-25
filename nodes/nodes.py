import io
import re
from typing import Any, Dict, List, Tuple

import numpy as np
import requests
import torch
from PIL import Image

headers = {"User-Agent": "ComfyUI_e621_booru_toolkit/1.0 (by draconicdragon on github)"}

# create a blank image tensor to use as a placeholder
blank_img_tensor = torch.from_numpy(np.zeros((512, 512, 3), dtype=np.float32) / 255.0).unsqueeze(0)


def to_tensor(image: Image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


def calculate_dimensions_for_diffusion(img_width, img_height, zoom):
    # Ensure dimensions are divisible by 64
    def make_divisible_by_64(x):
        return (x // 64) * 64

    img_max_length = min(img_width, img_height)
    img_zoom = zoom / img_max_length

    img_width = int(img_width * img_zoom)
    img_height = int(img_height * img_zoom)

    img_width = make_divisible_by_64(img_width)
    img_height = make_divisible_by_64(img_height)

    return img_width, img_height


def get_e621_post_data(response, img_size):
    post = response.get("post", {})
    # NOTE: e621 has contributor key in tags since 18th dec., not useful for image gen
    # Get tags, e6 tags are in a list instead of space separated string like dbr
    tags = post.get("tags", {})
    tags_dict = {
        "general_tags": ", ".join(tags.get("general", [])),
        "character_tags": ", ".join(tags.get("artist", [])),
        "copyright_tags": ", ".join(tags.get("copyright", [])),
        "artist_tags": ", ".join(tags.get("character", [])),
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

    # Get tags
    tags_dict = {
        "general_tags": response.get("tag_string_general", "").replace(" ", ", "),
        "character_tags": response.get("tag_string_character", "").replace(" ", ", "),
        "copyright_tags": response.get("tag_string_copyright", "").replace(" ", ", "),
        "artist_tags": response.get("tag_string_artist", "").replace(" ", ", "),
        "species_tags": "",  # danbooru doesn't have this
    }

    # Get image size and dimensions of original image
    img_width = response.get("image_width", 0)
    img_height = response.get("image_height", 0)

    if img_size == "none - don't download image":
        img_tensor = blank_img_tensor

    else:
        # Get image size variant for selected variant and output desired image size
        variants = response.get("media_asset", {}).get("variants", [])
        selected_variant = next((variant for variant in variants if variant["type"] == img_size), None)

        if selected_variant:
            image_url = selected_variant["url"]
            img_width = selected_variant["width"]
            img_height = selected_variant["height"]
        else:  # fallback to original image
            image_url = response.get("file_url")

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


class GetBooruPost:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {"multiline": False, "tooltip": "Enter the URL of the Danbooru/e621 post"}),
                "scale_target": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 16384,
                        "step": 8,
                        "tooltip": "[BETA] Calculates the image's width/height to be close to the scale target and be divisible by 64, keeping the aspect ratio. Use 1024 for SDXL",
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

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = (
        "IMAGE",
        "GENERAL_TAGS",
        "CHARACTER_TAGS",
        "COPYRIGHT_TAGS",
        "ARTIST_TAGS",
        "E6_SPECIES_TAGS",
        "SCALED_WIDTH",
        "SCALED_HEIGHT",
    )
    FUNCTION = "get_data"
    CATEGORY = "E621 Booru Toolkit"

    def get_data(self, url, scale_target, img_size, format_tags, exclude_tags, user_excluded_tags):
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

        # todo: check if e6 api format or dbr, or other, needs to get api response first
        if any(keyword in json_url for keyword in ["e621", "e926", "e6ai"]):
            response = requests.get(json_url, headers=headers).json()
            img_tensor, tags_dict, img_width, img_height = get_e621_post_data(response, img_size)

        else:  # danbooru used / used as fallback
            response = requests.get(json_url, headers=headers).json()
            img_tensor, tags_dict, img_width, img_height = get_danbooru_post_data(response, img_size)

        # scale image to diffusion-compatible size
        # todo: rework calculation, does not use scale_target as medium but likely as lowest for either width or height
        scaled_img_width, scaled_img_height = calculate_dimensions_for_diffusion(img_width, img_height, scale_target)

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
        )


class TagWikiFetch:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tag": ("STRING",),
                "booru": (["danbooru", "e621, e6ai, e926"], {"default": "danbooru"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_wiki_data"
    OUTPUT_NODE = True

    CATEGORY = "E621 Booru Toolkit"

    def get_wiki_data(self, tag, booru):
        # Escape brackets and replace spaces with underscores after stripping whitespace
        tag = re.sub(r"(?<!\\)([()])", r"\\\1", tag.strip().replace(" ", "_"))

        if booru == "e621, e6ai, e926":
            url = "https://e621.net/wiki_pages.json"
            params = {"title": tag}
        elif booru == "danbooru":
            url = "https://danbooru.donmai.us/wiki_pages.json"
            params = {"search[title]": tag, "limit": 1}
        else:
            return {
                "ui": {"text": "If this appears then poopy uh yeah idk what wrong"},
                "result": "If this appears then poopy uh yeah idk what wrong",
            }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raises HTTPError for 4xx or 5xx
            # data = response.json()
            # print(response.text)
            # return {
            #     "ui": {"text": f"Nothing found? Code:{response.status_code} Response:{response.text}"},
            #     "result": f"Nothing found? Code:{response.status_code} Response:{response.text}",
            # }
            if booru == "e621, e6ai, e926":
                data = response.json()
                if data:
                    wiki_page = data[0]  # Extract the first wiki page
                    result = wiki_page.get("body", "No description found.")
                    return {"ui": {"text": result}, "result": (result,)}
                else:
                    return {
                        "ui": {"text": f"Nothing found? Code:{response.status_code} Response:{response.text}"},
                        "result": f"Nothing found? Code:{response.status_code} Response:{response.text}",
                    }

            # Handle Danbooru API response (response is a list of dictionaries)
            elif booru == "danbooru":
                data = response.json()
                if data:
                    wiki_page = data[0]  # Extract the first wiki page
                    result = wiki_page.get("body", "No description found.")
                    return {"ui": {"text": result}, "result": (result,)}

        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Error occurred: {e} - Code: {response.status_code} - Response: {response.text}")


# whatever this does idk but im leaving this here
class TagPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tags": ("STRING", {"forceInput": True}),
                "basic": ("STRING", {"multiline": True}),
                "remove": ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "to_prompt"

    CATEGORY = "Danbooru"

    def remove(self, tags: str, remove: str):
        tags = [t.strip() for t in tags.split(",")]
        remove = [r.strip() for r in remove.split(",")]

        remove_tags = []
        for t_ in tags:
            for r_ in remove:
                if r_ in t_:
                    remove_tags.append(t_)
                    break

        tag_set = set(tags) - set(remove_tags)
        tag_str = ", ".join(tag_set)
        return tag_str

    def to_prompt(self, tags, basic, remove):
        remove_tags = self.remove(tags, remove)
        prompt_str = f"{basic}, {remove_tags}"

        return (prompt_str,)
