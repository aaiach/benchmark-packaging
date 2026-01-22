"""Point d'entrée principal pour le scraper de produits.

Architecture en plusieurs étapes LLM avec web search:
1. Découverte des marques: Gemini + Google Search grounding
2. Détails par marque: OpenAI + Web Search (Responses API)
3. Scraping optionnel via Firecrawl
4. Sélection d'images: OpenAI Mini + téléchargement local
5. Analyse visuelle: Gemini Vision (hiérarchie visuelle, eye-tracking)
6. Génération de heatmaps: Gemini Vision (overlay de chaleur visuelle)

Usage:
    # Nouveau run avec toutes les étapes
    uv run python main.py "lait d'avoine" --steps 1-6
    
    # Nouveau run jusqu'à l'étape 5 (sans heatmaps)
    uv run python main.py "lait d'avoine" --steps 1-5
    
    # Continuer un run existant avec heatmaps
    uv run python main.py --run-id 20260120_184854 --steps 6
    
    # Relancer les étapes 5-6 sur un run existant
    uv run python main.py --run-id 20260120_184854 --steps 5-6
    
    # Lister les runs disponibles
    uv run python main.py --list-runs
    
    # Voir le statut d'un run
    uv run python main.py --run-id 20260120_184854 --status
"""
import argparse
import sys
from pathlib import Path

from src import get_config
from src.pipeline import PipelineContext, STEPS, list_steps
from src.image_selector import list_runs
from src.runner import run_pipeline


def main():
    """Fonction principale pour orchestrer la découverte et le scraping."""
    config = get_config()
    max_step = max(STEPS.keys())
    
    parser = argparse.ArgumentParser(
        description='Découvre et scrape les informations produits pour une catégorie donnée',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s "lait d'avoine" --steps 1-6     # Run complet avec heatmaps
  %(prog)s "lait d'avoine" --steps 1-5     # Sans heatmaps
  %(prog)s --run-id 20260120_184854 --steps 6  # Ajouter heatmaps
  %(prog)s --list-runs                     # Voir les runs existants
  %(prog)s --run-id 20260120_184854 --status   # Statut d'un run
        """
    )
    
    # Positional argument (optional when using --run-id or --list-runs)
    parser.add_argument(
        'category',
        type=str,
        nargs='?',
        default=None,
        help='Catégorie de produit à rechercher (ex: "lait d\'avoine")'
    )
    
    # Step control
    parser.add_argument(
        '--steps',
        type=str,
        default=f"1-{max_step}",
        help=f'Étapes à exécuter: "1-4", "3", "2-3,4" (défaut: 1-{max_step})'
    )
    
    # Resume from existing run
    parser.add_argument(
        '--run-id',
        type=str,
        metavar='RUN_ID',
        help='ID d\'un run existant (ex: 20260120_184854)'
    )
    
    # Discovery settings
    parser.add_argument(
        '--count',
        type=int,
        default=config.default_count,
        help=f'Nombre de produits à découvrir (défaut: {config.default_count})'
    )
    parser.add_argument(
        '--country',
        type=str,
        default=config.default_country,
        help=f'Pays cible (défaut: {config.default_country})'
    )
    
    # Output settings
    parser.add_argument(
        '--output-dir',
        type=str,
        default=config.output_dir,
        help=f'Répertoire de sortie (défaut: {config.output_dir})'
    )
    
    # Information commands
    parser.add_argument(
        '--list-runs',
        action='store_true',
        help='Lister tous les runs disponibles'
    )
    parser.add_argument(
        '--list-steps',
        action='store_true',
        help='Lister toutes les étapes du pipeline'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Afficher le statut d\'un run (nécessite --run-id)'
    )

    # Legacy compatibility (deprecated)
    parser.add_argument(
        '--no-scrape',
        action='store_true',
        help='[DEPRECATED] Utiliser --steps 1-2 à la place'
    )
    parser.add_argument(
        '--no-images',
        action='store_true',
        help='[DEPRECATED] Utiliser --steps 1-3 à la place'
    )
    parser.add_argument(
        '--images-only',
        type=str,
        metavar='RUN_ID',
        help='[DEPRECATED] Utiliser --run-id RUN_ID --steps 4 à la place'
    )

    args = parser.parse_args()
    
    # ==========================================================================
    # Handle legacy arguments with deprecation warnings
    # ==========================================================================
    
    if args.images_only:
        print("[!] AVERTISSEMENT: --images-only est déprécié.")
        print(f"    Utilisez: --run-id {args.images_only} --steps 4")
        print()
        args.run_id = args.images_only
        args.steps = "4"
    
    if args.no_scrape:
        print("[!] AVERTISSEMENT: --no-scrape est déprécié.")
        print("    Utilisez: --steps 1-2")
        print()
        args.steps = "1-2"
    
    if args.no_images:
        print("[!] AVERTISSEMENT: --no-images est déprécié.")
        print("    Utilisez: --steps 1-3")
        print()
        args.steps = "1-3"
    
    # ==========================================================================
    # Handle --list-steps
    # ==========================================================================
    
    if args.list_steps:
        print("\nÉtapes du pipeline:")
        print("-" * 70)
        for step_info in list_steps():
            deps = f" (requiert: {step_info['requires']})" if step_info['requires'] else ""
            print(f"  {step_info['number']}. {step_info['name']:<12} - {step_info['description']}{deps}")
        print("-" * 70)
        return 0
    
    # ==========================================================================
    # Handle --list-runs
    # ==========================================================================
    
    if args.list_runs:
        print("\nRuns disponibles:")
        print("-" * 70)
        runs = list_runs()
        if not runs:
            print("  Aucun run trouvé dans le répertoire de sortie")
        else:
            for run in runs:
                print(f"  {run['run_id']}  |  {run['category']}")
        print("-" * 70)
        return 0
    
    # ==========================================================================
    # Handle --status
    # ==========================================================================
    
    if args.status:
        if not args.run_id:
            print("[!] --status nécessite --run-id")
            return 1
        
        ctx = PipelineContext.from_run_id(args.run_id, args.output_dir)
        if not ctx:
            print(f"[!] Run non trouvé: {args.run_id}")
            return 1
        
        pipeline = Pipeline(STEPS, config)
        pipeline.print_status(ctx)
        return 0
    
    # ==========================================================================
    # Validate category argument
    # ==========================================================================

    # New run requires category
    if not args.run_id and not args.category:
        print("[!] Catégorie requise pour un nouveau run")
        print("    Utilisez: main.py \"catégorie\" --steps 1-4")
        print("    Ou reprenez un run: main.py --run-id RUN_ID --steps N")
        return 1

    # For resuming, load context to get category for printing
    if args.run_id:
        temp_ctx = PipelineContext.from_run_id(args.run_id, args.output_dir)
        if not temp_ctx:
            print(f"[!] Run non trouvé: {args.run_id}")
            print("\nRuns disponibles:")
            for run in list_runs():
                print(f"  {run['run_id']}  |  {run['category']}")
            return 1
        display_category = temp_ctx.category
        display_run_id = args.run_id
    else:
        display_category = args.category
        display_run_id = "nouveau"

    # ==========================================================================
    # Print configuration
    # ==========================================================================

    print("=" * 80)
    print(f"PIPELINE DE PRODUITS - {display_category.upper()}")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  - Run ID:             {display_run_id}")
    print(f"  - Catégorie:          {display_category}")
    print(f"  - Pays:               {args.country}")
    print(f"  - Nombre demandé:     {args.count}")
    print(f"  - Étapes à exécuter:  {args.steps}")
    print(f"  - Répertoire:         {args.output_dir}")
    print("-" * 80)
    print("Modèles LLM:")
    print(f"  - Step 1 (Discovery): {config.gemini.model} + Google Search")
    print(f"  - Step 2 (Details):   {config.openai.model} + Web Search")
    print(f"  - Step 4 (Images):    {config.openai_mini.model}")
    print(f"  - Step 5-6 (Vision):  {config.gemini_vision.model}")
    print("=" * 80)

    # ==========================================================================
    # Run pipeline using runner function
    # ==========================================================================

    result = run_pipeline(
        category=args.category or display_category,
        country=args.country,
        count=args.count,
        output_dir=args.output_dir,
        steps=args.steps,
        run_id=args.run_id
    )

    # ==========================================================================
    # Print summary
    # ==========================================================================

    print("\n" + "=" * 80)
    if result['status'] == 'success':
        print("✓ PIPELINE TERMINÉ AVEC SUCCÈS")
    else:
        print("✗ PIPELINE TERMINÉ AVEC ERREURS")
        print("\nErreurs:")
        for error in result.get('errors', []):
            print(f"  - {error}")
    print("=" * 80)

    print(f"\nRun ID: {result['run_id']}")

    if result['status'] == 'success':
        print("Fichiers créés:")
        for output_file in result.get('output_files', []):
            print(f"  - {Path(args.output_dir) / output_file}")

        # Show next steps hint
        completed = result['completed_steps']
        remaining_steps = [s for s in sorted(STEPS.keys()) if s not in completed and s > max(completed)]
        if remaining_steps:
            print(f"\nPour continuer avec les étapes suivantes:")
            print(f"  uv run python main.py --run-id {result['run_id']} --steps {remaining_steps[0]}-{max(remaining_steps)}")

    return 0 if result['status'] == 'success' else 1


if __name__ == "__main__":
    sys.exit(main())
