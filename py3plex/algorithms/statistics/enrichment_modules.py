# modules directed towards enrichment of node partitions..

# this python code enables enrichment calculation from graph results from previous step

# this is to calculate enrichment scores

import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

import pandas as pd
from scipy.stats import fisher_exact

try:
    from statsmodels.sandbox.stats.multicomp import multipletests  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    multipletests = None

from py3plex.algorithms.term_parsers import read_topology_mappings, read_uniprot_GO

logging.basicConfig(format="%(asctime)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S")
logging.getLogger().setLevel(logging.INFO)

# Module-level globals for parallel processing
_partition_name: str = ""
_alternative: str = "two-sided"
_partition_entries: List[Any] = []
_term_database: Dict[int, Tuple[str, int]] = {}
_map_term_database: Dict[str, List[str]] = {}
_number_of_all_annotated: int = 0
_number_of_communities: int = 0
_normalize_by_comsize: bool = False


def calculate_pval(term: Tuple[str, int], alternative: str = "two-sided") -> float:
    """
    Parallel kernel for computation of p vals. All partitions are considered with respect to agiven GO term! Counts in a given partition are compared to population.

    Args:
        term: Tuple of (query_term, query_term_count_population)
        alternative: Alternative hypothesis for Fisher's exact test

    Returns:
        p-value from Fisher's exact test
    """

    query_term = term[0]
    query_term_count_population = term[1]

    inside_local = 0
    outside_local = 0
    for x in _partition_entries:
        terms = _map_term_database[x]
        if query_term in terms:
            inside_local += 1
        else:
            outside_local += 1

    if _normalize_by_comsize:
        query_term_count_population = int(
            query_term_count_population / _number_of_communities
        )

    outside_hits = query_term_count_population - inside_local
    outside_misses = _number_of_all_annotated - query_term_count_population - outside_local
    p_value = fisher_exact(
        [[inside_local, outside_local], [outside_hits, outside_misses]],
        alternative=alternative,
    )[1]
    return float(p_value)


def multiple_test_correction(input_dataset: str) -> None:
    """
    Multiple test correction. Given a dataset with corresponding significance levels, perform MTC.

    Args:
        input_dataset: Path to input file with test results
    """

    _require_statsmodels()

    pvals = defaultdict(list)
    with open(input_dataset) as ods:
        for line in ods:
            try:
                component, term, pval = line.split()
                pvals[component].append((term, pval))
            except ValueError as e:
                logging.debug(f"Skipping malformed line: {line.strip()} - {e}")
                pass

    logging.info("Component_by_size PFAM_term pvalue")
    for key, values in pvals.items():
        tmpP = [float(val[1]) for val in values]
        termN = [val[0] for val in values]
        significant, pvals, sidak, bonf = multipletests(
            tmpP, method="hs", is_sorted=False, returnsorted=False
        )

        # Holm Sidak
        output = zip(termN, significant, pvals, tmpP)
        for term, significant, pval, tmp in output:
            if significant:
                print(key, term, significant, tmp, pval)


def parallel_enrichment(term):
    """
    A simple kernel for parallel computation of p-values. (assuming independence of experiments)
    """

    pval = calculate_pval(_term_database[term], alternative=_alternative)
    return {
        "observation": _partition_name,
        "term": _term_database[term][0],
        "pval": pval,
    }


def _require_statsmodels() -> None:
    """Raise a helpful error if statsmodels is not installed."""
    if multipletests is None:
        raise ImportError(
            "statsmodels is required for enrichment analysis. "
            "Install with 'pip install statsmodels' or the 'algos' extra."
        )


def compute_enrichment(
    term_dataset,
    term_database,
    topology_map,
    all_counts,
    whole_term_list=False,
    pvalue=0.05,
    multitest_method="fdr_bh",
    alternative="two-sided",
    intra_community=False,
):
    """
    Test partition membership and annotation on disjoint sets of unique entities.

    The term database specifies which terms to test. Background counts are
    computed from term_dataset; all_counts is retained for callers that pass
    a count of annotation rows. With intra_community, the background is
    restricted to annotated entities in the union of the partitions.
    """
    if multitest_method != "raw":
        _require_statsmodels()

    population = set(term_dataset)
    if intra_community:
        population &= {item for part in topology_map.values() for item in part}
    if whole_term_list:
        topology_map = {"1_community": {item for part in topology_map.values() for item in part}}

    # The observations are unique annotated entities, not annotation rows.
    background = Counter(term for item in population for term in set(term_dataset[item]))
    results = []
    for name, items in topology_map.items():
        selected = set(items) & population
        selected_terms = Counter(term for item in selected for term in set(term_dataset[item]))
        rows = []
        for term in term_database:
            hits = selected_terms[term]
            misses = len(selected) - hits
            outside_hits = background[term] - hits
            outside_misses = len(population) - len(selected) - outside_hits
            _, p = fisher_exact(
                [[hits, misses], [outside_hits, outside_misses]], alternative=alternative
            )
            rows.append({"observation": name, "term": term, "pval": float(p)})
        if not rows:
            continue
        frame = pd.DataFrame(rows)
        if multitest_method == "raw":
            frame = frame[frame["pval"] < pvalue]
        else:
            significant, adjusted, _, _ = multipletests(
                frame["pval"], method=multitest_method, alpha=pvalue
            )
            frame["corrected_pval" + "_" + multitest_method] = adjusted
            frame["significant"] = significant
            frame = frame[significant]
        results.append(frame)

    return pd.concat(results, ignore_index=True) if results else pd.DataFrame(
        columns=["observation", "term", "pval"]
    )


# specifiy how this is formatted..
def fet_enrichment_generic(term_dataset, term_database, all_counts, topology_map):
    """
    A generic enrichment method useful for arbitrary partition enrichment (CBSSD baseline).

    term_dataset = defaultdict(list) of node:[a1..an] mappings
    term_datset = Counter object of individual annotation occurrences
    all_counts = number of all annotation occurences

    """
    # 3.) calculate p-vals.
    significant_results = compute_enrichment(
        term_dataset, term_database, topology_map, all_counts, whole_term_list=False
    )
    return significant_results


def fet_enrichment_terms(
    partition_mappings,
    annotation_mappings,
    alternative="two-sided",
    intra_community=False,
    pvalue=0.1,
    multitest_method="fdr_bh",
):
    """
    This is the most generic enrichment process.
    """

    # 1.) read the database.
    term_dataset, term_database, all_counts = read_uniprot_GO(annotation_mappings)

    # 2.) partition function dict.
    topology_map = read_topology_mappings(partition_mappings)

    # 3.) calculate p-vals.
    significant_results = compute_enrichment(
        term_dataset,
        term_database,
        topology_map,
        all_counts,
        whole_term_list=False,
        alternative=alternative,
        intra_community=intra_community,
        pvalue=pvalue,
        multitest_method=multitest_method,
    )

    return significant_results


# write this so it uses vanilla data structures
def fet_enrichment_uniprot(partition_mappings, annotation_mappings):
    """
    This is a pre-designed wrapper for uniprot-like annotation.
    """

    # 1.) read the database.
    term_dataset, term_database, all_counts = read_uniprot_GO(annotation_mappings)

    # 2.) partition function dict.
    topology_map = read_topology_mappings(partition_mappings)

    # 3.) calculate p-vals.
    significant_results = compute_enrichment(
        term_dataset, term_database, topology_map, all_counts, whole_term_list=False
    )

    return significant_results


if __name__ == "__main__":

    pass
