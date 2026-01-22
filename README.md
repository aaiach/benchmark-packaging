# Lead Generation Platform

A comprehensive lead generation platform combining AI-powered product analysis with an interactive web interface.

## Project Structure

```
├── analysis_engine/     # Python backend - LLM-powered product analysis
├── web_app/             # React frontend (coming soon)
├── docker-compose.yml   # Docker orchestration (coming soon)
└── README.md            # This file
```

## Components

### Analysis Engine (`analysis_engine/`)

Python-based backend that handles:
- **Product Discovery**: LLM-powered brand and product research using Gemini + Google Search
- **Product Details**: Detailed information extraction using OpenAI + Web Search
- **Web Scraping**: Automated data collection via Firecrawl
- **Image Analysis**: Visual hierarchy and eye-tracking analysis using Gemini Vision
- **Competitive Analysis**: PODs/POPs extraction for BCG-style presentations

See [analysis_engine/README.md](./analysis_engine/README.md) for setup and usage.

### Web App (`web_app/`) - Coming Soon

React-based frontend for:
- Interactive dashboards
- Visual analysis visualization
- Competitive landscape exploration
- Report generation

## Quick Start

### Analysis Engine

```bash
cd analysis_engine
uv sync
uv run python main.py "your product category" --steps 1-7
```

## Requirements

- **Analysis Engine**: Python 3.9+, OpenAI API key, Google API key, Firecrawl API key
- **Web App**: Node.js 18+ (coming soon)
- **Docker**: Docker & Docker Compose (coming soon)

## License

Proprietary - All rights reserved
