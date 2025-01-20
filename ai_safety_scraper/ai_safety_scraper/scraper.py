import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
from datetime import datetime
import time
from bs4 import NavigableString
from abc import ABC, abstractmethod
import re

class BaseScraper(ABC):
    def __init__(self, base_url):
        self.base_url = base_url
        self.scraped_urls = set()
        self.session = requests.Session()
        self.data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'base_url': self.base_url
            },
            'home': None,
            'about': None,
            'blog_posts': []
        }
        # Be nice to the server
        self.request_delay = 0.2  # seconds

    def get_page(self, url):
        """Fetch a page with rate limiting and error handling."""
        try:
            time.sleep(self.request_delay)
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
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_text_content(self, element, with_links=True):
        """Extract text content from an element, handling special cases."""
        if element.name == 'table':
            rows = []
            for row in element.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                rows.append('\t'.join(cells))
            return '\n'.join(rows)
            
        elif element.name in ['ul', 'ol']:
            items = []
            for item in element.find_all('li'):
                text = item.get_text(strip=True)
                if text:
                    items.append(f"- {text}")
            return '\n'.join(items)
            
        elif element.name == 'blockquote':
            text = element.get_text(strip=True)
            if text:
                return '> ' + text.replace('\n', '\n> ')
                
        elif element.name in ['pre', 'code']:
            text = element.get_text(strip=True)
            if text:
                return f"```\n{text}\n```"
                
        elif element.name == 'a' and with_links:
            href = element.get('href')
            text = element.get_text(strip=True)
            if href and text:
                href = urljoin(self.base_url, href)
                return f"[{text}]({href})"
            return text
            
        else:
            if with_links and element.find('a'):
                parts = []
                for content in element.contents:
                    if isinstance(content, NavigableString):
                        text = str(content).strip()
                        if text:
                            parts.append(text)
                    elif content.name == 'a':
                        parts.append(self.extract_text_content(content))
                return ' '.join(parts)
            else:
                return element.get_text(strip=True)

    def save_to_json(self, filename=None):
        """Save scraped data to a JSON file."""
        if filename is None:
            domain = self.base_url.split('//')[1].split('/')[0].replace('.', '_')
            filename = f"{domain}_data.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    @abstractmethod
    def is_blog_post_url(self, url):
        """Check if the URL is a blog post URL."""
        pass

    @abstractmethod
    def scrape_home_page(self):
        """Scrape the home page content."""
        pass

    @abstractmethod
    def scrape_about_page(self):
        """Scrape the about page content."""
        pass

    @abstractmethod
    def scrape_blog_post(self, url):
        """Scrape a single blog post."""
        pass

    @abstractmethod
    def scrape_blog_posts(self):
        """Scrape all blog posts."""
        pass

    def scrape_all(self):
        """Scrape all content from the website."""
        self.data['home'] = self.scrape_home_page()
        self.data['about'] = self.scrape_about_page()
        self.scrape_blog_posts()
        self.save_to_json()

class MetrScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://metr.org")

    def is_blog_post_url(self, url):
        """Check if the URL is a blog post URL."""
        if url.rstrip('/') == f"{self.base_url}/blog":
            return False
        if any(x in url for x in ['/page/', '/blog/?', '/blog/#', '/blog/$']):
            return False
        return '/blog/' in url

    def scrape_home_page(self):
        """Scrape the home page content."""
        print("Scraping home page...")
        soup = self.get_page(self.base_url)
        if not soup:
            return None

        content = {
            'url': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        main_content = soup.find('div', class_='content')
        if main_content:
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                content_elements.append(self.extract_text_content(element))
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_about_page(self):
        print("Scraping about page...")
        about_url = urljoin(self.base_url, '/about')
        soup = self.get_page(about_url)
        if not soup:
            return None

        content = {
            'url': about_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        main_content = soup.find('div', class_='content')
        if main_content:
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                content_elements.append(self.extract_text_content(element))
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_blog_post(self, url):
        if url in self.scraped_urls:
            return None
        
        if not self.is_blog_post_url(url):
            return None
        
        self.scraped_urls.add(url)
        print(f"Scraping blog post: {url}")
        soup = self.get_page(url)
        if not soup:
            return None
        
        post_content = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'title': '',
            'date': None,
            'content': '',
            'headings': [],
            'links': []
        }
        
        schema_json = soup.find('script', type='application/ld+json')
        if schema_json and schema_json.string:
            try:
                schema_data = json.loads(schema_json.string)
                post_content['title'] = schema_data.get('headline', '')
                post_content['date'] = schema_data.get('datePublished', None)
            except json.JSONDecodeError:
                pass

        content_div = soup.find('div', class_='content')
        if not content_div:
            print(f"Warning: No content div found for {url}")
            return None
            
        headings = content_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        post_content['headings'] = [h.get_text(strip=True) for h in headings]
        
        links = content_div.find_all('a')
        post_content['links'] = [
            {
                'text': link.get_text(strip=True),
                'href': urljoin(self.base_url, link.get('href', ''))
            }
            for link in links
            if link.get('href')
        ]
        
        for element in content_div.find_all(['script', 'style', 'nav', 'aside', 'footer']):
            element.decompose()
            
        content_section = soup.find('div', class_='section pt-0')
        if content_section:
            content_area = content_section.find('div', class_='content')
            if content_area:
                main_content = content_area
            else:
                main_content = content_section
        else:
            main_content = content_div
        
        content_elements = []
        for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table', 'div']):
            if element.get('class'):
                classes = element.get('class')
                if not isinstance(classes, (list, tuple)):
                    classes = [classes]
                if any(c in ['post-header', 'post-categories', 'post-authors', 'post-date', 'caption', 'hide-over-950', 'show-over-950', 'breakout-wider'] 
                       for c in classes):
                    continue
            
            text = self.extract_text_content(element)
            if text and text not in content_elements:
                content_elements.append(text)
        
        post_content['content'] = '\n\n'.join(content_elements)
        return post_content

    def scrape_blog_posts(self):
        print("Scraping blog posts...")
        blog_url = urljoin(self.base_url, '/blog')
        soup = self.get_page(blog_url)
        if not soup:
            return

        # Find all blog post links
        blog_links = set()
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                if self.is_blog_post_url(full_url):
                    blog_links.add(full_url)

        # Scrape each blog post
        for url in blog_links:
            post_content = self.scrape_blog_post(url)
            if post_content:
                self.data['blog_posts'].append(post_content)

class AisiScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.aisi.gov.uk")
        self.data.update({
            'work': None,
            'academic_engagement': None,
            'grants': None,
            'articles': []
        })

    def is_blog_post_url(self, url):
        # AISI articles are under /work/ directory
        return '/work/' in url and not url.rstrip('/').endswith('/work')

    def scrape_home_page(self):
        """Scrape the home page content."""
        print("Scraping AISI home page...")
        soup = self.get_page(self.base_url)
        if not soup:
            return None

        content = {
            'url': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        main_content = soup.find('main') or soup.find('div', class_='main-content')
        if main_content:
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                content_elements.append(self.extract_text_content(element))
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_about_page(self):
        """Scrape the about page content."""
        print("Scraping AISI about page...")
        about_url = urljoin(self.base_url, '/about')
        soup = self.get_page(about_url)
        if not soup:
            return None

        content = {
            'url': about_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        main_content = soup.find('main') or soup.find('div', class_='main-content')
        if main_content:
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                content_elements.append(self.extract_text_content(element))
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_blog_post(self, url):
        """Required by BaseScraper but not used - we use scrape_article instead."""
        return self.scrape_article(url)

    def scrape_blog_posts(self):
        """Required by BaseScraper but not used - articles are handled in scrape_all."""
        pass

    def scrape_work_page(self):
        """Scrape the work page content and collect article links."""
        print("Scraping AISI work page...")
        work_url = urljoin(self.base_url, '/work')
        soup = self.get_page(work_url)
        if not soup:
            print("Failed to get work page")
            return None

        content = {
            'url': work_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'article_links': []
        }

        # Get all headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        # Get main content - look for the section with class bg-c-white
        main_content = soup.find('div', class_='section bg-c-white')
        if main_content:
            print("Found main content section")
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                content_elements.append(self.extract_text_content(element))
            content['content'] = '\n\n'.join(content_elements)

            # Find the work cards container
            work_cards_container = main_content.find('div', {'class': 'work-cards', 'fs-cmsfilter-element': 'list'})
            if work_cards_container:
                print("Found work cards container")
                # Find all work card wrappers
                work_cards = work_cards_container.find_all('div', class_='work-card-wrapper')
                print(f"Found {len(work_cards)} work cards")
                
                for i, card in enumerate(work_cards, 1):
                    print(f"\nProcessing card {i}:")
                    # Try to get the link from the title
                    title_link = card.find('a', class_='text-link-hover')
                    if title_link:
                        print(f"Found title link: {title_link.get('href', 'No href')}")
                        if title_link.get('href'):
                            article_url = urljoin(self.base_url, title_link['href'])
                            if article_url not in content['article_links']:
                                content['article_links'].append(article_url)
                                print(f"Added article URL: {article_url}")
                            continue
                    else:
                        print("No title link found in card")

                    # If no title link, try to get the Read More button link
                    read_more = card.find('a', class_='button')
                    if read_more:
                        print(f"Found Read More button: {read_more.get('href', 'No href')}")
                        if read_more.get('href'):
                            article_url = urljoin(self.base_url, read_more['href'])
                            # Only include internal links
                            if article_url.startswith(self.base_url):
                                if article_url not in content['article_links']:
                                    content['article_links'].append(article_url)
                                    print(f"Added article URL from button: {article_url}")
                    else:
                        print("No Read More button found in card")

                print(f"\nTotal article links found: {len(content['article_links'])}")
            else:
                print("No work cards container found")
        else:
            print("No main content section found")

        return content

    def scrape_academic_engagement_page(self):
        """Scrape the academic engagement page content."""
        print("Scraping AISI academic engagement page...")
        academic_url = urljoin(self.base_url, '/academic-engagement')
        soup = self.get_page(academic_url)
        if not soup:
            return None

        content = {
            'url': academic_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        main_content = soup.find('main') or soup.find('div', class_='main-content')
        if main_content:
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                content_elements.append(self.extract_text_content(element))
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_grants_page(self):
        """Scrape the grants page content."""
        print("Scraping AISI grants page...")
        grants_url = urljoin(self.base_url, '/grants')
        soup = self.get_page(grants_url)
        if not soup:
            return None

        content = {
            'url': grants_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        main_content = soup.find('main') or soup.find('div', class_='main-content')
        if main_content:
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                content_elements.append(self.extract_text_content(element))
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_article(self, url):
        """Scrape an individual article page."""
        if url in self.scraped_urls:
            return None

        self.scraped_urls.add(url)
        print(f"Scraping AISI article: {url}")
        soup = self.get_page(url)
        if not soup:
            return None

        article = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'title': '',
            'date': None,
            'content': '',
            'headings': [],
            'category': None
        }

        # Get title from h1 in the interior-hero section
        hero_section = soup.find('section', class_='interior-hero')
        if hero_section:
            title_elem = hero_section.find('h1')
            if title_elem:
                article['title'] = title_elem.get_text(strip=True)

            # Get date from the breadcrumb div
            date_div = hero_section.find('div', class_='breadcrumb')
            if date_div:
                date_text = date_div.get_text(strip=True)
                article['date'] = date_text

            # Get category from the category-row div
            category_row = hero_section.find('div', class_='category-row')
            if category_row:
                category_link = category_row.find_all('a')[-1]  # Last link is usually the category
                if category_link:
                    article['category'] = category_link.get_text(strip=True)

        # Get content from the rtf-cms div
        content_div = soup.find('div', class_='rtf-cms')
        if content_div:
            # Get all headings
            headings = content_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            article['headings'] = [h.get_text(strip=True) for h in headings]

            # Extract content
            content_elements = []
            for element in content_div.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                text = self.extract_text_content(element)
                if text and text not in content_elements:
                    content_elements.append(text)

            article['content'] = '\n\n'.join(content_elements)
            return article
        else:
            print(f"Warning: No content div found for {url}")
            return None

    def scrape_all(self):
        """Scrape all content from the website."""
        # Scrape main pages
        self.data['home'] = self.scrape_home_page()
        self.data['about'] = self.scrape_about_page()
        self.data['work'] = self.scrape_work_page()
        self.data['academic_engagement'] = self.scrape_academic_engagement_page()
        self.data['grants'] = self.scrape_grants_page()

        # Scrape all articles from the work page
        if self.data['work'] and 'article_links' in self.data['work']:
            for url in self.data['work']['article_links']:
                article = self.scrape_article(url)
                if article:
                    self.data['articles'].append(article)

        self.save_to_json()

    def scrape_consortium_members(self):
        """Scrape the AISIC members page"""
        url = urljoin(self.base_url, '/artificial-intelligence-safety-institute-consortium/aisic-members')
        soup = self.get_page(url)
        if not soup:
            return None

        content = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'links': [],
            'members': []
        }

        main_content = soup.find('div', class_='node__content')
        if main_content:
            content['headings'] = [h.get_text(strip=True) for h in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
            
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                content_elements.append(self.extract_text_content(element))
            content['content'] = '\n\n'.join(content_elements)

            links = main_content.find_all('a')
            content['links'] = [
                {
                    'text': link.get_text(strip=True),
                    'href': urljoin(self.base_url, link.get('href', ''))
                }
                for link in links
                if link.get('href')
            ]

            # Add specific handling for member list
            members_list = main_content.find('div', class_='view-content')
            if members_list:
                content['members'] = [
                    member.get_text(strip=True)
                    for member in members_list.find_all(['p', 'div'], class_='member-name')
                ]

        return content

class LakeraScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.lakera.ai")

    def scrape_all(self):
        """Scrape all content from the website."""
        # Scrape main pages
        self.data['home'] = self.scrape_home_page()
        self.data['about'] = self.scrape_about_page()
        
        # Initialize blog posts list if not exists
        if 'blog_posts' not in self.data:
            self.data['blog_posts'] = []
        
        # Scrape all blog posts
        self.scrape_blog_posts()
        
        # Save the scraped data
        self.save_to_json()

    def is_blog_post_url(self, url):
        """Check if the URL is a blog post URL."""
        if url.rstrip('/') == f"{self.base_url}/blog":
            return False
        return '/blog/' in url and not any(x in url for x in ['/category/', '/author/'])

    def scrape_home_page(self):
        """Scrape the home page content."""
        print("Scraping Lakera home page...")
        soup = self.get_page(self.base_url)
        if not soup:
            return None

        content = {
            'url': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        # Get all headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        # Get main content
        main_content = soup.find('main')
        if main_content:
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table', 'div']):
                if element.get('class'):
                    classes = element.get('class')
                    if not isinstance(classes, (list, tuple)):
                        classes = [classes]
                    if any(c in ['navbar10_component', 'footer_component'] for c in classes):
                        continue
                text = self.extract_text_content(element)
                if text and text not in content_elements:
                    content_elements.append(text)
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_about_page(self):
        """Scrape the about page content."""
        print("Scraping Lakera about page...")
        about_url = urljoin(self.base_url, '/about')
        soup = self.get_page(about_url)
        if not soup:
            return None

        content = {
            'url': about_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        # Get all headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        # Get main content
        main_content = soup.find('main')
        if main_content:
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table', 'div']):
                if element.get('class'):
                    classes = element.get('class')
                    if not isinstance(classes, (list, tuple)):
                        classes = [classes]
                    if any(c in ['navbar10_component', 'footer_component'] for c in classes):
                        continue
                text = self.extract_text_content(element)
                if text and text not in content_elements:
                    content_elements.append(text)
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_blog_post(self, url):
        """Scrape a single blog post."""
        if url in self.scraped_urls:
            return None
        
        if not self.is_blog_post_url(url):
            return None
        
        self.scraped_urls.add(url)
        print(f"Scraping Lakera blog post: {url}")
        soup = self.get_page(url)
        if not soup:
            return None

        post = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'title': '',
            'date': None,
            'author': None,
            'category': None,
            'content': '',
            'headings': [],
            'reading_time': None
        }

        # Get title from the article title section
        article_title = soup.find('h1', class_='blog_title')
        if article_title:
            post['title'] = article_title.get_text(strip=True)
        else:
            # Fallback to page title
            title = soup.find('title')
            if title:
                post['title'] = title.get_text(strip=True).split('|')[0].strip()

        # Get author and date from the blog info section
        blog_info = soup.find('div', class_='blog_author-wrapper')
        if blog_info:
            # Get author
            author_link = blog_info.find('a', class_='blog_author-link')
            if author_link:
                post['author'] = author_link.get_text(strip=True)
            
            # Get date
            date_div = blog_info.find('div', {'id': 'original-date'})
            if date_div:
                post['date'] = date_div.get_text(strip=True)

        # Get reading time
        reading_time = soup.find('div', class_='blog_read-time')
        if reading_time:
            post['reading_time'] = reading_time.get_text(strip=True)

        # Get category
        category_link = soup.find('a', class_='blog_category-link')
        if category_link:
            post['category'] = category_link.get_text(strip=True)

        # Try to find the main content section
        content_containers = [
            soup.find('div', class_='text-rich-text w-richtext'),
            soup.find('div', class_='blog-post_rich-text w-richtext'),
            soup.find('div', class_='rich-text-block w-richtext'),
            soup.find('div', class_='blog_content-wrapper'),
            soup.find('article'),
            soup.find('main')
        ]

        main_content = None
        for container in content_containers:
            if container and len(container.get_text(strip=True)) > 100:  # Ensure it has substantial content
                main_content = container
                break

        if main_content:
            # First collect all headings
            for heading in main_content.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = heading.get_text(strip=True)
                if heading_text and heading_text not in post['headings']:
                    post['headings'].append(heading_text)

            # Then collect content elements
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                # Skip elements in non-content sections
                if element.parent.get('class') and any(cls in str(element.parent.get('class')) for cls in [
                    'blog_author-wrapper', 'blog-header', 'cookie', 'banner', 'nav', 'header', 'footer', 'modal',
                    'blog_category-wrapper', 'blog_date-wrapper', 'blog_read-time'
                ]):
                    continue
                
                # Skip promotional content
                text = element.get_text(strip=True)
                if text and not any(promo in text.lower() for promo in [
                    'subscribe to our newsletter',
                    'sign up for updates',
                    'download our whitepaper',
                    'contact us',
                    'book a demo'
                ]):
                    # Extract text based on element type
                    if element.name in ['ul', 'ol']:
                        # Handle lists
                        items = []
                        for item in element.find_all('li'):
                            item_text = self.extract_text_content(item)
                            if item_text:
                                items.append(f"- {item_text}")
                        if items:
                            content_elements.append('\n'.join(items))
                    elif element.name == 'blockquote':
                        # Handle blockquotes
                        quote_text = self.extract_text_content(element)
                        if quote_text:
                            content_elements.append(f"> {quote_text}")
                    elif element.name in ['pre', 'code']:
                        # Handle code blocks
                        code_text = element.get_text(strip=True)
                        if code_text:
                            content_elements.append(f"```\n{code_text}\n```")
                    else:
                        # Handle regular paragraphs and other elements
                        text = self.extract_text_content(element)
                        if text and len(text.strip()) > 0:  # Ensure non-empty content
                            content_elements.append(text)

            # Join all unique content elements
            post['content'] = '\n\n'.join(content_elements)

        return post

    def scrape_blog_posts(self):
        """Scrape all blog posts."""
        print("Scraping Lakera blog posts...")
        blog_url = urljoin(self.base_url, '/blog')
        
        # Find all blog post links across all pages
        blog_links = set()
        page = 1
        while True:
            # Construct page URL
            page_url = blog_url if page == 1 else f"{blog_url}?665a46a9_page={page}"
            print(f"Scanning blog page {page}...")
            
            soup = self.get_page(page_url)
            if not soup:
                break

            # Find blog posts on current page
            found_posts = False
            blog_items = soup.find_all('div', {'role': 'listitem', 'class': 'w-dyn-item'})
            for item in blog_items:
                found_posts = True
                link = item.find('a', class_='blog_main-title-link')
                if link:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if self.is_blog_post_url(full_url):
                            blog_links.add(full_url)

            # Check if we've reached the last page
            if not found_posts:
                break

            # Check if there's a next page button
            next_button = soup.find('a', {'aria-label': 'Next Page'})
            if not next_button:
                break

            page += 1
            time.sleep(1)  # Rate limiting between page requests

        # Scrape each blog post
        for url in blog_links:
            post_content = self.scrape_blog_post(url)
            if post_content:
                self.data['blog_posts'].append(post_content)
                time.sleep(1)  # Rate limiting

class NistAisiScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.nist.gov/aisi")
        # Additional pages specific to NIST AISI
        self.data.update({
            'strategic_vision': None,
            'guidance': None,
            'consortium': None,
            'consortium_members': None,
            'member_perspectives': None,
            'working_groups': None,
            'faqs': None,
            'ai_engagement': None,
            'related_links': None,
            'news_updates': []  # For storing news and updates
        })

    def is_blog_post_url(self, url):
        """NIST AISI news/updates are in the news section"""
        return '/news/' in url or '/updates/' in url

    def scrape_blog_post(self, url):
        """Scrape a news/update article"""
        if url in self.scraped_urls:
            return None
        
        if not self.is_blog_post_url(url):
            return None
        
        self.scraped_urls.add(url)
        print(f"Scraping article: {url}")
        soup = self.get_page(url)
        if not soup:
            return None

        article = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'title': '',
            'date': None,
            'content': '',
            'headings': [],
            'links': []
        }

        title = soup.find('h1', class_='page-title')
        if title:
            article['title'] = title.get_text(strip=True)

        date_element = soup.find('time')
        if date_element:
            article['date'] = date_element.get('datetime')

        content_div = soup.find('div', class_='node__content')
        if content_div:
            article['headings'] = [h.get_text(strip=True) for h in content_div.find_all(['h2', 'h3', 'h4', 'h5', 'h6'])]
            
            content_elements = []
            for element in content_div.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                content_elements.append(self.extract_text_content(element))
            article['content'] = '\n\n'.join(content_elements)

            links = content_div.find_all('a')
            article['links'] = [
                {
                    'text': link.get_text(strip=True),
                    'href': urljoin(self.base_url, link.get('href', ''))
                }
                for link in links
                if link.get('href')
            ]

        return article

    def scrape_blog_posts(self):
        """Scrape news and updates"""
        print("Scraping NIST AISI news and updates...")
        
        # News and updates are shown on the home page
        soup = self.get_page(self.base_url)
        if not soup:
            return

        # Find news section
        news_section = soup.find('div', class_='news-updates')
        if news_section:
            # Find all news links
            for link in news_section.find_all('a'):
                href = link.get('href')
                if href:
                    url = urljoin(self.base_url, href)
                    if self.is_blog_post_url(url):
                        article = self.scrape_blog_post(url)
                        if article:
                            self.data['news_updates'].append(article)
                            time.sleep(self.request_delay)  # Rate limiting

    def scrape_home_page(self):
        print("Scraping NIST AISI home page...")
        soup = self.get_page(self.base_url)
        if not soup:
            return None

        content = {
            'url': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'sections': []
        }

        # Find the main content section
        main_content = soup.find('section', class_='nist-page__content')
        if not main_content:
            return content

        # Get the main title
        title = main_content.find('h1', class_='nist-page__title')
        if title:
            content['headings'].append(title.get_text(strip=True))

        # Find the main content area
        content_area = main_content.find('div', class_='nist-content-row--width-legible')
        if content_area:
            # Get all content elements
            content_elements = []
            
            # Process text blocks
            text_blocks = content_area.find_all('div', class_='text-long')
            for block in text_blocks:
                # Process paragraphs
                for p in block.find_all('p'):
                    text = self.extract_text_content(p)
                    if text:
                        content_elements.append(text)
                
                # Process lists
                for lst in block.find_all(['ul', 'ol']):
                    text = self.extract_text_content(lst)
                    if text:
                        content_elements.append(text)
                
                # Process callouts
                callouts = block.find_all('div', class_='nist-callout')
                for callout in callouts:
                    text = self.extract_text_content(callout)
                    if text:
                        content_elements.append(f"[Callout] {text}")

                # Process tables
                tables = block.find_all('table')
                for table in tables:
                    text = self.extract_text_content(table)
                    if text:
                        content_elements.append(text)

                # Process blockquotes
                blockquotes = block.find_all('blockquote')
                for quote in blockquotes:
                    text = self.extract_text_content(quote)
                    if text:
                        content_elements.append(f"> {text}")

            content['content'] = '\n\n'.join(content_elements)

            # Get sections (News, Awards, etc.)
            sections = main_content.find_all('div', class_='paragraph--type--tagged-content-list')
            for section in sections:
                section_data = {
                    'title': '',
                    'items': []
                }
                
                # Get section title
                title_elem = section.find('h2', class_='nist-block__title')
                if title_elem:
                    section_data['title'] = title_elem.get_text(strip=True)
                
                # Get items in the section
                for article in section.find_all('article', class_='nist-teaser'):
                    item = {
                        'title': '',
                        'date': None,
                        'summary': '',
                        'url': ''
                    }
                    
                    # Get title and URL
                    title_link = article.find('h3', class_='nist-teaser__title').find('a')
                    if title_link:
                        item['title'] = title_link.get_text(strip=True)
                        item['url'] = urljoin(self.base_url, title_link.get('href', ''))
                    
                    # Get date
                    date_elem = article.find('time')
                    if date_elem:
                        item['date'] = date_elem.get('datetime')
                    
                    # Get summary
                    summary_elem = article.find('div', class_='text-with-summary')
                    if summary_elem:
                        item['summary'] = summary_elem.get_text(strip=True)
                    
                    section_data['items'].append(item)
                
                content['sections'].append(section_data)

        return content

    def scrape_about_page(self):
        """NIST AISI uses strategic vision as their about page"""
        return self.scrape_strategic_vision()

    def scrape_strategic_vision(self):
        """Scrape the strategic vision page"""
        url = urljoin(self.base_url, '/aisi/strategic-vision')
        return self._scrape_generic_page(url)

    def scrape_guidance(self):
        """Scrape the guidance page"""
        url = urljoin(self.base_url, '/aisi/guidance')
        return self._scrape_generic_page(url)

    def scrape_consortium(self):
        """Scrape the AISIC main page"""
        url = urljoin(self.base_url, '/aisi/artificial-intelligence-safety-institute-consortium-aisic')
        return self._scrape_generic_page(url)

    def scrape_consortium_members(self):
        """Scrape the AISIC members page"""
        url = urljoin(self.base_url, '/aisi/artificial-intelligence-safety-institute-consortium/aisic-members')
        soup = self.get_page(url)
        if not soup:
            return None

        content = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'links': [],
            'members': []
        }

        main_content = soup.find('div', class_='node__content')
        if main_content:
            content['headings'] = [h.get_text(strip=True) for h in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
            
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                content_elements.append(self.extract_text_content(element))
            content['content'] = '\n\n'.join(content_elements)

            links = main_content.find_all('a')
            content['links'] = [
                {
                    'text': link.get_text(strip=True),
                    'href': urljoin(self.base_url, link.get('href', ''))
                }
                for link in links
                if link.get('href')
            ]

            # Add specific handling for member list
            members_list = main_content.find('div', class_='view-content')
            if members_list:
                content['members'] = [
                    member.get_text(strip=True)
                    for member in members_list.find_all(['p', 'div'], class_='member-name')
                ]

        return content

    def scrape_member_perspectives(self):
        """Scrape the member perspectives page"""
        url = urljoin(self.base_url, '/aisi/aisic-member-perspectives')
        return self._scrape_generic_page(url)

    def scrape_working_groups(self):
        """Scrape the working groups page"""
        url = urljoin(self.base_url, '/aisi/aisic-working-groups')
        return self._scrape_generic_page(url)

    def scrape_faqs(self):
        """Scrape the FAQs page"""
        url = urljoin(self.base_url, '/aisi/artificial-intelligence-safety-institute-consortium-faqs')
        return self._scrape_generic_page(url)

    def scrape_ai_engagement(self):
        """Scrape the AI engagement page"""
        url = "https://www.nist.gov/artificial-intelligence/nist-ai-engagement"  # Full URL needed
        return self._scrape_generic_page(url)

    def scrape_related_links(self):
        """Scrape the related links page"""
        url = "https://www.nist.gov/artificial-intelligence/related-links"  # Full URL needed
        return self._scrape_generic_page(url)

    def _scrape_generic_page(self, url):
        """Helper method to scrape any generic NIST page"""
        print(f"Scraping {url}...")
        soup = self.get_page(url)
        if not soup:
            return None

        content = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'links': []
        }

        # Find the main content section
        main_content = soup.find('div', class_='text-with-summary')
        if not main_content:
            return content

        # Get the main title
        title = soup.find('h1', class_='nist-page__title')
        if title:
            content['headings'].append(title.get_text(strip=True))

        # Get all content elements
        content_elements = []
        
        # Process callouts
        callouts = main_content.find_all('div', class_='nist-callout')
        for callout in callouts:
            text = self.extract_text_content(callout)
            if text:
                content_elements.append(f"[Callout] {text}")

        # Process headings
        for heading in main_content.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text(strip=True)
            if text and text not in content['headings']:
                content['headings'].append(text)
                content_elements.append(f"\n{text}\n")

        # Process paragraphs
        for p in main_content.find_all('p'):
            text = self.extract_text_content(p)
            if text:
                content_elements.append(text)
        
        # Process lists
        for lst in main_content.find_all(['ul', 'ol']):
            text = self.extract_text_content(lst)
            if text:
                content_elements.append(text)

        # Process tables
        for table in main_content.find_all('table'):
            text = self.extract_text_content(table)
            if text:
                content_elements.append(text)

        # Process blockquotes
        for quote in main_content.find_all('blockquote'):
            text = self.extract_text_content(quote)
            if text:
                content_elements.append(f"> {text}")

        # Process images and their captions
        for img_container in main_content.find_all('div', class_='nist-image'):
            img = img_container.find('img')
            if img:
                alt_text = img.get('alt', '')
                if alt_text:
                    content_elements.append(f"[Image: {alt_text}]")
                
                credit_div = img_container.find('div', class_='nist-image__credit')
                if credit_div:
                    credit = credit_div.get_text(strip=True)
                    content_elements.append(f"[Image Credit: {credit}]")

        content['content'] = '\n\n'.join(content_elements)

        # Get all links from the content
        links = main_content.find_all('a')
        content['links'] = [
            {
                'text': link.get_text(strip=True),
                'href': urljoin(self.base_url, link.get('href', ''))
            }
            for link in links
            if link.get('href') and link.get_text(strip=True)
        ]

        return content

    def scrape_all(self):
        """Scrape all NIST AISI content"""
        print("Starting NIST AISI scrape...")
        self.data['home'] = self.scrape_home_page()
        self.data['strategic_vision'] = self.scrape_strategic_vision()
        self.data['guidance'] = self.scrape_guidance()
        self.data['consortium'] = self.scrape_consortium()
        self.data['consortium_members'] = self.scrape_consortium_members()
        self.data['member_perspectives'] = self.scrape_member_perspectives()
        self.data['working_groups'] = self.scrape_working_groups()
        self.data['faqs'] = self.scrape_faqs()
        self.data['ai_engagement'] = self.scrape_ai_engagement()
        self.data['related_links'] = self.scrape_related_links()
        self.scrape_blog_posts()  # This is a no-op for now
        self.save_to_json()

class CanadianAisiScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://ised-isde.canada.ca")
        # Additional data structure for Canadian AISI content
        self.data.update({
            'ised_aisi': None,  # Main AISI page
            'cifar_ai_safety': None,  # CIFAR AI Safety Program
            'cifar_news': [],  # CIFAR news articles
            'ised_inoai': None,  # International Network of AI Safety Institutes
            'ised_strategy': None,  # AI Strategy
            'ised_aida': None,  # AI and Data Act
            'ised_code': None,  # Voluntary Code of Conduct
            'cse_guidelines': None,  # CSE AI Security Guidelines
        })
        # Longer delay for government sites
        self.request_delay = 1.0  # 1 second delay

    def is_blog_post_url(self, url):
        """Check if URL is a news/article URL"""
        return 'cifar.ca/cifarnews' in url

    def scrape_ised_page(self, url, key):
        """Generic scraper for ISED pages"""
        print(f"Scraping ISED page: {url}")
        soup = self.get_page(url)
        if not soup:
            return None

        content = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'links': []
        }

        # Get main content area - try different possible content containers
        main_content = None
        
        # First try the main content area
        main_content = soup.find('div', {'id': 'wb-main'})
        if main_content:
            # Look for the actual content within the main area
            content_area = (
                main_content.find('div', {'id': 'wb-cont'}) or
                main_content.find('div', {'role': 'main'}) or
                main_content.find('div', {'class': 'container'})
            )
            if content_area:
                main_content = content_area

        # If that fails, try other common containers
        if not main_content or not main_content.get_text(strip=True):
            for selector in [
                ('main', {'role': 'main'}),
                ('div', {'class': 'mwsgeneric-base-html'}),
                ('article', {}),
                ('div', {'class': 'field-item'}),
                ('div', {'class': 'field-items'}),
                ('div', {'property': 'content:encoded'}),
                ('div', {'class': 'content'})
            ]:
                main_content = soup.find(selector[0], selector[1])
                if main_content and main_content.get_text(strip=True):
                    break

        if not main_content:
            return content

        # Get headings - exclude navigation headings
        skip_heading_classes = ['wb-inv', 'wb-hide']
        headings = []
        for h in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if not h.get('class') or not any(cls in str(h.get('class')) for cls in skip_heading_classes):
                text = h.get_text(strip=True)
                if text and text not in ['Language selection', 'WxT Search form']:
                    headings.append(text)
        content['headings'] = headings

        # Get content elements
        content_elements = []
        
        # Try to find the main content container
        content_container = None
        for selector in [
            ('div', {'class': 'mwsbodytext'}),
            ('div', {'class': 'mwsgeneric-base-html'}),
            ('div', {'class': 'field-item'}),
            ('div', {'class': 'field-items'}),
            ('div', {'property': 'content:encoded'}),
            ('div', {'class': 'content'})
        ]:
            content_container = main_content.find(selector[0], selector[1])
            if content_container and content_container.get_text(strip=True):
                break

        if not content_container:
            content_container = main_content

        # Skip these sections entirely
        skip_sections = [
            'wb-sec',      # Secondary menu
            'wb-share',    # Share buttons
            'pagedetails', # Page details
            'datemod',     # Date modified
            'defeatured',  # Featured content
            'gcweb-menu',  # Menu
            'wb-inv',      # Invisible elements
            'wb-hide',     # Hidden elements
            'wb-srch',     # Search
            'wb-lng',      # Language selection
            'wb-info'      # Site information
        ]

        # Remove unwanted sections before processing
        for section in skip_sections:
            for element in content_container.find_all(class_=section):
                element.decompose()

        # Process remaining content
        for element in content_container.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table', 'div']):
            # Skip empty elements
            if not element.get_text(strip=True):
                continue

            # Skip navigation and utility elements
            if element.get('class'):
                if any(cls in str(element.get('class')) for cls in skip_sections):
                    continue
                if any(cls in str(element.get('class')) for cls in ['breadcrumb', 'header', 'footer', 'nav', 'banner']):
                    continue

            # For divs, only include those with direct text or meaningful content
            if element.name == 'div':
                has_content = False
                # Check for direct text content
                direct_text = ''.join(str(c) for c in element.children if isinstance(c, NavigableString)).strip()
                if direct_text:
                    has_content = True
                # Check for meaningful child elements
                if any(child.name in ['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table'] for child in element.children):
                    has_content = True
                if not has_content:
                    continue

            text = self.extract_text_content(element)
            if text and text.strip():
                content_elements.append(text.strip())

        content['content'] = '\n\n'.join(filter(None, content_elements))

        # Get links - exclude utility links
        links = []
        for link in main_content.find_all('a'):
            if not link.get('class') or not any(cls in str(link.get('class')) for cls in skip_sections):
                href = link.get('href')
                text = link.get_text(strip=True)
                if href and text and not any(x in text for x in ['/Gouvernement du Canada', 'Françaisfr']):
                    links.append({
                        'text': text,
                        'href': urljoin(url, href)
                    })
        content['links'] = links

        return content

    def scrape_cifar_page(self, url, key):
        """Generic scraper for CIFAR pages"""
        print(f"Scraping CIFAR page: {url}")
        soup = self.get_page(url)
        if not soup:
            return None

        content = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'links': []
        }

        # Get main content area
        main_content = soup.find('main') or soup.find('article')
        if not main_content:
            return content

        # Get headings
        headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        # Get content elements
        content_elements = []
        for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
            text = self.extract_text_content(element)
            if text:
                content_elements.append(text)

        content['content'] = '\n\n'.join(content_elements)

        # Get links
        links = main_content.find_all('a')
        content['links'] = [
            {
                'text': link.get_text(strip=True),
                'href': urljoin(url, link.get('href', ''))
            }
            for link in links
            if link.get('href')
        ]

        return content

    def scrape_cse_page(self, url):
        """Scraper for CSE (cyber.gc.ca) pages"""
        print(f"Scraping CSE page: {url}")
        soup = self.get_page(url)
        if not soup:
            return None

        content = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'links': []
        }

        # Get main content area
        main_content = soup.find('main', {'role': 'main'})
        if not main_content:
            return content

        # Get headings
        headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        # Get content elements
        content_elements = []
        for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
            text = self.extract_text_content(element)
            if text:
                content_elements.append(text)

        content['content'] = '\n\n'.join(content_elements)

        # Get links
        links = main_content.find_all('a')
        content['links'] = [
            {
                'text': link.get_text(strip=True),
                'href': urljoin(url, link.get('href', ''))
            }
            for link in links
            if link.get('href')
        ]

        return content

    def scrape_cifar_news(self):
        """Scrape CIFAR news articles"""
        news_urls = [
            "https://cifar.ca/cifarnews/2024/11/12/government-of-canada-announces-canadian-ai-safety-institute/",
            "https://cifar.ca/cifarnews/2024/12/12/nicolas-papernot-and-catherine-regis-appointed-co-directors-of-the-caisi-research-program-at-cifar/"
        ]

        for url in news_urls:
            article = self.scrape_blog_post(url)
            if article:
                self.data['cifar_news'].append(article)
                time.sleep(self.request_delay)  # Rate limiting

    def scrape_blog_post(self, url):
        """Required by BaseScraper - handles CIFAR news articles"""
        if url in self.scraped_urls:
            return None
        
        if not self.is_blog_post_url(url):
            return None
        
        self.scraped_urls.add(url)
        print(f"Scraping CIFAR news article: {url}")
        soup = self.get_page(url)
        if not soup:
            return None

        article = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'title': '',
            'date': None,
            'content': '',
            'headings': [],
            'links': []
        }

        # Get main content area
        main_content = soup.find('main') or soup.find('article')
        if not main_content:
            return article

        # Get title
        title = main_content.find('h1')
        if title:
            article['title'] = title.get_text(strip=True)

        # Get date
        date_elem = main_content.find('time')
        if date_elem:
            article['date'] = date_elem.get('datetime')

        # Get headings
        headings = main_content.find_all(['h2', 'h3', 'h4', 'h5', 'h6'])
        article['headings'] = [h.get_text(strip=True) for h in headings]

        # Get content elements
        content_elements = []
        for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
            text = self.extract_text_content(element)
            if text:
                content_elements.append(text)

        article['content'] = '\n\n'.join(content_elements)

        # Get links
        links = main_content.find_all('a')
        article['links'] = [
            {
                'text': link.get_text(strip=True),
                'href': urljoin(url, link.get('href', ''))
            }
            for link in links
            if link.get('href')
        ]

        return article

    def scrape_home_page(self):
        """Required by BaseScraper but redirects to ISED AISI page"""
        return self.scrape_ised_page(
            "https://ised-isde.canada.ca/site/ised/en/canadian-artificial-intelligence-safety-institute",
            'home'
        )

    def scrape_about_page(self):
        """Required by BaseScraper but redirects to CIFAR AI Safety Program page"""
        return self.scrape_cifar_page(
            "https://cifar.ca/ai/ai-and-society/ai-safety-program/",
            'about'
        )

    def scrape_blog_posts(self):
        """Required by BaseScraper but redirects to CIFAR news"""
        self.scrape_cifar_news()

    def scrape_all(self):
        """Scrape all Canadian AISI related content"""
        print("Starting Canadian AISI scrape...")
        
        # ISED pages
        self.data['ised_aisi'] = self.scrape_ised_page(
            "https://ised-isde.canada.ca/site/ised/en/canadian-artificial-intelligence-safety-institute",
            'ised_aisi'
        )
        self.data['ised_inoai'] = self.scrape_ised_page(
            "https://ised-isde.canada.ca/site/ised/en/international-network-ai-safety-institutes-mission-statement",
            'ised_inoai'
        )
        self.data['ised_strategy'] = self.scrape_ised_page(
            "https://ised-isde.canada.ca/site/ai-strategy/en",
            'ised_strategy'
        )
        self.data['ised_aida'] = self.scrape_ised_page(
            "https://ised-isde.canada.ca/site/innovation-better-canada/en/artificial-intelligence-and-data-act-aida-companion-document",
            'ised_aida'
        )
        self.data['ised_code'] = self.scrape_ised_page(
            "https://ised-isde.canada.ca/site/ised/en/voluntary-code-conduct-responsible-development-and-management-advanced-generative-ai-systems",
            'ised_code'
        )

        # CIFAR pages
        self.data['cifar_ai_safety'] = self.scrape_cifar_page(
            "https://cifar.ca/ai/ai-and-society/ai-safety-program/",
            'cifar_ai_safety'
        )
        self.scrape_cifar_news()

        # CSE page
        self.data['cse_guidelines'] = self.scrape_cse_page(
            "https://www.cyber.gc.ca/en/news-events/guidelines-secure-ai-system-development"
        )

        self.save_to_json()

class ApolloScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.apolloresearch.ai")
        # Additional data structure for Apollo content
        self.data.update({
            'research': None,  # Research page content
            'research_posts': [],  # Individual research posts
            'blog_posts': []  # Blog posts
        })
        # Use standard delay
        self.request_delay = 1.0  # 1 second delay

    def is_blog_post_url(self, url):
        """Check if URL is a blog or research post URL"""
        if url.rstrip('/') == f"{self.base_url}/blog" or url.rstrip('/') == f"{self.base_url}/research":
            return False
        return '/blog/' in url or '/research/' in url

    def scrape_home_page(self):
        """Scrape the home page content."""
        print("Scraping Apollo home page...")
        soup = self.get_page(self.base_url)
        if not soup:
            return None

        content = {
            'url': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'sections': []
        }

        # Get main content area
        main_content = soup.find('main')
        if not main_content:
            return content

        # Get headings
        headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        # Process content by sections
        sections = main_content.find_all('section')
        for section in sections:
            section_data = {
                'title': '',
                'content': ''
            }

            # Get section title from heading
            heading = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if heading:
                section_data['title'] = heading.get_text(strip=True)

            # Get section content
            content_elements = []
            for element in section.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                text = self.extract_text_content(element)
                if text:
                    content_elements.append(text)

            section_data['content'] = '\n\n'.join(content_elements)
            if section_data['content']:
                content['sections'].append(section_data)

        # Combine all section content for the main content field
        content['content'] = '\n\n'.join(
            f"{section['title']}\n{section['content']}"
            for section in content['sections']
            if section['content']
        )

        return content

    def scrape_about_page(self):
        """Apollo doesn't have a dedicated about page, so we'll return None."""
        return None

    def scrape_research_page(self):
        """Scrape the research page and collect research post links."""
        print("Scraping Apollo research page...")
        research_url = urljoin(self.base_url, '/research')
        soup = self.get_page(research_url)
        if not soup:
            return None

        content = {
            'url': research_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'post_links': []
        }

        # Get main content area
        main_content = soup.find('main')
        if not main_content:
            return content

        # Get headings
        headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        # Get content elements
        content_elements = []
        for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
            text = self.extract_text_content(element)
            if text:
                content_elements.append(text)

        content['content'] = '\n\n'.join(content_elements)

        # Find research post links
        for link in main_content.find_all('a'):
            href = link.get('href')
            if href and '/research/' in href and href != '/research':
                full_url = urljoin(self.base_url, href)
                if full_url not in content['post_links']:
                    content['post_links'].append(full_url)

        return content

    def scrape_blog_posts(self):
        """Scrape all blog posts."""
        print("Scraping Apollo blog posts...")
        blog_url = urljoin(self.base_url, '/blog')
        soup = self.get_page(blog_url)
        if not soup:
            return

        # Find all blog post links
        blog_links = set()
        main_content = soup.find('main')
        if main_content:
            for link in main_content.find_all('a'):
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if '/blog/' in full_url and full_url != blog_url:
                        blog_links.add(full_url)

        # Scrape each blog post
        for url in blog_links:
            post_content = self.scrape_blog_post(url)
            if post_content:
                self.data['blog_posts'].append(post_content)
                time.sleep(self.request_delay)  # Rate limiting

    def scrape_blog_post(self, url):
        """Scrape a single blog or research post."""
        if url in self.scraped_urls:
            return None

        if not self.is_blog_post_url(url):
            return None

        self.scraped_urls.add(url)
        print(f"Scraping Apollo post: {url}")
        soup = self.get_page(url)
        if not soup:
            return None

        post = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'title': '',
            'date': None,
            'author': None,
            'category': None,
            'content': '',
            'headings': [],
            'type': 'blog' if '/blog/' in url else 'research'
        }

        # Get main content area
        main_content = soup.find('main')
        if not main_content:
            return post

        # Get title
        title = main_content.find('h1')
        if title:
            post['title'] = title.get_text(strip=True)

        # Get metadata (date and author)
        meta_section = main_content.find('div', class_='metadata')
        if meta_section:
            # Try to find date
            date_elem = meta_section.find('time') or meta_section.find(class_='date')
            if date_elem:
                post['date'] = date_elem.get_text(strip=True)

            # Try to find author
            author_elem = meta_section.find(class_='author')
            if author_elem:
                post['author'] = author_elem.get_text(strip=True)

        # Get headings
        headings = main_content.find_all(['h2', 'h3', 'h4', 'h5', 'h6'])
        post['headings'] = [h.get_text(strip=True) for h in headings]

        # Get content elements
        content_elements = []
        article = main_content.find('article') or main_content
        for element in article.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
            # Skip metadata section
            if element.find_parent(class_='metadata'):
                continue
            
            text = self.extract_text_content(element)
            if text:
                content_elements.append(text)

        post['content'] = '\n\n'.join(content_elements)
        return post

    def scrape_all(self):
        """Scrape all Apollo content."""
        print("Starting Apollo scrape...")
        
        # Scrape main pages
        self.data['home'] = self.scrape_home_page()
        self.data['research'] = self.scrape_research_page()
        
        # Scrape research posts
        if self.data['research'] and 'post_links' in self.data['research']:
            for url in self.data['research']['post_links']:
                post_content = self.scrape_blog_post(url)
                if post_content:
                    self.data['research_posts'].append(post_content)
                    time.sleep(self.request_delay)  # Rate limiting
        
        # Scrape blog posts
        self.scrape_blog_posts()
        
        self.save_to_json()

class AnthropicScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.anthropic.com")
        self.data['research_posts'] = []
        self.data['news_posts'] = []

    def is_blog_post_url(self, url):
        """Check if the URL is a blog post URL."""
        if not url.startswith(self.base_url):
            return False
        path = url.replace(self.base_url, '').strip('/')
        if path in ['research', 'news']:
            return False
        return path.startswith('research/') or path.startswith('news/')

    def scrape_home_page(self):
        """Scrape the home page content."""
        print("Scraping home page...")
        soup = self.get_page(self.base_url)
        if not soup:
            return None

        content = {
            'url': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        # Get all headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        # Get main content sections
        main_content = soup.find('main')
        if main_content:
            content_elements = []
            for element in main_content.find_all(['p', 'div', 'section']):
                text = self.extract_text_content(element)
                if text and len(text.strip()) > 0:
                    content_elements.append(text)
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_about_page(self):
        """About page doesn't exist."""
        return None

    def scrape_blog_post(self, url):
        """Scrape a single blog/research/news post."""
        if url in self.scraped_urls:
            return None
        
        self.scraped_urls.add(url)
        print(f"Scraping post: {url}")
        
        soup = self.get_page(url)
        if not soup:
            return None

        post_content = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'title': '',
            'date': None,
            'content': '',
            'headings': [],
            'links': []
        }

        # Get title
        title = soup.find(['h1', 'h2'])
        if title:
            post_content['title'] = title.get_text(strip=True)

        # Get date if available
        date_element = soup.find('time')
        if date_element:
            post_content['date'] = date_element.get('datetime', date_element.get_text(strip=True))

        # Get main content
        main_content = soup.find('main')
        if main_content:
            # Get all headings
            headings = main_content.find_all(['h2', 'h3', 'h4', 'h5', 'h6'])
            post_content['headings'] = [h.get_text(strip=True) for h in headings]

            # Get content elements
            content_elements = []
            article = main_content.find('article') or main_content
            
            # Process content sections
            for element in article.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table', 'div']):
                # Skip navigation elements and metadata
                if element.get('role') in ['navigation', 'banner', 'complementary']:
                    continue
                    
                # Skip elements with certain classes
                if element.get('class'):
                    classes = element.get('class')
                    if not isinstance(classes, (list, tuple)):
                        classes = [classes]
                    if any(c in ['nav', 'header', 'footer', 'metadata', 'sidebar'] for c in classes):
                        continue
                
                text = self.extract_text_content(element)
                if text and len(text.strip()) > 0:
                    content_elements.append(text)

            post_content['content'] = '\n\n'.join(content_elements)

            # Get all links
            links = article.find_all('a')
            post_content['links'] = [
                {
                    'text': link.get_text(strip=True),
                    'href': urljoin(self.base_url, link.get('href', ''))
                }
                for link in links if link.get('href')
            ]

        return post_content

    def scrape_research_posts(self):
        """Scrape research posts using hardcoded URLs."""
        print("Scraping research posts...")
        
        research_urls = [
            "https://www.anthropic.com/research/building-effective-agents",
            "https://www.anthropic.com/research/alignment-faking",
            "https://www.anthropic.com/research/clio",
            "https://www.anthropic.com/research/statistical-approach-to-model-evals",
            "https://www.anthropic.com/research/swe-bench-sonnet",
            "https://www.anthropic.com/research/evaluating-feature-steering",
            "https://www.anthropic.com/research/developing-computer-use",
            "https://www.anthropic.com/research/sabotage-evaluations",
            "https://www.anthropic.com/research/features-as-classifiers",
            "https://www.anthropic.com/research/circuits-updates-sept-2024",
            "https://www.anthropic.com/research/circuits-updates-august-2024",
            "https://www.anthropic.com/research/circuits-updates-july-2024",
            "https://www.anthropic.com/research/circuits-updates-june-2024",
            "https://www.anthropic.com/research/reward-tampering",
            "https://www.anthropic.com/research/engineering-challenges-interpretability",
            "https://www.anthropic.com/research/claude-character",
            "https://www.anthropic.com/research/testing-and-mitigating-elections-related-risks",
            "https://www.anthropic.com/research/mapping-mind-language-model",
            "https://www.anthropic.com/research/circuits-updates-april-2024",
            "https://www.anthropic.com/research/probes-catch-sleeper-agents",
            "https://www.anthropic.com/research/measuring-model-persuasiveness",
            "https://www.anthropic.com/research/many-shot-jailbreaking",
            "https://www.anthropic.com/research/transformer-circuits",
            "https://www.anthropic.com/research/sleeper-agents-training-deceptive-llms-that-persist-through-safety-training",
            "https://www.anthropic.com/research/evaluating-and-mitigating-discrimination-in-language-model-decisions",
            "https://www.anthropic.com/research/specific-versus-general-principles-for-constitutional-ai",
            "https://www.anthropic.com/research/towards-understanding-sycophancy-in-language-models",
            "https://www.anthropic.com/research/collective-constitutional-ai-aligning-a-language-model-with-public-input",
            "https://www.anthropic.com/research/decomposing-language-models-into-understandable-components",
            "https://www.anthropic.com/research/towards-monosemanticity-decomposing-language-models-with-dictionary-learning",
            "https://www.anthropic.com/research/evaluating-ai-systems",
            "https://www.anthropic.com/research/influence-functions",
            "https://www.anthropic.com/research/studying-large-language-model-generalization-with-influence-functions",
            "https://www.anthropic.com/research/measuring-faithfulness-in-chain-of-thought-reasoning",
            "https://www.anthropic.com/research/question-decomposition-improves-the-faithfulness-of-model-generated-reasoning",
            "https://www.anthropic.com/research/towards-measuring-the-representation-of-subjective-global-opinions-in-language-models",
            "https://www.anthropic.com/research/circuits-updates-may-2023",
            "https://www.anthropic.com/research/interpretability-dreams",
            "https://www.anthropic.com/research/distributed-representations-composition-superposition",
            "https://www.anthropic.com/research/privileged-bases-in-the-transformer-residual-stream",
            "https://www.anthropic.com/research/the-capacity-for-moral-self-correction-in-large-language-models",
            "https://www.anthropic.com/research/superposition-memorization-and-double-descent",
            "https://www.anthropic.com/research/discovering-language-model-behaviors-with-model-written-evaluations",
            "https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback",
            "https://www.anthropic.com/research/measuring-progress-on-scalable-oversight-for-large-language-models",
            "https://www.anthropic.com/research/toy-models-of-superposition",
            "https://www.anthropic.com/research/red-teaming-language-models-to-reduce-harms-methods-scaling-behaviors-and-lessons-learned",
            "https://www.anthropic.com/research/language-models-mostly-know-what-they-know",
            "https://www.anthropic.com/research/softmax-linear-units",
            "https://www.anthropic.com/research/scaling-laws-and-interpretability-of-learning-from-repeated-data",
            "https://www.anthropic.com/research/training-a-helpful-and-harmless-assistant-with-reinforcement-learning-from-human-feedback",
            "https://www.anthropic.com/research/in-context-learning-and-induction-heads",
            "https://www.anthropic.com/research/predictability-and-surprise-in-large-generative-models",
            "https://www.anthropic.com/research/a-mathematical-framework-for-transformer-circuits",
            "https://www.anthropic.com/research/a-general-language-assistant-as-a-laboratory-for-alignment"
        ]
        
        print(f"Found {len(research_urls)} research posts")
        
        # Scrape each research post
        for url in research_urls:
            post_content = self.scrape_blog_post(url)
            if post_content:
                self.data['research_posts'].append(post_content)
                time.sleep(self.request_delay)  # Rate limiting

    def scrape_news_posts(self):
        """Scrape all news posts."""
        print("Scraping news posts...")
        news_url = urljoin(self.base_url, '/news')
        soup = self.get_page(news_url)
        if not soup:
            return

        main_content = soup.find('main')
        if main_content:
            # Find all news post links
            news_links = set()
            
            # Look for links in article cards or similar containers
            for link in main_content.find_all('a'):
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if full_url.startswith(self.base_url + '/news/') and full_url != news_url:
                        news_links.add(full_url)

            # Scrape each news post
            for url in news_links:
                post_content = self.scrape_blog_post(url)
                if post_content:
                    self.data['news_posts'].append(post_content)
                    time.sleep(self.request_delay)  # Rate limiting

    def scrape_blog_posts(self):
        """Scrape both research and news posts."""
        self.scrape_research_posts()
        self.scrape_news_posts()

    def scrape_all(self):
        """Scrape all content from the website."""
        self.data['home'] = self.scrape_home_page()
        self.scrape_blog_posts()
        self.save_to_json()

class DeepMindScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://deepmind.google")
        # Additional data structure for DeepMind content
        self.data.update({
            'publications': [],  # List of publication entries
            'research_areas': []  # Research areas from publications page
        })

    def is_blog_post_url(self, url):
        """Check if the URL is a publication URL."""
        if not url.startswith(self.base_url):
            return False
        path = url.replace(self.base_url, '').strip('/')
        if path == 'research/publications':
            return False
        return path.startswith('research/publications/')

    def scrape_home_page(self):
        """Scrape the home page content."""
        print("Scraping DeepMind home page...")
        soup = self.get_page(self.base_url)
        if not soup:
            return None

        content = {
            'url': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        # Get all headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content['headings'] = [h.get_text(strip=True) for h in headings]

        # Get main content
        main_content = soup.find('main')
        if main_content:
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table', 'div']):
                # Skip navigation elements
                if element.get('role') in ['navigation', 'banner', 'complementary']:
                    continue
                    
                # Skip elements with certain classes
                if element.get('class'):
                    classes = element.get('class')
                    if not isinstance(classes, (list, tuple)):
                        classes = [classes]
                    if any(c in ['nav', 'header', 'footer', 'metadata', 'sidebar'] for c in classes):
                        continue
                
                text = self.extract_text_content(element)
                if text and len(text.strip()) > 0:
                    content_elements.append(text)

            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_about_page(self):
        """Scrape the about page content."""
        print("Scraping DeepMind about page...")
        about_url = urljoin(self.base_url, '/about')
        soup = self.get_page(about_url)
        if not soup:
            return None

        content = {
            'url': about_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'sections': []
        }

        # Get main content
        main_content = soup.find('main')
        if main_content:
            # Get all headings
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content['headings'] = [h.get_text(strip=True) for h in headings]

            # Process content by sections
            sections = main_content.find_all('section')
            for section in sections:
                section_data = {
                    'title': '',
                    'content': ''
                }

                # Get section title from heading
                heading = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if heading:
                    section_data['title'] = heading.get_text(strip=True)

                # Get section content
                content_elements = []
                for element in section.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                    text = self.extract_text_content(element)
                    if text:
                        content_elements.append(text)

                section_data['content'] = '\n\n'.join(content_elements)
                if section_data['content']:
                    content['sections'].append(section_data)

            # Combine all section content for the main content field
            content['content'] = '\n\n'.join(
                f"{section['title']}\n{section['content']}"
                for section in content['sections']
                if section['content']
            )

        return content

    def scrape_blog_post(self, url):
        """Scrape a single publication."""
        if url in self.scraped_urls:
            return None
        
        if not self.is_blog_post_url(url):
            return None
        
        self.scraped_urls.add(url)
        print(f"Scraping DeepMind publication: {url}")
        soup = self.get_page(url)
        if not soup:
            return None

        publication = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'title': '',
            'date': None,
            'authors': [],
            'abstract': '',
            'content': '',
            'headings': [],
            'links': [],
            'research_areas': [],
            'citation': None,
            'pdf_url': None
        }

        # Get main content
        main_content = soup.find('main')
        if not main_content:
            return publication

        # Get title
        title = main_content.find('h1')
        if title:
            publication['title'] = title.get_text(strip=True)

        # Get date
        date_element = main_content.find('time')
        if date_element:
            publication['date'] = date_element.get('datetime', date_element.get_text(strip=True))

        # Get authors
        authors_section = main_content.find('div', class_=lambda x: x and 'authors' in x.lower())
        if authors_section:
            authors = authors_section.find_all(['span', 'a'])
            publication['authors'] = [author.get_text(strip=True) for author in authors if author.get_text(strip=True)]

        # Get abstract
        abstract_section = main_content.find(['div', 'section'], class_=lambda x: x and 'abstract' in x.lower())
        if abstract_section:
            publication['abstract'] = self.extract_text_content(abstract_section)

        # Get research areas
        areas_section = main_content.find(['div', 'section'], class_=lambda x: x and 'research-areas' in x.lower())
        if areas_section:
            areas = areas_section.find_all(['span', 'a'])
            publication['research_areas'] = [area.get_text(strip=True) for area in areas if area.get_text(strip=True)]

        # Get PDF link
        pdf_link = main_content.find('a', href=lambda x: x and x.endswith('.pdf'))
        if pdf_link:
            publication['pdf_url'] = urljoin(self.base_url, pdf_link['href'])

        # Get citation
        citation_section = main_content.find(['div', 'section'], class_=lambda x: x and 'citation' in x.lower())
        if citation_section:
            publication['citation'] = self.extract_text_content(citation_section)

        # Get headings
        headings = main_content.find_all(['h2', 'h3', 'h4', 'h5', 'h6'])
        publication['headings'] = [h.get_text(strip=True) for h in headings]

        # Get main content
        content_elements = []
        article = main_content.find('article') or main_content
        for element in article.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
            # Skip metadata sections
            if element.find_parent(class_=lambda x: x and any(term in x.lower() for term in [
                'authors', 'abstract', 'citation', 'research-areas', 'metadata'
            ])):
                continue
            
            text = self.extract_text_content(element)
            if text:
                content_elements.append(text)

        publication['content'] = '\n\n'.join(content_elements)

        # Get all links
        links = article.find_all('a')
        publication['links'] = [
            {
                'text': link.get_text(strip=True),
                'href': urljoin(self.base_url, link.get('href', ''))
            }
            for link in links if link.get('href')
        ]

        return publication

    def scrape_publications(self):
        """Scrape all publications from the publications page."""
        print("Scraping DeepMind publications...")
        publications_url = urljoin(self.base_url, '/research/publications/')
        
        # Get all publication links
        publication_links = set()
        page = 1
        while True:
            print(f"Scanning publications page {page}...")
            
            # Construct page URL with DeepMind's pagination format
            page_url = f"{publications_url}?page={page}" if page > 1 else publications_url
            print(f"Fetching {page_url}")
            
            soup = self.get_page(page_url)
            if not soup:
                break

            main_content = soup.find('main')
            if not main_content:
                break

            # Find publication links in article cards
            found_publications = False
            
            # Try multiple ways to find article links
            # 1. Look for article elements
            articles = main_content.find_all('article')
            for article in articles:
                # Try to find the link in the article title
                title_link = article.find('h2').find('a') if article.find('h2') else None
                if title_link and title_link.get('href'):
                    href = title_link.get('href')
                    full_url = urljoin(self.base_url, href)
                    if self.is_blog_post_url(full_url):
                        publication_links.add(full_url)
                        found_publications = True
                        continue

                # If no title link, try any link in the article
                for link in article.find_all('a'):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if self.is_blog_post_url(full_url):
                            publication_links.add(full_url)
                            found_publications = True

            # 2. Look for links in a list/grid of publications
            publication_list = main_content.find('ul', attrs={'data-testid': 'publication-list'})
            if publication_list:
                for link in publication_list.find_all('a'):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if self.is_blog_post_url(full_url):
                            publication_links.add(full_url)
                            found_publications = True

            # 3. Look for any links that match our publication pattern
            for link in main_content.find_all('a', href=True):
                href = link.get('href')
                if href and '/research/publications/' in href and not href.endswith('/publications/'):
                    full_url = urljoin(self.base_url, href)
                    if self.is_blog_post_url(full_url):
                        publication_links.add(full_url)
                        found_publications = True

            print(f"Found {len(publication_links)} publication links so far...")

            # Get research areas if on first page
            if page == 1:
                # Look for research area filters
                filter_section = main_content.find('div', attrs={'data-testid': 'filter-section'})
                if filter_section:
                    area_buttons = filter_section.find_all('button')
                    self.data['research_areas'] = [
                        btn.get_text(strip=True)
                        for btn in area_buttons
                        if btn.get_text(strip=True) and btn.get_text(strip=True).lower() != 'all'
                    ]

            # Look for pagination controls
            pagination = main_content.find('nav', attrs={'aria-label': 'Pagination'})
            if not pagination:
                break

            # Find all page links
            page_links = pagination.find_all('a')
            current_page_found = False
            next_page_exists = False
            
            for link in page_links:
                # Check if this is the current page
                if 'aria-current' in link.attrs:
                    current_page_found = True
                    continue
                
                # If we found current page, next link is the next page
                if current_page_found:
                    href = link.get('href')
                    if href:
                        # Extract page number from href
                        match = re.search(r'page=(\d+)', href)
                        if match:
                            page = int(match.group(1))
                            next_page_exists = True
                            break

            if not next_page_exists:
                break

            time.sleep(self.request_delay)  # Rate limiting

        print(f"Found total of {len(publication_links)} publication links")

        # Scrape each publication
        for url in publication_links:
            publication = self.scrape_blog_post(url)
            if publication:
                self.data['publications'].append(publication)
                time.sleep(self.request_delay)  # Rate limiting

    def scrape_blog_posts(self):
        """Scrape publications instead of blog posts."""
        self.scrape_publications()

    def scrape_all(self):
        """Scrape all content from the website."""
        print("Starting DeepMind scrape...")
        self.data['home'] = self.scrape_home_page()
        self.data['about'] = self.scrape_about_page()
        self.scrape_publications()
        self.save_to_json()

class CSERScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.cser.ac.uk")
        self.data['resources'] = []  # Add resources section for CSER-specific content

    def is_blog_post_url(self, url):
        """Check if the URL is a resource/blog post URL."""
        if not url.startswith(self.base_url):
            return False
        return '/resources/' in url

    def scrape_home_page(self):
        """Scrape the home page content."""
        print("Scraping CSER home page...")
        soup = self.get_page(self.base_url)
        if not soup:
            return None

        content = {
            'url': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        main_content = soup.find('main')
        if main_content:
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content['headings'] = [h.get_text(strip=True) for h in headings]

            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                text = self.extract_text_content(element)
                if text:
                    content_elements.append(text)
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_about_page(self):
        """Scrape the about page content."""
        print("Scraping CSER about page...")
        about_url = urljoin(self.base_url, '/about-us/')
        soup = self.get_page(about_url)
        if not soup:
            return None

        content = {
            'url': about_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        main_content = soup.find('main')
        if main_content:
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content['headings'] = [h.get_text(strip=True) for h in headings]

            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                text = self.extract_text_content(element)
                if text:
                    content_elements.append(text)
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_blog_post(self, url):
        """Scrape a single resource/blog post."""
        if url in self.scraped_urls:
            return None
        
        self.scraped_urls.add(url)
        print(f"Scraping CSER resource: {url}")
        soup = self.get_page(url)
        if not soup:
            return None

        post = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'title': '',
            'date': None,
            'authors': [],
            'content': '',
            'headings': [],
            'links': []
        }

        # Extract title
        title_elem = soup.find(['h1', 'header', 'div'], class_=lambda x: x and ('title' in x.lower() or 'heading' in x.lower()))
        if title_elem:
            post['title'] = title_elem.get_text(strip=True)

        # Extract date
        date_elem = soup.find(['time', 'span', 'div'], class_=lambda x: x and 'date' in x.lower())
        if date_elem:
            post['date'] = date_elem.get_text(strip=True)

        # Extract authors
        author_elems = soup.find_all(['span', 'div', 'p'], class_=lambda x: x and 'author' in x.lower())
        for author in author_elems:
            author_text = author.get_text(strip=True)
            if author_text:
                post['authors'].append(author_text)

        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        if main_content:
            # Extract headings
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            post['headings'] = [h.get_text(strip=True) for h in headings]

            # Extract content
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                text = self.extract_text_content(element)
                if text:
                    content_elements.append(text)
            post['content'] = '\n\n'.join(content_elements)

            # Extract links
            links = main_content.find_all('a')
            post['links'] = [
                {
                    'text': link.get_text(strip=True),
                    'href': urljoin(self.base_url, link.get('href', ''))
                }
                for link in links
                if link.get('href') and link.get_text(strip=True)
            ]

        return post

    def scrape_blog_posts(self):
        """Scrape all specified resource pages."""
        resource_urls = [
            '/research/risks-from-artificial-intelligence/',
            '/resources/ai-governance-displacement-and-defragmentation-international-law/',
            '/resources/aligning-ai-regulation-sociotechnical-change/',
            '/resources/why-and-how-governments-should-monitor-ai-development/',
            '/resources/exploring-ai-safety-degrees-generality-capability-and-control/',
            '/resources/bridging-gap-case-incompletely-theorized-agreement-ai-policy/',
            '/resources/ai-issues-covid/',
            '/resources/fragmentation-and-future-investigating-architectures-international-ai-governance/',
            '/resources/oases-cooperation-empirical-evaluation-reinforcement-learning-iterated-prisoners-dilemma/',
            '/resources/solving-x/',
            '/resources/it-takes-village/',
            '/resources/competition-law-levers/',
            '/resources/safeguarding-safeguards-how-best-promote-ai-alignment-public-interest/'
        ]

        for relative_url in resource_urls:
            url = urljoin(self.base_url, relative_url)
            post = self.scrape_blog_post(url)
            if post:
                self.data['resources'].append(post)

    def scrape_all(self):
        """Scrape all content from the website."""
        self.data['home'] = self.scrape_home_page()
        self.data['about'] = self.scrape_about_page()
        self.scrape_blog_posts()
        self.save_to_json()

class CHAIScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://humancompatible.ai")

    def is_blog_post_url(self, url):
        """Check if the URL is a blog post URL."""
        # CHAI doesn't have a traditional blog, but we'll treat research updates and progress reports as posts
        if not url.startswith(self.base_url):
            return False
        return any(x in url for x in ['/research/', '/progress-report/'])

    def scrape_home_page(self):
        """Scrape the home page content."""
        print("Scraping CHAI home page...")
        soup = self.get_page(self.base_url)
        if not soup:
            return None

        content = {
            'url': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': ''
        }

        # Get main content area
        main_content = soup.find('main')
        if main_content:
            # Extract headings
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content['headings'] = [h.get_text(strip=True) for h in headings]

            # Extract content sections
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                text = self.extract_text_content(element)
                if text:
                    content_elements.append(text)
            
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_about_page(self):
        """Scrape the about page content."""
        print("Scraping CHAI about page...")
        about_url = urljoin(self.base_url, '/about/')
        soup = self.get_page(about_url)
        if not soup:
            return None

        content = {
            'url': about_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'team': []
        }

        main_content = soup.find('main')
        if main_content:
            # Extract headings
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content['headings'] = [h.get_text(strip=True) for h in headings]

            # Extract main content
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                text = self.extract_text_content(element)
                if text:
                    content_elements.append(text)
            
            content['content'] = '\n\n'.join(content_elements)

            # Extract team members if present
            team_section = main_content.find(class_=lambda x: x and 'team' in x.lower())
            if team_section:
                team_members = []
                for member in team_section.find_all(class_=lambda x: x and 'member' in x.lower()):
                    member_data = {
                        'name': '',
                        'role': '',
                        'bio': '',
                        'image_url': ''
                    }
                    
                    name_elem = member.find(['h3', 'h4', 'strong'])
                    if name_elem:
                        member_data['name'] = name_elem.get_text(strip=True)
                    
                    role_elem = member.find(['h4', 'h5', 'em'])
                    if role_elem:
                        member_data['role'] = role_elem.get_text(strip=True)
                    
                    bio_elem = member.find('p')
                    if bio_elem:
                        member_data['bio'] = bio_elem.get_text(strip=True)
                    
                    img = member.find('img')
                    if img and img.get('src'):
                        member_data['image_url'] = urljoin(self.base_url, img['src'])
                    
                    team_members.append(member_data)
                
                content['team'] = team_members

        return content

    def scrape_research_page(self):
        """Scrape the research page content."""
        print("Scraping CHAI research page...")
        research_url = urljoin(self.base_url, '/research')
        soup = self.get_page(research_url)
        if not soup:
            return None

        content = {
            'url': research_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'research_areas': []
        }

        main_content = soup.find('main')
        if main_content:
            # Extract headings
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content['headings'] = [h.get_text(strip=True) for h in headings]

            # Extract research areas
            research_areas = []
            for section in main_content.find_all(['section', 'div']):
                if section.find(['h2', 'h3']):  # Likely a research area section
                    area = {
                        'title': '',
                        'description': '',
                        'papers': []
                    }
                    
                    title_elem = section.find(['h2', 'h3'])
                    if title_elem:
                        area['title'] = title_elem.get_text(strip=True)
                    
                    desc_elem = section.find('p')
                    if desc_elem:
                        area['description'] = self.extract_text_content(desc_elem)
                    
                    # Extract related papers/links
                    papers = []
                    for paper_elem in section.find_all('a'):
                        if paper_elem.get('href'):
                            papers.append({
                                'title': paper_elem.get_text(strip=True),
                                'url': urljoin(self.base_url, paper_elem['href'])
                            })
                    area['papers'] = papers
                    
                    research_areas.append(area)
            
            content['research_areas'] = research_areas

            # Extract general content
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                if not any(area['title'] in element.get_text() for area in research_areas):
                    text = self.extract_text_content(element)
                    if text:
                        content_elements.append(text)
            
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_progress_report(self):
        """Scrape the progress report page."""
        print("Scraping CHAI progress report...")
        report_url = urljoin(self.base_url, '/progress-report/')
        soup = self.get_page(report_url)
        if not soup:
            return None

        content = {
            'url': report_url,
            'timestamp': datetime.now().isoformat(),
            'headings': [],
            'content': '',
            'highlights': []
        }

        main_content = soup.find('main')
        if main_content:
            # Extract headings
            headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content['headings'] = [h.get_text(strip=True) for h in headings]

            # Extract highlights/key achievements
            highlights_section = main_content.find(lambda tag: tag.name in ['section', 'div'] and 
                                                 any(x in tag.get_text().lower() for x in ['highlight', 'achievement', 'progress']))
            if highlights_section:
                for item in highlights_section.find_all(['li', 'article']):
                    highlight = {
                        'title': '',
                        'description': '',
                        'date': None
                    }
                    
                    title_elem = item.find(['h3', 'h4', 'strong'])
                    if title_elem:
                        highlight['title'] = title_elem.get_text(strip=True)
                    
                    desc_elem = item.find('p')
                    if desc_elem:
                        highlight['description'] = self.extract_text_content(desc_elem)
                    
                    # Try to extract date if present
                    date_elem = item.find(string=re.compile(r'\d{4}'))
                    if date_elem:
                        highlight['date'] = date_elem.strip()
                    
                    content['highlights'].append(highlight)

            # Extract general content
            content_elements = []
            for element in main_content.find_all(['p', 'ul', 'ol', 'blockquote', 'pre', 'code', 'table']):
                text = self.extract_text_content(element)
                if text:
                    content_elements.append(text)
            
            content['content'] = '\n\n'.join(content_elements)

        return content

    def scrape_blog_post(self, url):
        """Treat research updates and progress reports as blog posts."""
        if url in self.scraped_urls:
            return None
        
        self.scraped_urls.add(url)
        print(f"Scraping CHAI content: {url}")
        
        if 'research' in url:
            return self.scrape_research_page()
        elif 'progress-report' in url:
            return self.scrape_progress_report()
        return None

    def scrape_blog_posts(self):
        """Scrape research and progress report pages as blog posts."""
        research_url = urljoin(self.base_url, '/research')
        progress_url = urljoin(self.base_url, '/progress-report/')
        
        research_content = self.scrape_blog_post(research_url)
        if research_content:
            self.data['blog_posts'].append(research_content)
        
        progress_content = self.scrape_blog_post(progress_url)
        if progress_content:
            self.data['blog_posts'].append(progress_content)

    def scrape_all(self):
        """Scrape all content from the CHAI website."""
        print("Starting CHAI website scraping...")
        self.data['home'] = self.scrape_home_page()
        self.data['about'] = self.scrape_about_page()
        self.scrape_blog_posts()
        self.save_to_json()
        print("Finished scraping CHAI website.")

def create_scraper(website_url):
    """Factory function to create the appropriate scraper based on the website URL."""
    if 'metr.org' in website_url:
        return MetrScraper()
    elif 'aisi.gov.uk' in website_url:
        return AisiScraper()
    elif 'lakera.ai' in website_url:
        return LakeraScraper()
    elif 'nist.gov/aisi' in website_url:
        return NistAisiScraper()
    elif 'ised-isde.canada.ca' in website_url:
        return CanadianAisiScraper()
    elif 'apolloresearch.ai' in website_url:
        return ApolloScraper()
    elif 'anthropic.com' in website_url:
        return AnthropicScraper()
    elif 'deepmind.google' in website_url:
        return DeepMindScraper()
    elif 'cser.ac.uk' in website_url:
        return CSERScraper()
    elif 'humancompatible.ai' in website_url:
        return CHAIScraper()
    else:
        raise ValueError(f"No scraper available for {website_url}")

# Example usage:
if __name__ == "__main__":
    import sys
    
    # Default websites to scrape if no argument is provided
    websites = [
        "https://metr.org",
        "https://www.aisi.gov.uk",
        "https://www.lakera.ai",
        "https://www.nist.gov/aisi",
        "https://ised-isde.canada.ca/site/ised/en/canadian-artificial-intelligence-safety-institute",
        "https://www.apolloresearch.ai",
        "https://www.anthropic.com",
        "https://deepmind.google",
        "https://www.cser.ac.uk",
        "https://humancompatible.ai"
    ]
    
    # If a website is specified as command line argument, only scrape that one
    if len(sys.argv) > 1:
        website = sys.argv[1].lower()
        if "metr" in website:
            websites = ["https://metr.org"]
        elif "aisi" in website and "nist" not in website and "canada" not in website:
            websites = ["https://www.aisi.gov.uk"]
        elif "lakera" in website:
            websites = ["https://www.lakera.ai"]
        elif "nist" in website:
            websites = ["https://www.nist.gov/aisi"]
        elif "canada" in website or "ised" in website:
            websites = ["https://ised-isde.canada.ca/site/ised/en/canadian-artificial-intelligence-safety-institute"]
        elif "apollo" in website:
            websites = ["https://www.apolloresearch.ai"]
        elif "anthropic" in website:
            websites = ["https://www.anthropic.com"]
        elif "deepmind" in website:
            websites = ["https://deepmind.google"]
        elif "cser" in website:
            websites = ["https://www.cser.ac.uk"]
        elif "chai" in website:
            websites = ["https://humancompatible.ai"]
        else:
            print(f"Unsupported website: {website}")
            print("Supported websites: metr.org, aisi.gov.uk, lakera.ai, nist.gov/aisi, ised-isde.canada.ca, apolloresearch.ai, anthropic.com, deepmind.google, cser.ac.uk, humancompatible.ai")
            sys.exit(1)
    
    for website in websites:
        try:
            print(f"\nScraping {website}...")
            scraper = create_scraper(website)
            scraper.scrape_all()
            print(f"Finished scraping {website}")
        except Exception as e:
            print(f"Error scraping {website}: {e}")
