# ComfyUI e621 booru Toolkit


Nodes:
Fetch e621/Booru Post node:
![Main fetch node showcase](./assets_gh/main_fetch_node_showcase.png)
`url`: insert any post url from e621 or danbooru (see Supported sites at the bottom)
`scale_target_avg`: determines what average to scale the image dimensions to. SCALED_WIDTH and SCALED_HEIGHT will then output diffusion-compatible values by keeping the numbers multiples of 64. (e.g.: Use ~1024 for SDXL)
`img_size`: set the size variant of the output image (sizes are in danbooru format, if you select a size unsupported by e621 it will use `preview` as fallback)
`format_tags`: if set to `true` the output will format the tags to remove any underscores and adds backslashes infront of parenthesis
`exclude_tags`: excludes tags based on bottom textbox

Tag Wiki Lookup node:
![Tag Wiki Lookup node showcase](./assets_gh/tag_wiki_node_showcase.png)

old-ish image:
![workflow image](./example_workflows/workflow_old.png)
`tags`: input any tag you want to get the wiki description of
`booru`: select what image board site you want to get the info from
`extended_info`: more of an experimental setting but for danbooru at least it gets rid of related tags and such that is below that
`Fetch Wiki Button`: You don't have to queue to get the wiki description. Since nothing is queued, it will only show the text in a read-only textbox in the node

#### Supported sites
(Note: there may be NSFW content if you visit these)

- [Danbooru](https://danbooru.donmai.us)
- [e621](https://e621.net/) / [e926](https://e926.net/) / [e6ai](https://e6ai.net)

this repo is originally a rewrite of: https://github.com/yffyhk/comfyui_auto_danbooru
