

# NYCLIMATEMARCH2014 MULTIPLEX SOCIAL NETWORK

###### Last update: 05 Oct 2015
 
### Reference and Acknowledgments

This README file accompanies the dataset representing the multiplex social network of users in Twitter.
If you use this dataset in your work either for analysis or for visualization, you should acknowledge/cite the following paper:
	
	'Characterizing interactions in online social networks during exceptional events'
	E. Omodei, M. De Domenico, A. Arenas
	Front. Phys. 2015 3, 59


that can be found at the following URL:

<http://journal.frontiersin.org/article/10.3389/fphy.2015.00059/abstract>

This work has been supported by European Commission FET-Proactive project PLEXMATH (Grant No. 317614), the European project devoted to the investigation of multi-level complex systems and has been developed at the Alephsys Lab. 

Visit

PLEXMATH: <http://www.plexmath.eu/>

ALEPHSYS: <http://deim.urv.cat/~alephsys/>

for further details.



### Description of the dataset

We consider different types of social relationships amoung users, obtained from Twitter during an exceptional event. In this specific dataset we focused on [People's Climate March](https://en.wikipedia.org/wiki/People’s_Climate_March) in 2014

The multiplex network used in the paper makes use of 3 layers, corresponding to retweet, mentions and replies observed between


    Start: 2014-09-19 00:46:19
    End: 2014-09-22 06:56:25

There are 102439 nodes, labelled with integer ID between 1 and 102439 and 353495 connections.
The multiplex is directed and weighted (obtained by summing up the number of a specific type of interaction over time), stored as edges list in the file

    NYClimateMarch2014_multiplex.edges

with format

    layerID nodeID nodeID weight

The IDs of all layers are stored in

    NYClimateMarch2014_layers.txt

The IDs of nodes (note that screen names are not provided for privacy reasons) can be found in the file

    NYClimateMarch2014_nodes.txt


In addition, online interactions of users are provided with the temporal information in the file

    NYClimateMarch2014_activity.txt

with format

    nodeID nodeID timestamp type

where timestamp is in seconds and type is the layer name. There are 413350 temporal interactions, in total.

Note 1: the direction of links depends on the application, in general. For instance, if one is interested in building a network of how information flows, then the direction of RT should be reversed when used in the analysis. Nevertheless, the choice is left to the researcher and his/her own interpretation of the data, whereas we just provide the observed actions, i.e., who retweets/mentions/replies/follows whom.

Note 2: users mentioned in retweeted tweets are considered as mentions. For instance, if @A retweets the tweet 'hello @C @D' sent by @B, then the following links are created: @A @B timeX RT, @A @C timeX MT, @A @D timeX MT, because @C and @D can be notified that they have been mentioned in a retweet. Similarly in the case of a reply. If for some reason the researcher does not agree with this choice, he/she can easily identify this type of links and remove the mentions, for instance.


### License

This NYCLIMATEMARCH2014 MULTIPLEX SOCIAL NETWORK is made available under the Open Database License: <http://opendatacommons.org/licenses/odbl/1.0/>. Any rights in individual contents of the database are licensed under the Database Contents License: <http://opendatacommons.org/licenses/dbcl/1.0/>

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

email: <manlio.dedomenico@urv.cat>

web: <http://deim.urv.cat/~manlio.dedomenico/>

