

# C.ELEGANS MULTIPLEX CONNECTOME

###### Last update: 1 July 2014

### Reference and Acknowledgments

This README file accompanies the dataset representing the multiplex neuronal network of the nematode "Caenorhabditis Elegans". 
If you use this dataset in your work either for analysis or for visualization, you should acknowledge/cite the following papers:

	“Wiring optimization can relate neuronal structure and function”
	Beth L. Chen, David H. Hall, and Dmitri B. Chklovskii
	PNAS 2006 103 (12) 4723–4728
	
	“MuxViz: A Tool for Multilayer Analysis and Visualization of Networks”
	Manlio De Domenico, Mason A. Porter, and Alex Arenas
	Journal of Complex Networks 2015 3 (2) 159-176
	
that can be found at the following URLs:

<http://www.pnas.org/content/103/12/4723.abstract>

<http://comnet.oxfordjournals.org/content/3/2/159>

This work has been supported by European Commission FET-Proactive project PLEXMATH (Grant No. 317614), the European project devoted to the investigation of multi-level complex systems and has been developed at the Alephsys Lab. 

Visit

PLEXMATH: <http://www.plexmath.eu/>

ALEPHSYS: <http://deim.urv.cat/~alephsys/>

for further details.



### Description of the dataset

Caenorhabditis elegans connectome, where the multiplex consists of layers corresponding to different synaptic junctions: electric (“ElectrJ”), chemical monadic (“MonoSyn”), and polyadic (“PolySyn”). 

The multiplex network used in the paper makes use of three layers corresponding to:

1.	Electric (“ElectrJ”)
2.	Chemical Monadic (“MonoSyn”)
3.	Chemical Polyadic (“PolySyn”)

There are 279 nodes, labelled with integer ID between 1 and 279, and 5863 synaptic connections.
The multiplex is undirected (with only one direction specified) and unweighted, stored as edges list in the file
    
    celegans_connectome_multiplex.edges

with format

    layerID nodeID nodeID weight

(Note: weight is 1 for all edges)

The IDs of all layers are stored in 

    celegans_connectome_layers.txt

The IDs of nodes, together with their name can be found in the file

    celegans_connectome_nodes.txt



### License

This C.ELEGANS MULTIPLEX CONNECTOME DATASET is made available under the Open Database License: <http://opendatacommons.org/licenses/odbl/1.0/>. Any rights in individual contents of the database are licensed under the Database Contents License: <http://opendatacommons.org/licenses/dbcl/1.0/>

You should find a copy of the above licenses accompanying this dataset. If it is not the case, please contact us (see below).

A friendly summary of this license can be found here:

<http://opendatacommons.org/licenses/odbl/summary/>

and is reported in the following.

======================================================
ODC Open Database License (ODbL) Summary

This is a human-readable summary of the ODbL 1.0 license. Please see the disclaimer below.

You are free:

*    To Share: To copy, distribute and use the database.
*    To Create: To produce works from the database.
*    To Adapt: To modify, transform and build upon the database.

As long as you:
    
*	Attribute: You must attribute any public use of the database, or works produced from the database, in the manner specified in the ODbL. For any use or redistribution of the database, or works produced from it, you must make clear to others the license of the database and keep intact any notices on the original database.
    
*	Share-Alike: If you publicly use any adapted version of this database, or works produced from an adapted database, you must also offer that adapted database under the ODbL.
    
*	Keep open: If you redistribute the database, or an adapted version of it, then you may use technological measures that restrict the work (such as DRM) as long as you also redistribute a version without such measures.

======================================================


### Contacts

If you find any error in the dataset or you have questions, please contact

	Manlio De Domenico
	Universitat Rovira i Virgili 
	Tarragona (Spain)

email: <manlio.dedomenico@urv.cat>web: <http://deim.urv.cat/~manlio.dedomenico/>