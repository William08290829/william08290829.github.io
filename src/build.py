import os
import argparse
from shutil import rmtree
from urllib.parse import urljoin

from bs4 import BeautifulSoup, element
from jinja2 import Environment, FileSystemLoader, select_autoescape

first_name = "William"
last_name = "Chen"
nickname = "William"
name = f"{first_name} {last_name}"
title_name = name
domain = "william08290829.github.io"
generic_username = "William08290829"
twitter_username = ""
url = f"https://{domain}"  # for opengraph


def bs(content):
    return BeautifulSoup(content, "html.parser")


parser = argparse.ArgumentParser(description="Build the website")
parser.add_argument("--output", help="Output directory", default="dist")
parser.add_argument(
    "--no-clean", help="Don't clean the output directory", action="store_true"
)

args = parser.parse_args()

script_path = os.path.dirname(os.path.realpath(__file__))

env = Environment(
    loader=FileSystemLoader(f"{script_path}/templates"),
    autoescape=select_autoescape(["html"]),
)

if not args.no_clean:
    # delete everything inside the output directory
    for root, dirs, files in os.walk(args.output):
        for file in files:
            if file == "index.css":
                continue
            os.remove(os.path.join(root, file))

        for dir in dirs:
            rmtree(os.path.join(root, dir))


def write_output(content, *path):
    # make sure every directory in the path exists
    for i in range(len(path) - 1):
        if not os.path.exists(os.path.join(args.output, *path[: i + 1])):
            os.makedirs(os.path.join(args.output, *path[: i + 1]))

    with open(os.path.join(args.output, *path), "w", encoding="utf-8") as f:
        f.write(content)


def render_template(template_name, **context):
    template = env.get_template(template_name)
    rendered = template.render(**context)
    soup = bs(rendered)

    for img_tag in soup.find_all("img"):
        img_tag_rule(img_tag)

    return soup


def og_tags(data: dict):
    tags = []
    for key, value in data.items():
        tags.append(f'<meta property="og:{key}" content="{value}">')

    if "description" in data:
        tags.append(f'<meta name="description" content="{data["description"]}">')

    return tags


twitter_tags_common = {
    "domain": domain,
    "card": "summary_large_image",
    "site": twitter_username,
}


def twitter_tags(data: dict):
    lut = {
        "card": "name",
        "domain": "property",
        "url": "property",
        "title": "name",
        "description": "name",
        "image": "name",
        "site": "name",
    }

    data = {**twitter_tags_common, **data}

    tags = []
    for key, value in data.items():
        tags.append(f'<meta {lut[key]}="twitter:{key}" content="{value}">')

    return tags


def img_tag_rule(img_tag: element.Tag):
    if not img_tag.has_attr("decoding"):
        img_tag["decoding"] = "async"
    if not img_tag.has_attr("loading"):
        img_tag["loading"] = "lazy"


seo_common = {
    "url": url,
    "title": title_name,
    "description": f"{title_name}'s personal website",
    "image": urljoin(url, "/assets/me.jpg"),
}

og = og_tags(
    {
        **seo_common,
        "type": "profile",
        "profile:first_name": first_name,
        "profile:last_name": last_name,
        "profile:username": generic_username,
    }
)

twitter = twitter_tags({**seo_common, "card": "summary"})
seotags = og + twitter

index_soup = render_template("index.html", name=name, title=title_name)
for item in seotags:
    index_soup.head.append(bs(item))

write_output(index_soup.encode_contents().decode("utf-8"), "index.html")

custom_pages = [
    {
        "template": "random/travel.html",
        "output": ("random", "travel.html"),
        "title": f"{title_name} | Travel",
        "seo": {
            **seo_common,
            "url": urljoin(url, "/random/travel"),
            "title": f"{title_name} | Travel",
            "description": f"{title_name}'s travel map and bucket list",
            "image": urljoin(url, "/assets/me.jpg"),
        },
    },
    {
        "template": "random/favorite.html",
        "output": ("random", "favorite.html"),
        "title": f"{title_name} | Favorite",
        "seo": {
            **seo_common,
            "url": urljoin(url, "/random/favorite"),
            "title": f"{title_name} | Favorite",
            "description": f"{title_name}'s bouncing favorite wall",
            "image": urljoin(url, "/assets/me.jpg"),
        },
    },
    {
        "template": "random/wins.html",
        "output": ("random", "wins.html"),
        "title": f"{title_name} | Wins",
        "seo": {
            **seo_common,
            "url": urljoin(url, "/random/wins"),
            "title": f"{title_name} | Wins",
            "description": f"{title_name}'s trophy case of wins and milestones",
            "image": urljoin(url, "/assets/me.jpg"),
        },
    },
    {
        "template": "random/lore.html",
        "output": ("random", "lore.html"),
        "title": f"{title_name} | Lore",
        "seo": {
            **seo_common,
            "url": urljoin(url, "/random/lore"),
            "title": f"{title_name} | Lore",
            "description": f"The questions {title_name} gets asked, and the answers actually given",
            "image": urljoin(url, "/assets/me.jpg"),
        },
    },
    {
        "template": "random/cv.html",
        "output": ("random", "cv.html"),
        "title": f"{title_name} | CV",
        "seo": {
            **seo_common,
            "url": urljoin(url, "/random/cv"),
            "title": f"{title_name} | CV",
            "description": f"{title_name}'s Curriculum Vitae (CV)",
            "image": urljoin(url, "/assets/me.jpg"),
        },
    },
    {
        "template": "resources.html",
        "output": ("resources.html",),
        "title": f"{title_name} | Resources",
        "seo": {
            **seo_common,
            "url": urljoin(url, "/resources"),
            "title": f"{title_name} | Resources",
            "description": f"{title_name}'s shelf of resources for visitors from videos and posts",
            "image": urljoin(url, "/assets/me.jpg"),
        },
    },
    {
        "template": "tt.html",
        "output": ("tt.html",),
        "title": f"{title_name} | TikTok",
        "seo": {
            **seo_common,
            "url": urljoin(url, "/tt"),
            "title": f"{title_name} | TikTok",
            "description": f"landing page for visitors coming from tiktok",
            "image": urljoin(url, "/assets/me.jpg"),
        },
    }
]

for page in custom_pages:
    soup = render_template(page["template"], name=name, title=page["title"])
    page_tags = og_tags({**page["seo"], "type": "website"}) + twitter_tags(page["seo"])

    for item in page_tags:
        soup.head.append(bs(item))

    write_output(soup.encode_contents().decode("utf-8"), *page["output"])
