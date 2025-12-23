import importlib.util
import os
import sys
from pathlib import Path

import pytest


DOC_CONF_PATH = Path(__file__).resolve().parent.parent / "docfiles" / "conf.py"
DOC_DIR = DOC_CONF_PATH.parent


@pytest.fixture
def load_doc_conf(monkeypatch):
    """Load docfiles/conf.py with controlled working directory and sys.path."""

    def _load(path_entries=None, cwd=DOC_DIR):
        sys.modules.pop("doc_conf", None)
        monkeypatch.setattr(sys, "path", list(path_entries) if path_entries is not None else [])
        if cwd:
            monkeypatch.chdir(cwd)

        spec = importlib.util.spec_from_file_location("doc_conf", DOC_CONF_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return _load


def test_conf_resolves_path_relative_to_cwd(load_doc_conf, tmp_path):
    elsewhere = tmp_path / "docs"
    elsewhere.mkdir()

    conf = load_doc_conf(path_entries=[], cwd=elsewhere)

    expected = os.path.abspath(elsewhere / "../py3plex")
    assert sys.path[0] == expected
    assert conf.project == "py3plex"


def test_conf_inserts_py3plex_path_first(load_doc_conf):
    original_entries = ["/tmp/one", "/tmp/two"]
    conf = load_doc_conf(path_entries=original_entries, cwd=DOC_DIR)

    expected = os.path.abspath(DOC_DIR / "../py3plex")
    assert sys.path[0] == expected
    assert sys.path[1:] == original_entries
    assert conf.master_doc == "index"


def test_conf_exposes_metadata_and_html_options(load_doc_conf):
    conf = load_doc_conf()

    assert conf.project == "py3plex"
    assert conf.version == conf.release == "1.0.3"
    assert conf.author == "Blaž Škrlj"
    assert conf.language == "en"

    assert "sphinx.ext.autodoc" in conf.extensions
    assert "sphinx.ext.napoleon" in conf.extensions
    assert "sphinx.ext.mathjax" in conf.extensions
    assert conf.templates_path == ["_templates"]
    assert conf.source_suffix == ".rst"
    assert conf.exclude_patterns == ["_build", "Thumbs.db", ".DS_Store"]

    assert conf.html_theme == "sphinx_rtd_theme"
    assert conf.html_theme_options["navigation_depth"] == 3
    assert conf.html_theme_options["logo_only"] is True
    assert conf.html_logo == "logo.png"
    assert conf.html_static_path == ["_static"]
    assert "custom.css" in conf.html_css_files
    assert conf.html_sidebars["**"] == ["relations.html", "searchbox.html"]


def test_conf_sets_latex_and_output_configs(load_doc_conf):
    conf = load_doc_conf()

    assert conf.htmlhelp_basename == "py3plexdoc"

    assert conf.latex_elements["papersize"] == "a4paper"
    assert conf.latex_elements["pointsize"] == "11pt"
    assert conf.latex_elements["extraclassoptions"] == "openany,oneside"
    assert conf.latex_elements["figure_align"] == "htbp"
    assert "\\usepackage{lmodern}" in conf.latex_elements["preamble"]
    assert "\\setlength{\\parskip}" in conf.latex_elements["preamble"]

    assert conf.latex_show_urls == "footnote"
    assert conf.latex_show_pagerefs is False

    latex_doc = conf.latex_documents[0]
    assert latex_doc[0] == conf.master_doc
    assert latex_doc[1] == "py3plex.tex"
    assert "Multilayer Network Analysis" in latex_doc[2]
    assert latex_doc[3] == conf.author
    assert latex_doc[4] == "manual"

    assert conf.latex_logo == "logo.png"

    man_page = conf.man_pages[0]
    assert man_page[0] == conf.master_doc
    assert man_page[1] == "py3plex"
    assert man_page[2] == "py3plex Documentation"
    assert man_page[3] == [conf.author]
    assert man_page[4] == 1

    texinfo_doc = conf.texinfo_documents[0]
    assert texinfo_doc[0] == conf.master_doc
    assert texinfo_doc[1] == "py3plex"
    assert texinfo_doc[2] == "py3plex Documentation"
    assert texinfo_doc[3] == conf.author
    assert texinfo_doc[4] == "py3plex"
    assert texinfo_doc[5] == "One line description of project."
    assert texinfo_doc[6] == "Miscellaneous"
