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
5. Run `touch ~/.synapseConfig` to get rid of a warning message that the library prints to STDOUT (otherwise 
it messages "Could not find a config file (/Users/kellrott/.synapseConfig" to STDOUT).  Using defaults."). This bug will 
be fixed in future releases.

##Additional commandlines to track status

The processing of the files follows 4 steps:

1. Claim a bam file from CGHub to be split into lane level bam files. This is done with the getBamFileForSplice subcommand
   ```
   synapseICGCMonitor getBamForWork ucsc
   ```
where the second parameter is the center that is claiming the file.

2. For each stage, you can obtain work using the request 'getAssignmentForWork', which will: 1) print out the UUID for bam file of a given state
   2)Update the state in the tracking system to the next active state according to the state chain:

   The state chain is:
   unassigned -> todownload -> downloading -> downloaded -> splitting -> split -> aligning -> aligned -> uploading -> uploaded

   If no valid work remains to be done, a non-zero exit status will be returned.
   Active states are ones that can be completed, or return an error. They include: downloading, splitting, aligning, uploading

   Example BASH control loop

   ```
   while :
   do
      UUID=`synapseICGCMonitor getAssignmentForWork ucsc todownload`
      if [ $? != 0 ]; then 
         sleep 60
      else
         gtdownload $UUID
         if [ $? != 0]; then
            synapseICGCMonitor errorAssignment $UUID "Error happened during gtdownload"
         else
            synapseICGCMonitor returnAssignment $UUID
         fi
      fi
    done
    ```

3. When BAM is split, entities to store the readgroup meta-data will need to be generated. This is done with the addBamGroups subcommand.  

   ```
   synapseICGCMonitor addBamGroups b445f98f-05d4-458b-9141-4dee44774660 /path/to/file1.bam
   ```

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


##Extracting status using the Query engine
Most of the functionality described above uses queries (with additional handling of collisions and prioritization of files."  This means it is possible to track the status using the Synapse query services. For example to find all bam files currently awaiting to be handled you can from the command line:
```
synapse query "select name, id, accession_identifier from file where parentId=='syn2364746' and status=='unassigned'"
```
additional filtering can be done on columns such as fileSize, donor_identifier, fileMd5 etc.
