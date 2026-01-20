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
