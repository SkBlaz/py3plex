## core data structures

import networkx as nx
import numpy as np
import scipy.sparse as sp
from .decomposition import get_calculation_method

class Class:
    def __init__(self, lab_id, name, members):
        self.name = name
        self.id = lab_id
        self.index = -1
        self.members = members  # ids of members calculated using hierarchy of labels
        self.member_indices = []
        self.train_indices = []  # indices of training instances with this label
        self.validate_indices = []  # indices of validate instances with this label
        self.test_indices = []  # indices of test instances with this label
        self.train_members = set()  # ids of train members (intersection of basic_members and the train set)
        self.test_members = set()  # ids of test members (intersection of basic_members and the test set)
        self.validate_members = set()  # ids of validate members (intersection of basic_members and the validate set)
        self.not_test_members = set()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class HeterogeneousInformationNetwork:
    def __init__(self, network, label_delimiter, weight_tag=False, target_tag=True):
        self.label_list = []  # list of labels.
        self.labels_by_id = {}  # IDs of each label
        self.graph = network
        self.target_tag = target_tag
        self.node_list = []  # List of all nodes in decomposition
        self.node_indices = {}  # Indices of all nodes in decomposition
        self.basic_type = None  # Basic node type (for decomposition)
        self.label_array = None
        self.label_matrix = None

        self.train_indices = []
        self.validate_indices = []
        self.test_indices = []
        self.train_ids = set()
        self.validate_ids = set()
        self.test_ids = set()

        self.weighted = weight_tag ## include info on weighted edges
        
        self.decomposed = {}  # Dictionary of all performed decompositions (self.decomposed['PAP'] is one)
        self.pairs = {}
        self.midpoints = {}

        self.validate_pprs = {}
        self.test_pprs = {}
        self.train_pprs = {}

        self.validate_distances = {}
        self.test_distances = {}

        self.midpoint_files = {}
        self.feature_vectors = {}
        if  network != None:            
            self.process_network(label_delimiter)

    def add_label(self, node, label_id, label_name=None):
        if label_name is None:
            label_name = str(label_id)
        if label_id in self.labels_by_id:
            if self.labels_by_id[label_id] not in self.graph.node[node]['labels']:
                self.graph.node[node]['labels'].append(self.labels_by_id[label_id])
                self.labels_by_id[label_id].members.append(node)
        else:
            new_class = Class(label_id, label_name, [node])
            self.label_list.append(new_class)
            self.labels_by_id[label_id] = new_class
            new_class.index = len(self.label_list) - 1
            self.graph.node[node]['labels'].append(new_class)

    def process_network(self, label_delimiter):        
        if self.target_tag:
            basic_types = set([self.graph.node[x]['type'] for x in self.graph.node if 'labels' in self.graph.node[x]])
            
            print("Target type: {}".format(basic_types))
            if len(basic_types) != 1:
                ## tukej naredi, da enostavno sejvne grafek, to je uporabno za embedding
                print(basic_types)
                raise Exception('Unclear target type!')

            self.basic_type = basic_types.pop()                      
            self.node_list = [x for x in self.graph.node if self.graph.node[x]['type'] == self.basic_type]
            try:
                self.node_list.sort(key=lambda x: float(x[0]))
            except ValueError:
                self.node_list.sort()
            self.node_indices = dict([(item, index) for index, item in enumerate(self.node_list)])

            for node_id in self.node_list:
                if 'labels' in self.graph.node[node_id]:
                    if len(self.graph.node[node_id]['labels']) > 0:
                        labels = self.graph.node[node_id]['labels'].split(label_delimiter)
                        self.graph.node[node_id]['labels'] = []
                        for label in labels:
                            self.add_label(node_id, label, label_name=label)
                else:
                    pass
            
            for lab in self.label_list:
                if lab is not None:
                    temp_list = [mem for mem in lab.members if self.graph.node[mem]['type'] == self.basic_type]
                    lab.basic_members = set(temp_list)
            self.label_array = - np.ones((max([len(self.graph.node[node]['labels']) for node in self.node_list]), len(self.node_list)))
            for node in self.node_list:
                tmp = self.graph.node[node]['labels']
                self.label_array[:len(tmp), self.node_indices[node]] = [label.index for label in tmp]
            self.create_label_matrix()

    def create_label_matrix(self, weights=None):

        self.label_matrix = np.zeros((len(self.node_list), len(self.label_list)))
        for i, label in enumerate(self.label_list):
            member_indices = [self.node_indices[x] for x in label.members]
            if weights == 'balanced':
                self.label_matrix[member_indices, i] = 1.0 / max(len(label.train_indices), 1)
            else:
                self.label_matrix[member_indices, i] = 1

        

    def calculate_schema(self):
        schema = nx.MultiDiGraph()
        for node_start in self.graph.node:
            for node_end in self.graph[node_start]:
                for key in self.graph[node_start][node_end]:
#                    print(node_start,node_end,key,self.graph[node_start][node_end])
                    start_type = self.graph.node[node_start]['type']
                    end_type = self.graph.node[node_end]['type']
                    edge_type = self.graph[node_start][node_end][key]['type']
                    has_type = False
                    if schema.has_edge(start_type, end_type):
                        for key in schema[start_type][end_type]:
                            if schema[start_type][end_type][key]['type'] == edge_type:
                                has_type = True
                                break
                        # if schema[start_type][end_type]['type'] != edge_type:
                        #     raise Exception('Multiple edge types between equal node types are not supported!')
                    if not has_type:
                        schema.add_edge(start_type, end_type, type=edge_type)
        return schema

    def calculate_decomposition_candidates(self, max_decomposition_length=10):
        schema = self.calculate_schema()
        under_construction = [{'node_list': [self.basic_type], 'edge_list': []}]
        candidate_lists = []
        for i in range(max_decomposition_length - 1):
            next_gens = []
            for list_so_far in under_construction:
                if list_so_far['node_list'][-1] != self.basic_type or len(list_so_far['node_list']) == 1:
                    current = list_so_far['node_list'][-1]
                    for neighbor in schema[current]:
                        if neighbor == self.basic_type:
                            append_to = candidate_lists
                        else:
                            append_to = next_gens
                        for key in schema[current][neighbor]:
                            append_to.append({
                                'node_list': list_so_far['node_list'] + [neighbor],
                                'edge_list': list_so_far['edge_list'] + [schema[current][neighbor][key]['type']]
                            })
            under_construction = next_gens
        return candidate_lists

    def split_to_indices(self, train_indices=(), validate_indices=(), test_indices=()):
        self.train_indices = train_indices
        self.validate_indices = validate_indices
        self.test_indices = test_indices

        self.train_ids = set([self.node_list[i] for i in self.train_indices])
        self.validate_ids = set([self.node_list[i] for i in self.validate_indices])
        self.test_ids = set([self.node_list[i] for i in self.test_indices])

        # calculate test representatives:
        for train_index in self.train_indices:
            train_node = self.node_list[train_index]
            for label in self.graph.node[train_node]['labels']:
                label.train_indices.append(train_index)
                label.train_members.add(self.node_list[train_index])
                label.not_test_members.add(self.node_list[train_index])
        for validate_index in self.validate_indices:
            validate_node = self.node_list[validate_index]
            for label in self.graph.node[validate_node]['labels']:
                label.validate_indices.append(validate_index)
                label.validate_members.add(self.node_list[validate_index])
                label.not_test_members.add(self.node_list[validate_index])
        for test_index in self.test_indices:
            test_node = self.node_list[test_index]
            for label in self.graph.node[test_node]['labels']:
                label.test_indices.append(test_index)
                label.test_members.add(self.node_list[test_index])
        for label in self.label_list:
            label.not_test_members_num = len(label.not_test_members)

    def split_to_parts(self,lst,n):
        return [lst[i::n] for i in range(n)]
    

    def decompose_from_iterator(self, name, weighing, summing ,generator=None, degrees=None, parallel=True,pool=None):
        classes = [lab for lab in self.label_list if lab and len(lab.not_test_members) > 0]
        universal_set = list(set(self.train_ids).union(self.validate_ids))
        universal_inv = {}
        for i, item in enumerate(universal_set):
            universal_inv[item] = i
        universal_set = set(universal_set)
        label_matrix = np.zeros((len(universal_set), len(classes)))
        for i, label in enumerate(classes):
            label_matrix[[universal_inv[item] for item in label.not_test_members], i] = 1
        nn = len(self.node_list)
        matrix = sp.csr_matrix((nn, nn))
        n = len(universal_set)
        
        importance_calculator = get_calculation_method(weighing)
        if generator is None:
            raise Exception('No midpoint generator!')
        avgdegree = None
        if weighing != 'okapi':
            degrees = None
            avgdegree = None
        if degrees is not None:
            avgdegree = sum(degrees.values()) * 1.0 / len(degrees)
        i=0
        tmp_container = []
        bsize = 5
        
        if parallel:
            ## parallel for edge type
            
            while True:
                tmp_container = list(next(generator) for _ in range(bsize))                

                if  len(tmp_container)  == 0:
                    break

                pinput = []
                
                for j in tmp_container:
                    pinput.append((classes,universal_set,j,n))
                results = pool.starmap(importance_calculator,pinput)
                
                ## construct main matrix
                for item, importances in zip(tmp_container, results):
                    importance = np.sum(importances, axis=0)
                    i1 = [self.node_indices[x] for x in item]
                    i2 = [[x] for x in i1]

                    to_add = sp.csr_matrix((nn, nn))
                    
                    if len(i1) > 1000:

                        ## split to prevent memory leaks when doing hadamand products
                        parts_first = self.split_to_parts(i1,4)
                        parts_second = self.split_to_parts(i2,4)
                        
                        for x in range(len(parts_first)):
                            to_add[parts_first[x], parts_second[x]] = importance
                            
                    else:
                        to_add[i2, i1] = importance

                        
                    to_add = to_add.tocsr()
                    matrix += to_add

        else:
            
            ## non-parallel                        
            for item in generator:
            
                ## to za vsak class poracun importance
                importances = importance_calculator(classes, universal_set, item, n, degrees=degrees, avgdegree=avgdegree)
                importance = np.sum(importances, axis=0)
                i1 = [self.node_indices[x] for x in item]
                i2 = [[x] for x in i1]

                
                
                to_add = sp.csr_matrix((nn, nn))
                to_add[i2, i1] = importance
                to_add = to_add.tocsr() # this prevents memory leaks
                matrix += to_add


        ## hadamand product
        
        self.decomposed[name] = matrix

    def midpoint_generator(self, node_sequence, edge_sequence):
        if len(node_sequence) % 2 == 0:
            raise Exception('In a split of length %i, a midpoint is not well defined!' % len(node_sequence))
        middle_type = node_sequence[int(len(node_sequence) / 2)]
        # forward_sequence = %TODO: INVERSE SEQUENCES!!!!!!!!!
        for node in self.graph:
            if self.graph.node[node]['type'] == middle_type:
                points = [node]
                i = int(len(node_sequence)/2 + 1)
                while i < len(node_sequence):
                    current_type = node_sequence[i]
                    new_points = []
                    for point in points:
                        new_points += [x for x in self.graph[point] if self.graph.node[x]['type'] == current_type]
                    points = new_points
                    i += 1
                if len(points) > 1:
                    yield points
