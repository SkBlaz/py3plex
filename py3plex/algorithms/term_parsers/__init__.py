"""Parsers for working with semantic and biological annotation data.

This module provides utilities for parsing Gene Ontology (GO) annotations,
UniProt data, and other semantic/biological data formats commonly used in
network biology and bioinformatics.
"""

# some generic methods used at many places..

import gzip
from collections import Counter, defaultdict


def read_termlist(terms):
    """Read a list of terms from a text file.

    Parses a text file where each line contains a term (first column) and
    possibly additional fields. Extracts only the first column.

    Args:
        terms: Path to text file containing terms (one per line)

    Returns:
        list: List of term identifiers (strings)

    Notes:
        - Only the first whitespace-separated column is extracted
        - Lines are stripped of whitespace before parsing
        - Empty lines are not handled specially

    Examples:
        >>> # File content:
        >>> # GO:0001234 biological_process
        >>> # GO:0005678 cellular_component
        >>> terms = read_termlist('go_terms.txt')
        >>> terms
        ['GO:0001234', 'GO:0005678']
    """

    termlist = []
    with open(terms) as nl:
        for line in nl:
            parts = line.strip().split()
            termlist.append(parts[0])

    return termlist


def parse_gaf_file(gaf_mappings, whole_list_counts=False):
    """Parse Gene Association Format (GAF) file for GO annotations.

    Reads a GAF 2.0/2.1 format file (plain text or gzipped) and extracts
    mappings between gene/protein identifiers and GO terms.

    Args:
        gaf_mappings: Path to GAF file (.gaf or .gaf.gz)
        whole_list_counts: If True, also return list of all GO terms for counting
                          (default: False)

    Returns:
        If whole_list_counts=False:
            dict: {gene_id: set(GO_terms)}
        If whole_list_counts=True:
            tuple: (mappings_dict, list of all GO terms)

    File Format:
        GAF 2.0/2.1 tab-separated format:
        - Column 2: Gene/protein identifier
        - Column 5: GO term identifier
        See: http://geneontology.org/docs/go-annotation-file-gaf-format-2.1/

    Notes:
        - Automatically handles .gz compressed files
        - Skips lines with empty GO term field (column 5)
        - Multiple GO terms per gene are accumulated in a set
        - Errors in parsing individual lines are caught and printed

    Examples:
        >>> # Parse GAF file
        >>> mappings = parse_gaf_file('annotations.gaf.gz')
        >>> mappings['UniProt123']
        {'GO:0001234', 'GO:0005678'}

        >>> # Get counts of all terms
        >>> mappings, all_terms = parse_gaf_file('annotations.gaf.gz',
        ...                                       whole_list_counts=True)
        >>> len(all_terms)  # Total annotation count
        50000

    See Also:
        read_uniprot_GO: Convenience wrapper with term counting
    """

    uniGO = defaultdict(set)
    if whole_list_counts:
        whole_list = []

    #    print("parsing GAF file.. {}".format(gaf_mappings))
    if ".gz" in gaf_mappings:
        with gzip.open(gaf_mappings, "rb") as im:
            for line in im:
                line = line.decode("utf-8")
                parts = line.strip().split("\t")
                try:
                    if parts[4] != "":
                        uniGO[parts[1]].add(parts[4])  # GO and ref both added

                    if whole_list_counts:
                        whole_list.append(parts[4])
                except Exception as es:
                    print(es)
    else:
        with open(gaf_mappings) as im:
            for line in im:
                parts = line.strip().split("\t")
                try:
                    if parts[4] != "":
                        uniGO[parts[1]].add(parts[4])  # GO and ref both added

                    if whole_list_counts:
                        whole_list.append(parts[4])
                except Exception as es:
                    print(es)

    if whole_list_counts:
        return (uniGO, whole_list)
    else:
        return uniGO


def read_topology_mappings(mapping):
    """Read node-to-module/community mappings from file or dict.

    Parses a mapping between network nodes and their assigned modules, clusters,
    or communities. Accepts either a file path or an existing dictionary.

    Args:
        mapping: Either:
                - str: Path to mapping file (format: "node module" per line)
                - dict: Pre-existing mapping dictionary (returned as-is)

    Returns:
        dict: {module_id: set(node_ids)}
            Inverted mapping from modules to sets of nodes

    File Format (if path provided):
        node_id module_id
        node_id module_id
        ...

    Notes:
        - If a dict is provided, returns it unchanged (no validation)
        - File format is whitespace-separated: node_id module_id
        - Multiple nodes can belong to the same module
        - Node IDs are stored as strings

    Examples:
        >>> # From file
        >>> mappings = read_topology_mappings('clusters.txt')
        >>> mappings
        {'module1': {'nodeA', 'nodeB'}, 'module2': {'nodeC'}}

        >>> # Pass-through existing dict
        >>> existing = {'m1': {'n1', 'n2'}}
        >>> result = read_topology_mappings(existing)
        >>> result is existing
        True

    See Also:
        Community detection algorithms that produce such mappings
    """

    # read the mapping in for of n:term
    if isinstance(mapping, dict):
        return mapping
    else:
        components = defaultdict(set)
        with open(mapping) as cf:
            for line in cf:
                node, module = line.strip().split()
                components[module].add(node)
        return components


def read_uniprot_GO(filename, verbose=True):
    """Read UniProt GO annotations from GAF file with term statistics.

    Convenience wrapper around parse_gaf_file that also computes term frequencies
    and total annotation counts. Useful for enrichment analysis.

    Args:
        filename: Path to GAF file (.gaf or .gaf.gz)
        verbose: Print total annotation count (default: True)

    Returns:
        tuple: (gene_mappings, term_counts, total_annotations)
            - gene_mappings: dict {gene_id: set(GO_terms)}
            - term_counts: Counter {GO_term: frequency}
            - total_annotations: int, total number of annotations

    Notes:
        - Uses parse_gaf_file internally with whole_list_counts=True
        - Term counts include all annotations (not unique per gene)
        - Useful for computing term frequencies and background distributions

    Examples:
        >>> mappings, counts, total = read_uniprot_GO('annotations.gaf.gz')
        All annotations 50000
        >>> mappings['P12345']
        {'GO:0001234', 'GO:0005678'}
        >>> counts['GO:0001234']
        150  # Number of times this term appears
        >>> total
        50000

    See Also:
        parse_gaf_file: Lower-level GAF parser
    """
    # read the GAF file..
    unigo_counts, whole_termlist = parse_gaf_file(filename, whole_list_counts=True)
    term_counts = Counter(whole_termlist)
    all_terms = sum(term_counts.values())
    if verbose:
        print(f"All annotations {all_terms}")
    return (unigo_counts, term_counts, all_terms)
