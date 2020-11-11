# a converter set of methods for obtaining  normal inputs
import rdflib
from .term_parsers import parse_gaf_file
from collections import defaultdict
import gzip


def convert_mapping_to_rdf(input_mapping_file,
                           extract_subnode_info=False,
                           split_node_by=":",
                           keep_index=1,
                           layer_type="uniprotkb",
                           annotation_mapping_file="test.gaf",
                           go_identifier="GO:",
                           prepend_string=None):

    # generate input examples based on community assignment
    g = rdflib.graph.Graph()
    KT = rdflib.Namespace('http://kt.ijs.si/hedwig#')
    amp_uri = 'http://kt.ijs.si/ontology/hedwig#'
    obo_uri = "http://purl.obolibrary.org/obo/"
    rdflib.Namespace(amp_uri)

    # include neighbors as instances or not..
    mapping_file = {}
    if extract_subnode_info:
        for k, v in input_mapping_file.items():
            node, layer = k
            if layer_type == None:
                mapping_file[node] = v
            if layer_type != False:
                if layer == layer_type:
                    mapping_file[node.split(split_node_by)[keep_index]] = v
    else:
        for k, v in input_mapping_file.items():
            try:
                node, layer = k
            except Exception:
                parts = k.split(split_node_by)  # PSI-MI format
                if layer_type in parts:
                    layer, node = k.split(split_node_by)  # PSI-MI format
                else:
                    continue
            if layer_type == None:
                mapping_file[node] = v
            if layer_type != False:
                if layer == layer_type:
                    mapping_file[node] = v

    id_identifier = 0
    if ".gaf" in annotation_mapping_file:
        uniGO = parse_gaf_file(annotation_mapping_file)

    else:
        print("Please, provide gaf-based item-term mappings")

    # iterate through community assignments and construct the trainset
    # tukaj morda dodaj example name

    for node, com in mapping_file.items():
        try:
            id_identifier += 1
            u = rdflib.term.URIRef('%sexample#%s%s' %
                                   (amp_uri, node, str(id_identifier)))
            g.add((u, rdflib.RDF.type, KT.Example))
            g.add((u, KT.class_label, rdflib.Literal(str(com) + "_community")))
            for goterm in uniGO[node]:
                if prepend_string is not None:
                    goterm = prepend_string + goterm
                if go_identifier is not None:
                    if go_identifier in goterm:
                        annotation_uri = rdflib.term.URIRef(
                            '%s%s' % (obo_uri, rdflib.Literal(goterm)))
                        blank = rdflib.BNode()
                        g.add((u, KT.annotated_with, blank))
                        g.add((blank, KT.annotation, annotation_uri))
                else:
                    annotation_uri = rdflib.term.URIRef(
                        '%s%s' % (obo_uri, rdflib.Literal(goterm)))
                    blank = rdflib.BNode()
                    g.add((u, KT.annotated_with, blank))
                    g.add((blank, KT.annotation, annotation_uri))

        except Exception:
            # incorrect mappings are ignored..
            pass

    return g


def obo2n3(obofile, n3out, gaf_file):

    ontology = defaultdict(list)
    current_term = ""
    #obofile = obofile.replace("/","")

    parse_gaf_file(gaf_file)

    # iterate through all files
    if ".gz" in obofile:
        with gzip.open(obofile, "rt") as obo:
            for line in obo:
                parts = line.split()
                try:
                    if parts[0] == "id:":
                        current_term = parts[1]
                    if parts[0] == "is_a:":
                        ontology[current_term].append(parts[1])
                except:
                    pass
    else:
        with open(obofile, "rt") as obo:
            for line in obo:
                parts = line.split()
                try:
                    if parts[0] == "id:":
                        current_term = parts[1]
                    if parts[0] == "is_a:":
                        ontology[current_term].append(parts[1])
                except:
                    pass

    print("INFO: ontology terms added:", len(ontology.keys()))
    # construct an ontology graph
    g = rdflib.graph.Graph()
    KT = rdflib.Namespace('http://kt.ijs.si/hedwig#')
    amp_uri = 'http://kt.ijs.si/ontology/hedwig#'
    obo_uri = "http://purl.obolibrary.org/obo/"
    rdflib.Namespace(amp_uri)

    for k, v in ontology.items():
        u = rdflib.term.URIRef('%s%s' % (obo_uri, k))
        for item in v:
            annotation_uri = rdflib.term.URIRef(
                '%s%s' % (obo_uri, rdflib.Literal(item)))
            g.add((annotation_uri, rdflib.RDFS.subClassOf, u))

    g.serialize(destination=n3out, format="n3")
