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
    with open('ai-tool-scraper-config.json', 'r') as f:
        config = json.load(f)

    if domain not in config:
        print(f"Domain {domain} not supported in ai-tool-scraper-config.json")
        return

    selectors = config[domain]
    image_dom = selectors["image_dom"]
    prompt_dom = selectors["prompt_dom"]

    # Get page HTML with headers to request English content
    headers = {
        "Accept-Language": "en-US,en;q=0.9", # Prioritize US English, then general English
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" # Good practice to include a User-Agent
    }

    # Fetch the page content with the specified headers
    resp = requests.get(url, headers=headers)
    resp.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

    soup = BeautifulSoup(resp.text, 'html.parser')

    ### debug
    # print(soup.prettify())

    # Extract image URL and prompt
    image_tag = soup.select_one(image_dom)
    prompt_tag = soup.select_one(prompt_dom)


    ## imdb data management

    if "more" in config[domain]:
        # print(f"Domain {domain} contains more attribute")
        more_keys = list(config[domain]["more"].keys())
        print("attributes: ", more_keys)

        print("title: ", soup.select_one(config[domain]["more"]["title_dom"]))
        print("year: ", soup.select_one(config[domain]["more"]["year_dom"]))

        # genres = [genre.get_text(strip=True) for genre in soup.select(config[domain]["more"]["genre_dom"])]
        # print("Genres: {', '.join(genres) if genres else 'N/A'}")

        genres_elements = soup.select("span.genres a")
        genres = [genre.get_text(strip=True) for genre in genres_elements]
        print(f"Genres: {', '.join(genres) if genres else 'N/A'}")

        print("tagline: ", soup.select_one(config[domain]["more"]["tagline_dom"]))
        print("runtime: ", soup.select_one(config[domain]["more"]["runtime_dom"]))
        print("overview: ", soup.select_one(config[domain]["more"]["overview_dom"]))

        ### CAST
        crew_list = []
        crew_elements = soup.select("ol.people.no_image li.profile")

        for crew_member in crew_elements:
            name_element = crew_member.select_one("p a")
            job_element = crew_member.select_one("p.character") # They use 'character' for job in this context

            name = name_element.get_text(strip=True) if name_element else "N/A"
            job = job_element.get_text(strip=True) if job_element else "N/A"

            crew_list.append({"name": name, "job": job})

        # Filter for specific roles
        directors = [c["name"] for c in crew_list if "Director" in c["job"]]
        writers = [c["name"] for c in crew_list if "Writer" in c["job"] or "Screenplay" in c["job"] or "Novel" in c["job"]]

        print(f"Director(s): {', '.join(directors) if directors else 'N/A'}")
        print(f"Writer(s): {', '.join(writers) if writers else 'N/A'}")

        ### CAST
        cast_list = []
        # Select all list items in the 'scroller' within the 'cast_list'
        cast_elements = soup.select("ol.cast_list li.card")

        for cast_member in cast_elements:
            name_element = cast_member.select_one("p a")
            character_element = cast_member.select_one("p.character")

            actor_name = name_element.get_text(strip=True) if name_element else "N/A"
            character_name = character_element.get_text(strip=True) if character_element else "N/A"

            cast_list.append({"actor": actor_name, "character": character_name})

        print("\nTop Billed Cast:")
        for i, actor in enumerate(cast_list[:5]): # Print top 5 for brevity
            print(f"- {actor['actor']} as {actor['character']}")
            if i == 4 and len(cast_list) > 5:
                print(f"... and {len(cast_list) - 5} more cast members.")

        ### FACTS
        # Select the facts section and then its list items
        fact_items = soup.select("section.facts ul.facts li")

        movie_facts = {}
        for item in fact_items:
            label_element = item.select_one("strong")
            if label_element:
                label = label_element.get_text(strip=True).replace(':', '')
                # Get the text directly after the strong tag, skipping any other tags
                value = ''.join(item.find_all(string=True, recursive=False)[1:]).strip()
                movie_facts[label] = value

        print("\nMovie Facts:")
        print(f"Status: {movie_facts.get('Status', 'N/A')}")
        print(f"Original Language: {movie_facts.get('Original Language', 'N/A')}")
        print(f"Budget: {movie_facts.get('Budget', 'N/A')}")
        print(f"Revenue: {movie_facts.get('Revenue', 'N/A')}")


#    else: 
#        print(f"Domain {domain} does not contain more attribute")
        


    if not image_tag:
        print(f"Image tag not found using selector: {image_dom}")
    if not prompt_tag:
        print(f"Prompt tag not found using selector: {prompt_dom}")
#    if more_tag:
#        print(f"More tag found using selector: {more_dom}")

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
