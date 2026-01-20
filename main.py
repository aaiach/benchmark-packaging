"""Point d'entrée principal pour le scraper de produits.

Architecture en deux étapes LLM avec web search:
1. Découverte des marques: Gemini + Google Search grounding
2. Détails par marque: OpenAI + Web Search (Responses API)
3. Scraping optionnel via Firecrawl
"""
import json
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd
from src import ProductDiscovery, ProductScraper, get_config


def main():
    """Fonction principale pour orchestrer la découverte et le scraping."""
    config = get_config()
    
    parser = argparse.ArgumentParser(
        description='Découvre et scrape les informations produits pour une catégorie donnée'
    )
    parser.add_argument(
        'category',
        type=str,
        help='Catégorie de produit à rechercher (ex: "lait d\'avoine")'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=config.default_count,
        help=f'Nombre de produits à découvrir (défaut: {config.default_count})'
    )
    parser.add_argument(
        '--no-scrape',
        action='store_true',
        help='Uniquement découvrir les produits, sans scraper les pages'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=config.output_dir,
        help=f'Répertoire de sortie (défaut: {config.output_dir})'
    )
    parser.add_argument(
        '--country',
        type=str,
        default=config.default_country,
        help=f'Pays cible (défaut: {config.default_country})'
    )

    args = parser.parse_args()

    print("=" * 80)
    print(f"SCRAPER DE PRODUITS - {args.category.upper()}")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  - Étape 1 (Marques):  {config.gemini.model} + Google Search")
    print(f"  - Étape 2 (Détails):  {config.openai.model} + Web Search")
    print(f"  - Pays cible:         {args.country}")
    print(f"  - Nombre demandé:     {args.count}")
    print("=" * 80)

    # Créer le répertoire de sortie
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Timestamp pour les fichiers
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    category_slug = args.category.replace(' ', '_').replace("'", '')

    # ==========================================================================
    # Phase 1: Découverte LLM (2 étapes internes)
    # ==========================================================================
    print("\n" + "=" * 80)
    print("PHASE 1: Découverte via LLM (Gemini → OpenAI)")
    print("=" * 80)

    try:
        discovery = ProductDiscovery(config=config)
        products = discovery.discover_products(
            category=args.category,
            count=args.count,
            country=args.country
        )

        if not products:
            print("\n[!] Aucun produit découvert. Fin.")
            return

        # Afficher le résumé
        print(f"\n{'=' * 70}")
        print(f"RÉSUMÉ DÉCOUVERTE: {len(products)} produits")
        print("=" * 70)
        for i, product in enumerate(products, 1):
            site = product.brand_website or "—"
            name = product.full_name[:35] if product.full_name else "—"
            print(f"{i:2}. {product.brand:<18} | {name:<35} | {site}")

        # Sauvegarder les produits découverts
        discovered_file = output_dir / f"{category_slug}_discovered_{timestamp}.json"
        with open(discovered_file, 'w', encoding='utf-8') as f:
            json.dump(
                [p.to_dict() for p in products],
                f,
                indent=2,
                ensure_ascii=False
            )
        print(f"\n[✓] Produits découverts sauvegardés: {discovered_file}")

    except Exception as e:
        print(f"\n[!] Erreur pendant la découverte: {e}")
        import traceback
        traceback.print_exc()
        return

    # ==========================================================================
    # Phase 2: Scraping Firecrawl (optionnel)
    # ==========================================================================
    if not args.no_scrape:
        print("\n" + "=" * 80)
        print("PHASE 2: Scraping via Firecrawl")
        print("=" * 80)

        try:
            scraper = ProductScraper()
            scraped_products = scraper.scrape_products_batch(products)

            # Sauvegarder les produits scrapés
            scraped_file = output_dir / f"{category_slug}_scraped_{timestamp}.json"
            with open(scraped_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [p.to_dict() for p in scraped_products],
                    f,
                    indent=2,
                    ensure_ascii=False
                )
            print(f"\n[✓] Produits scrapés sauvegardés: {scraped_file}")

            # Créer le CSV
            csv_file = output_dir / f"{category_slug}_results_{timestamp}.csv"
            df_data = []
            for p in scraped_products:
                df_data.append({
                    'Marque': p.brand,
                    'Nom Produit': p.full_name,
                    'Catégorie': p.category,
                    'Public Cible': p.target_audience,
                    'Site Marque': p.brand_website or '',
                    'URL Produit': p.product_url or '',
                    'Prix': p.price or '',
                    'Disponibilité': p.availability or '',
                    'Description': (p.description or '')[:200],
                    'Nb Images': len(p.images) if p.images else 0,
                    'Segment Prix': p.additional_data.get('segment_prix', '') if p.additional_data else '',
                    'Distribution': p.additional_data.get('distribution', '') if p.additional_data else '',
                })

            df = pd.DataFrame(df_data)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            print(f"[✓] CSV sauvegardé: {csv_file}")

            # Résumé final
            print("\n" + "=" * 80)
            print("RÉSUMÉ FINAL")
            print("=" * 80)
            print(f"  Produits découverts:  {len(products)}")
            print(f"  Avec site marque:     {sum(1 for p in scraped_products if p.brand_website)}")
            print(f"  Avec URL produit:     {sum(1 for p in scraped_products if p.product_url)}")
            print(f"  Avec prix:            {sum(1 for p in scraped_products if p.price)}")
            print(f"  Avec images:          {sum(1 for p in scraped_products if p.images)}")
            print("\nFichiers créés:")
            print(f"  - {discovered_file}")
            print(f"  - {scraped_file}")
            print(f"  - {csv_file}")

        except Exception as e:
            print(f"\n[!] Erreur pendant le scraping: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("✓ Terminé!")
    print("=" * 80)


if __name__ == "__main__":
    main()
