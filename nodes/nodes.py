import io

import numpy as np
import requests
import torch
from PIL import Image

# note: gelbooru api url https://gelbooru.com/index.php?page=dapi&s=post&q=index&id=1&json=1


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


def process_e621(response, scale_target, img_size, format_tags):
    post = response.get("post", {})
    # NOTE: e621 has contributor key in tags, unused
    # Get tags, e6 tags are in a list instead of space separated string like dbr
    tags = post.get("tags", {})
    general_tags = ", ".join(tags.get("general", []))
    artist_tags = ", ".join(tags.get("artist", []))
    copyright_tags = ", ".join(tags.get("copyright", []))
    character_tags = ", ".join(tags.get("character", []))

    if format_tags:
        general_tags = general_tags.replace("_", " ").replace("(", "\(").replace(")", "\)")
        artist_tags = artist_tags.replace("_", " ").replace("(", "\(").replace(")", "\)")
        copyright_tags = copyright_tags.replace("_", " ").replace("(", "\(").replace(")", "\)")
        character_tags = character_tags.replace("_", " ").replace("(", "\(").replace(")", "\)")

    if img_size == "none - don't download image":
        # Create a blank placeholder image
        scaled_img_width, scaled_img_height = calculate_dimensions_for_diffusion(64, 64, scale_target)
        img_tensor = torch.from_numpy(
            np.zeros((scaled_img_height, scaled_img_width, 3), dtype=np.float32) / 255.0
        ).unsqueeze(0)

    else:
        # use original dimensions for scaling
        img_width = post.get("file", {}).get("width", 0)
        img_height = post.get("file", {}).get("height", 0)

        # Select image size variant based on img_size, default to "file"'s url if not img_size
        image_url = post.get(img_size, {}).get("url", post.get("file", {}).get("url"))

        scaled_img_width, scaled_img_height = calculate_dimensions_for_diffusion(img_width, img_height, scale_target)

        img_data = requests.get(image_url).content

        img_stream = io.BytesIO(img_data)
        image_ = Image.open(img_stream)

        img_tensor = to_tensor(image_)

    return (
        img_tensor,
        general_tags,
        character_tags,
        copyright_tags,
        artist_tags,
        scaled_img_width,
        scaled_img_height,
    )


def process_danbooru(response, scale_target, img_size, format_tags):

    # Get tags
    general_tags = response.get("tag_string_general", "").replace(" ", ", ")
    character_tags = response.get("tag_string_character", "").replace(" ", ", ")
    copyright_tags = response.get("tag_string_copyright", "").replace(" ", ", ")
    artist_tags = response.get("tag_string_artist", "").replace(" ", ", ")

    if format_tags:
        general_tags = general_tags.replace("_", " ").replace("(", "\(").replace(")", "\)")
        character_tags = character_tags.replace("_", " ").replace("(", "\(").replace(")", "\)")
        copyright_tags = copyright_tags.replace("_", " ").replace("(", "\(").replace(")", "\)")
        artist_tags = artist_tags.replace("_", " ").replace("(", "\(").replace(")", "\)")

    if img_size == "none - don't download image":
        # Create a blank placeholder image
        scaled_img_width, scaled_img_height = calculate_dimensions_for_diffusion(64, 64, scale_target)
        img_tensor = torch.from_numpy(
            np.zeros((scaled_img_height, scaled_img_width, 3), dtype=np.float32) / 255.0
        ).unsqueeze(0)

    else:
        # Get image size variant for selected variant and output desired image size
        variants = response.get("media_asset", {}).get("variants", [])

        selected_variant = next((variant for variant in variants if variant["type"] == img_size), None)

        if selected_variant:
            image_url = selected_variant["url"]
            img_width = selected_variant["width"]
            img_height = selected_variant["height"]
        else:  # fallback
            image_url = response.get("file_url")
            img_width = response.get("image_width", 0)
            img_height = response.get("image_height", 0)

        scaled_img_width, scaled_img_height = calculate_dimensions_for_diffusion(img_width, img_height, scale_target)

        img_data = requests.get(image_url).content

        img_stream = io.BytesIO(img_data)
        image_ = Image.open(img_stream)

        img_tensor = to_tensor(image_)

    return (
        img_tensor,
        general_tags,
        character_tags,
        copyright_tags,
        artist_tags,
        scaled_img_width,
        scaled_img_height,
    )


class GetBooruPost:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {"multiline": False, "tooltip": "Enter the URL of the Danbooru post"}),
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
                        "default": "none - don't download image",
                        "tooltip": "Select the image size variant to output through 'IMAGE'. Choose 'none' to output a blank image",
                    },
                ),
                "format_tags": (
                    "BOOLEAN",
                    {"default": True, "tooltip": "Removes underscores and adds backslashes to brackets if set to True"},
                ),
                # "clean_tags": (
                #     "BOOLEAN",
                #     {"default": False, "tooltip": "Removes tags before output based on blacklisted_tags.json located in the custom nodes folder for this node"},
                # ),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = (
        "IMAGE",
        "GENERAL_TAGS",
        "CHARACTER_TAGS",
        "COPYRIGHT_TAGS",
        "ARTIST_TAGS",
        "SCALED_WIDTH",
        "SCALED_HEIGHT",
    )
    FUNCTION = "get_data"
    CATEGORY = "Danbooru"

    def get_data(self, url, scale_target, img_size, format_tags):
        # Check if URL already ends with .json
        if ".json" not in url:
            # Split URL into base and query parts if it contains a query
            if "?" in url:
                base_url, sep, query = url.partition("?")  # sep = "?"
            else:
                base_url = url
                sep = ""
                query = ""

            # Add .json to the base URL for JSON API
            json_url = base_url + ".json"

            # Remake full URL with query part, if any
            if query:
                json_url = json_url + sep + query
        else:
            json_url = url

        # todo: check if e6 api format or dbr, or other
        if "e621" in json_url or "e926" in json_url:
            api_key = " "
            user_agent = "ComfyUI_e621_booru_toolkit/1.0 (by draconicdragon on e621)"

            # Headers including Authorization and User-Agent
            headers = {
                # "Authorization": "Basic " + api_key,
                "User-Agent": user_agent
            }

            response = requests.get(json_url, headers=headers).json()
            print(response.json())

            return process_e621(response, scale_target, img_size, format_tags)
        else:
            response = requests.get(json_url).json()
            return process_danbooru(response, scale_target, img_size, format_tags)


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
