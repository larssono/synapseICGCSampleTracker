
#Step one Split file:
synapseICGCMonitor.py getBamForSplit ucsc


#Reset the status in case of mistakes:
synapseICGCMonitor.py resetStatus b445f98f-05d4-458b-9141-4dee44774660

#Add split bam files
synapseICGCMonitor.py addSplitBamFiles b445f98f-05d4-458b-9141-4dee44774660 127.0.0.1 path/to/file1.bam /path/to/file2.bam

synapseICGCMonitor.py getBamForAlignment asdf