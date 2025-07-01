import sys
import requests
import json
import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def transform_url_to_filename(url):
    stripped = url.replace("https://", "").replace("http://", "")
    return "site-" + stripped.replace("/", "|").replace("-", "=") + "-AI-TOOL-"

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <URL>")
        return

    url = sys.argv[1]
    parsed_url = urlparse(url)
    domain = parsed_url.hostname

    # Load JSON configuration
    with open('config.json', 'r') as f:
        config = json.load(f)

    if domain not in config:
        print(f"Domain {domain} not supported in config.json")
        return

    selectors = config[domain]
    image_dom = selectors["image_dom"]
    prompt_dom = selectors["prompt_dom"]

    # Get page HTML
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Extract image URL and prompt
    image_tag = soup.select_one(image_dom)
    prompt_tag = soup.select_one(prompt_dom)

    if not image_tag:
        print(f"Image tag not found using selector: {image_dom}")
    if not prompt_tag:
        print(f"Prompt tag not found using selector: {prompt_dom}")

    if not image_tag or not prompt_tag:
        print("Image or prompt not found on the page. Saving full HTML to 'page_dump.html' for inspection.")
        with open("page_dump.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        return

    image_url = image_tag.get('src')
    if not image_url:
        print("No 'src' attribute found on image tag.")
        return

    if image_url.startswith("/"):
        image_url = f"https://{domain}{image_url}"
    elif not image_url.startswith("http"):
        image_url = f"https://{domain}/{image_url}"

    prompt_text = prompt_tag.get_text(strip=True)

    # Construct base filename without extension
    base_filename = transform_url_to_filename(url)

    # Extract image extension
    image_ext = image_url.split('.')[-1].split('?')[0]

    # Final filenames
    # image_filename = f"{base_filename}.{image_ext}"
    image_filename = f"{base_filename}large.webp"
    text_filename = f"{base_filename}large.txt"

    # Make filenames safe (strip paths)
    image_filename = os.path.basename(image_filename)
    text_filename = os.path.basename(text_filename)

    # Download image
    try:
        img_data = requests.get(image_url, headers=headers).content
        with open(image_filename, 'wb') as f:
            f.write(img_data)
        print(f"Saved image as {image_filename}")
    except Exception as e:
        print(f"Failed to download or save image: {e}")

    # Write prompt file
    try:
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write(f"from: {url}\nprompt: {prompt_text}\n")
        print(f"Saved prompt as {text_filename}")
    except Exception as e:
        print(f"Failed to save prompt file: {e}")

if __name__ == "__main__":
    main()
