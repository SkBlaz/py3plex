'''
Reading input data.

@author: anze.vavpetic@ijs.si
'''
import rdflib
import hashlib
import os
import _pickle as cPickle

from .settings import logger, HEDWIG, GENERIC_NAMESPACE


def rdf(paths, def_format='n3'):
    '''
    Loads the ontology into an rdf graph.
    '''
    g = rdflib.graph.Graph()
    errorMsg = ''
    errorCount = 0
    for path in paths:
        if path.endswith(def_format):
            try:
                g.parse(path, format=def_format)
            except Exception as e:
                errorMsg = errorMsg + 'Error parsing file: ' + path + '.\n' + str(
                    e) + '\n\n'
                errorCount += 1
    if errorCount > 0:
        raise Exception(
            str(errorCount) + " errors loading files:\n" + errorMsg)
    return g


def build_uri(class_string):
    '''
    Checks if the string is a proper URI, if not it builds an URI
    with the generic namespace.
    '''
    class_string = class_string.strip()
    if class_string.startswith('http://'):
        class_uri = rdflib.term.URIRef(class_string)
    else:
        class_uri = rdflib.term.URIRef('%s%s' %
                                       (str(GENERIC_NAMESPACE), class_string))

    return class_uri


def csv_parse_hierarchy(g, path):
    '''
    Assumes a hierarchy file of the following format:

    class_1<tab>superclass_1_1; superclass_1_2; ...; superclass_1_n
    class_2<tab>superclass_2_1; superclass_2_2; ...; superclass_2_n
    ...
    class_m<tab>superclass_m_1; superclass_m_2; ...; superclass_m_n
    '''
    with open(path) as f:
        lines = f.read().splitlines()
        for line in lines:
            class_ = line.split('\t')[0]
            superclasses = line.split('\t')[1].split(';')
            for superclass in superclasses:
                class_uri = build_uri(class_)
                superclass_uri = build_uri(superclass)
                g.add((class_uri, rdflib.RDFS.subClassOf, superclass_uri))


def csv_parse_data(g, data_file):
    '''
    Assumes the following csv format:

    example_uri_or_label; attr_uri_1; attr_uri_2; ...; attr_uri_n
    http://example.org/uri_1; 0/1; 0/1; 0/1; 0/1; ...
    http://example.org/uri_2; 0/1; 0/1; 0/1; 0/1; ...
    ...

    Alternatively attribute values can be URIs themselves.
    '''
    attributes = []
    examples = []

    with open(data_file) as f:
        data_lines = f.readlines()
        domain = [a.strip() for a in data_lines[0].split(';')]
        attributes = domain[:-1]

        logger.debug('Attributes: %s' % str(attributes))
        logger.debug('# Examples: %d' % (len(data_lines) - 1))

        for ex_i, example_line in enumerate(data_lines[1:]):
            values = [v.strip() for v in example_line.split(';')]
            if len(values) != len(attributes) + 1:
                raise Exception(
                    'Whoa! The number of values %d != the number of attributes (%d) on line %d.'
                    % (len(values), len(attributes) + 1, ex_i + 2))

            examples.append(values)

    for example in examples:
        # Write to rdf graph
        u = build_uri(example[0])
        g.add((u, rdflib.RDF.type, HEDWIG.Example))
        g.add((u, HEDWIG.class_label, rdflib.Literal(example[-1])))

        for att_idx, att in enumerate(attributes):

            # Skip the label
            if att_idx == 0:
                continue

            attribute_value = example[att_idx]
            value_is_uri = attribute_value.startswith('http://')
            if not (value_is_uri or attribute_value == '1'):
                continue
            annotation_uri = build_uri(
                attribute_value) if value_is_uri else build_uri(att)
            blank = rdflib.BNode()
            g.add((u, HEDWIG.annotated_with, blank))
            g.add((blank, HEDWIG.annotation, annotation_uri))


def csv(hierarchy_files, data):
    '''
    Loads a simple hierarchy of features and data in csv format.
    '''
    g = rdflib.graph.Graph()
    errorMsg = ''
    errorCount = 0
    for path in hierarchy_files + [data]:
        try:
            if path.endswith('tsv'):
                csv_parse_hierarchy(g, path)
            elif path.endswith('csv'):
                csv_parse_data(g, data)
        except Exception as e:
            errorMsg = errorMsg + 'Error parsing file: ' + path + '.\n' + str(
                e) + '\n\n'
            errorCount += 1
    if errorCount > 0:
        raise Exception(
            str(errorCount) + " errors loading files:\n" + errorMsg)
    return g


def load_graph(ontology_list, data, def_format='n3', cache=True):
    def filter_valid_files(paths):
        if def_format == 'csv':

            def filter_fn(p):
                return p.endswith('.csv') or p.endswith('.tsv')
        else:

            def filter_fn(p):
                return p.endswith(def_format)

        return filter(filter_fn, paths)

    logger.info('Calculating data checksum')
    paths = ontology_list + [data]
    md5 = _md5_checksum(filter_valid_files(paths))

    cached_fn = '.%s' % md5
    if os.path.exists(cached_fn) and cache:
        logger.info('Loading cached graph structure')
        g = _load_cached_graph(cached_fn)
    else:
        logger.info('Building graph structure')

        if def_format == 'n3':
            g = rdf(paths, def_format=def_format)
        elif def_format == 'csv':
            g = csv(ontology_list, data)
        if cache:
            _save_graph_to_cache(g, cached_fn)

    return g


def _md5_checksum(paths):
    md5 = hashlib.md5()
    for path in paths:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(2**20), b''):
                md5.update(chunk)
    return md5.hexdigest()


def _load_cached_graph(fn):
    g = cPickle.load(open(fn))
    return g


def _save_graph_to_cache(g, fn):
    with open(fn, 'wb') as f:
        cPickle.dump(g, f)
