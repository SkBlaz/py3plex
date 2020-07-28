## parsers for working with semantic data..

## some generic methods used at many places..

from collections import defaultdict, Counter
import itertools
import gzip


def read_termlist(terms):

    termlist = []
    with open(terms) as nl:
        for line in nl:
            parts = line.strip().split()
            termlist.append(parts[0])

    return termlist


def parse_gaf_file(gaf_mappings, whole_list_counts=False):

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
                        uniGO[parts[1]].add(parts[4])  ## GO and ref both added

                    if whole_list_counts:
                        whole_list.append(parts[4])
                except Exception as es:
                    pass
    else:
        with open(gaf_mappings, "r") as im:
            for line in im:
                parts = line.strip().split("\t")
                try:
                    if parts[4] != "":
                        uniGO[parts[1]].add(parts[4])  ## GO and ref both added

                    if whole_list_counts:
                        whole_list.append(parts[4])
                except Exception as es:
                    pass


#                    print(es)

    if whole_list_counts:
        return (uniGO, whole_list)
    else:
        return uniGO


def read_topology_mappings(mapping):

    ## read the mapping in for of n:term
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
    ## read the GAF file..
    unigo_counts, whole_termlist = parse_gaf_file(filename,
                                                  whole_list_counts=True)
    term_counts = Counter(whole_termlist)
    all_terms = sum(list(term_counts.values()))
    if verbose:
        print("All annotations {}".format(all_terms))
    return (unigo_counts, term_counts, all_terms)
