#!/usr/bin/env python3
"""
PDF Artifact Verifier Script

This script checks a generated PDF for common text-layer artifacts
that should have been eliminated by the Sphinx configuration fixes.

Usage:
    python verify_pdf_artifacts.py path/to/py3plex_book.pdf

Requirements:
    pip install PyPDF2
"""

import sys
import re
from pathlib import Path

def check_pdf_artifacts(pdf_path):
    """Check PDF for text-layer artifacts."""
    try:
        import PyPDF2
    except ImportError:
        print("ERROR: PyPDF2 not installed. Run: pip install PyPDF2")
        return False
    
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: PDF file not found: {pdf_path}")
        return False
    
    print(f"Checking PDF: {pdf_path}")
    print("-" * 60)
    
    issues_found = []
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)
            print(f"Total pages: {total_pages}")
            
            # Artifacts to check for
            artifacts = {
                '˓→': 'Code wrap continuation marker',
                '␣': 'Visible space marker',
                '￾': 'Soft-hyphen/Unicode artifact',
            }
            
            # Track which artifacts were found
            found_artifacts = {key: [] for key in artifacts.keys()}
            
            # Check each page
            for page_num in range(total_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                for artifact, description in artifacts.items():
                    if artifact in text:
                        found_artifacts[artifact].append(page_num + 1)
            
            # Report findings
            print("\nArtifact Check Results:")
            print("-" * 60)
            
            any_found = False
            for artifact, description in artifacts.items():
                pages = found_artifacts[artifact]
                if pages:
                    any_found = True
                    print(f" {description} ({repr(artifact)})")
                    print(f"   Found on pages: {', '.join(map(str, pages[:10]))}")
                    if len(pages) > 10:
                        print(f"   ... and {len(pages) - 10} more pages")
                    issues_found.append(f"{description} on {len(pages)} pages")
                else:
                    print(f" {description} ({repr(artifact)}) - CLEAN")
            
            # Check for "(continues on next page)" in code blocks
            # This is harder to verify automatically, but we can look for the pattern
            continues_pattern = re.compile(r'\(continues on next page\)', re.IGNORECASE)
            continues_pages = []
            
            for page_num in range(total_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                if continues_pattern.search(text):
                    continues_pages.append(page_num + 1)
            
            print(f"\n'(continues on next page)' markers:")
            if continues_pages:
                print(f" Found on pages: {', '.join(map(str, continues_pages[:10]))}")
                if len(continues_pages) > 10:
                    print(f"   ... and {len(continues_pages) - 10} more pages")
                print("   Note: These may be intentional in tables/figures")
            else:
                print(" No continuation markers found")
            
            print("-" * 60)
            
            if any_found:
                print("\n FAILED: Found artifacts that should have been eliminated")
                print("\nIssues found:")
                for issue in issues_found:
                    print(f"  - {issue}")
                return False
            else:
                print("\n PASSED: No problematic artifacts found!")
                return True
                
    except Exception as e:
        print(f"ERROR: Failed to read PDF: {e}")
        return False

def check_docker_consistency(pdf_path):
    """Check Docker chapter for port consistency."""
    try:
        import PyPDF2
    except ImportError:
        return None
    
    print("\n" + "=" * 60)
    print("Docker Chapter Consistency Check")
    print("=" * 60)
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            # Look for Docker appendix (usually near the end)
            issues = []
            port_5000_pages = []
            port_8000_pages = []
            version_pages = []
            
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                # Check for port references
                if 'gui:5000' in text or 'localhost:5000' in text:
                    port_5000_pages.append(page_num + 1)
                
                if 'gui:8000' in text or 'localhost:8000' in text:
                    port_8000_pages.append(page_num + 1)
                
                # Check for version references
                if 'py3plex:2.0.0' in text:
                    version_pages.append(page_num + 1)
            
            print("\nPort References:")
            if port_5000_pages:
                print(f" Port 5000 found on pages: {', '.join(map(str, port_5000_pages))}")
                issues.append("Old port 5000 still present")
            else:
                print(" No old port 5000 references found")
            
            if port_8000_pages:
                print(f" Port 8000 found on pages: {', '.join(map(str, port_8000_pages))}")
            
            print("\nVersion References:")
            if version_pages:
                print(f" Version 2.0.0 found on pages: {', '.join(map(str, version_pages))}")
            
            if issues:
                print(f"\n Found {len(issues)} consistency issues")
                return False
            else:
                print("\n Docker chapter appears consistent")
                return True
                
    except Exception as e:
        print(f"ERROR: Failed to check Docker consistency: {e}")
        return None

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python verify_pdf_artifacts.py path/to/py3plex_book.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Run checks
    artifacts_ok = check_pdf_artifacts(pdf_path)
    docker_ok = check_docker_consistency(pdf_path)
    
    # Exit with appropriate code
    if artifacts_ok and (docker_ok is None or docker_ok):
        sys.exit(0)
    else:
        sys.exit(1)
