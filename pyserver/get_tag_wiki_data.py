import re

import requests
from aiohttp import web
from server import PromptServer

headers = {"User-Agent": "ComfyUI_e621_booru_toolkit/1.0 (by draconicdragon on github)"}


@PromptServer.instance.routes.post("/booru/tag_wiki")
async def handle_tag_wiki(request, booru="danbooru", extended_info="no"):
    try:
        data = await request.json()
        tags = data.get("tag", "")
        node_id = data.get("node_id", "")

        processed_data = f"got tags: {tags}"

        # replace spaces with underscores, remove backslashes, strip leading/trailing underscores
        tags = tags.replace(" ", "_")
        tags = re.sub(r"(?<=\w)_+", "_", tags)  # remove too much extra underscores
        tags = tags.replace("\\", "")
        tags = ",".join(re.sub(r"^_+|_+$", "", tag) for tag in tags.split(","))

        first_tag = tags.split(",")[0]  # temp

        if booru == "e621, e6ai, e926":
            url = "https://e621.net/wiki_pages.json"  # i kinda doubt e6ai or 926 have different wiki
            params = {"title": first_tag}
        elif booru == "danbooru":
            url = "https://danbooru.donmai.us/wiki_pages.json"
            params = {"search[title]": first_tag, "limit": 1}
        else:
            return web.json_response(
                {"status": "success", "data": "If this appears then poopy uh yeah idk what wrong", "node_id": node_id}
            )

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raises HTTPError for 4xx or 5xx

            result = ""

            if booru == "e621, e6ai, e926":
                data = response.json()
                if data:
                    wiki_page = data[0]  # Extract the first wiki page
                    result = wiki_page.get("body", "No description found.")

            # Handle Danbooru API response (response is a list of dictionaries)
            elif booru == "danbooru":
                data = response.json()
                if data:
                    wiki_page = data[0]  # Extract the first wiki page
                    result = wiki_page.get("body", "No description found.")

            if extended_info == "yes":
                return {"ui": {"text": result}, "result": (result,)}

            else:  # trim response to only important-ish parts, prone to error if no match possibly, expect exception to be raised
                match = re.search(r"h\d\.", result)
                if match:
                    matches = result[: match.start()], result[match.start() :]
                    if extended_info == "only_extended":
                        return web.json_response({"status": "success", "data": matches[1], "node_id": node_id})
                    else:
                        return web.json_response({"status": "success", "data": matches[0], "node_id": node_id})

                else:
                    # line prone to error?
                    return web.json_response({"status": "success", "data": result, "node_id": node_id})

            # return {
            #     "ui": {"text": f"Nothing found? Code:{response.status_code} Response:{response.text}"},
            #     "result": f"Nothing found? Code:{response.status_code} Response:{response.text}",
            # }

        except requests.exceptions.HTTPError as e:
            # unneeded try except?
            raise RuntimeError(f"Error occurred: {e} - Code: {response.status_code} - Response: {response.text}")

    except Exception as e:
        return web.json_response({"error": str(e), "status": "error"}, status=500)  #
