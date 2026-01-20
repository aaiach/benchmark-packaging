# Product Scraper

A scalable Python scraper that discovers and extracts detailed product information for any product category using LLM-powered research and web scraping.

## Features

- **LLM-Powered Product Discovery**: Uses OpenAI GPT-4o to find the most popular products in any category
- **Intelligent Web Scraping**: Leverages Firecrawl to extract product details including:
  - Pricing
  - Product descriptions
  - Images
  - Availability
  - Reviews (when available)
  - Additional metadata
- **Representative Sampling**: Automatically selects products across different:
  - Price segments (budget to premium)
  - Distribution types (mass market to regional)
  - Value propositions
  - Target audiences
- **Multiple Export Formats**: Saves results as JSON and CSV for easy analysis
- **Scalable**: Works with any product category in any country

## Setup

1. Ensure you have the required API keys in your `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

2. Install dependencies:
```bash
uv sync
```

## Usage

### Basic Usage

Discover and scrape products for a category:

```bash
uv run python main.py "lait d'avoine"
```

### Advanced Options

```bash
# Specify country and language
uv run python main.py "oat milk" --country usa --language en

# Change number of products to discover
uv run python main.py "lait d'avoine" --count 50

# Only discover products without scraping
uv run python main.py "lait d'avoine" --no-scrape

# Specify custom output directory
uv run python main.py "lait d'avoine" --output-dir my_results
```

### Command-Line Arguments

- `category` (required): Product category to search
- `--country`: Target country (default: france)
- `--count`: Number of products to discover (default: 30)
- `--language`: Language for queries (default: fr)
- `--no-scrape`: Only discover products, skip scraping
- `--output-dir`: Output directory for results (default: output)

## Output

The scraper creates three files in the output directory:

1. **`{category}_discovered_{timestamp}.json`**: Raw discovered products from LLM
2. **`{category}_scraped_{timestamp}.json`**: Complete product data after scraping
3. **`{category}_results_{timestamp}.csv`**: Easy-to-read CSV format

### Output Structure

Each product includes:
- Brand name
- Full product name
- Category
- Target audience
- Official product URL
- Price
- Description
- Images
- Availability
- Price segment (budget/mid-range/premium)
- Distribution type
- Value proposition

## Example

```bash
uv run python main.py "lait d'avoine"
```

This will:
1. Query OpenAI to find 30 popular oat milk brands sold in France
2. Get official product URLs from e-commerce sites
3. Scrape each product page for detailed information
4. Generate JSON and CSV reports

## Architecture

```
src/
├── models.py              # Product data model
├── product_discovery.py   # LLM-based product research
└── scraper.py            # Web scraping with Firecrawl
main.py                   # Main orchestration script
```

## Requirements

- Python 3.8+
- OpenAI API key (for GPT-4o with search)
- Firecrawl API key (for web scraping)

## Notes

- The LLM automatically searches the web for current product information
- Scraping respects website terms of service through Firecrawl
- Results are timestamped to avoid overwriting previous runs
- Failed scrapes are handled gracefully and don't stop the entire process
