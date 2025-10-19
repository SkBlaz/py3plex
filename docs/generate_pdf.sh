#!/bin/bash
# Generate PDF documentation from Markdown using Pandoc
#
# Requirements:
#   - pandoc (https://pandoc.org/installing.html)
#   - xelatex (from TeX Live or MiKTeX)
#
# Usage:
#   ./generate_pdf.sh
#   ./generate_pdf.sh MASTER_DOCUMENTATION.md output.pdf

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default input/output
INPUT="${1:-MASTER_DOCUMENTATION.md}"
OUTPUT="${2:-py3plex_documentation.pdf}"

echo -e "${GREEN}Generating PDF documentation...${NC}"
echo "Input:  $INPUT"
echo "Output: $OUTPUT"
echo ""

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo -e "${RED}Error: pandoc is not installed.${NC}"
    echo "Install with: sudo apt-get install pandoc (Ubuntu/Debian)"
    echo "Or visit: https://pandoc.org/installing.html"
    exit 1
fi

# Check if xelatex is installed
if ! command -v xelatex &> /dev/null; then
    echo -e "${YELLOW}Warning: xelatex not found. Trying pdflatex...${NC}"
    PDF_ENGINE="pdflatex"
else
    PDF_ENGINE="xelatex"
fi

# Check if input file exists
if [ ! -f "$INPUT" ]; then
    echo -e "${RED}Error: Input file '$INPUT' not found.${NC}"
    exit 1
fi

# Generate PDF
echo -e "${GREEN}Running pandoc with $PDF_ENGINE...${NC}"
pandoc "$INPUT" \
    -o "$OUTPUT" \
    --pdf-engine="$PDF_ENGINE" \
    --toc \
    --toc-depth=3 \
    --number-sections \
    -V geometry:margin=1in \
    -V fontsize=10pt \
    -V documentclass=article \
    -V linkcolor=blue \
    -V urlcolor=blue \
    --highlight-style=tango \
    --metadata title="Py3plex Documentation" \
    --metadata author="Blaž Škrlj, Jan Kralj, Nada Lavrač" \
    --metadata date="$(date +'%B %Y')"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ PDF generated successfully: $OUTPUT${NC}"
    
    # Show file size
    if command -v du &> /dev/null; then
        SIZE=$(du -h "$OUTPUT" | cut -f1)
        echo "  Size: $SIZE"
    fi
    
    # Show page count (requires pdfinfo)
    if command -v pdfinfo &> /dev/null; then
        PAGES=$(pdfinfo "$OUTPUT" 2>/dev/null | grep "Pages:" | awk '{print $2}')
        echo "  Pages: $PAGES"
    fi
else
    echo -e "${RED}✗ PDF generation failed.${NC}"
    exit 1
fi

echo ""
echo "To view: xdg-open $OUTPUT  # Linux"
echo "         open $OUTPUT      # macOS"
