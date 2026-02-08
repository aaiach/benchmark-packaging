"""Data models for the product scraper."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


# =============================================================================
# Pydantic Models for LLM Structured Outputs
# =============================================================================

class Brand(BaseModel):
    """A single brand discovered by the LLM."""
    name: str = Field(description="Nom de la marque")
    country_of_origin: Optional[str] = Field(None, description="Pays d'origine de la marque")


class BrandList(BaseModel):
    """List of brands discovered in a category."""
    brands: List[Brand] = Field(description="Liste des marques découvertes")


class ProductDetails(BaseModel):
    """Detailed product information for a single brand."""
    brand: str = Field(description="Nom de la marque")
    full_name: str = Field(description="Nom complet du produit phare")
    brand_website: Optional[str] = Field(None, description="Domaine du site officiel (ex: oatly.com)")
    product_url: Optional[str] = Field(None, description="URL complète de la page produit")
    price_segment: Literal["économique", "moyen", "premium"] = Field(
        description="Segment de prix"
    )
    distribution: str = Field(description="Canaux de distribution (ex: grande distribution, bio)")
    value_proposition: str = Field(description="Proposition de valeur principale")
    target_audience: str = Field(description="Public cible (ex: grand public, bio, sportifs)")


class ProductDetailsList(BaseModel):
    """List of product details (for batch processing fallback)."""
    products: List[ProductDetails] = Field(description="Liste des détails produits")


# =============================================================================
# Pydantic Models for Image Selection
# =============================================================================

class ImageSelection(BaseModel):
    """Result of AI-powered image selection for a product."""
    selected_url: str = Field(
        description="URL of the selected best product image"
    )
    confidence: float = Field(
        description="Confidence score from 0.0 to 1.0",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Brief explanation of why this image was selected"
    )
    is_product_image: bool = Field(
        description="Whether the selected image actually shows the product"
    )


# =============================================================================
# Pydantic Models for Front Extraction (Step 4.5)
# =============================================================================

class FrontExtractionBoundingBox(BaseModel):
    """Bounding box for the front-facing product packaging.
    
    Coordinates are normalized to 0-1000 scale (relative to image dimensions).
    Format: [ymin, xmin, ymax, xmax] as per Gemini's standard.
    """
    ymin: int = Field(
        description="Top edge Y coordinate (0-1000 scale)",
        ge=0,
        le=1000
    )
    xmin: int = Field(
        description="Left edge X coordinate (0-1000 scale)",
        ge=0,
        le=1000
    )
    ymax: int = Field(
        description="Bottom edge Y coordinate (0-1000 scale)",
        ge=0,
        le=1000
    )
    xmax: int = Field(
        description="Right edge X coordinate (0-1000 scale)",
        ge=0,
        le=1000
    )


class FrontExtractionResult(BaseModel):
    """Result of front-facing packaging extraction analysis.
    
    The AI identifies the front face of the product packaging and returns
    bounding box coordinates for cropping. No image modification is performed -
    only coordinates are returned for lossless cropping.
    """
    can_extract: bool = Field(
        description="Whether a front-facing view can be extracted from this image"
    )
    bounding_box: Optional[FrontExtractionBoundingBox] = Field(
        None,
        description="Bounding box coordinates for the front face (only if can_extract is True)"
    )
    confidence: float = Field(
        description="Confidence score from 0.0 to 1.0 for the extraction",
        ge=0.0,
        le=1.0
    )
    image_type: str = Field(
        description="Type of product image: 'front_facing', 'angled', 'multiple_items', 'lifestyle', 'cropped', 'other'"
    )
    reasoning: str = Field(
        description="Explanation of the image composition and extraction decision"
    )
    extraction_notes: Optional[str] = Field(
        None,
        description="Any notes about the extraction (e.g., 'slight angle corrected', 'selected main product from group')"
    )


class ImageSelectionResult(BaseModel):
    """Complete result for a product's image selection."""
    brand: str = Field(description="Brand name")
    product_name: str = Field(description="Product full name")
    selected_image_url: Optional[str] = Field(
        None, 
        description="URL of the selected image (None if no suitable image found)"
    )
    local_image_path: Optional[str] = Field(
        None,
        description="Local filesystem path to the downloaded image"
    )
    selection_confidence: float = Field(
        default=0.0,
        description="Confidence score of the selection"
    )
    selection_reasoning: Optional[str] = Field(
        None,
        description="AI reasoning for the selection"
    )


# =============================================================================
# Pydantic Models for Visual Analysis (Step 5)
# =============================================================================

class VisualElement(BaseModel):
    """A single visual element identified in the image."""
    element_type: str = Field(
        description="Type of element: 'product', 'text', 'logo', 'illustration', 'background', 'icon', 'pattern', 'other'"
    )
    description: str = Field(
        description="Brief description of the element"
    )
    position: str = Field(
        description="Position in image: 'top-left', 'top-center', 'top-right', 'center-left', 'center', 'center-right', 'bottom-left', 'bottom-center', 'bottom-right'"
    )
    visual_weight: int = Field(
        description="Visual weight/importance from 1 (lowest) to 10 (highest)",
        ge=1,
        le=10
    )
    dominant_color: str = Field(
        description="Primary color of this element (e.g., 'deep blue', 'bright red', 'white')"
    )
    size_percentage: Optional[int] = Field(
        None,
        description="Approximate percentage of image area occupied (0-100)"
    )


class EyeTrackingPattern(BaseModel):
    """Eye movement pattern analysis."""
    pattern_type: Literal["Z", "F", "circular", "diagonal", "centered", "scattered"] = Field(
        description="Primary eye movement pattern"
    )
    entry_point: str = Field(
        description="Where the eye first enters the image"
    )
    fixation_sequence: List[str] = Field(
        description="Ordered list of fixation points (what the eye looks at in sequence)"
    )
    exit_point: str = Field(
        description="Where the eye naturally exits or rests"
    )
    dwell_zones: List[str] = Field(
        description="Areas where the eye likely dwells longer"
    )


class MassingAnalysis(BaseModel):
    """Analysis of visual mass distribution."""
    balance_type: Literal["symmetric", "asymmetric", "dynamic", "radial", "mosaic"] = Field(
        description="Type of visual balance"
    )
    dense_zones: List[str] = Field(
        description="Areas with high visual density/weight"
    )
    light_zones: List[str] = Field(
        description="Areas with visual breathing room/whitespace"
    )
    center_of_gravity: str = Field(
        description="Where the visual 'weight' of the image is centered"
    )


# =============================================================================
# Section 2: Chromatic & Semiotic Mapping
# =============================================================================

class ColorEntry(BaseModel):
    """A single color in the palette."""
    color_name: str = Field(
        description="Descriptive color name (e.g., 'Deep Forest Green', 'Warm Beige')"
    )
    hex_code: str = Field(
        description="Hex color code approximation (e.g., '#2D5A3D')"
    )
    pantone_approximation: Optional[str] = Field(
        None,
        description="Closest Pantone reference if identifiable (e.g., 'Pantone 349 C')"
    )
    usage: str = Field(
        description="Where this color is used (e.g., 'background', 'primary branding', 'accent text', 'logo')"
    )
    coverage_percentage: Optional[int] = Field(
        None,
        description="Approximate percentage of package surface using this color (0-100)"
    )


class ChromaticMapping(BaseModel):
    """Chromatic & Semiotic Mapping - Color codes and surface finishes."""
    color_palette: List[ColorEntry] = Field(
        description="Complete color palette extracted from the packaging, ordered by visual prominence"
    )
    background_colors: List[str] = Field(
        description="Primary background color(s) with hex codes"
    )
    primary_branding_colors: List[str] = Field(
        description="Main brand identity colors with hex codes"
    )
    accent_colors: List[str] = Field(
        description="Accent and highlight colors with hex codes"
    )
    surface_finish: Literal["matte", "satin", "semi-gloss", "high-gloss", "metallic", "textured", "mixed"] = Field(
        description="Surface finish based on light reflections analysis"
    )
    surface_finish_description: str = Field(
        description="Detailed description of surface finish characteristics based on light reflections, shadows, and highlights visible in the image"
    )
    color_harmony: str = Field(
        description="Color harmony type (e.g., 'complementary', 'analogous', 'triadic', 'monochromatic', 'split-complementary')"
    )
    color_psychology_notes: str = Field(
        description="Brief analysis of the psychological impact of the color choices for the product category"
    )


# =============================================================================
# Section 3: Textual & Claim Inventory
# =============================================================================

class TextBlock(BaseModel):
    """A single text block on the packaging."""
    text_content: str = Field(
        description="Exact transcription of the text"
    )
    font_category: str = Field(
        description="Font category: 'Rounded Sans-Serif', 'Geometric Sans-Serif', 'Humanist Sans-Serif', 'Traditional Serif', 'Modern Serif', 'Slab Serif', 'Script', 'Display', 'Handwritten', 'Monospace'"
    )
    font_weight: str = Field(
        description="Font weight: 'thin', 'light', 'regular', 'medium', 'semi-bold', 'bold', 'extra-bold', 'black'"
    )
    text_size: Literal["extra-small", "small", "medium", "large", "extra-large", "headline"] = Field(
        description="Relative text size on the packaging"
    )
    text_color: str = Field(
        description="Text color with hex code approximation"
    )
    position: str = Field(
        description="Position on packaging (e.g., 'top-center', 'below logo')"
    )
    emphasis_techniques: List[str] = Field(
        description="How this text is emphasized: 'bold', 'larger size', 'color contrast', 'color block background', 'underline', 'uppercase', 'isolation/whitespace', 'none'"
    )
    is_claim: bool = Field(
        description="Whether this text is a marketing claim or certification statement"
    )
    hierarchy_level: int = Field(
        description="Text hierarchy level: 1 (most prominent) to 5 (least prominent)",
        ge=1,
        le=5
    )


class TextualInventory(BaseModel):
    """Textual & Claim Inventory - Lexicon, typography, and hierarchy."""
    all_text_blocks: List[TextBlock] = Field(
        description="All text blocks on the front-of-pack, ordered by hierarchy level (most prominent first)"
    )
    brand_name_typography: str = Field(
        description="Detailed description of brand name font and styling"
    )
    product_name_typography: str = Field(
        description="Detailed description of product name font and styling"
    )
    claims_summary: List[str] = Field(
        description="List of all marketing claims and benefit statements"
    )
    emphasized_claims: List[str] = Field(
        description="Claims that are visually emphasized through bolding, size, or distinct color blocks"
    )
    typography_consistency: str = Field(
        description="Assessment of typographic consistency across the packaging (e.g., 'highly consistent 2-font system', 'varied with 4+ fonts')"
    )
    readability_assessment: str = Field(
        description="Assessment of overall text readability considering size, contrast, and spacing"
    )


# =============================================================================
# Section 4: Asset & Trust Symbolism
# =============================================================================

class GraphicalAsset(BaseModel):
    """A non-text graphical asset on the packaging."""
    asset_type: Literal["photography", "illustration", "line-art", "icon", "pattern", "abstract", "logo", "badge", "symbol"] = Field(
        description="Type of graphical asset"
    )
    description: str = Field(
        description="Detailed description of the asset"
    )
    style: str = Field(
        description="Visual style (e.g., 'photorealistic', 'stylized line art', 'flat icon', 'watercolor illustration', 'geometric pattern')"
    )
    position: str = Field(
        description="Position on the packaging"
    )
    size_percentage: Optional[int] = Field(
        None,
        description="Approximate percentage of packaging area (0-100)"
    )
    purpose: str = Field(
        description="Purpose of this asset (e.g., 'product visualization', 'ingredient showcase', 'brand identity', 'decorative', 'trust signal')"
    )


class TrustMark(BaseModel):
    """A certification, trust mark, or origin symbol."""
    name: str = Field(
        description="Name of the certification or symbol (e.g., 'EU Organic', 'Fairtrade', 'Non-GMO Project')"
    )
    mark_type: Literal["organic-certification", "quality-certification", "environmental-certification", "dietary-certification", "origin-symbol", "brand-quality-mark", "recycling-symbol", "other"] = Field(
        description="Category of trust mark"
    )
    visual_description: str = Field(
        description="Visual description of the mark/badge"
    )
    position: str = Field(
        description="Position on the packaging"
    )
    prominence: Literal["highly-prominent", "prominent", "moderate", "subtle"] = Field(
        description="How prominently the mark is displayed"
    )
    colors: List[str] = Field(
        description="Colors used in the mark"
    )


class AssetSymbolism(BaseModel):
    """Asset & Trust Symbolism - Graphical assets and third-party badges."""
    graphical_assets: List[GraphicalAsset] = Field(
        description="All non-text visual assets, differentiating between photography, line art, and patterns"
    )
    trust_marks: List[TrustMark] = Field(
        description="All visible certifications, trust marks, and origin symbols"
    )
    photography_vs_illustration_ratio: str = Field(
        description="Ratio of photographic vs illustrated content (e.g., '70% photography / 30% illustration')"
    )
    visual_storytelling_elements: List[str] = Field(
        description="Elements that contribute to brand storytelling (e.g., 'rustic farm imagery', 'fresh ingredient photography')"
    )
    trust_signal_effectiveness: str = Field(
        description="Assessment of how effectively trust marks and certifications are communicated"
    )


# =============================================================================
# Pydantic Models for Competitive Analysis (Step 7)
# =============================================================================

class PointOfDifference(BaseModel):
    """A Point-of-Difference axis for radar chart comparison."""
    axis_id: str = Field(
        description="Short unique identifier (e.g., 'premium_craft', 'health_focus')"
    )
    axis_name: str = Field(
        description="Display name for the axis (2-4 words, English, e.g., 'Premium Craft')"
    )
    description: str = Field(
        description="What this axis measures and what visual elements indicate high scores"
    )
    high_score_indicators: List[str] = Field(
        description="Visual/textual elements that indicate a high score on this axis"
    )


class PointOfParity(BaseModel):
    """A Point-of-Parity attribute for matrix comparison."""
    pop_id: str = Field(
        description="Short unique identifier (e.g., 'organic_certified', 'no_sugar')"
    )
    pop_name: str = Field(
        description="Display name for the attribute (e.g., 'Organic Certified')"
    )
    pop_type: Literal["certification", "nutritional_claim", "category_attribute", "origin_claim"] = Field(
        description="Type of point-of-parity"
    )
    description: str = Field(
        description="Brief description of what this POP represents"
    )


class ProductPODScore(BaseModel):
    """A single POD score for a product."""
    axis_id: str = Field(description="References PointOfDifference.axis_id")
    score: int = Field(description="Score from 1-10", ge=1, le=10)
    reasoning: str = Field(description="Brief justification for this score based on visual elements")


class ProductPOPStatus(BaseModel):
    """A single POP status for a product."""
    pop_id: str = Field(description="References PointOfParity.pop_id")
    has_attribute: bool = Field(description="Whether the product has this attribute")
    evidence: Optional[str] = Field(None, description="Visual evidence if present")


class ProductCompetitiveProfile(BaseModel):
    """Complete competitive profile for a single product."""
    brand: str = Field(description="Brand name")
    product_name: str = Field(description="Full product name")
    image_path: Optional[str] = Field(None, description="Path to product image")
    
    # Radar chart data
    pod_scores: List[ProductPODScore] = Field(
        description="Scores for each Point-of-Difference axis"
    )
    
    # Matrix data
    pop_status: List[ProductPOPStatus] = Field(
        description="Status for each Point-of-Parity attribute"
    )
    
    # Summary
    positioning_summary: str = Field(
        description="One-sentence positioning summary for this product"
    )
    key_differentiator: str = Field(
        description="The single most distinctive aspect of this product"
    )


class StrategicInsight(BaseModel):
    """A strategic insight from the competitive analysis."""
    insight_type: Literal["competitive_landscape", "differentiation_opportunity", "visual_trend", "positioning_gap"] = Field(
        description="Category of insight"
    )
    title: str = Field(
        description="Short title for the insight"
    )
    description: str = Field(
        description="Detailed explanation of the insight"
    )
    affected_brands: List[str] = Field(
        default_factory=list,
        description="Brands most relevant to this insight"
    )


class CompetitiveAnalysisResult(BaseModel):
    """Complete competitive analysis output for frontend consumption."""
    
    # Metadata
    category: str = Field(description="Product category analyzed")
    analysis_date: str = Field(description="ISO date of analysis")
    product_count: int = Field(description="Number of products analyzed")
    
    # PODs for Radar Chart
    points_of_difference: List[PointOfDifference] = Field(
        description="5 axes of differentiation for radar chart"
    )
    
    # POPs for Matrix
    points_of_parity: List[PointOfParity] = Field(
        description="5 common attributes for parity matrix"
    )
    
    # Product Profiles
    products: List[ProductCompetitiveProfile] = Field(
        description="Competitive profile for each product"
    )
    
    # Strategic Insights
    strategic_insights: List[StrategicInsight] = Field(
        description="3-5 key strategic observations"
    )
    
    # Category Summary
    category_summary: str = Field(
        description="Executive summary of the competitive landscape (2-3 sentences)"
    )


# =============================================================================
# Intermediate Models for Multi-Phase Competitive Analysis (Step 7)
# =============================================================================

class CategoryAxesResult(BaseModel):
    """Phase 1 output: PODs and POPs identified for the category."""
    
    # PODs for Radar Chart
    points_of_difference: List[PointOfDifference] = Field(
        description="5 axes of differentiation for radar chart"
    )
    
    # POPs for Matrix
    points_of_parity: List[PointOfParity] = Field(
        description="5 common attributes for parity matrix"
    )
    
    # Brief category overview (helps Phase 2 scoring)
    category_positioning_context: str = Field(
        description="Brief overview of how products in this category are positioned (2-3 sentences)"
    )


class SingleProductProfile(BaseModel):
    """Phase 2 output: Complete competitive profile for a single product."""
    
    brand: str = Field(description="Brand name")
    product_name: str = Field(description="Full product name")
    
    # Radar chart data
    pod_scores: List[ProductPODScore] = Field(
        description="Scores for each Point-of-Difference axis"
    )
    
    # Matrix data
    pop_status: List[ProductPOPStatus] = Field(
        description="Status for each Point-of-Parity attribute"
    )
    
    # Summary
    positioning_summary: str = Field(
        description="One-sentence positioning summary for this product"
    )
    key_differentiator: str = Field(
        description="The single most distinctive aspect of this product"
    )


class StrategicInsightsResult(BaseModel):
    """Phase 3 output: Strategic insights from the complete analysis."""
    
    strategic_insights: List[StrategicInsight] = Field(
        description="3-5 key strategic observations"
    )
    
    category_summary: str = Field(
        description="Executive summary of the competitive landscape (2-3 sentences)"
    )


class VisualHierarchyAnalysis(BaseModel):
    """Complete visual hierarchy analysis result with 4 sections."""
    
    # =========================================================================
    # SECTION 1: Visual Hierarchy (existing)
    # =========================================================================
    
    # Visual anchor (the dominant element)
    visual_anchor: str = Field(
        description="The largest, highest-contrast element that captures immediate attention"
    )
    visual_anchor_description: str = Field(
        description="Detailed description of why this element is the visual anchor"
    )
    
    # Ranked elements
    elements: List[VisualElement] = Field(
        description="All visual elements ranked by visual weight (descending order)"
    )
    
    # Eye tracking
    eye_tracking: EyeTrackingPattern = Field(
        description="Eye movement pattern analysis"
    )
    
    # Massing
    massing: MassingAnalysis = Field(
        description="Visual mass distribution analysis"
    )
    
    # Overall scores
    hierarchy_clarity_score: int = Field(
        description="How clear is the visual hierarchy (1-10)",
        ge=1,
        le=10
    )
    
    # Free-form detailed analysis for section 1
    detailed_analysis: str = Field(
        description="Comprehensive free-form analysis of the visual hierarchy, eye-tracking simulation, and design effectiveness. Be thorough and technical."
    )
    
    # =========================================================================
    # SECTION 2: Chromatic & Semiotic Mapping
    # =========================================================================
    
    chromatic_mapping: ChromaticMapping = Field(
        description="Color palette analysis and surface finish assessment"
    )
    
    # =========================================================================
    # SECTION 3: Textual & Claim Inventory
    # =========================================================================
    
    textual_inventory: TextualInventory = Field(
        description="Complete transcription and typography analysis of all text on the packaging"
    )
    
    # =========================================================================
    # SECTION 4: Asset & Trust Symbolism
    # =========================================================================
    
    asset_symbolism: AssetSymbolism = Field(
        description="Graphical assets and trust marks/certifications analysis"
    )


# =============================================================================
# Pydantic Models for 4-Step Rebrand Pipeline
# =============================================================================

class ElementBoundingBox(BaseModel):
    """Normalized coordinates (0-1000 scale) for element cropping."""
    xmin: int = Field(
        description="Left edge X coordinate (0-1000 scale)",
        ge=0,
        le=1000
    )
    ymin: int = Field(
        description="Top edge Y coordinate (0-1000 scale)",
        ge=0,
        le=1000
    )
    xmax: int = Field(
        description="Right edge X coordinate (0-1000 scale)",
        ge=0,
        le=1000
    )
    ymax: int = Field(
        description="Bottom edge Y coordinate (0-1000 scale)",
        ge=0,
        le=1000
    )


class ExtractedElement(BaseModel):
    """A single visual element extracted from an image with bounding box for cropping."""
    element_id: str = Field(
        description="Unique identifier (e.g., 'text_1', 'logo', 'trust_mark_1', 'product_image')"
    )
    element_type: Literal[
        "text", "logo", "trust_mark", "product_image", 
        "illustration", "icon", "pattern", "badge", "background", "decorative"
    ] = Field(
        description="Type of visual element"
    )
    content: str = Field(
        description="Exact text content (for text elements) or visual description (for images)"
    )
    position: str = Field(
        description="Position on packaging: 'top-left', 'top-center', 'top-right', 'center-left', 'center', 'center-right', 'bottom-left', 'bottom-center', 'bottom-right'"
    )
    bounding_box: ElementBoundingBox = Field(
        description="Bounding box coordinates for cropping this element"
    )
    visual_description: str = Field(
        description="Detailed visual description: colors (hex), fonts, style, effects"
    )
    size_percentage: float = Field(
        description="Approximate percentage of image area occupied (0-100)",
        ge=0,
        le=100
    )
    hierarchy_level: int = Field(
        description="Visual hierarchy level: 1 (most prominent) to 5 (least prominent)",
        ge=1,
        le=5
    )


class CompositionDescription(BaseModel):
    """Overall composition structure of a packaging image."""
    layout_type: str = Field(
        description="Layout structure (e.g., 'centered', 'asymmetric', 'grid', 'diagonal')"
    )
    visual_flow: str = Field(
        description="Eye movement pattern (e.g., 'top-to-bottom', 'Z-pattern', 'circular')"
    )
    balance: str = Field(
        description="Visual balance type: 'symmetric', 'asymmetric', 'radial'"
    )
    dominant_zone: str = Field(
        description="Area with highest visual weight"
    )
    whitespace_zones: List[str] = Field(
        description="Areas with breathing room/empty space"
    )
    overall_style: str = Field(
        description="Design style (e.g., 'minimalist', 'premium', 'playful', 'organic')"
    )


class ColorInfo(BaseModel):
    """Color information with hex code and usage."""
    hex_code: str = Field(
        description="Hex color code (e.g., '#FF5733')"
    )
    color_name: str = Field(
        description="Descriptive color name (e.g., 'Deep Navy Blue')"
    )
    usage: str = Field(
        description="Where this color is used (e.g., 'background', 'primary text', 'accent')"
    )
    coverage_percentage: Optional[int] = Field(
        None,
        description="Approximate percentage of surface using this color"
    )


class InspirationExtraction(BaseModel):
    """Step 1 output: All elements extracted from inspiration image."""
    elements: List[ExtractedElement] = Field(
        description="All visual elements extracted with bounding boxes"
    )
    composition: CompositionDescription = Field(
        description="Overall composition structure"
    )
    color_palette: List[ColorInfo] = Field(
        description="Color palette extracted from the image"
    )
    packaging_format_description: str = Field(
        default="",
        description="LLM-generated description of the packaging format: shape, size, material, finish, 3D/2D, physical characteristics"
    )
    total_elements: int = Field(
        description="Total number of elements extracted"
    )
    image_dimensions: Optional[Dict[str, int]] = Field(
        None,
        description="Original image dimensions (width, height)"
    )


class SourceExtraction(BaseModel):
    """Step 2 output: Elements extracted from source image matching constraints."""
    elements: List[ExtractedElement] = Field(
        description="Visual elements extracted based on brand identity"
    )
    brand_name: str = Field(
        description="Detected brand name"
    )
    product_name: str = Field(
        description="Detected product name"
    )
    available_claims: List[str] = Field(
        description="List of claims/trust marks available from source"
    )
    color_palette: List[ColorInfo] = Field(
        description="Brand color palette"
    )
    packaging_format_description: str = Field(
        default="",
        description="LLM-generated description of the packaging format: shape, size, material, finish, 3D/2D, physical characteristics"
    )
    total_elements: int = Field(
        description="Total number of elements extracted"
    )


class ElementMappingEntry(BaseModel):
    """Step 3: Single mapping decision for one inspiration element."""
    inspiration_element_id: str = Field(
        description="References the element_id from InspirationExtraction"
    )
    action: Literal["adapt", "replace", "omit", "keep"] = Field(
        description="Action to take: adapt (recreate in source style), replace with source content, or omit. 'keep' is deprecated, use 'adapt'"
    )
    replacement_source: Optional[str] = Field(
        None,
        description="If action='replace': source element_id OR literal text from constraints"
    )
    replacement_content: Optional[str] = Field(
        default="",
        description="The actual content to use (element content or constraint text). Empty for adapt/omit actions."
    )
    adaptation_concept: Optional[str] = Field(
        None,
        description="For action='adapt': what the element represents conceptually (e.g., 'leaf illustration', 'wave pattern')"
    )
    styling_notes: Optional[str] = Field(
        default="",
        description="How to style the element. For 'adapt': detailed instructions for recreating in source brand style"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Brief explanation of why this mapping decision was made"
    )


class RebrandColorScheme(BaseModel):
    """Color scheme for the rebranded output."""
    primary: str = Field(description="Primary brand color hex")
    secondary: str = Field(description="Secondary color hex")
    background: str = Field(description="Background color hex")
    text_primary: str = Field(description="Primary text color hex")
    text_secondary: Optional[str] = Field(None, description="Secondary text color hex")
    accent: Optional[str] = Field(None, description="Accent color hex")


class RebrandMapping(BaseModel):
    """Step 3 output: Complete element-by-element mapping."""
    mappings: List[ElementMappingEntry] = Field(
        description="Mapping for each inspiration element"
    )
    packaging_format_choice: Literal["source", "inspiration"] = Field(
        default="inspiration",
        description="Which packaging format to follow: 'inspiration' (default) or 'source' (only if explicitly requested)"
    )
    packaging_format_description: str = Field(
        default="",
        description="The chosen packaging format description (copied from either source or inspiration extraction)"
    )
    composition_description: str = Field(
        description="Textual description of final composition with precise positioning"
    )
    color_scheme: RebrandColorScheme = Field(
        description="Color scheme for the rebranded output"
    )
    assembly_notes: str = Field(
        description="Additional notes for assembling the final image"
    )


class RebrandStepResult(BaseModel):
    """Verbose output for a single pipeline step - for frontend visualization."""
    step_name: str = Field(
        description="Step identifier: 'inspiration_extraction', 'source_extraction', 'element_mapping', 'image_generation'"
    )
    step_number: int = Field(
        description="Step number (1-4)",
        ge=1,
        le=4
    )
    status: Literal["pending", "in_progress", "complete", "error"] = Field(
        description="Current status of this step"
    )
    duration_ms: Optional[int] = Field(
        None,
        description="Duration in milliseconds (once complete)"
    )
    input_summary: str = Field(
        description="Brief description of inputs to this step"
    )
    output_summary: str = Field(
        description="Brief description of outputs from this step"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Step-specific detailed data"
    )
    cropped_images: List[str] = Field(
        default_factory=list,
        description="URLs/paths to cropped element images (for steps 1 & 2)"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if status='error'"
    )


class RebrandResult(BaseModel):
    """Complete rebrand pipeline result with all intermediate step data."""
    status: Literal["success", "error", "partial"] = Field(
        description="Overall pipeline status"
    )
    job_id: str = Field(
        description="Unique job identifier"
    )
    steps: List[RebrandStepResult] = Field(
        description="Results from each pipeline step"
    )
    generated_image_path: Optional[str] = Field(
        None,
        description="Path to final generated image"
    )
    source_image_path: str = Field(
        description="Path to original source image"
    )
    inspiration_image_path: str = Field(
        description="Path to original inspiration image"
    )
    brand_identity: str = Field(
        description="Brand identity text provided by user"
    )
    created_at: str = Field(
        description="ISO timestamp of job creation"
    )
    completed_at: Optional[str] = Field(
        None,
        description="ISO timestamp of job completion"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of error messages if any"
    )


# =============================================================================
# Pydantic Models for Rebrand Session (Multi-product rebrand from analysis)
# =============================================================================

class ProductRebrandEntry(BaseModel):
    """A single product rebrand entry within a session."""
    product_index: int = Field(
        description="Index of the product in the analysis"
    )
    product_name: str = Field(
        description="Name of the product/brand"
    )
    inspiration_image_path: str = Field(
        description="Path to the inspiration image (competitor's cropped image)"
    )
    rebrand_job_id: Optional[str] = Field(
        None,
        description="ID of the rebrand job (once started)"
    )
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"] = Field(
        default="pending",
        description="Status of this individual rebrand"
    )
    generated_image_path: Optional[str] = Field(
        None,
        description="Path to generated image (once completed)"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if failed"
    )
    result: Optional[Dict[str, Any]] = Field(
        None,
        description="Full rebrand result (once completed)"
    )


class RebrandSessionProgress(BaseModel):
    """Progress tracking for a rebrand session."""
    total: int = Field(
        description="Total number of products to rebrand"
    )
    completed: int = Field(
        default=0,
        description="Number of completed rebrands"
    )
    failed: int = Field(
        default=0,
        description="Number of failed rebrands"
    )
    current_product: Optional[str] = Field(
        None,
        description="Name of currently processing product"
    )


class RebrandSession(BaseModel):
    """A rebrand session linked to a category analysis.
    
    Allows users to rebrand their product against all competitors
    found in a competitive analysis.
    """
    session_id: str = Field(
        description="Unique session identifier"
    )
    analysis_id: str = Field(
        description="Reference to the parent category analysis (run_id)"
    )
    category: str = Field(
        description="Product category name"
    )
    source_image_path: str = Field(
        description="Path to the user's source product image"
    )
    brand_identity: str = Field(
        description="Brand identity and constraints text"
    )
    status: Literal["pending", "in_progress", "completed", "partial", "failed"] = Field(
        default="pending",
        description="Overall session status"
    )
    created_at: str = Field(
        description="ISO timestamp of session creation"
    )
    completed_at: Optional[str] = Field(
        None,
        description="ISO timestamp of session completion"
    )
    rebrands: List[ProductRebrandEntry] = Field(
        default_factory=list,
        description="List of individual product rebrands"
    )
    progress: RebrandSessionProgress = Field(
        default_factory=lambda: RebrandSessionProgress(total=0),
        description="Progress tracking"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of error messages if any"
    )


# =============================================================================
# Dataclass for Internal Product Representation
# =============================================================================

@dataclass
class Product:
    """Représente un produit avec ses métadonnées."""
    brand: str
    full_name: str
    category: str
    target_audience: str
    brand_website: Optional[str] = None
    product_url: Optional[str] = None
    url: Optional[str] = None
    price: Optional[str] = None
    reviews: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[str]] = None
    description: Optional[str] = None
    availability: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_product_details(cls, details: ProductDetails, category: str) -> "Product":
        """Create a Product from ProductDetails Pydantic model."""
        return cls(
            brand=details.brand,
            full_name=details.full_name,
            category=category,
            target_audience=details.target_audience,
            brand_website=details.brand_website,
            product_url=details.product_url,
            additional_data={
                'segment_prix': details.price_segment,
                'distribution': details.distribution,
                'proposition_valeur': details.value_proposition,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le produit en dictionnaire."""
        return {
            'brand': self.brand,
            'full_name': self.full_name,
            'category': self.category,
            'target_audience': self.target_audience,
            'brand_website': self.brand_website,
            'product_url': self.product_url,
            'url': self.url,
            'price': self.price,
            'reviews': self.reviews,
            'images': self.images,
            'description': self.description,
            'availability': self.availability,
            'additional_data': self.additional_data
        }


# =============================================================================
# Pydantic Models for Review Analysis (Phase 1.3)
# =============================================================================

class ReviewSentiment(BaseModel):
    """Sentiment analysis result for a review."""
    overall_score: float = Field(
        description="Overall sentiment score from -1 (very negative) to 1 (very positive)",
        ge=-1.0,
        le=1.0
    )
    confidence: float = Field(
        description="Confidence score from 0 to 1",
        ge=0.0,
        le=1.0
    )
    sentiment_label: Literal["very_negative", "negative", "neutral", "positive", "very_positive"] = Field(
        description="Categorical sentiment label"
    )


class PackagingTopic(BaseModel):
    """A packaging-related topic mentioned in a review."""
    topic: Literal["design", "readability", "claims_believability", "shelf_appeal", "color", "typography", "trust_marks", "overall_appearance"] = Field(
        description="Type of packaging topic"
    )
    sentiment: float = Field(
        description="Sentiment score for this topic (-1 to 1)",
        ge=-1.0,
        le=1.0
    )
    relevance_score: float = Field(
        description="How relevant this topic is to the review (0 to 1)",
        ge=0.0,
        le=1.0
    )
    mentioned_phrases: List[str] = Field(
        description="Specific phrases from the review related to this topic"
    )


class ReviewAnalysis(BaseModel):
    """Complete analysis of a single customer review."""
    review_id: str = Field(description="Unique review identifier")
    brand: str = Field(description="Product brand")
    product_name: str = Field(description="Product name")
    review_text: str = Field(description="Original review text")
    rating: Optional[float] = Field(
        None,
        description="Original review rating (e.g., 1-5 stars)",
        ge=1.0,
        le=5.0
    )
    sentiment: ReviewSentiment = Field(
        description="Overall sentiment analysis"
    )
    packaging_topics: List[PackagingTopic] = Field(
        description="Packaging-related topics identified in the review"
    )
    is_packaging_focused: bool = Field(
        description="Whether this review primarily discusses packaging"
    )
    review_date: Optional[str] = Field(
        None,
        description="Date of review (ISO format)"
    )
    verified_purchase: Optional[bool] = Field(
        None,
        description="Whether this was a verified purchase"
    )


class PackagingAttributeCorrelation(BaseModel):
    """Correlation between a packaging attribute and customer satisfaction."""
    attribute_category: str = Field(
        description="Category of attribute: 'color', 'typography', 'claim', 'layout', 'trust_mark', 'surface_finish'"
    )
    attribute_value: str = Field(
        description="Specific attribute value (e.g., 'matte finish', 'blue color', 'organic claim')"
    )
    correlation_score: float = Field(
        description="Correlation coefficient (-1 to 1) with customer satisfaction",
        ge=-1.0,
        le=1.0
    )
    statistical_significance: float = Field(
        description="P-value for statistical significance (0 to 1)",
        ge=0.0,
        le=1.0
    )
    average_sentiment: float = Field(
        description="Average sentiment score for products with this attribute",
        ge=-1.0,
        le=1.0
    )
    sample_size: int = Field(
        description="Number of reviews/products in sample",
        ge=0
    )
    impact_category: Literal["strong_positive", "positive", "neutral", "negative", "strong_negative"] = Field(
        description="Categorical impact on customer satisfaction"
    )


class AttributeRanking(BaseModel):
    """Ranked packaging attribute by customer impact."""
    rank: int = Field(description="Rank position (1 is highest impact)", ge=1)
    attribute: PackagingAttributeCorrelation = Field(
        description="The attribute and its correlation data"
    )
    supporting_evidence: List[str] = Field(
        description="Example review phrases that support this correlation"
    )


class TopicCorrelation(BaseModel):
    """Correlation between packaging topic mentions and sentiment."""
    topic: str = Field(description="Packaging topic name")
    mention_count: int = Field(description="Number of times mentioned in reviews", ge=0)
    average_sentiment_when_mentioned: float = Field(
        description="Average sentiment in reviews mentioning this topic",
        ge=-1.0,
        le=1.0
    )
    average_sentiment_when_not_mentioned: float = Field(
        description="Average sentiment in reviews not mentioning this topic",
        ge=-1.0,
        le=1.0
    )
    sentiment_delta: float = Field(
        description="Difference in sentiment (mentioned - not mentioned)"
    )


class ReviewPackagingCorrelationResult(BaseModel):
    """Complete correlation analysis between reviews and packaging design."""
    
    # Metadata
    category: str = Field(description="Product category analyzed")
    analysis_date: str = Field(description="ISO date of analysis")
    total_reviews: int = Field(description="Total number of reviews analyzed", ge=0)
    packaging_focused_reviews: int = Field(
        description="Number of reviews that discuss packaging",
        ge=0
    )
    products_analyzed: int = Field(description="Number of products in analysis", ge=0)
    
    # Attribute Rankings
    attribute_rankings: List[AttributeRanking] = Field(
        description="Packaging attributes ranked by customer impact (highest to lowest)"
    )
    
    # Topic Correlations
    topic_correlations: List[TopicCorrelation] = Field(
        description="Correlations between packaging topics and sentiment"
    )
    
    # Product-specific insights
    product_insights: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Per-product insights with packaging attributes and review sentiment"
    )
    
    # Key Findings
    key_findings: List[str] = Field(
        description="3-5 key strategic insights from the correlation analysis"
    )
    
    # Category Summary
    executive_summary: str = Field(
        description="Executive summary of the correlation analysis (2-3 sentences)"
    )
