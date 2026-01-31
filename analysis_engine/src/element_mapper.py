"""Element mapping module for rebrand pipeline Step 3.

This module uses Claude Opus 4.5 to create intelligent element-by-element
mappings between inspiration and source elements.

For each element in the inspiration, decides whether to:
- keep: Use the inspiration element as-is
- replace: Replace with a source element or constraint text
- omit: Remove the element (only if constraints forbid it)

Uses Anthropic Claude Opus 4.5 - pure text, no images.
"""
import json
from typing import Optional

from anthropic import Anthropic

from .config import get_config, DiscoveryConfig
from .models import (
    InspirationExtraction,
    SourceExtraction,
    RebrandMapping,
    ElementMappingEntry,
    RebrandColorScheme,
)
from .utils import load_prompt


# =============================================================================
# Step 3: Element Mapping with Opus 4.5
# =============================================================================

def format_extraction_for_prompt(extraction, label: str) -> str:
    """Format extraction data into a readable string for the prompt.
    
    Args:
        extraction: InspirationExtraction or SourceExtraction
        label: Label for the section (e.g., 'INSPIRATION', 'SOURCE')
        
    Returns:
        Formatted string for prompt inclusion
    """
    lines = [f"## {label} ELEMENTS"]
    lines.append("")
    
    for elem in extraction.elements:
        lines.append(f"[{elem.element_id}]")
        lines.append(f"  Type: {elem.element_type}")
        lines.append(f"  Content: \"{elem.content}\"")
        lines.append(f"  Position: {elem.position}")
        lines.append(f"  Size: {elem.size_percentage}%")
        lines.append(f"  Hierarchy: {elem.hierarchy_level}/5")
        lines.append(f"  Visual: {elem.visual_description}")
        lines.append("")
    
    # Add color palette
    lines.append("COLOR PALETTE:")
    for color in extraction.color_palette:
        lines.append(f"  - {color.color_name}: {color.hex_code} ({color.usage})")
    
    return "\n".join(lines)


def format_composition_for_prompt(composition) -> str:
    """Format composition description for the prompt."""
    lines = [
        "## COMPOSITION STRUCTURE",
        f"Layout: {composition.layout_type}",
        f"Visual Flow: {composition.visual_flow}",
        f"Balance: {composition.balance}",
        f"Dominant Zone: {composition.dominant_zone}",
        f"Whitespace: {', '.join(composition.whitespace_zones)}",
        f"Style: {composition.overall_style}",
    ]
    return "\n".join(lines)


def create_element_mapping(
    inspiration: InspirationExtraction,
    source: SourceExtraction,
    brand_identity: str,
    config: Optional[DiscoveryConfig] = None
) -> tuple[Optional[RebrandMapping], dict]:
    """Step 3: Create element-by-element mapping using Opus 4.5.
    
    For each inspiration element, determines the best action (keep/replace/omit)
    and specifies the replacement content if needed.
    
    This is a pure text call - no images are sent to the model.
    The model works from the extracted element descriptions.
    
    Args:
        inspiration: Extraction result from inspiration image (Step 1)
        source: Extraction result from source image (Step 2)
        brand_identity: User-provided brand identity and constraints
        config: Optional configuration
        
    Returns:
        Tuple of (RebrandMapping, debug_info_dict) where debug_info contains prompts and response
    """
    debug_info = {
        "system_prompt": "",
        "user_prompt": "",
        "raw_response": "",
        "model": "",
    }
    if config is None:
        config = get_config()
    
    print("[Step 3] Creating element mapping with Opus 4.5...")
    print(f"  Inspiration elements: {len(inspiration.elements)}")
    print(f"  Source elements: {len(source.elements)}")
    
    # Initialize Anthropic client
    client = Anthropic(api_key=config.anthropic.api_key)
    
    # Load prompts
    system_prompt = load_prompt("element_mapping_system.txt")
    user_prompt_template = load_prompt("element_mapping_user.txt")
    
    # Format data for prompt
    inspiration_text = format_extraction_for_prompt(inspiration, "INSPIRATION")
    source_text = format_extraction_for_prompt(source, "SOURCE")
    composition_text = format_composition_for_prompt(inspiration.composition)
    
    # Build element ID lists for reference
    insp_ids = [e.element_id for e in inspiration.elements]
    src_ids = [e.element_id for e in source.elements]
    
    # Build user prompt
    user_prompt = user_prompt_template.format(
        inspiration_elements=inspiration_text,
        source_elements=source_text,
        composition=composition_text,
        brand_identity=brand_identity,
        source_brand=source.brand_name,
        source_product=source.product_name,
        source_claims=", ".join(source.available_claims) if source.available_claims else "None detected",
        inspiration_element_ids=", ".join(insp_ids),
        source_element_ids=", ".join(src_ids),
        total_mappings_needed=len(inspiration.elements)
    )
    
    # Store prompts in debug info
    debug_info["system_prompt"] = system_prompt
    debug_info["user_prompt"] = user_prompt
    debug_info["model"] = config.anthropic.model
    
    try:
        # Call Opus 4.5
        response = client.messages.create(
            model=config.anthropic.model,
            max_tokens=config.anthropic.max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract response text
        response_text = response.content[0].text
        debug_info["raw_response"] = response_text
        
        # Parse JSON from response
        # Handle potential markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        result_data = json.loads(response_text)
        
        # Build mappings list
        mappings = []
        for mapping_data in result_data.get('mappings', []):
            mapping = ElementMappingEntry(
                inspiration_element_id=mapping_data.get('inspiration_element_id', ''),
                action=mapping_data.get('action', 'keep'),
                replacement_source=mapping_data.get('replacement_source'),
                replacement_content=mapping_data.get('replacement_content', ''),
                styling_notes=mapping_data.get('styling_notes', ''),
                reasoning=mapping_data.get('reasoning')
            )
            mappings.append(mapping)
        
        # Build color scheme
        color_data = result_data.get('color_scheme', {})
        color_scheme = RebrandColorScheme(
            primary=color_data.get('primary', '#000000'),
            secondary=color_data.get('secondary', '#FFFFFF'),
            background=color_data.get('background', '#FFFFFF'),
            text_primary=color_data.get('text_primary', '#000000'),
            text_secondary=color_data.get('text_secondary'),
            accent=color_data.get('accent')
        )
        
        # Build final mapping result
        mapping_result = RebrandMapping(
            mappings=mappings,
            composition_description=result_data.get('composition_description', ''),
            color_scheme=color_scheme,
            assembly_notes=result_data.get('assembly_notes', '')
        )
        
        # Log summary
        actions = {'keep': 0, 'replace': 0, 'omit': 0}
        for m in mappings:
            actions[m.action] = actions.get(m.action, 0) + 1
        
        print(f"  [✓] Created {len(mappings)} mappings")
        print(f"    Keep: {actions['keep']}, Replace: {actions['replace']}, Omit: {actions['omit']}")
        
        return mapping_result, debug_info
        
    except json.JSONDecodeError as e:
        print(f"  [!] JSON parsing error: {e}")
        print(f"  Response text: {response_text[:500]}...")
        return None, debug_info
    except Exception as e:
        print(f"  [!] Mapping error: {e}")
        return None, debug_info


def validate_mapping(
    mapping: RebrandMapping,
    inspiration: InspirationExtraction
) -> tuple[bool, list[str]]:
    """Validate that the mapping covers all inspiration elements.
    
    Args:
        mapping: The mapping result to validate
        inspiration: Original inspiration extraction
        
    Returns:
        Tuple of (is_valid, list of warning messages)
    """
    warnings = []
    
    # Get all inspiration element IDs
    insp_ids = {e.element_id for e in inspiration.elements}
    
    # Get all mapped element IDs
    mapped_ids = {m.inspiration_element_id for m in mapping.mappings}
    
    # Check for missing mappings
    missing = insp_ids - mapped_ids
    if missing:
        warnings.append(f"Missing mappings for: {', '.join(missing)}")
    
    # Check for extra mappings (referencing non-existent elements)
    extra = mapped_ids - insp_ids
    if extra:
        warnings.append(f"Mappings for non-existent elements: {', '.join(extra)}")
    
    # Check that replace actions have replacement content
    for m in mapping.mappings:
        if m.action == 'replace' and not m.replacement_content:
            warnings.append(f"Replace action for {m.inspiration_element_id} has no replacement content")
    
    is_valid = len(warnings) == 0
    
    if warnings:
        print(f"  [!] Mapping validation warnings:")
        for w in warnings:
            print(f"    - {w}")
    else:
        print(f"  [✓] Mapping validation passed")
    
    return is_valid, warnings
