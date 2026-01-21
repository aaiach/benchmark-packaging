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


class VisualHierarchyAnalysis(BaseModel):
    """Complete visual hierarchy analysis result."""
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
    
    # Free-form detailed analysis
    detailed_analysis: str = Field(
        description="Comprehensive free-form analysis of the visual hierarchy, eye-tracking simulation, and design effectiveness. Be thorough and technical."
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
