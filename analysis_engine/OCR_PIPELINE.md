# OCR Pipeline for Packaging Text Extraction

## Overview

The OCR Pipeline (Step 8) extracts and categorizes all text from product packaging images for competitive intelligence and market analysis. It uses Gemini Vision with structured output to ensure reliable categorization.

## Features

### Text Extraction & Categorization

Automatically categorizes extracted text into:

1. **Brand Identity**
   - Brand name
   - Slogan/tagline
   - Product name
   - Sub-brand

2. **Product Claims**
   - Health claims (nutritional benefits, wellness)
   - Taste claims (flavor profiles, sensory descriptions)
   - Eco claims (sustainability, environmental)
   - Origin claims (geographic, traditional)
   - Quality claims (premium, artisanal)
   - Ethical claims (fair trade, social responsibility)

3. **Nutritional Information**
   - Nutrition table detection
   - Key nutritional values
   - Highlighted nutrients
   - Allergen information
   - Ingredients list

4. **Certifications & Labels**
   - Organic certifications (Bio, EU Organic, AB)
   - Fair trade certifications
   - Environmental certifications
   - Quality seals (PDO, PGI, TSG)
   - Dietary certifications (Vegan, Gluten-Free, etc.)
   - Origin indicators

5. **Regulatory Mentions**
   - Recycling instructions
   - Storage instructions
   - Usage instructions
   - Warnings
   - Legal notices
   - Producer information

6. **Visual Codes**
   - Dominant colors (with hex codes)
   - Color psychology analysis
   - Typography style
   - Primary font category
   - Layout structure
   - Design style
   - Surface finish

### Multilingual Support

Handles text in multiple languages:
- **French** (primary market: Belgium/France)
- **Dutch** (Flemish market: Belgium/Netherlands)  
- **English** (international products)

Text is extracted in its original language without translation, with language tags for each text element.

## Usage

### Standalone OCR Extraction

Run OCR on an existing pipeline run:

```bash
python main.py --run-id 20260208_143000 --steps 8
```

### Complete Pipeline with OCR

Run the full pipeline including OCR:

```bash
python main.py "lait d'avoine" --steps 1-8
```

### OCR Only on New Images

Run OCR after downloading images (steps 1-4):

```bash
python main.py "oat milk" --steps 1-4,8
```

## Output Format

Results are saved as structured JSON in:
```
output/analysis/{category}_ocr_{run_id}.json
```

### Example Output Structure

```json
[
  {
    "image_path": "output/images/lait_davoine_20260208/bjorg_8ec5db.png",
    "brand": "Bjorg",
    "product_name": "Bjorg Oat Milk",
    "analysis_timestamp": "2026-02-08T14:30:00",
    
    "brand_identity": {
      "brand_name": "Bjorg",
      "slogan": "L'agriculture biologique",
      "product_name": "Boisson Avoine",
      "sub_brand": null
    },
    
    "product_claims": [
      {
        "claim_text": "100% végétal",
        "claim_type": "health",
        "prominence": "primary",
        "language": "fr",
        "position": "front-center"
      },
      {
        "claim_text": "Source de calcium",
        "claim_type": "health",
        "prominence": "secondary",
        "language": "fr",
        "position": "front-left"
      }
    ],
    
    "nutritional_info": {
      "has_nutrition_table": true,
      "key_values": [
        {"nutrient": "Énergie", "value": "47 kcal", "per": "100ml"},
        {"nutrient": "Matières grasses", "value": "1.5g", "per": "100ml"}
      ],
      "highlighted_nutrients": ["Sans sucres ajoutés", "Source de calcium"],
      "allergen_info": ["Contient de l'avoine"],
      "ingredients_list": "Eau, avoine* 14%, huile de tournesol*..."
    },
    
    "certifications": [
      {
        "name": "AB - Agriculture Biologique",
        "certification_type": "organic",
        "issuing_body": "Ecocert France",
        "visual_description": "Green AB logo with leaf motif",
        "prominence": "highly-visible"
      },
      {
        "name": "EU Organic",
        "certification_type": "organic",
        "issuing_body": "EU",
        "visual_description": "Green leaf made of stars on EU flag background",
        "prominence": "visible"
      }
    ],
    
    "regulatory_mentions": [
      {
        "text": "À conserver au réfrigérateur après ouverture",
        "mention_type": "storage-instructions",
        "language": "fr"
      },
      {
        "text": "Agiter avant emploi",
        "mention_type": "usage-instructions",
        "language": "fr"
      }
    ],
    
    "visual_codes": {
      "dominant_colors": [
        "#2D5A3D Deep Forest Green",
        "#F5F5DC Warm Beige",
        "#FFFFFF White"
      ],
      "color_psychology": "Green conveys natural/organic positioning; beige/earth tones reinforce authenticity",
      "typography_style": "Modern rounded sans-serif with friendly, approachable character",
      "primary_font_category": "Rounded Sans-Serif",
      "layout_structure": "Centered vertical hierarchy with clear top-to-bottom reading flow",
      "design_style": "Clean minimalist with organic/natural cues",
      "surface_finish": "Matte cardboard with subtle texture"
    },
    
    "detected_languages": ["fr", "en"],
    "extraction_confidence": 0.95,
    "notes": "High-quality front-facing image with excellent text clarity"
  }
]
```

## Technical Details

### Architecture

- **LLM Model**: Gemini 1.5 Pro (via `langchain-google-genai`)
- **Processing**: Parallel execution using `ParallelExecutor`
- **Output**: Pydantic models with structured validation
- **Temperature**: 0.0 (deterministic for accuracy)

### Data Models

Located in `src/models.py`:
- `OCRResult`: Main result container
- `BrandIdentity`: Brand name and slogan
- `ProductClaim`: Individual marketing claim
- `NutritionalInformation`: Nutrition data
- `Certification`: Certification/label
- `RegulatoryMention`: Legal/regulatory text
- `VisualCodes`: Design analysis

### Prompts

Located in `src/prompts/`:
- `ocr_extraction_system.txt`: Comprehensive extraction instructions
- `ocr_extraction_user.txt`: Task-specific prompts

## Integration with Pipeline

The OCR step integrates seamlessly with the existing pipeline:

```
Step 1: Discovery → Step 2: Details → Step 3: Scraping → Step 4: Images
                                                             ↓
Step 5: Visual Analysis ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← Step 8: OCR
         ↓
Step 6: Heatmaps → Step 7: Competitive Analysis
```

**Dependencies**: 
- Requires Step 4 (images must be downloaded)
- Independent of visual analysis (can run in parallel)

## Use Cases

### Competitive Intelligence
- Compare claims across competitor products
- Identify certification strategies
- Analyze color and design trends

### Market Positioning
- Extract value propositions
- Map claim types by segment
- Track multilingual messaging

### Compliance & Regulation
- Audit regulatory compliance
- Track nutritional claims
- Monitor certification usage

### Design Analysis
- Typography patterns by category
- Color psychology trends
- Layout structure comparison

## API Configuration

Required environment variables:
```bash
GOOGLE_API_KEY=your_gemini_api_key
```

Set in `.env` file or environment.

## Performance

- **Speed**: ~10-15 images/minute (with parallel processing)
- **Accuracy**: 95%+ confidence on high-quality images
- **Rate Limits**: 14 RPM (configurable in `ParallelExecutor`)

## Limitations

- Requires clear, front-facing product images
- Text readability depends on image quality
- May miss small print or obscured text
- Best results with resolution > 800px

## Future Enhancements

- [ ] Add OCR confidence scoring per text block
- [ ] Support for side/back panel analysis
- [ ] Multi-image product analysis (front+back)
- [ ] Custom claim taxonomy per category
- [ ] Export to Excel/CSV format
- [ ] Batch comparison reports

## Support

For issues or questions:
1. Check image quality and resolution
2. Review confidence scores in output
3. Verify API key configuration
4. Check `analysis/` directory for results
