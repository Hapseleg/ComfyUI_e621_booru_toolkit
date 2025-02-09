import re

import requests
from aiohttp import web
from server import PromptServer

headers = {"User-Agent": "ComfyUI_e621_booru_toolkit/1.0 (by draconicdragon on github)"}


# use separate function to fetch wiki data for python node code so no interference from route
# also allows for faster debug without restarting server using ComfyUI-HotReloadHack because not in frozen route
async def fetch_wiki_data(tags, booru, extended_info):
    # replace spaces with underscores, remove backslashes, strip leading/trailing underscores
    tags = tags.replace(" ", "_")
    tags = re.sub(r"(?<=\w)_+", "_", tags)  # remove extra underscores
    tags = tags.replace("\\", "")
    tags = ",".join(re.sub(r"^_+|_+$", "", tag) for tag in tags.split(","))

    first_tag = tags.split(",")[0]  # temp # todo: handle multiple tags
    print(first_tag)
    if booru == "e621, e6ai, e926":
        url = "https://e621.net/wiki_pages.json"
        params = {"title": first_tag}
    elif booru == "danbooru":
        url = "https://danbooru.donmai.us/wiki_pages.json"
        params = {"search[title]": first_tag, "limit": 1}
    else:
        return {"status": "success", "data": "Invalid booru selection"}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # raises HTTPError for 4xx or 5xx

        result = ""

        if booru == "e621, e6ai, e926":
            data = response.json()
            if data:
                wiki_page = data[0]  # extract first wiki page
                result = wiki_page.get("body", "No description found.")

        elif booru == "danbooru":
            data = response.json()
            if data:
                wiki_page = data[0]  # extract first wiki page
                result = wiki_page.get("body", "No description found.")

        if extended_info == "yes":
            return {"status": "success", "data": result}

        else:  # trim response to only important-ish parts
            match = re.search(r"h\d\.", result)
            if match:
                matches = result[: match.start()], result[match.start() :]
                if extended_info == "only_extended":
                    return {"status": "success", "data": matches[1]}
                else:
                    return {"status": "success", "data": matches[0]}

            else:
                return {"status": "success", "data": result}

    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Error occurred: {e} - Code: {response.status_code} - Response: {response.text}")


# add route for JS/client to server communication
@PromptServer.instance.routes.post("/booru/tag_wiki")
async def handle_tag_wiki(request):
    try:
        data = await request.json()
        tags = data.get("tag", "")
        booru = data.get("booru", "danbooru")
        extended_info = data.get("extended_info", "yes")
        node_id = data.get("node_id", "")

        result = await fetch_wiki_data(tags, booru, extended_info)
        result["node_id"] = node_id  # Add node_id to response, idk if really needed

        return web.json_response(result)

    except Exception as e:
        return web.json_response({"error": str(e), "status": "error"}, status=500)
