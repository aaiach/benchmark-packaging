"""Découverte de produits via LLM avec architecture en deux étapes.

Architecture:
- Étape 1 (Brand Discovery): Gemini + Google Search grounding (1 call)
- Étape 2 (Product Details): OpenAI + Web Search (N calls - PARALLELIZED)

Utilise LangChain pour une structure propre et extensible.
Parallelization via ParallelExecutor for Step 2.
"""
import json
from typing import List, Optional, Tuple
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from .config import get_config, DiscoveryConfig
from .models import Product, Brand, BrandList, ProductDetails
from .utils import load_prompt, extract_json
from .parallel_executor import (
    ParallelExecutor, 
    Provider, 
    ProviderLimits,
    wrap_sync_func,
    create_print_progress
)


# =============================================================================
# LLM Factory Functions
# =============================================================================

def create_gemini_with_search(config: DiscoveryConfig) -> BaseChatModel:
    """Create Gemini LLM with Google Search grounding for brand discovery.
    
    Uses the google_search built-in tool for real-time web grounding.
    """
    llm = ChatGoogleGenerativeAI(
        model=config.gemini.model,
        google_api_key=config.gemini.api_key,
        temperature=config.gemini.temperature,
    )
    
    # Bind Google Search tool for grounding
    # This enables real-time web search during generation
    llm_with_search = llm.bind_tools([{"google_search": {}}])
    
    return llm_with_search


def create_openai_with_search(config: DiscoveryConfig) -> BaseChatModel:
    """Create OpenAI LLM with Web Search for product details.
    
    Uses the Responses API with web_search tool.
    """
    llm = ChatOpenAI(
        model=config.openai.model,
        api_key=config.openai.api_key,
        temperature=config.openai.temperature,
        use_responses_api=True,  # Required for web search tool
    )
    
    # Bind Web Search tool (Responses API)
    # This enables real-time web search during generation
    llm_with_search = llm.bind_tools([{"type": "web_search"}])
    
    return llm_with_search


# =============================================================================
# Chain Builders
# =============================================================================

def build_brands_discovery_chain(config: DiscoveryConfig):
    """Build the chain for discovering brands using Gemini + Google Search.
    
    Returns a chain that outputs a BrandList Pydantic model.
    """
    system_prompt = load_prompt("brands_discovery_system.txt")
    user_prompt = load_prompt("brands_discovery_user.txt")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt),
    ])
    
    # Create Gemini with Google Search, then add structured output
    llm = ChatGoogleGenerativeAI(
        model=config.gemini.model,
        google_api_key=config.gemini.api_key,
        temperature=config.gemini.temperature,
    )
    
    # For structured output with search, we use the base LLM with structured output
    # The search grounding enhances the model's knowledge
    structured_llm = llm.bind_tools(
        [{"google_search": {}}]
    ).with_structured_output(BrandList)
    
    return prompt | structured_llm


def build_product_details_chain(config: DiscoveryConfig):
    """Build the chain for getting product details using OpenAI + Web Search.
    
    Returns a chain that outputs raw text (JSON) for manual parsing.
    Note: We don't use .with_structured_output() as it conflicts with web_search tool.
    """
    system_prompt = load_prompt("product_details_system.txt")
    user_prompt = load_prompt("product_details_user.txt")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt),
    ])
    
    # Create OpenAI with Web Search (Responses API)
    # Note: NOT using .with_structured_output() as it conflicts with web_search tool
    llm = ChatOpenAI(
        model=config.openai.model,
        api_key=config.openai.api_key,
        temperature=config.openai.temperature,
        use_responses_api=True,  # Required for web search tool
    )
    
    # Bind web search tool only - no structured output (conflicts with web_search)
    llm_with_search = llm.bind_tools([{"type": "web_search"}])
    
    return prompt | llm_with_search


# =============================================================================
# Main Discovery Class
# =============================================================================

class ProductDiscovery:
    """Découvre des produits via LLM avec architecture en deux étapes.
    
    Architecture:
    - Étape 1: Gemini + Google Search → Liste des marques
    - Étape 2: OpenAI + Web Search → Détails par marque
    """

    def __init__(self, config: Optional[DiscoveryConfig] = None):
        """Initialise le service de découverte.

        Args:
            config: Configuration optionnelle. Si None, utilise la config globale.
        """
        self.config = config or get_config()
        
        # Build chains
        self.brands_chain = build_brands_discovery_chain(self.config)
        self.details_chain = build_product_details_chain(self.config)
        
        print(f"[ProductDiscovery] Initialisé")
        print(f"  - Étape 1 (Marques): {self.config.gemini.model} + Google Search")
        print(f"  - Étape 2 (Détails): {self.config.openai.model} + Web Search")

    def discover_brands(
        self,
        category: str,
        count: int = 30,
        country: str = "France"
    ) -> List[Brand]:
        """Étape 1: Découvre les marques via Gemini + Google Search.
        
        Args:
            category: Catégorie de produit (ex: "lait d'avoine")
            count: Nombre de marques à découvrir
            country: Pays cible
            
        Returns:
            Liste d'objets Brand
        """
        print(f"\n[Étape 1] Découverte de {count} marques '{category}' via Gemini...")
        print(f"  Modèle: {self.config.gemini.model} + Google Search grounding")
        
        result: BrandList = self.brands_chain.invoke({
            "count": count,
            "category": category,
            "country": country,
        })
        
        print(f"[Étape 1] ✓ {len(result.brands)} marques découvertes:")
        for i, brand in enumerate(result.brands, 1):
            origin = f" ({brand.country_of_origin})" if brand.country_of_origin else ""
            print(f"  {i:2}. {brand.name}{origin}")
        
        return result.brands

    def get_product_details(
        self,
        brand: Brand,
        category: str,
        country: str = "France"
    ) -> Optional[ProductDetails]:
        """Étape 2: Obtient les détails via OpenAI + Web Search.
        
        Args:
            brand: Objet Brand
            category: Catégorie de produit
            country: Pays cible
            
        Returns:
            ProductDetails ou None si erreur
        """
        try:
            # Get raw response (AIMessage) from chain with web search
            result = self.details_chain.invoke({
                "brand": brand.name,
                "category": category,
                "country": country,
            })
            
            # Extract text content from AIMessage
            # Responses API returns content as a list of content blocks
            content = result.content if hasattr(result, 'content') else result
            
            if isinstance(content, list):
                # Extract text from content blocks
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        # Handle dict format: {"type": "text", "text": "..."}
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                    elif hasattr(block, 'text'):
                        # Handle object format with .text attribute
                        text_parts.append(block.text)
                    elif isinstance(block, str):
                        text_parts.append(block)
                raw_text = "\n".join(text_parts)
            else:
                raw_text = str(content)
            
            # Parse JSON from response
            json_str = extract_json(raw_text)
            data = json.loads(json_str)
            
            # Convert to ProductDetails model
            return ProductDetails(
                brand=data.get("brand", brand.name),
                full_name=data.get("full_name", ""),
                brand_website=data.get("brand_website"),
                product_url=data.get("product_url"),
                price_segment=data.get("price_segment", "moyen"),
                distribution=data.get("distribution", ""),
                value_proposition=data.get("value_proposition", ""),
                target_audience=data.get("target_audience", ""),
            )
        except json.JSONDecodeError as e:
            print(f"  [!] Erreur JSON pour {brand.name}: {e}")
            return None
        except Exception as e:
            print(f"  [!] Erreur pour {brand.name}: {e}")
            return None

    def get_product_details_parallel(
        self,
        brands: List[Brand],
        category: str,
        country: str = "France"
    ) -> List[Tuple[Brand, Optional[ProductDetails]]]:
        """Étape 2 PARALLÉLISÉE: Obtient les détails pour toutes les marques.
        
        Uses ParallelExecutor for concurrent API calls with rate limiting.
        
        Args:
            brands: Liste de Brand objects
            category: Catégorie de produit
            country: Pays cible
            
        Returns:
            List of (brand, details) tuples in original order
        """
        if not brands:
            return []
        
        # Create executor with OpenAI limits from config
        limits = ProviderLimits(
            max_concurrent=self.config.parallel.openai.max_concurrent,
            rate_limit_rpm=self.config.parallel.openai.rate_limit_rpm,
            min_delay_seconds=self.config.parallel.openai.min_delay_seconds
        )
        executor = ParallelExecutor(provider=Provider.OPENAI, limits=limits)
        
        # Create async wrapper for the sync get_product_details method
        async def process_brand(brand: Brand) -> Optional[ProductDetails]:
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                lambda: self.get_product_details(brand, category, country)
            )
        
        # Progress callback
        completed_count = [0]
        def on_progress(completed: int, total: int, status: str, item_id: Optional[str]):
            completed_count[0] = completed
            if item_id:
                print(f"  [{completed:2}/{total}] {item_id}... {status}", flush=True)
        
        # Execute in parallel
        print(f"  [Parallel] Processing {len(brands)} brands with {limits.max_concurrent} concurrent requests")
        batch_result = executor.execute_sync(
            items=brands,
            process_func=process_brand,
            get_item_id=lambda b: b.name,
            progress_callback=on_progress
        )
        
        print(f"  [Parallel] Done: {batch_result.successful_count}/{batch_result.total_items} succeeded "
              f"in {batch_result.total_duration_seconds:.1f}s")
        
        # Reconstruct results in original order
        results: List[Tuple[Brand, Optional[ProductDetails]]] = []
        ordered_results = batch_result.get_all_results_ordered()
        for brand, details in zip(brands, ordered_results):
            results.append((brand, details))
        
        return results

    def discover_products(
        self,
        category: str,
        count: int = 30,
        country: str = "France",
        city: Optional[str] = None,  # Kept for API compatibility
        parallel: bool = True  # Enable parallelization by default
    ) -> List[Product]:
        """Découvre des produits via pipeline LLM en 2 étapes.

        Args:
            category: Catégorie de produit (ex: "lait d'avoine")
            count: Nombre de produits à découvrir
            country: Pays cible (défaut: France)
            city: Ville optionnelle (non utilisée actuellement)
            parallel: Use parallel execution for Step 2 (default: True)

        Returns:
            Liste d'objets Product
        """
        print("=" * 70)
        print(f"DÉCOUVERTE DE PRODUITS: {category}")
        print("=" * 70)
        
        # Étape 1: Découvrir les marques (Gemini + Google Search)
        brands = self.discover_brands(category, count, country)
        
        if not brands:
            print("[!] Aucune marque découverte")
            return []
        
        # Étape 2: Obtenir les détails pour chaque marque (OpenAI + Web Search)
        print(f"\n[Étape 2] Récupération des détails pour {len(brands)} marques via OpenAI...")
        print(f"  Modèle: {self.config.openai.model} + Web Search")
        
        if parallel and len(brands) > 1:
            # PARALLEL execution
            print(f"  Mode: PARALLEL ({self.config.parallel.openai.max_concurrent} concurrent)")
            print("-" * 70)
            
            results = self.get_product_details_parallel(brands, category, country)
            
            products: List[Product] = []
            for brand, details in results:
                if details:
                    product = Product.from_product_details(details, category)
                    products.append(product)
        else:
            # SEQUENTIAL execution (fallback)
            print("  Mode: SEQUENTIAL")
            print("-" * 70)
            
            products: List[Product] = []
            
            for i, brand in enumerate(brands, 1):
                print(f"  [{i:2}/{len(brands)}] {brand.name}...", end=" ", flush=True)
                
                details = self.get_product_details(brand, category, country)
                
                if details:
                    product = Product.from_product_details(details, category)
                    products.append(product)
                    site = details.brand_website or "—"
                    print(f"✓ {details.full_name[:40]} | {site}")
                else:
                    print("✗ Échec")
        
        print("-" * 70)
        print(f"[Résultat] {len(products)}/{len(brands)} produits récupérés")
        
        return products


# =============================================================================
# Convenience Functions
# =============================================================================

def discover_products(
    category: str,
    count: int = 30,
    country: str = "France"
) -> List[Product]:
    """Fonction utilitaire pour découvrir des produits.
    
    Args:
        category: Catégorie de produit
        count: Nombre de produits
        country: Pays cible
        
    Returns:
        Liste de Product
    """
    discovery = ProductDiscovery()
    return discovery.discover_products(category, count, country)
