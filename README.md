# AI Safety Scraper

A comprehensive Python package for scraping and analyzing AI safety related content from various sources including Anthropic, DeepMind, CSER, CHAI, and other leading AI safety organizations.

## Features

- **Multi-Source Scraping**: Built-in scrapers for multiple AI safety organizations:
  - Anthropic
  - DeepMind/Google
  - CSER (Centre for the Study of Existential Risk)
  - CHAI (Center for Human-Compatible AI)
  - Apollo Research
  - AISI (AI Safety Institute)
  - Lakera
  - NIST
  - Canadian AISI
  - METR

- **Content Types**:
  - Blog posts and research articles
  - About pages and organizational information
  - Publications and academic work
  - News and updates
  - Team and consortium member information

- **Data Processing**:
  - JSON data filtering based on dates and content
  - Large JSON file splitting for easier handling
  - Text content extraction with link preservation
  - Structured data output in JSON format

## Installation

```bash
pip install -e .
```

## Usage

### Basic Scraping

```python
from ai_safety_scraper import create_scraper

# Create a scraper for a specific organization
scraper = create_scraper("https://www.anthropic.com")

# Scrape all content
scraper.scrape_all()

# Save the results
scraper.save_to_json("anthropic_data.json")
```

### Data Filtering

```python
from ai_safety_scraper import filter_json

# Filter scraped data (e.g., by date or content)
filter_json(source='anthropic')  # Creates a filtered JSON file
```

### JSON File Management

```python
from ai_safety_scraper import split_json_file

# Split large JSON files into manageable parts
split_json_file("large_data.json", num_parts=5)
```

## Data Storage

All scraped and processed data is stored in the `data/` directory, including:
- Raw scraped data (JSON)
- Filtered data
- Split JSON files
- HTML and text content

## Requirements

See `requirements.txt` for package dependencies. Main dependencies include:
- requests
- beautifulsoup4
- json
- datetime

## Ethical Considerations

This scraper:
- Implements rate limiting to be respectful to servers
- Uses proper user agent headers
- Follows robots.txt guidelines
- Is intended for research and analysis purposes only

## Contributing

Contributions are welcome! Please feel free to submit pull requests for:
- Adding new organization scrapers
- Improving existing scrapers
- Adding new filtering capabilities
- Enhancing documentation 