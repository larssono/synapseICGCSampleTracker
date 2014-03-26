##Background
This tool is used specifically for tracking the re-alignment of the TCGA whole genome samples across multiple data centers.  The state is kept in Synapse and can be tracked at:

[https://www.synapse.org/#!Synapse:syn2364746](https://www.synapse.org/#!Synapse:syn2364746) 

for all TCGA and ICGC samples. Lane level bam files for the TCGA samples are tracked at:

[https://www.synapse.org/#!Synapse:syn2381914]([https://www.synapse.org/#!Synapse:syn2381914)

##Prerequisites

In order to use this tool you will have to register an account with Synapse and install the Python Synapse client.

1. Register for an account on [Synapse registration page](https://www.synapse.org/#!RegisterAccount:0)
2. Request write access to the ICGC/TCGA Whole Genome PAWG by contacting Larsson or Kyle
3. Install the Python Synapse client
```
pip install synapseclient
```
or follow the instructions on the getting started [help pages](https://www.synapse.org/#!Synapse:syn1768504)
4. Set-up caching of credentials so you don't have to specify login credentials for each command.  Run the synapse login command:
```
synapse login -u username -p secret --rememberMe
```


##Additional commandlines to track status

The processing of the files follows 4 steps:

1. Claim a bam file from CGHub to be split into lane level bam files. This is done with the getBamFileForSplice subcommand
```
synapseICGCMonitor getBamForSplit ucsc
```
where the second parameter is the center that is claiming the file.

2. "Upload" the locations of the split bam files.  This is done with the addSplitBamFiles subcommand.  In order to keep track of the location of the file the ip address of the machine where it is stored as well as the acccession identifier of the parent bam file needs to be specified.
```
synapseICGCMonitor addSplitBamFiles b445f98f-05d4-458b-9141-4dee44774660 127.0.0.1 path/to/file1.bam /path/to/file2.bam
```
3. Lane level bam files can then be checked out for the aligners by calling getBamForAlignment.
```
synapseICGCMonitor getBamForAlignment ucsc_computer1
```
which takes a parameters indicating the assignee of the job such as a processId or node.

4. Adding of the aligned file location.  Once the data has been aligned and re-uploaded to CGHub the status table is updated with the file location with:
```
synapseICGCMonitor submitAlignedBam syn123 1324bxcv-05d4-458b-9141-4dee44774770
```
which takes the id representing the split bam file and the accession uuid of the newly aligned file in cghub.

In addition it is possible to reset the status of an accession with

```
synapseICGCMonitor resetStatus b445f98f-05d4-458b-9141-4dee44774660
```

##Getting Help
All commands are handled by synapseICGCMonitor followed by a subcommand.  Most of these subcommands come with  additional paramters that can be explored with the help system.

```
synapseICGCMonitor -h
```
list the subcommands and 
```
synapseICGCMonitor SUBCOMMMAND -h
```
gets help on a specific subcommand.


