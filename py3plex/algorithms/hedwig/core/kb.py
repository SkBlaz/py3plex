'''
Knowledge-base class.

@author: anze.vavpetic@ijs.si
'''
from collections import defaultdict
from bitarray import bitarray
from rdflib import RDF, RDFS, URIRef

from .example import Example
from .predicate import UnaryPredicate
from .helpers import avg, std, user_defined
from .settings import EXAMPLE_SCHEMA, logger, W3C, HEDWIG


class ExperimentKB:
    '''
    The knowledge base for one specific experiment.
    '''
    def __init__(self, triplets, score_fun,
                 instances_as_leaves=True):
        '''
        Initialize the knowledge base with the given triplet graph.
        The target class is given with 'target_class' - this is the
        class to be described in the induction step.
        '''
        self.instances_as_leaves = instances_as_leaves
        self.score_fun = score_fun
        self.sub_class_of = defaultdict(list)
        self.super_class_of = defaultdict(list)
        self.predicates = set()
        self.binary_predicates = set()
        self.class_values = set()
        self.annotation_name = defaultdict(list)

        self.examples, all_annotations = self._build_examples(triplets)

        # Ranked or class-labeled data
        self.target_type = self.examples[0].target_type

        self._build_subclassof(triplets)
        self._calc_predicate_members(triplets)
        self._find_roots(all_annotations)
        self._calc_members_closure()
        self._calc_binary_members()
        self._propagate_annotation_names(triplets)

        # Statistics
        if self.target_type == Example.Ranked:
            self.mean = avg([ex.score for ex in self.examples])
            self.sd = std([ex.score for ex in self.examples])
        else:
            self.distribution = defaultdict(int)
            for ex in self.examples:
                self.distribution[ex.score] += 1
            logger.debug('Class distribution: %s' % str(self.distribution))


    def _build_examples(self, g):
        g.parse(EXAMPLE_SCHEMA, format='n3')

        # Extract the available examples from the graph
        ex_subjects = g.subjects(predicate=RDF.type, object=HEDWIG.Example)
        self.examples_uris = [ex for ex in ex_subjects]
        self.uri_to_idx = {}

        all_annotations = set()
        examples = []
        for i, ex_uri in enumerate(self.examples_uris):

            # Query for annotation link objects
            annot_objects = g.objects(subject=ex_uri,
                                           predicate=HEDWIG.annotated_with)

            annotation_links = [annot for annot in annot_objects]
            annotations = []
            weights = {}
#            to_uni = lambda s: str(s, 'utf-8').encode('ascii', 'ignore')

            for link in annotation_links:

                # Query for annotation objects via this link
                annot_objects = g.objects(subject=link,
                                               predicate=HEDWIG.annotation)
                annotation = [one for one in annot_objects][0]

                # Query for weights on this link
                weight_objects = g.objects(subject=link,
                                                predicate=HEDWIG.weight)
                weights_list = [one for one in weight_objects]

                if weights_list:
                    weights[annotation] = float(weights_list[0])

                annotations.append(annotation)

            all_annotations.update(annotations)

            # Scores
            score_list = list(g.objects(subject=ex_uri,
                                        predicate=HEDWIG.score))
            if score_list:
                score = float(score_list[0])
            else:
                # Classes
                score_list = list(g.objects(subject=ex_uri,
                                            predicate=HEDWIG.class_label))

                # If no scores or labels found at this stage
                if not score_list:
                    raise Exception("No example labels or scores found! Examples should be " +
                                    "instances of %s, with %s or %s provided." % (HEDWIG.Example, HEDWIG.score, HEDWIG.class_label))

                score = str(score_list[0])
                self.class_values.add(score)

            self.uri_to_idx[ex_uri] = i

            examples.append(Example(i, str(ex_uri), score,
                                    annotations=annotations,
                                    weights=weights))

        if not examples:
            raise Exception("No examples provided! Examples should be " +
                            "instances of %s." % HEDWIG.Example)
        
        return examples, all_annotations


    def _build_subclassof(self, g):

        for predicate in g.subjects(predicate=RDF.type,
                                    object=HEDWIG.GeneralizationPredicate):
            for sub, obj in g.subject_objects(predicate=predicate):
                if user_defined(sub) and user_defined(obj):
                    self.add_sub_class(sub, obj)

        for predicate in g.subjects(predicate=RDF.type,
                                    object=HEDWIG.SpecializationPredicate):
            for sub, obj in g.subject_objects(predicate=predicate):
                if user_defined(sub) and user_defined(obj):
                    # The subclass relation is reversed for predicates
                    # that specialize
                    self.add_sub_class(obj, sub)

        # Include the instances as predicates as well
        if self.instances_as_leaves:
            for sub, obj in g.subject_objects(predicate=RDF.type):
                if user_defined(sub) and user_defined(obj):
                    self.add_sub_class(sub, obj)

        # Find the user-defined object predicates defined between examples
        examples_as_domain = set(g.subjects(object=HEDWIG.Example,
                                                 predicate=RDFS.domain))

        examples_as_range = set(g.subjects(object=HEDWIG.Example,
                                                predicate=RDFS.range))

        for pred in examples_as_domain.intersection(examples_as_range):
            if user_defined(pred):
                self.binary_predicates.add(str(pred))


    def _calc_predicate_members(self, g):
        self.members = defaultdict(set)
        for ex in self.examples:
            for inst in ex.annotations:
                if self.instances_as_leaves:
                    self.members[inst].add(ex.id)
                else:
                    # Query for 'parents' of a given instance
                    inst_parents = list(g.objects(subject=URIRef(inst),
                                                       predicate=RDF.type))
                    inst_parents += list(g.objects(subject=URIRef(inst),
                                                    predicate=RDFS.subClassOf))
                    for obj in inst_parents:
                        self.members[str(obj)].add(ex.id)


    def _find_roots(self, all_annotations):
        roots = list(filter(lambda pred: not self.sub_class_of[pred],
                       self.super_class_of.keys()))

        # Check for annotations not in the ontology to add them as roots
        for annotation in all_annotations:
            if annotation not in self.predicates:
                roots.append(annotation)
                logger.debug('Adding leaf %s as root, as it is not specified in the ontology' % annotation)

        logger.debug('Detected root nodes: %s' % str(roots))

        # Add a dummy root
        self.dummy_root = 'root'
        self.predicates.add(self.dummy_root)
        for root in roots:
            self.add_sub_class(root, self.dummy_root)


    def _calc_members_closure(self):
        self.sub_class_of_closure = defaultdict(set)
        for pred in self.super_class_of.keys():
            self.sub_class_of_closure[pred].update(self.sub_class_of[pred])

        # Calc the closure to get the members of the subClassOf hierarchy
        def closure(pred, lvl, visited=[]):

            if pred in visited:
                raise Exception('Cycle detected in the hierarchy at predicate %s!' % pred)

            children = self.super_class_of[pred]
            self.levels[lvl].add(pred)

            if children:
                mems = set()
                visited.append(pred)
                for child in children:
                    parent_closure = self.sub_class_of_closure[pred]
                    self.sub_class_of_closure[child].update(parent_closure)
                    mems.update(closure(child, lvl + 1, visited=visited))
                self.members[pred].update(mems)
                visited.remove(pred)

                return self.members[pred]
            else:
                return self.members[pred]

        # Level-wise predicates
        self.levels = defaultdict(set)

        # Run the closure from root
        closure(self.dummy_root, 0)


    def _calc_binary_members(self):
        self.binary_members = defaultdict(dict)
        self.reverse_binary_members = defaultdict(dict)

        for pred in self.binary_predicates:
            pairs = g.subject_objects(predicate=URIRef(pred))

            for pair in pairs:
                el1, el2 = self.uri_to_idx[pair[0]], self.uri_to_idx[pair[1]]
                if self.binary_members[pred].has_key(el1):
                    self.binary_members[pred][el1].append(el2)
                else:
                    self.binary_members[pred][el1] = [el2]

                # Add the reverse as well
                if self.reverse_binary_members[pred].has_key(el2):
                    self.reverse_binary_members[pred][el2].append(el1)
                else:
                    self.reverse_binary_members[pred][el2] = [el1]

        # Bitset of examples for input and output
        self.binary_domains = {}
        for pred in self.binary_predicates:
            self.binary_domains[pred] = (
                self.indices_to_bits(self.binary_members[pred].keys()),
                self.indices_to_bits(self.reverse_binary_members[pred].keys())
            )

        # Calc the corresponding bitsets
        self.bit_members = {}
        for pred in self.members.keys():
            self.bit_members[pred] = self.indices_to_bits(self.members[pred])

        self.bit_binary_members = defaultdict(dict)
        self.reverse_bit_binary_members = defaultdict(dict)

        for pred in self.binary_members.keys():

            for el in self.binary_members[pred].keys():
                indices = self.indices_to_bits(self.binary_members[pred][el])
                self.bit_binary_members[pred][el] = indices

            for el in self.reverse_binary_members[pred].keys():
                reverse_members = self.reverse_binary_members[pred][el]
                indices = self.indices_to_bits(reverse_members)
                self.reverse_bit_binary_members[pred][el] = indices

    def _propagate_annotation_names(self, g):
        #to_uni = lambda s:  s.decode('unicode-escape')#str(s, 'utf-8').encode('ascii', 'ignore')

        # Query for annotation names
        for sub, obj in g.subject_objects(predicate=HEDWIG.annotation_name):
            sub, obj = sub, obj
            self.annotation_name[sub].append(obj)
            logger.debug('Annotation name root: %s, %s' % (sub, obj))

        # Propagate the annotation names to children
        annotation_name_roots = list(self.annotation_name.keys())
        for pred in self.predicates:
            for annotation_root in annotation_name_roots:
                if annotation_root in self.super_classes(pred):
                    name = self.annotation_name[annotation_root]
                    self.annotation_name[pred] = name

    def add_sub_class(self, sub, obj):
        '''
        Adds the resource 'sub' as a subclass of 'obj'.
        '''
        #to_uni = lambda s:  s.decode('unicode-escape')#str(s, 'utf-8').encode('ascii', 'ignore')
        sub, obj = sub, obj

        self.predicates.update([sub, obj])
        if obj not in self.sub_class_of[sub]:
            self.sub_class_of[sub].append(obj)
        if sub not in self.super_class_of[obj]:
            self.super_class_of[obj].append(sub)

    def super_classes(self, pred):
        '''
        Returns all super classes of pred (with transitivity).
        '''
        return self.sub_class_of_closure[pred]

    def get_root(self):
        '''
        Root predicate, which covers all examples.
        '''
        return UnaryPredicate(self.dummy_root, self.get_full_domain(), self,
                              custom_var_name='X')

    def get_subclasses(self, predicate, producer_pred=None):
        '''
        Returns a list of subclasses (as predicate objects) for 'predicate'.
        '''
        if isinstance(predicate, UnaryPredicate):
            return self.super_class_of[predicate.label]
        else:
            return self.super_class_of[predicate]

    def get_members(self, predicate, bit=True):
        '''
        Returns the examples for this predicate,
        either as a bitset or a set of ids.
        '''
        members = None
        if predicate in self.predicates:
            if bit:
                members = self.bit_members[predicate]
            else:
                members = self.members[predicate]
        else:
            if bit:
                members = self.bit_binary_members[predicate]
            else:
                members = self.binary_members[predicate]

        return members

    def get_reverse_members(self, predicate, bit=True):
        '''
        Returns the examples for this predicate,
        either as a bitset or a set of ids.
        '''
        reverse_members = None
        if bit:
            reverse_members = self.reverse_bit_binary_members[predicate]
        else:
            reverse_members = self.reverse_binary_members[predicate]

        return reverse_members

    def n_members(self, predicate):
        return self.get_members(predicate, bit=True).count()

    def get_domains(self, predicate):
        '''
        Returns the bitsets for input and outputexamples
        of the binary predicate 'predicate'.
        '''
        return self.binary_domains[predicate]

    def get_examples(self):
        '''
        Returns all examples for this experiment.
        '''
        return self.examples

    def n_examples(self):
        '''
        Returns the number of examples.
        '''
        return len(self.examples)

    def get_full_domain(self):
        '''
        Returns a bitset covering all examples.
        '''
        return bitarray([True] * self.n_examples())

    def get_empty_domain(self):
        '''
        Returns a bitset covering no examples.
        '''
        return bitarray([False] * self.n_examples())

    def get_score(self, ex_idx):
        '''
        Returns the score for example id 'ex_idx'.
        '''
        return self.examples[ex_idx].score

    def bits_to_indices(self, bits):
        '''
        Converts the bitset to a set of indices.
        '''
        return bits.search(bitarray([1]))

    def indices_to_bits(self, indices):
        '''
        Converts the indices to a bitset.
        '''
        bits = self.get_empty_domain()
        for idx in indices:
            bits[idx] = True
        return bits

    def is_discrete_target(self):
        return bool(self.class_values)
