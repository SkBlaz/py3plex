#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test DSL Patterns Quick Reference File
======================================

Validates that the dsl_patterns_quick_reference.py file contains all
essential patterns for onboarding.
"""

import os
import pytest


def test_quick_reference_file_exists():
    """Test that the quick reference file exists."""
    path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'examples',
        'getting_started',
        'dsl_patterns_quick_reference.py'
    )
    assert os.path.exists(path), f"Quick reference file not found at {path}"


def test_quick_reference_has_essential_patterns():
    """Test that quick reference contains all 7 essential patterns."""
    path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'examples',
        'getting_started',
        'dsl_patterns_quick_reference.py'
    )
    
    with open(path, 'r') as f:
        content = f.read()
    
    # Essential patterns that must be present (check for pattern numbers)
    essential_patterns = [
        "Pattern 1:",
        "Pattern 2:",
        "Pattern 3:", 
        "Pattern 4:",
        "Pattern 5:",
        "Pattern 6:",
        "Pattern 7:"
    ]
    
    for pattern in essential_patterns:
        assert pattern in content, f"Missing essential pattern: {pattern}"
    
    # Verify key concepts are covered
    assert "filtering" in content.lower() or "where" in content.lower()
    assert "layer" in content.lower()
    assert "uncertainty" in content.lower() or "uq" in content.lower()
    assert "aggregate" in content.lower() or "aggregation" in content.lower()


def test_quick_reference_has_code_examples():
    """Test that quick reference has executable code examples."""
    path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'examples',
        'getting_started',
        'dsl_patterns_quick_reference.py'
    )
    
    with open(path, 'r') as f:
        content = f.read()
    
    # Should have imports
    assert "from py3plex.dsl import Q" in content
    assert "from py3plex.core import multinet" in content
    
    # Should have key DSL methods
    assert "Q.nodes()" in content
    assert ".where(" in content
    assert ".compute(" in content
    assert ".execute(" in content
    
    # Should demonstrate layer algebra
    assert 'L["' in content or "L['" in content
    
    # Should demonstrate UQ
    assert ".uq(" in content or "uncertainty" in content.lower()


def test_quick_reference_has_comments():
    """Test that quick reference has helpful comments."""
    path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'examples',
        'getting_started',
        'dsl_patterns_quick_reference.py'
    )
    
    with open(path, 'r') as f:
        content = f.read()
    
    # Count comment lines
    comment_lines = [line for line in content.split('\n') if line.strip().startswith('#')]
    
    # Should have at least 15 comment lines for basic documentation
    assert len(comment_lines) >= 15, f"Expected at least 15 comment lines, found {len(comment_lines)}"


def test_quick_reference_is_runnable():
    """Test that quick reference file is syntactically valid Python."""
    path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'examples',
        'getting_started',
        'dsl_patterns_quick_reference.py'
    )
    
    with open(path, 'r') as f:
        content = f.read()
    
    # Should be valid Python syntax
    try:
        compile(content, path, 'exec')
    except SyntaxError as e:
        pytest.fail(f"Quick reference has syntax error: {e}")
