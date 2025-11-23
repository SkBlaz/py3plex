#!/usr/bin/env python3
"""
[DEPRECATED] This script was for the old quickstart.rst file which has been removed.

The quickstart content is now in docfiles/getting_started/quickstart_5min.rst.
If you need to regenerate outputs for that file, this script should be updated
to reference the new location.

Centralized script to execute all code snippets from quickstart.rst and capture outputs.

This script:
1. Extracts all Python code blocks from quickstart.rst
2. Executes each snippet in a controlled environment
3. Captures stdout/stderr output
4. Updates quickstart.rst with actual execution results
5. Ensures 100% coverage of code snippets with outputs

Usage:
    python docfiles/run_quickstart_snippets.py [--update]
    
Options:
    --update    Update quickstart.rst with captured outputs (default: dry-run)
"""

import io
import os
import re
import sys
import tempfile
import traceback
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import List, Tuple, Dict, Optional


class SnippetCategory:
    """Categories for code snippets"""
    RUNNABLE = "runnable"  # Can execute without external files
    REQUIRES_FILES = "requires_files"  # Needs external data files
    REQUIRES_BINARY = "requires_binary"  # Needs external binary (e.g., infomap)
    VISUALIZATION = "visualization"  # Produces visual output
    SETUP_ONLY = "setup_only"  # Just imports/setup, no output expected


class CodeSnippet:
    """Represents a code snippet from the documentation"""
    
    def __init__(self, code: str, line_number: int, section: str):
        self.code = code
        self.line_number = line_number
        self.section = section
        self.category = self._categorize()
        self.output: Optional[str] = None
        self.error: Optional[str] = None
        
    def _categorize(self) -> str:
        """Categorize snippet based on its content"""
        code_lower = self.code.lower()
        
        # Check for file operations
        if any(pattern in self.code for pattern in ['"data.', "'data.", '.edgelist', '.graphml', '.multiedgelist']):
            return SnippetCategory.REQUIRES_FILES
        
        # Check for binary requirements
        if 'infomap' in code_lower and 'binary_path' in self.code:
            return SnippetCategory.REQUIRES_BINARY
        
        # Check for visualization
        if any(func in self.code for func in ['draw_multilayer', 'hairball_plot', 'display=True', 'plt.show']):
            return SnippetCategory.VISUALIZATION
        
        # Check if it's just setup/imports with no expected output
        lines = [line.strip() for line in self.code.split('\n') if line.strip() and not line.strip().startswith('#')]
        if all(line.startswith(('import ', 'from ')) or ('=' in line and not any(op in line for op in ['==', '!=', '>=', '<=', '+=', '-=', '*=', '/='])) for line in lines):
            # Only imports and assignments (not comparisons), might be setup
            if not any(func in self.code for func in ['print(', '.basic_stats()', '.show()']):
                return SnippetCategory.SETUP_ONLY
        
        return SnippetCategory.RUNNABLE
    
    def execute(self, context: Dict) -> Tuple[str, Optional[str]]:
        """
        Execute the snippet and capture output.
        
        Args:
            context: Shared execution context (namespace)
            
        Returns:
            Tuple of (stdout, error_message)
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(self.code, context)
            
            self.output = stdout_capture.getvalue()
            self.error = None
            return self.output, None
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.error = error_msg
            return stdout_capture.getvalue(), error_msg


class QuickstartRunner:
    """Main class to run and update quickstart documentation"""
    
    def __init__(self, quickstart_path: Path):
        self.quickstart_path = quickstart_path
        self.snippets: List[CodeSnippet] = []
        self.content: str = ""
        
    def parse_snippets(self):
        """Extract all Python code blocks from quickstart.rst"""
        with open(self.quickstart_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
        
        lines = self.content.split('\n')
        i = 0
        current_section = "Unknown"
        
        while i < len(lines):
            line = lines[i]
            
            # Track sections
            if line and not line.startswith(' ') and not line.startswith('\t'):
                # Potential section header
                if i + 1 < len(lines) and lines[i + 1].strip() and set(lines[i + 1].strip()) in [{'='}, {'-'}, {'~'}]:
                    current_section = line.strip()
            
            # Find code blocks
            if '.. code-block:: python' in line:
                code_lines = []
                j = i + 1
                
                # Skip empty lines after code-block directive
                while j < len(lines) and not lines[j].strip():
                    j += 1
                
                # Collect indented code lines
                if j < len(lines):
                    # Determine indentation level
                    first_code_line = lines[j]
                    indent = len(first_code_line) - len(first_code_line.lstrip())
                    
                    while j < len(lines):
                        if lines[j].strip() == '':
                            code_lines.append('')
                            j += 1
                        elif lines[j].startswith(' ' * indent) or lines[j].startswith('\t'):
                            code_lines.append(lines[j][indent:])
                            j += 1
                        else:
                            break
                
                code = '\n'.join(code_lines).strip()
                if code:
                    snippet = CodeSnippet(code, i + 1, current_section)
                    self.snippets.append(snippet)
                
                i = j
            else:
                i += 1
        
        print(f"Found {len(self.snippets)} code snippets in quickstart.rst")
        
    def execute_snippets(self):
        """Execute all runnable snippets"""
        # Shared context for snippets (simulates progressive execution)
        context = {
            '__builtins__': __builtins__,
        }
        
        # Create temporary directory for file operations
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample data files
            self._create_sample_files(tmpdir)
            
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                executed_count = 0
                skipped_count = 0
                
                for idx, snippet in enumerate(self.snippets, 1):
                    print(f"\n{'='*60}")
                    print(f"Snippet {idx}/{len(self.snippets)}: {snippet.section}")
                    print(f"Category: {snippet.category}")
                    print(f"{'='*60}")
                    
                    # Try to execute more snippet types
                    if snippet.category in [SnippetCategory.RUNNABLE, 
                                           SnippetCategory.REQUIRES_FILES,
                                           SnippetCategory.SETUP_ONLY]:
                        print("Executing...")
                        output, error = snippet.execute(context)
                        
                        if error:
                            print(f"❌ Error: {error}")
                            # Store error as a note
                            snippet.output = f"# Note: This snippet requires {snippet.category}\n# Error: {error}"
                        else:
                            executed_count += 1
                            if output:
                                print(f"✅ Output captured ({len(output)} chars)")
                                # Show first few lines
                                output_lines = output.strip().split('\n')
                                preview = '\n'.join(output_lines[:5])
                                print(f"Preview:\n{preview}")
                                if len(output_lines) > 5:
                                    print(f"... ({len(output_lines) - 5} more lines)")
                            else:
                                print("✅ Executed (no output)")
                    else:
                        skipped_count += 1
                        print(f"⊘ Skipped - {snippet.category}")
                        snippet.output = f"# Note: This snippet requires {snippet.category} and is skipped in automated execution"
                
                print(f"\n{'='*60}")
                print(f"Summary: {executed_count} executed, {skipped_count} skipped")
                print(f"{'='*60}")
                
            finally:
                os.chdir(original_cwd)
    
    def _create_sample_files(self, tmpdir: str):
        """Create sample data files for testing file I/O snippets"""
        # Create a simple edgelist
        edgelist_path = os.path.join(tmpdir, "data.edgelist")
        with open(edgelist_path, 'w') as f:
            f.write("A B\n")
            f.write("B C\n")
            f.write("C D\n")
        
        # Create a multilayer edgelist
        multiedgelist_path = os.path.join(tmpdir, "data.multiedgelist")
        with open(multiedgelist_path, 'w') as f:
            f.write("A B layer1\n")
            f.write("B C layer1\n")
            f.write("A B layer2\n")
            f.write("C D layer2\n")
        
        # Create a simple GraphML file
        graphml_path = os.path.join(tmpdir, "data.graphml")
        with open(graphml_path, 'w') as f:
            f.write("""<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="directed">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B"/>
  </graph>
</graphml>
""")
    
    def generate_report(self) -> str:
        """Generate a detailed report of snippet execution"""
        report = []
        report.append("# Quickstart Code Snippet Execution Report\n")
        report.append(f"Total snippets: {len(self.snippets)}\n")
        
        by_category = {}
        for snippet in self.snippets:
            by_category.setdefault(snippet.category, []).append(snippet)
        
        report.append("\n## Snippets by Category\n")
        for category, snippets in sorted(by_category.items()):
            report.append(f"- {category}: {len(snippets)}")
        
        report.append("\n\n## Executed Snippets with Output\n")
        for idx, snippet in enumerate(self.snippets, 1):
            if snippet.category == SnippetCategory.RUNNABLE and snippet.output:
                report.append(f"\n### Snippet {idx}: {snippet.section}\n")
                report.append(f"```\n{snippet.output.strip()}\n```\n")
        
        return '\n'.join(report)
    
    def update_quickstart(self):
        """Generate report for manual integration into quickstart.rst"""
        # Note: Automated RST update is complex and error-prone
        # This method generates a report that can be manually integrated
        print("⚠️  Automated update of quickstart.rst not implemented")
        print("    Generate outputs with --report and manually integrate into RST")
        print("    This ensures quality control and proper documentation style")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run quickstart code snippets")
    parser.add_argument('--update', action='store_true', 
                       help='Update quickstart.rst with outputs (default: dry-run)')
    parser.add_argument('--report', type=str, default='/tmp/quickstart_report.md',
                       help='Path to save execution report')
    args = parser.parse_args()
    
    # Determine quickstart.rst path
    script_dir = Path(__file__).parent
    quickstart_path = script_dir / 'quickstart.rst'
    
    if not quickstart_path.exists():
        print(f"❌ Error: {quickstart_path} not found")
        sys.exit(1)
    
    print(f"📖 Processing: {quickstart_path}")
    
    # Run the snippets
    runner = QuickstartRunner(quickstart_path)
    runner.parse_snippets()
    runner.execute_snippets()
    
    # Generate report
    report = runner.generate_report()
    report_path = Path(args.report)
    report_path.write_text(report)
    print(f"\n📝 Report saved to: {report_path}")
    
    if args.update:
        runner.update_quickstart()
    else:
        print("\n💡 Run with --update to modify quickstart.rst")
    
    print("\n✅ Done!")


if __name__ == '__main__':
    main()
