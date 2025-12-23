import importlib
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture
def conf_module(monkeypatch):
    """Load book.conf with a clean sys.path and controlled cwd."""
    book_dir = Path(__file__).resolve().parent.parent / "book"
    monkeypatch.chdir(book_dir)

    expected_path = os.path.abspath("../py3plex")

    # Remove any pre-existing copy so we can verify insertion.
    cleaned_path = [p for p in sys.path if os.path.abspath(p) != expected_path]
    monkeypatch.setattr(sys, "path", cleaned_path)

    sys.modules.pop("book.conf", None)
    module = importlib.import_module("book.conf")
    try:
        yield module, expected_path
    finally:
        sys.modules.pop("book.conf", None)


def test_conf_inserts_py3plex_path_once(conf_module):
    module, expected_path = conf_module

    assert sys.path[0] == expected_path
    assert sys.path.count(expected_path) == 1
    assert module.sys.path[0] == expected_path  # module sees same mutation


def test_conf_exposes_expected_metadata(conf_module):
    module, expected_path = conf_module

    assert module.project == "Practical Multilayer Network Analysis with Py3plex"
    assert module.version == module.release == "1.0.3"
    assert module.language == "en"
    assert module.master_doc == "index"
    assert module.templates_path == ["_templates"]
    assert module.html_theme == "sphinx_rtd_theme"
    assert module.html_css_files == ["custom.css"]
    assert module.html_static_path == ["_static"]
    assert module.exclude_patterns == ["_build", "Thumbs.db", ".DS_Store"]

    required_extensions = {
        "sphinx.ext.autodoc",
        "sphinx.ext.napoleon",
        "sphinx.ext.mathjax",
        "sphinx.ext.viewcode",
        "sphinx.ext.intersphinx",
    }
    assert required_extensions.issubset(module.extensions)

    assert module.html_theme_options["navigation_depth"] == 4
    assert module.html_theme_options["sticky_navigation"] is True

    assert module.napoleon_google_docstring is True
    assert module.napoleon_numpy_docstring is True
    assert module.napoleon_use_param is True
    assert module.napoleon_use_rtype is True

    assert module.latex_engine == "pdflatex"
    assert r"\usepackage{amsmath}" in module.latex_elements["preamble"]
    assert module.latex_documents[0][0] == module.master_doc
    assert module.latex_documents[0][1] == "py3plex_book.tex"
    assert module.latex_documents[0][3] == module.author

    assert module.intersphinx_mapping["python"][0].startswith("https://docs.python.org/3")
    assert module.intersphinx_mapping["numpy"][0].startswith("https://numpy.org/doc/stable/")
    assert module.intersphinx_mapping["networkx"][0].startswith(
        "https://networkx.org/documentation/stable/"
    )
    assert module.mathjax_path.endswith("tex-mml-chtml.js")
