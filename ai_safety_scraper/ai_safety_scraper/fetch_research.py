import requests
import re
import json
from bs4 import BeautifulSoup

def get_page():
    url = "https://www.anthropic.com/research"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('content-type', 'Not specified')}")
        print(f"Response Length: {len(response.text)} characters")
        
        # Look for the exact slug pattern
        print("\nSearching for research post slugs...")
        slug_pattern = r'"slug":\s*{\s*"current":\s*"([^"]+)"'
        slugs = re.findall(slug_pattern, response.text)
        
        if slugs:
            print(f"\nFound {len(slugs)} research post slugs:")
            print("-" * 80)
            for slug in slugs:
                research_url = f"https://www.anthropic.com/research/{slug}"
                print(f"- {research_url}")
            print("-" * 80)
        else:
            print("No research post slugs found")
        
        # Save the raw HTML to a file
        with open('research_output.txt', 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        print("\nSuccessfully saved research page HTML to research_output.txt")
        
    except Exception as e:
        print(f"Error fetching page: {e}")

if __name__ == "__main__":
    get_page() 