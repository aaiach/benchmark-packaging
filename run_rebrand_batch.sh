#!/bin/bash
# =============================================================================
# Batch Rebrand Script
# =============================================================================
# Runs rebrand tasks for all oat milk images against quinoat source image
# Usage: ./run_rebrand_batch.sh [--limit N]
# =============================================================================

set -e

# Parse arguments
LIMIT=0  # 0 means no limit
while [[ $# -gt 0 ]]; do
    case $1 in
        --limit|-l)
            LIMIT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./run_rebrand_batch.sh [--limit N]"
            exit 1
            ;;
    esac
done

# Configuration
API_URL="${API_URL:-http://localhost:5000}"
SOURCE_IMAGE="data/output/rebrand/quinoat.png"
INSPIRATION_DIR="data/output/images/Lait_davoine_20260124_162127"

# Brand identity constraints
BRAND_IDENTITY="L'apparence du logo \"quinoat + recolt\" doit etre inchangée mais son orientation peut varier.
La dominance du noir doit rester (+50%)
Le format exacte de la brique (hauteur longeur)
Le style de dessin d'illustrations doit rester consistent avec le style minimaliste
Voici les uniques trust marks factueles et disponibles. Aucune autre certification n'est légalement utilisable
\"Sans sucre ajouté
Sans conservateurs et colorants
Naturellement sans lactose
Sans soja
Haut taux de céréales
100% végétal
Drapeau belge\""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "==========================================="
echo "Batch Rebrand Script"
echo "==========================================="
echo ""

# Check if source image exists
if [ ! -f "$SOURCE_IMAGE" ]; then
    echo -e "${RED}ERROR: Source image not found at $SOURCE_IMAGE${NC}"
    echo "Please ensure the quinoat.png file exists at the specified location."
    exit 1
fi

# Check if inspiration directory exists
if [ ! -d "$INSPIRATION_DIR" ]; then
    echo -e "${RED}ERROR: Inspiration directory not found at $INSPIRATION_DIR${NC}"
    exit 1
fi

# Check API availability
echo "Checking API availability..."
if ! curl -s "${API_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: API not available at ${API_URL}${NC}"
    echo "Please ensure Docker containers are running: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}API is available${NC}"
echo ""

# Get list of inspiration images (excluding 10_ and 40_ prefixes, and heatmaps folder)
declare -a IMAGES
while IFS= read -r file; do
    filename=$(basename "$file")
    # Skip files starting with 10_ or 40_
    if [[ "$filename" == 10_* ]] || [[ "$filename" == 40_* ]]; then
        echo -e "${YELLOW}Skipping: $filename (excluded by prefix)${NC}"
        continue
    fi
    # Skip non-image files (like .svg)
    if [[ "$filename" == *.svg ]]; then
        echo -e "${YELLOW}Skipping: $filename (SVG not supported)${NC}"
        continue
    fi
    IMAGES+=("$file")
done < <(find "$INSPIRATION_DIR" -maxdepth 1 -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.webp" \) | sort)

echo ""

# Apply limit if specified
if [ "$LIMIT" -gt 0 ] && [ "$LIMIT" -lt "${#IMAGES[@]}" ]; then
    IMAGES=("${IMAGES[@]:0:$LIMIT}")
    echo "Limiting to first $LIMIT images"
fi

echo "Found ${#IMAGES[@]} images to process"
echo "==========================================="
echo ""

# Array to store job IDs
declare -a JOB_IDS

# Submit all rebrand tasks
for img in "${IMAGES[@]}"; do
    filename=$(basename "$img")
    echo -n "Submitting rebrand for: $filename ... "
    
    response=$(curl -s -X POST "${API_URL}/api/rebrand/start" \
        -F "source_image=@${SOURCE_IMAGE}" \
        -F "inspiration_image=@${img}" \
        -F "brand_identity=${BRAND_IDENTITY}")
    
    job_id=$(echo "$response" | grep -o '"job_id": "[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$job_id" ]; then
        echo -e "${GREEN}OK${NC} - Job ID: $job_id"
        JOB_IDS+=("$job_id:$filename")
    else
        echo -e "${RED}FAILED${NC}"
        echo "Response: $response"
    fi
    
    # Small delay to avoid overwhelming the API
    sleep 0.5
done

echo ""
echo "==========================================="
echo "Submitted ${#JOB_IDS[@]} rebrand tasks"
echo "==========================================="
echo ""

# Save job IDs to file for reference
JOBS_FILE="rebrand_jobs_$(date +%Y%m%d_%H%M%S).txt"
echo "Saving job IDs to $JOBS_FILE"
for job in "${JOB_IDS[@]}"; do
    echo "$job" >> "$JOBS_FILE"
done

echo ""
echo "Monitor progress:"
echo "  - Flower UI: http://localhost:5555"
echo "  - Individual status: curl ${API_URL}/api/rebrand/status/<job_id>"
echo ""
echo "List all jobs:"
echo "  curl ${API_URL}/api/rebrand/list"
echo ""
