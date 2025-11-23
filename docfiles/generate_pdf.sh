#!/bin/bash
# Generate PDF documentation from Sphinx RST files
#
# This script builds the py3plex documentation as a PDF using Sphinx and LaTeX.
# The PDF will be placed in the docs/ directory for distribution.
#
# Requirements:
#   - sphinx (pip install sphinx sphinx-rtd-theme)
#   - LaTeX distribution (texlive-latex-base, texlive-latex-extra, latexmk)
#
# Usage:
#   ./generate_pdf.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Py3plex PDF Documentation Generator${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if we're in the docfiles directory
if [ ! -f "conf.py" ]; then
    echo -e "${RED}Error: This script must be run from the docfiles/ directory.${NC}"
    echo "Usage: cd docfiles && ./generate_pdf.sh"
    exit 1
fi

# Check if sphinx-build is available
if ! command -v sphinx-build &> /dev/null; then
    echo -e "${RED}Error: sphinx-build is not installed.${NC}"
    echo "Install with: pip install sphinx sphinx-rtd-theme"
    exit 1
fi

# Check if latexmk is available
if ! command -v latexmk &> /dev/null; then
    echo -e "${RED}Error: latexmk is not installed.${NC}"
    echo "Install LaTeX tools:"
    echo "  Ubuntu/Debian: sudo apt-get install texlive-latex-base texlive-latex-extra latexmk"
    echo "  macOS: brew install --cask mactex"
    exit 1
fi

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf _build/latex

# Build LaTeX files from Sphinx
echo ""
echo -e "${GREEN}Step 1/3: Building LaTeX files from Sphinx documentation...${NC}"
sphinx-build -b latex . _build/latex --keep-going

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Sphinx LaTeX build failed.${NC}"
    exit 1
fi

# Compile PDF
echo ""
echo -e "${GREEN}Step 2/3: Compiling PDF with latexmk...${NC}"
cd _build/latex
latexmk -pdf -interaction=nonstopmode py3plex.tex

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: PDF compilation had some issues, but may have succeeded.${NC}"
fi

# Check if PDF was created
if [ ! -f "py3plex.pdf" ]; then
    echo -e "${RED}Error: PDF file was not created.${NC}"
    exit 1
fi

cd ../..

# Copy PDF to docs directory
echo ""
echo -e "${GREEN}Step 3/3: Copying PDF to docs directory...${NC}"
mkdir -p ../docs
cp _build/latex/py3plex.pdf ../docs/py3plex_documentation.pdf

# Show results
echo ""
echo -e "${GREEN}✓ PDF generation completed successfully!${NC}"
echo ""
echo -e "Output file: ${BLUE}../docs/py3plex_documentation.pdf${NC}"

# Show file size
if command -v du &> /dev/null; then
    SIZE=$(du -h ../docs/py3plex_documentation.pdf | cut -f1)
    echo -e "File size:   ${BLUE}${SIZE}${NC}"
fi

# Show page count (requires pdfinfo)
if command -v pdfinfo &> /dev/null; then
    PAGES=$(pdfinfo ../docs/py3plex_documentation.pdf 2>/dev/null | grep "Pages:" | awk '{print $2}')
    if [ ! -z "$PAGES" ]; then
        echo -e "Pages:       ${BLUE}${PAGES}${NC}"
    fi
fi

echo ""
echo -e "${BLUE}To view the PDF:${NC}"
echo "  Linux:  xdg-open ../docs/py3plex_documentation.pdf"
echo "  macOS:  open ../docs/py3plex_documentation.pdf"
echo ""
