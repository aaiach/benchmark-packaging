"""Utilitaires pour le scraper de produits."""
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, TypeVar

T = TypeVar('T')


def invoke_with_retry(
    llm_call: Callable[[], T],
    max_retries: int = 3,
    delay: float = 1.0,
    label: str = "LLM"
) -> T:
    """Retry wrapper for LLM calls that may fail on JSON parsing.
    
    Args:
        llm_call: Zero-argument callable that invokes the LLM
        max_retries: Maximum number of attempts (default 3)
        delay: Seconds to wait between retries (default 1.0)
        label: Label for logging (default "LLM")
    
    Returns:
        The result from the successful LLM call
    
    Raises:
        The last exception if all retries fail
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return llm_call()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                print(f"    [!] {label} attempt {attempt + 1} failed: {str(e)[:80]}... retrying")
                time.sleep(delay)
    raise last_error

# Répertoire des prompts
PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(filename: str) -> str:
    """Charge un template de prompt depuis le répertoire prompts."""
    prompt_path = PROMPTS_DIR / filename
    return prompt_path.read_text(encoding="utf-8").strip()


def extract_json(text: str, verbose: bool = False) -> str:
    """Extrait le JSON d'une réponse qui peut contenir du texte autour.
    
    Gère les cas où le LLM ajoute du texte avant/après le JSON.
    
    Args:
        text: Texte brut contenant potentiellement du JSON
        verbose: Afficher les détails de debug
        
    Returns:
        Chaîne JSON extraite
    """
    if not text:
        if verbose:
            print("[DEBUG extract_json] Texte vide")
        return "[]"
        
    cleaned = text.strip()
    
    # Cas 1: Bloc de code markdown ```json ... ```
    if "```json" in cleaned:
        match = re.search(r'```json\s*([\s\S]*?)\s*```', cleaned)
        if match:
            if verbose:
                print("[DEBUG extract_json] Trouvé bloc ```json```")
            return match.group(1).strip()
    
    # Cas 2: Bloc de code markdown ``` ... ```
    if "```" in cleaned:
        match = re.search(r'```\s*([\s\S]*?)\s*```', cleaned)
        if match:
            if verbose:
                print("[DEBUG extract_json] Trouvé bloc ```")
            return match.group(1).strip()

    # Cas 3: Trouver le premier '[' et le dernier ']' pour un tableau
    first_bracket = cleaned.find('[')
    last_bracket = cleaned.rfind(']')
    
    if verbose:
        print(f"[DEBUG extract_json] Position '[': {first_bracket}, ']': {last_bracket}")
    
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        if verbose:
            print("[DEBUG extract_json] Extraction tableau [...]")
        return cleaned[first_bracket:last_bracket + 1]

    # Cas 4: Trouver le premier '{' et le dernier '}' pour un objet
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    
    if verbose:
        print(f"[DEBUG extract_json] Position '{{': {first_brace}, '}}': {last_brace}")
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        if verbose:
            print("[DEBUG extract_json] Extraction objet {...}")
        return cleaned[first_brace:last_brace + 1]

    # Cas 5: JSON tronqué - essayer de fermer le tableau
    if first_bracket != -1 and last_bracket == -1:
        partial = cleaned[first_bracket:]
        last_obj_end = partial.rfind('}')
        if last_obj_end != -1:
            if verbose:
                print("[DEBUG extract_json] JSON tronqué, fermeture du tableau")
            return partial[:last_obj_end + 1] + ']'

    if verbose:
        print("[DEBUG extract_json] Aucune extraction, retour texte brut")
    return cleaned


def find_json_objects(text: str) -> List[Dict[str, Any]]:
    """Trouve et parse tous les objets JSON individuels dans un texte.
    
    Utile pour récupérer des données même si le JSON global est mal formé.
    
    Args:
        text: Texte contenant des objets JSON
        
    Returns:
        Liste des objets JSON parsés
    """
    objects = []
    pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(pattern, text)
    
    for match in matches:
        try:
            obj = json.loads(match)
            objects.append(obj)
        except json.JSONDecodeError:
            continue
    
    return objects


def parse_json_response(text: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """Parse une réponse JSON en liste d'objets.
    
    Essaie d'abord de parser le JSON complet, puis tente une récupération
    partielle si ça échoue.
    
    Args:
        text: Texte contenant du JSON
        verbose: Afficher les détails de debug
        
    Returns:
        Liste d'objets dictionnaires
        
    Raises:
        ValueError: Si aucun JSON valide n'est trouvé
    """
    if verbose:
        print(f"\n[DEBUG] Réponse brute ({len(text)} chars):")
        print(f"[DEBUG] Début: {text[:500]}...")
        if len(text) > 500:
            print(f"[DEBUG] Fin: ...{text[-200:]}")
    
    # Extraire le JSON du texte
    json_str = extract_json(text, verbose=verbose)
    
    if verbose:
        print(f"\n[DEBUG] JSON extrait ({len(json_str)} chars):")
        print(f"[DEBUG] {json_str[:500]}...")
    
    try:
        data = json.loads(json_str)
        
        if verbose:
            print(f"[DEBUG] Type de données: {type(data)}")
            if isinstance(data, list):
                print(f"[DEBUG] Nombre d'éléments: {len(data)}")
            elif isinstance(data, dict):
                print(f"[DEBUG] Clés: {list(data.keys())}")
        
        # Normaliser en liste
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Chercher une liste dans les clés communes
            for key in ['products', 'items', 'data', 'produits']:
                if key in data and isinstance(data[key], list):
                    if verbose:
                        print(f"[DEBUG] Liste trouvée dans clé '{key}': {len(data[key])} éléments")
                    return data[key]
            # Sinon retourner l'objet seul dans une liste
            if verbose:
                print("[DEBUG] Objet unique, conversion en liste")
            return [data]
        else:
            raise ValueError(f"Structure JSON inattendue: {type(data)}")
            
    except json.JSONDecodeError as e:
        print(f"Erreur JSON: {e}")
        print(f"Aperçu du JSON extrait: {json_str[:300]}...")
        
        # Tentative de récupération partielle
        objects = find_json_objects(json_str)
        if objects:
            print(f"Récupération partielle: {len(objects)} objets trouvés")
            return objects
            
        raise ValueError("Aucun JSON valide trouvé dans la réponse")


def extract_url_citations(annotations: List[Any]) -> Dict[str, str]:
    """Extrait les URLs vérifiées des annotations OpenAI.
    
    Args:
        annotations: Liste d'annotations de la réponse API
        
    Returns:
        Dict mapping URL -> titre
    """
    verified_urls = {}
    
    for annotation in annotations:
        # Format objet (SDK)
        if hasattr(annotation, 'type') and annotation.type == 'url_citation':
            url_citation = getattr(annotation, 'url_citation', None)
            if url_citation:
                url = getattr(url_citation, 'url', None)
                if url:
                    verified_urls[url] = getattr(url_citation, 'title', '')
        # Format dict
        elif isinstance(annotation, dict) and annotation.get('type') == 'url_citation':
            url_citation = annotation.get('url_citation', {})
            url = url_citation.get('url')
            if url:
                verified_urls[url] = url_citation.get('title', '')
    
    return verified_urls
