import requests
from bs4 import BeautifulSoup
import json
import argparse # Import the argparse module
import re
from urllib.parse import urljoin

def scrape_movie_data(url):
    """
    Scrapes movie data from a TMDb movie page
    
    Args:
        url (str): The TMDb movie page URL
        
    Returns:
        dict: Dictionary containing scraped movie information
    """
    
    # Set up headers to mimic a real browser request and force English language
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    # Add language parameter to URL to force English
    if '?' in url:
        url += '&language=en-US'
    else:
        url += '?language=en-US'
    
    try:
        # Send GET request to the movie page
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Initialize dictionary to store movie data
        movie_data = {}
        
        # Extract poster URL
        poster_element = soup.find('img', class_='poster')
        if poster_element and poster_element.get('src'):
            # Convert relative URL to absolute URL
            poster_url = urljoin('https://www.themoviedb.org', poster_element['src'])
            movie_data['poster_url'] = poster_url
        else:
            movie_data['poster_url'] = None

        # Movie Title
        movie_title_element = soup.select_one("div.title.ott_true h2 a")
        movie_title = movie_title_element.get_text(strip=True) if movie_title_element else "N/A"
        print(f"Movie Title: {movie_title}")

        if movie_title:
            movie_data['original_title'] = movie_title
        else:
            movie_data['original_title'] = None
        
        # If the genres_span is found, find all the <a> tags within it
#        if genres_span:
#            genre_links = genres_span.find_all('a')
#            for link in genre_links:
#                genres.append(link.get_text(strip=True))

        # Extract movie genres
        genres = []
        genre_elements = soup.find_all('span', class_='genres')
#        for genre_element in genre_elements:
#            genre_text = genre_element.get_text(strip=True)
#            if genre_text:
#                genres.append(genre_text)


        for genre_span in genre_elements:
            # Find all <a> tags within the current span.genres element
            genre_links = genre_span.find_all('a')
            for link in genre_links:
                genre_name = link.get_text(strip=True)
                if genre_name: # Ensure the text is not empty
                    genres.append(genre_name)


        movie_data['genres'] = genres

        
        # Extract release date
        release_date_element = soup.find('span', class_='release')
        if release_date_element:
            movie_data['release_date'] = release_date_element.get_text(strip=True)
        else:
            movie_data['release_date'] = None
        
        # Extract director information
        directors = []
        
        # Method 1: Look in the main content area for crew info
        crew_section = soup.find('section', class_='header_poster_wrapper')
        if crew_section:
            # Look for all paragraph elements that might contain director info
            for p in crew_section.find_all('p'):
                text = p.get_text(strip=True)
                if 'Director' in text:
                    # Try to find the name in an anchor tag within this paragraph
                    director_link = p.find('a')
                    if director_link:
                        directors.append(director_link.get_text(strip=True))
        
        # Method 2: Look for crew information in lists
        if not directors:
            crew_lists = soup.find_all('ol', class_='people')
            for crew_list in crew_lists:
                for item in crew_list.find_all('li'):
                    # Check if this item contains director information
                    paragraphs = item.find_all('p')
                    for p in paragraphs:
                        if 'Director' in p.get_text():
                            # Look for the name in the same item
                            name_link = item.find('a')
                            if name_link:
                                directors.append(name_link.get_text(strip=True))
        
        # Method 3: Look for director in facts section
        if not directors:
            facts_section = soup.find('section', class_='facts')
            if facts_section:
                for p in facts_section.find_all('p'):
                    text = p.get_text(strip=True)
                    if 'Director' in text:
                        # Extract everything after "Director"
                        director_name = text.split('Director')[-1].strip()
                        if director_name:
                            directors.append(director_name)
        
        # Method 4: Look for any element with director information
        if not directors:
            director_elements = soup.find_all(string=re.compile(r'Director', re.IGNORECASE))
            for elem in director_elements:
                parent = elem.parent
                if parent:
                    # Look for links in the parent or siblings
                    links = parent.find_all('a')
                    for link in links:
                        link_text = link.get_text(strip=True)
                        if link_text and link_text not in directors:
                            directors.append(link_text)
                            break
        
        movie_data['directors'] = directors
        
        # Extract cast information
        cast_members = []
        
        # Method 1: Look for cast in scroller sections with better filtering
        cast_scroller = soup.find('div', class_='scroller')
        if cast_scroller:
            cast_items = cast_scroller.find_all('div', class_='card')
            for item in cast_items:
                # Find actor name in the link
                name_link = item.find('a')
                if name_link:
                    actor_name = name_link.get_text(strip=True)
                    # Filter out navigation text and non-actor content
                    if (actor_name and 
                        len(actor_name) > 2 and 
                        actor_name.lower() not in ['view more', 'more', 'see all', 'view all', 'cast', 'crew']):
                        cast_members.append({'actor_name': actor_name})
        
        # Method 2: Look for cast in people lists with better filtering
        if not cast_members:
            people_lists = soup.find_all('ol', class_='people')
            for people_list in people_lists:
                # Skip if this looks like crew (contains "Director" text)
                list_text = people_list.get_text()
                if 'Director' not in list_text:
                    for item in people_list.find_all('li'):
                        name_link = item.find('a')
                        if name_link:
                            actor_name = name_link.get_text(strip=True)
                            # Better filtering for actor names
                            if (actor_name and 
                                len(actor_name) > 2 and 
                                not any(word in actor_name.lower() for word in ['view', 'more', 'see all', 'cast', 'crew', 'show all'])):
                                cast_members.append({'actor_name': actor_name})
        
        # Method 3: Look for specific cast section with h3 "Cast" heading
        if not cast_members:
            cast_headings = soup.find_all('h3', string=re.compile(r'Cast', re.IGNORECASE))
            for heading in cast_headings:
                # Look for the next sibling that contains cast information
                next_section = heading.find_next_sibling()
                if next_section:
                    links = next_section.find_all('a')
                    for link in links:
                        actor_name = link.get_text(strip=True)
                        # Filter out non-actor content
                        if (actor_name and 
                            len(actor_name) > 2 and 
                            not any(word in actor_name.lower() for word in ['view', 'more', 'see', 'all', 'cast', 'crew', 'show'])):
                            cast_members.append({'actor_name': actor_name})
        
        # Method 4: Look for profile cards specifically
        if not cast_members:
            profile_cards = soup.find_all('div', class_='profile')
            for card in profile_cards:
                name_link = card.find('a')
                if name_link:
                    actor_name = name_link.get_text(strip=True)
                    # Check if this is in a cast context (not crew)
                    card_text = card.get_text().lower()
                    if ('director' not in card_text and 
                        'producer' not in card_text and
                        actor_name and 
                        len(actor_name) > 2 and 
                        not any(word in actor_name.lower() for word in ['view', 'more', 'see', 'all', 'cast', 'crew', 'show'])):
                        cast_members.append({'actor_name': actor_name})
        
        # Method 5: Look for cast member names in any section with "cast" in the class or id
        if not cast_members:
            cast_sections = soup.find_all(['div', 'section'], class_=re.compile(r'cast', re.IGNORECASE))
            cast_sections.extend(soup.find_all(['div', 'section'], id=re.compile(r'cast', re.IGNORECASE)))
            
            for section in cast_sections:
                # Look for person names (typically in <a> tags)
                links = section.find_all('a')
                for link in links:
                    # Check if the link has an href that looks like a person URL
                    href = link.get('href', '')
                    if '/person/' in href:
                        actor_name = link.get_text(strip=True)
                        if (actor_name and 
                            len(actor_name) > 2 and 
                            not any(word in actor_name.lower() for word in ['view', 'more', 'see', 'all', 'cast', 'crew', 'show'])):
                            cast_members.append({'actor_name': actor_name})
        
        # Remove duplicates while preserving order
        seen = set()
        unique_cast = []
        for member in cast_members:
            name = member['actor_name']
            if name not in seen:
                seen.add(name)
                unique_cast.append(member)
        
        movie_data['cast'] = unique_cast
        
        # Extract additional interesting data
        
        # Extract runtime
        runtime_element = soup.find('span', class_='runtime')
        if runtime_element:
            movie_data['runtime'] = runtime_element.get_text(strip=True)
        else:
            movie_data['runtime'] = None
        
        # Extract rating/score
        score_element = soup.find('div', class_='user_score_chart')
        if score_element:
            score_text = score_element.get('data-percent')
            if score_text:
                movie_data['user_score'] = f"{score_text}%"
        else:
            movie_data['user_score'] = None
        
        # Extract overview/plot
        overview_element = soup.find('div', class_='overview')
        if overview_element:
            overview_text = overview_element.find('p')
            if overview_text:
                movie_data['overview'] = overview_text.get_text(strip=True)
        else:
            movie_data['overview'] = None
        
        # Extract tagline
        tagline_element = soup.find('h3', class_='tagline')
        if tagline_element:
            movie_data['tagline'] = tagline_element.get_text(strip=True)
        else:
            movie_data['tagline'] = None
        
        return movie_data
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the webpage: {e}")
        return None

def print_movie_data(movie_data):
    """
    Pretty prints the scraped movie data
    
    Args:
        movie_data (dict): Dictionary containing movie information
    """
    if not movie_data:
        print("No movie data to display.")
        return
    
    print("=" * 50)
    print("MOVIE INFORMATION")
    print("=" * 50)
    
    print(f"Title: {movie_data.get('original_title', 'N/A')}")
    print(f"Release Date: {movie_data.get('release_date', 'N/A')}")
    print(f"Runtime: {movie_data.get('runtime', 'N/A')}")
    print(f"Genres: {', '.join(movie_data.get('genres', []))}")
    print(f"User Score: {movie_data.get('user_score', 'N/A')}")
    print(f"Tagline: {movie_data.get('tagline', 'N/A')}")
    print(f"Poster URL: {movie_data.get('poster_url', 'N/A')}")
    
    print(f"\nOverview: {movie_data.get('overview', 'N/A')}")
    
    # Print directors
    directors = movie_data.get('directors', [])
    if directors:
        print(f"\nDirector(s): {', '.join(directors)}")
    else:
        print("\nDirector(s): N/A")
    
    # Print cast
    cast = movie_data.get('cast', [])
    if cast:
        print(f"\nCast ({len(cast)} members):")
        for i, actor in enumerate(cast[:10]):  # Show first 10 cast members
            actor_name = actor.get('actor_name', 'Unknown Actor')
            print(f"  {i+1}. {actor_name}")
        if len(cast) > 10:
            print(f"  ... and {len(cast) - 10} more cast members")
    else:
        print("\nCast: N/A")

def save_to_json(movie_data, filename='movie_data.json'):
    """
    Saves the scraped movie data to a JSON file
    
    Args:
        movie_data (dict): Dictionary containing movie information
        filename (str): Output filename for the JSON file
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(movie_data, f, indent=2, ensure_ascii=False)
        print(f"\nMovie data saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON file: {e}")

def main():
    """
    Main function to run the movie scraper
    """

    # The Shawshank Redemption TMDb URL with English language parameter
    movie_url = "https://www.themoviedb.org/movie/278-the-shawshank-redemption?language=en-US"

    # Create the parser
    parser = argparse.ArgumentParser(description="Scrape movie data from TMDb.")

    # Add the URL argument
    parser.add_argument('url', type=str, nargs='?',
                        default="https://www.themoviedb.org/movie/278-the-shawshank-redemption?language=en-US",
                        help="The URL of the movie page to scrape. Defaults to The Shawshank Redemption.")

    # Parse the arguments
    args = parser.parse_args()

    # Use the URL from the arguments
    movie_url = args.url    
    print("Scraping movie data from TMDb...")
    print(f"URL: {movie_url}")
    
    # Scrape the movie data
    movie_data = scrape_movie_data(movie_url)
    
    if movie_data:
        # Print the scraped data
        print_movie_data(movie_data)
        
        # Save to JSON file
        save_to_json(movie_data)
        
        print("\nScraping completed successfully!")
    else:
        print("Failed to scrape movie data.")

if __name__ == "__main__":
    # Install required packages if not already installed
    # pip install requests beautifulsoup4
    main()