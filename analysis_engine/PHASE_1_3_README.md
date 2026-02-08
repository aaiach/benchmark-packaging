# Phase 1.3 — Review-Packaging Cross-Reference Analysis

This module correlates packaging design elements with customer satisfaction signals from reviews to identify which design attributes drive higher customer satisfaction.

## Overview

The review-packaging correlation analysis system consists of three main components:

1. **Review Scraping** - Fetch customer reviews from various sources
2. **Review Analysis** - NLP-based sentiment and topic extraction
3. **Correlation Engine** - Statistical analysis linking packaging attributes with satisfaction

## Architecture

```
src/
├── review_scraper.py        # Review collection from web sources
├── review_analyzer.py        # NLP sentiment & topic extraction
├── correlation_engine.py     # Statistical correlation analysis
├── visualization.py          # Report generation and visualization
└── pipeline/
    └── steps.py             # Pipeline step 8: Review correlation
```

## Features

### 1. Review Scraping (`review_scraper.py`)

- **Multi-source support**: Amazon, retailer websites, web search
- **Smart extraction**: Uses LLM to extract structured review data
- **Rate limiting**: Built-in delays to respect API limits
- **Filtering**: Minimum length requirements, verified purchases

### 2. Review Analysis (`review_analyzer.py`)

- **Sentiment Analysis**: Transformer-based (DistilBERT) sentiment classification
  - Sentence-level analysis aggregated to review level
  - Score range: -1 (very negative) to +1 (very positive)
  - Confidence scoring

- **Topic Extraction**: Identifies packaging-related topics:
  - Design & aesthetics
  - Readability & legibility
  - Claims believability
  - Shelf appeal
  - Color palette
  - Typography
  - Trust marks/certifications
  - Overall appearance

- **Context-aware**: Topic sentiment is analyzed separately from overall sentiment

### 3. Correlation Engine (`correlation_engine.py`)

- **Statistical Tests**:
  - Pearson correlation for numerical attributes
  - t-tests for categorical attributes
  - Significance testing (p < 0.05)

- **Packaging Attributes Analyzed**:
  - Color count and harmony
  - Surface finish (matte, gloss, etc.)
  - Typography consistency
  - Number of claims
  - Trust mark count
  - Hierarchy clarity
  - Visual balance

- **Output**:
  - Ranked list of attributes by customer impact
  - Topic-sentiment correlations
  - Per-product insights
  - Strategic findings

### 4. Visualization (`visualization.py`)

- **Markdown Report**: Comprehensive analysis report with tables
- **JSON Summary**: API-friendly concise summary
- **CSV Export**: Attribute rankings for further analysis

## Usage

### As Pipeline Step

```bash
# Run complete pipeline including review correlation
cd analysis_engine
uv run python main.py "lait d'avoine" --steps 1-8

# Run only review correlation (requires steps 1-5 complete)
uv run python main.py --run-id EXISTING_RUN_ID --steps 8
```

### Standalone Testing

```bash
# Test with sample data
cd analysis_engine
python3 test_review_correlation.py
```

## Output Format

The correlation analysis produces a JSON file with this structure:

```json
{
  "category": "Oat Milk",
  "analysis_date": "2026-02-08T...",
  "total_reviews": 150,
  "packaging_focused_reviews": 45,
  "products_analyzed": 5,
  "attribute_rankings": [
    {
      "rank": 1,
      "attribute": {
        "attribute_category": "surface_finish",
        "attribute_value": "matte finish",
        "correlation_score": 0.78,
        "statistical_significance": 0.002,
        "average_sentiment": 0.65,
        "sample_size": 3,
        "impact_category": "strong_positive"
      },
      "supporting_evidence": [...]
    }
  ],
  "topic_correlations": [...],
  "product_insights": [...],
  "key_findings": [...],
  "executive_summary": "..."
}
```

## Data Models

Key Pydantic models (see `src/models.py`):

- `ReviewAnalysis`: Complete review with sentiment and topics
- `ReviewSentiment`: Sentiment score and confidence
- `PackagingTopic`: Topic mention with sentiment
- `PackagingAttributeCorrelation`: Correlation coefficient and significance
- `AttributeRanking`: Ranked attribute with evidence
- `ReviewPackagingCorrelationResult`: Complete analysis output

## Dependencies

Core NLP and statistical libraries:

```
transformers==4.48.0        # Transformer models (DistilBERT)
torch==2.5.1                # PyTorch backend
nltk==3.9.1                 # Natural language toolkit
scikit-learn==1.6.1         # Machine learning utilities
scipy==1.15.0               # Statistical tests
pandas==2.2.3               # Data processing
numpy==2.1.3                # Numerical computing
```

## Statistical Methodology

### Correlation Analysis

1. **Numerical Attributes** (e.g., number of colors, trust marks):
   - Pearson correlation coefficient
   - Tests linear relationship with sentiment
   - Significance via p-value

2. **Categorical Attributes** (e.g., surface finish, color harmony):
   - Independent samples t-test
   - Compares sentiment between groups
   - Effect size via Cohen's d (normalized to [-1, 1])

3. **Impact Categorization**:
   - Strong positive: r > 0.5, p < 0.05
   - Positive: r > 0.2, p < 0.05
   - Neutral: |r| ≤ 0.2 or p ≥ 0.05
   - Negative: r < -0.2, p < 0.05
   - Strong negative: r < -0.5, p < 0.05

### Sample Size Requirements

- Minimum 3 products for correlation analysis
- Bootstrapping for small samples (future enhancement)
- Cross-validation for model validation (future enhancement)

## Key Findings Example

From test data, typical findings include:

1. **Matte finish** shows strong positive correlation (r=0.78) with customer satisfaction
2. Reviews mentioning "design" show 0.35 higher sentiment on average
3. Products with 4+ trust marks achieve highest satisfaction scores
4. High packaging mention rate (>30%) correlates with better sentiment

## Integration with Existing Pipeline

Step 8 integrates seamlessly with the existing analysis pipeline:

- **Depends on**:
  - Step 2: Product details (brands, URLs)
  - Step 5: Visual analysis (packaging attributes)

- **Provides**:
  - Statistical validation of design choices
  - Customer-validated attribute rankings
  - Actionable insights for packaging optimization

## Future Enhancements

1. **Multi-language support**: Analyze reviews in French, Dutch
2. **Image-text matching**: Link review mentions to specific visual elements
3. **Temporal analysis**: Track sentiment trends over time
4. **Competitive benchmarking**: Compare attribute effectiveness across brands
5. **A/B testing predictions**: Predict satisfaction for new designs
6. **Advanced NLP**: Use GPT-4 for deeper semantic analysis

## Example Use Case: Recolt (Quinoat)

For the Recolt oat milk packaging project:

1. **Scrape reviews** for Alpro, Oatly, Bjorg, Roa Ra, Hély
2. **Extract packaging topics**: Design, readability, trust marks
3. **Correlate with attributes**: Color palette, matte finish, certifications
4. **Identify winners**: Which attributes drive satisfaction in Belgian market?
5. **Apply to concepts**: Use insights to optimize 50 generated prototypes

## Testing

Run the comprehensive test suite:

```bash
cd analysis_engine
python3 test_review_correlation.py
```

This generates:
- `output/test_correlation/correlation_result.json` - Full results
- `output/test_correlation/correlation_report.md` - Markdown report
- `output/test_correlation/correlation_summary.json` - API summary
- `output/test_correlation/attribute_rankings.csv` - CSV export

## Troubleshooting

### Common Issues

1. **"Not enough products for correlation"**
   - Need at least 3 products with both reviews and packaging analysis
   - Run steps 1-5 first to gather sufficient data

2. **"Firecrawl not configured"**
   - Add `FIRECRAWL_API_KEY` to `.env` file
   - Alternative: Use OpenAI web search fallback

3. **"Transformer model download failed"**
   - Models download automatically on first run (~500MB)
   - Ensure internet connection and disk space
   - Pre-download: `python3 -c "from transformers import pipeline; pipeline('sentiment-analysis')"`

4. **Low correlation significance**
   - Small sample size may reduce statistical power
   - Collect more reviews per product (target 50+)
   - Ensure variety in packaging attributes

## Performance

- **Review scraping**: ~2-5s per product (API-dependent)
- **Sentiment analysis**: ~0.1s per review (GPU) / ~0.5s (CPU)
- **Correlation analysis**: <1s for typical dataset
- **Full pipeline** (30 reviews × 5 products): ~5-10 minutes

## References

- **Sentiment Model**: DistilBERT (Sanh et al., 2019)
- **Statistical Methods**: Pearson, 1895; Student's t-test, 1908
- **Topic Extraction**: Keyword-based with context analysis
- **Packaging Psychology**: Color theory, Gestalt principles

---

**Author**: AI Analysis Engine Team  
**Date**: February 2026  
**Version**: 1.0.0  
**License**: Proprietary
