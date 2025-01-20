import json
from datetime import datetime
import re
import sys

def filter_anthropic_data(data):
    """Filter Anthropic data to keep only posts from June 2024 onwards and remove links."""
    def extract_date_from_content(content):
        if not content:
            return None
            
        # Try to find date patterns like "Dec 19, 2024" or "Oct 29, 2024"
        date_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}'
        match = re.search(date_pattern, content)
        if match:
            try:
                return datetime.strptime(match.group(), '%b %d, %Y')
            except ValueError:
                return None
        return None
    
    # Filter function for posts
    def filter_post(post):
        if not post.get('content'):
            return False
            
        post_date = extract_date_from_content(post['content'])
        if not post_date:
            return False
            
        cutoff_date = datetime(2024, 6, 1)
        return post_date >= cutoff_date
    
    # Filter research posts
    if 'research_posts' in data:
        filtered_research = []
        for post in data['research_posts']:
            if filter_post(post):
                # Remove links and timestamp
                post.pop('links', None)
                post.pop('timestamp', None)
                filtered_research.append(post)
        data['research_posts'] = filtered_research
        print(f"Kept {len(filtered_research)} research posts from June 2024 onwards")
    
    # Filter news posts
    if 'news_posts' in data:
        filtered_news = []
        for post in data['news_posts']:
            if filter_post(post):
                # Remove links and timestamp
                post.pop('links', None)
                post.pop('timestamp', None)
                filtered_news.append(post)
        data['news_posts'] = filtered_news
        print(f"Kept {len(filtered_news)} news posts from June 2024 onwards")
    
    return data

def filter_deepmind_data(data):
    """Filter DeepMind data to keep only publications from January 2024 onwards and remove links."""
    # Filter function for publications
    def filter_publication(pub):
        if not pub.get('date'):
            return False
            
        try:
            # Try parsing the date directly from the date field
            pub_date = datetime.strptime(pub['date'], '%Y-%m-%d') if '-' in pub['date'] else datetime.strptime(pub['date'], '%b %d, %Y')
            cutoff_date = datetime(2024, 1, 1)
            return pub_date >= cutoff_date
        except (ValueError, TypeError):
            return False
    
    # Filter publications
    if 'publications' in data:
        filtered_publications = []
        for pub in data['publications']:
            if filter_publication(pub):
                # Remove links and timestamp
                pub.pop('links', None)
                pub.pop('timestamp', None)
                filtered_publications.append(pub)
        data['publications'] = filtered_publications
        print(f"Kept {len(filtered_publications)} publications from January 2024 onwards")
    
    # Remove links from home page
    if 'home' in data and data['home']:
        data['home'].pop('links', None)
        data['home'].pop('timestamp', None)
        print("Removed links from home page")
    
    # Remove links from about page
    if 'about' in data and data['about']:
        data['about'].pop('links', None)
        data['about'].pop('timestamp', None)
        print("Removed links from about page")
    
    return data

def filter_cser_data(data):
    """Filter CSER data to remove links from all entries."""
    
    # Remove links from home page
    if 'home' in data and data['home']:
        data['home'].pop('links', None)
        data['home'].pop('timestamp', None)
        print("Removed links from home page")
    
    # Remove links from about page
    if 'about' in data and data['about']:
        data['about'].pop('links', None)
        data['about'].pop('timestamp', None)
        print("Removed links from about page")
    
    # Remove links from resources
    if 'resources' in data:
        for resource in data['resources']:
            resource.pop('links', None)
            resource.pop('timestamp', None)
        print(f"Removed links from {len(data['resources'])} resources")
    
    return data

def filter_chai_data(data):
    """Filter CHAI data to remove papers and clean up entries."""
    
    # Remove links and timestamp from home page
    if 'home' in data and data['home']:
        data['home'].pop('timestamp', None)
        print("Cleaned home page")
    
    # Remove links and timestamp from about page
    if 'about' in data and data['about']:
        data['about'].pop('timestamp', None)
        print("Cleaned about page")
    
    # Clean up blog posts
    if 'blog_posts' in data:
        cleaned_posts = []
        for post in data['blog_posts']:
            if 'research_areas' in post:
                # Remove papers from research areas
                for area in post['research_areas']:
                    area.pop('papers', None)
            post.pop('timestamp', None)
            cleaned_posts.append(post)
        data['blog_posts'] = cleaned_posts
        print(f"Cleaned {len(cleaned_posts)} blog posts")
    
    return data

def filter_json(source='anthropic'):
    """Filter JSON data based on source."""
    # Determine input and output files based on source
    if source.lower() == 'anthropic':
        input_file = 'www_anthropic_com_data.json'
        output_file = 'www_anthropic_com_data_filtered.json'
        filter_func = filter_anthropic_data
    elif source.lower() == 'deepmind':
        input_file = 'deepmind_google_data.json'
        output_file = 'deepmind_google_data_filtered.json'
        filter_func = filter_deepmind_data
    elif source.lower() == 'cser':
        input_file = 'www_cser_ac_uk_data.json'
        output_file = 'www_cser_ac_uk_data_filtered.json'
        filter_func = filter_cser_data
    elif source.lower() == 'chai':
        input_file = 'humancompatible_ai_data.json'
        output_file = 'humancompatible_ai_data_filtered.json'
        filter_func = filter_chai_data
    else:
        raise ValueError(f"Unsupported source: {source}. Use 'anthropic', 'deepmind', 'cser', or 'chai'.")

    # Read the original JSON file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_file} not found")
        return
    
    # Apply the appropriate filter
    filtered_data = filter_func(data)
    
    # Save the filtered data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, indent=2, ensure_ascii=False)
    print(f"Saved filtered data to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python filter_json.py [anthropic|deepmind|cser|chai]")
        sys.exit(1)
    
    source = sys.argv[1].lower()
    if source not in ['anthropic', 'deepmind', 'cser', 'chai']:
        print("Error: Source must be either 'anthropic', 'deepmind', 'cser', or 'chai'")
        sys.exit(1)
    
    filter_json(source) 