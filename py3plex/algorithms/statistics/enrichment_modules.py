## modules directed towards enrichment of node partitions..

##### this pyton code enables enrichment calculation from graph results from previous step

## this is to calculate enrichment scores

from scipy.stats import fisher_exact
import multiprocessing as mp
import random
from statsmodels.sandbox.stats.multicomp import multipletests
from collections import defaultdict, Counter
from ..term_parsers import parse_gaf_file,read_termlist,read_topology_mappings,read_uniprot_GO
import pandas as pd

def calculate_pval(term):

#    _partition_name,_partition_entries,term,_map_term_database,_number_of_all_annotated
    ## this calculates p value
    #print(component, term_dataset, term, count_all)

    query_term = term[0]
    query_term_count_population = term[1]

    inside_local = 0
    outside_local = 0
    for x in _partition_entries:
        terms = _map_term_database[x]
        if query_term in terms:
            inside_local+=1
        else:
            outside_local+=1

    query_counts = [inside_local, query_term_count_population]
    pop_counts = [outside_local, _number_of_all_annotated-query_term_count_population]
    p_value = fisher_exact([query_counts,pop_counts])[1]
    return p_value

def multiple_test_correction(input_dataset):
    from statsmodels.sandbox.stats.multicomp import multipletests
    pvals = defaultdict(list)
    with open(input_dataset) as ods:
        for line in ods:
            try:
                component, term, pval = line.split()
                pvals[component].append((term,pval))
            except:
                pass

    print ("Component_by_size PFAM_term pvalue")
    for key, values in pvals.items():
        tmpP = [float(val[1]) for val in values]
        termN = [val[0] for val in values]
        significant, pvals, sidak, bonf = multipletests(tmpP,method="hs",is_sorted=False,returnsorted=False)

        ## Holm Sidak        
        output = zip(termN,significant,pvals,tmpP)
        for term,significant,pval,tmp in output:
            if (significant == True):
                print (key,term,significant,tmp,pval)


def parallel_enrichment(term):
    pval = calculate_pval(_term_database[term])
    return {'observation' : _partition_name,'term' : _term_database[term][0],'pval' : pval}

def compute_enrichment(term_dataset, term_database, topology_map, all_counts, whole_term_list=False,pvalue=0.05,multitest_method="fdr_bh"):

    if whole_term_list:
        tvals = set.union(*[x for x in topology_map.values()])
        topology_map = {}
        topology_map['1_community'] = tvals
    
    global _partition_name
    global _partition_entries
    global _term_database
    global _map_term_database
    global _number_of_all_annotated

    _number_of_all_annotated = all_counts
    _term_database = {en : x for en, x in enumerate(term_database.items())} ## database of all annotations
    
    _map_term_database = term_dataset ## entry to acc mappings

    finalFrame = pd.DataFrame()
    
    for k, v in topology_map.items():

        print("Computing enrichment for partition {}".format(k))
        ## reassign for parallel usage
        _partition_name = k
        _partition_entries = v

        ## computational pool instantiation
        ncpu = 2 #mp.cpu_count()
        pool = mp.Pool(ncpu)
        
        ## compute the results
        n = len(term_database)
        step = ncpu ## number of parallel processes
        jobs = [range(n)[i:i + step] for i in range(0, n, step)] ## generate jobs

        ## result container
        tmpframe = pd.DataFrame(columns=['observation','term','pval'])
        results = [parallel_enrichment(x) for x in range(n)]
        
        # for batch in jobs:
        #     results = pool.map(parallel_enrichment,batch)
        tmpframe = tmpframe.append(results,ignore_index=True)

        ## multitest corrections on partition level
        significant, p_adjusted, sidak, bonf = multipletests(tmpframe['pval'],method=multitest_method,is_sorted=False, returnsorted=False, alpha=pvalue)
        tmpframe['corrected_pval'+"_"+multitest_method] = pd.Series(p_adjusted)
        tmpframe['significant'] = pd.Series(significant)
        tmpframe = tmpframe[tmpframe['significant'] == True]
        finalFrame = finalFrame.append(tmpframe,ignore_index=True)
    
    return finalFrame

## specifiy how this is formatted..
def fet_enrichment_generic(term_dataset,term_database,all_counts,topology_map):
    """
    A generic enrichment method useful for arbitrary partition enrichment (CBSSD baseline).

    term_dataset = defaultdict(list) of node:[a1..an] mappings
    term_datset = Counter object of individual annotation occurrences
    all_counts = number of all annotation occurences

    """
    ## 3.) calculate p-vals.
    significant_results = compute_enrichment(term_dataset, term_database, topology_map, all_counts,whole_term_list=False)
    return significant_results


## write this so it uses vanilla data structures
def fet_enrichment_uniprot(partition_mappings,annotation_mappings):
    
    ## 1.) read the database.
    term_dataset, term_database, all_counts =  read_uniprot_GO(annotation_mappings)
    
    ## 2.) partition function dict.
    topology_map = read_topology_mappings(partition_mappings)

    ## 3.) calculate p-vals.
    significant_results = compute_enrichment(term_dataset, term_database, topology_map, all_counts,whole_term_list=False)

    return significant_results

if __name__ == "__main__":

    pass
