# Analysis Engine

LLM-powered product analysis engine that discovers, scrapes, and analyzes products using multiple AI models.

## Features

- **Multi-LLM Pipeline**: Orchestrates multiple AI models for different tasks
  - Gemini + Google Search for brand discovery
  - OpenAI + Web Search for product details
  - Gemini Vision for visual analysis and heatmap generation
- **Visual Analysis**: Eye-tracking simulation and visual hierarchy analysis
- **Competitive Intelligence**: PODs/POPs extraction for BCG-style presentations
- **Intelligent Web Scraping**: Leverages Firecrawl for data extraction
- **Flexible Pipeline**: Run specific steps or resume from previous runs

## Setup

1. Create a `.env` file in this directory with your API keys:

```env
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

2. Install dependencies:

```bash
cd analysis_engine
uv sync
```

## Usage

### Basic Usage

Run the complete pipeline:

```bash
uv run python main.py "lait d'avoine" --steps 1-7
```

### Pipeline Steps

| Step | Name | Description |
|------|------|-------------|
| 1 | Discovery | Brand discovery with Gemini + Google Search |
| 2 | Details | Product details with OpenAI + Web Search |
| 3 | Scraping | Web scraping via Firecrawl |
| 4 | Images | Image selection and download |
| 5 | Visual | Visual hierarchy analysis |
| 6 | Heatmaps | Eye-tracking heatmap generation |
| 7 | Competitive | PODs/POPs competitive analysis |

### Advanced Options

```bash
# Run specific steps
uv run python main.py "lait d'avoine" --steps 1-5

# Resume from existing run
uv run python main.py --run-id 20260120_184854 --steps 6-7

# List available runs
uv run python main.py --list-runs

# Check run status
uv run python main.py --run-id 20260120_184854 --status

# Customize discovery
uv run python main.py "oat milk" --country USA --count 50
```

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `category` | Product category to search | Required for new runs |
| `--steps` | Steps to execute (e.g., "1-4", "3", "2-3,5") | 1-7 |
| `--run-id` | Resume from existing run ID | None |
| `--country` | Target country | France |
| `--count` | Number of products to discover | 30 |
| `--output-dir` | Output directory | output |
| `--list-runs` | List all available runs | - |
| `--list-steps` | List all pipeline steps | - |
| `--status` | Show run status (requires --run-id) | - |

## Output

Results are saved in the `output/` directory:

```
output/
├── {category}_discovered_{timestamp}.json    # Brand discovery results
├── {category}_details_{timestamp}.json       # Product details
├── analysis/
│   ├── {category}_visual_analysis_{timestamp}.json
│   └── {category}_competitive_analysis_{timestamp}.json
└── images/
    └── {category}_{timestamp}/
        ├── {brand}_{hash}.{ext}              # Product images
        └── heatmaps/
            └── {brand}_{hash}_heatmap.{ext}  # Visual heatmaps
```

## Architecture

```
analysis_engine/
├── main.py                           # CLI entry point
├── generate_golden_rules_standalone.py # Golden Rules report generator
├── pyproject.toml                     # Dependencies
└── src/
    ├── config.py                      # Configuration management
    ├── models.py                      # Pydantic data models
    ├── golden_rules_generator.py      # Phase 1.4: Golden Rules analysis
    ├── pipeline/                      # Pipeline orchestration
    │   ├── base.py                    # Base pipeline classes
    │   └── steps.py                   # Step implementations
    ├── product_discovery.py           # Gemini brand discovery
    ├── scraper.py                     # Firecrawl web scraping
    ├── image_selector.py              # Image selection & download
    ├── visual_analyzer.py             # Gemini Vision analysis
    ├── competitive_analyzer.py        # PODs/POPs extraction
    └── prompts/                       # LLM prompt templates
```

## Golden Rules Report Generator (Phase 1.4)

After completing the competitive analysis pipeline (steps 1-7), generate a comprehensive "Golden Rules" report that synthesizes findings into actionable insights:

```bash
# Generate Golden Rules report from analysis data
python3 generate_golden_rules_standalone.py --category lait_davoine --run-id 20260120_184854

# Generate as JSON
python3 generate_golden_rules_standalone.py --category lait_davoine --run-id 20260120_184854 --format json

# Save to file
python3 generate_golden_rules_standalone.py --category lait_davoine --run-id 20260120_184854 --output reports/golden_rules.md

# List available runs
python3 generate_golden_rules_standalone.py --list-runs
```

### Report Contents

The Golden Rules report synthesizes competitive intelligence to identify:

1. **Market Patterns**:
   - Recurring keywords and messaging themes
   - Color codes and visual conventions
   - Text structure and information hierarchy patterns
   - Trust marks and certification usage

2. **Market Gaps (Blue Ocean Opportunities)**:
   - Under-represented positioning axes
   - Unused color palettes
   - Rare claim types
   - Differentiation opportunities

3. **Strategic Recommendations**:
   - What to ADOPT (market standards >60% adoption)
   - What to DISRUPT (high-potential gaps)
   - Brand-specific positioning guidelines

### Output Formats

- **Markdown** (default): Human-readable report with tables and structure
- **JSON**: Structured data for programmatic access
- **HTML**: Styled web page with visual formatting

## Requirements

- Python 3.9+
- API Keys:
  - OpenAI (GPT-5 for product details and image selection)
  - Google (Gemini for discovery and visual analysis)
  - Firecrawl (for web scraping)
