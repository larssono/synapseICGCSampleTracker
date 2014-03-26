#!/usr/bin/env python
"""
Tracker for ICGC realignment of TCGA data
"""
import argparse
import os
import sys
import synapseclient
import json
from synapseclient.exceptions import *
import itertools
import collections
TRACKER_ID='syn2364746'#'syn2381825' #
SPLIT_TRACKER_ID = 'syn2381914'


def getBamForSplit(args, syn):
    """Returns highest priority unassigned BAM files and changes status to splitting.

    Queries the list of remaining unassigned samples orderd by
    fileSize and tries to change status of to splitting of largest.  If successfull it returns the highest 
    """
    ids = getOrderedListOfUnassigned(syn)
    sys.stderr.write('%i Unprocessed TCGA Samples\n' %len(ids))
    i = 0 
    while True:
        if i==len(ids):
            sys.stderr.write('No more samples available\n')
            return 
        ent = syn.get(ids[i], downloadFile=False)
        if ent.status[0] !='unassigned': 
            i+=1 
            continue
        ent.assignee = args.assignee
        ent.status = 'splitting'
        try:
            syn.store(ent)
            print ent.accession_identifier[0]
            break
        except SynapseHTTPError:
            i+=1
    

def getOrderedListOfUnassigned(syn):
    """Performs a query and filters out donors with more than two files
    and return a list of ids inversly sorted by fileSize.
    """
    QUERY= "select accession_identifier, donor_identifier, fileSize from file where parentId=='%s' and location=='CGHub' and status=='unassigned'" %TRACKER_ID
    results = list(syn.chunkedQuery(QUERY))

    #Determine the donor ids of the samples with two files
    donors = syn.chunkedQuery("select donor_identifier from file where parentId=='%s' and location=='CGHub'" %TRACKER_ID)
    donorCounts = collections.Counter([result['file.donor_identifier'][0] for result in donors])
    donors = [donor for donor, count in donorCounts.iteritems() if count==2]

    #Go through query result and remove rows not in donor list
    fileSizes=list()
    accessions=list()
    ids = list()
    for result in results:
        if result['file.donor_identifier'][0] in donors:
            fileSizes.append(result['file.fileSize'][0] if result['file.fileSize'] is not None else None)
            accessions.append(result['file.accession_identifier'][0])
            ids.append(result['file.id'])

    #Sort by fileSize
    idx = argsort(fileSizes)    
    ids = [ids[i] for i in idx[::-1]]
    return ids
    
def addSplitBamFiles(args, syn):
    """Adds file entities for each of the split bam files """
    id =list(syn.chunkedQuery("select id from file where parentId=='%s' and accession_identifier=='%s'" %(TRACKER_ID, args.accession)))
    if len(id)==0:
        raise Exception('The accession id used is invalid')
    else:
        id = id[0]['file.id']
    for path in args.paths:
        file = synapseclient.File(path, parent=SPLIT_TRACKER_ID, synapseStore=False)
        file.host = args.host
        file.status = 'unassigned'
        file.derivedAccession = args.accession
        file.assignee = None
        syn.store(file, used = [id])


def getBamForAlignment(args, syn):
    ids = syn.chunkedQuery("select id from file where parentId=='%s' and status=='unassigned'" %SPLIT_TRACKER_ID)
    ids = list(ids)
    sys.stderr.write('%i Unprocessed split BAM files\n' %len(ids))
    i = 0 
    while True:
        if i==len(ids):
            sys.stderr.write('No more samples available\n')
            return 
        ent = syn.get(ids[i]['file.id'], downloadFile=False)
        if ent.status[0] !='unassigned': 
            i+=1 
            continue
        ent.assignee = args.assignee
        ent.status = 'aligning'
        try:
            syn.store(ent, forceVersion=False)
            print ent.id, ent.host[0], ent.path
            break
        except SynapseHTTPError:
            i+=1

def submitAlignedBam(args, syn):
    ent = syn.get(args.id, downloadFile=False)
    ent.status='aligned'
    ent.path = args.uuid
    syn.store(ent)



def resetStatus(args, syn):
    results =syn.chunkedQuery("select id from file where parentId=='%s' and accession_identifier=='%s'" %(TRACKER_ID, args.accession))
    for result in results:
        ent = syn.get(result['file.id'], downloadFile=False)
        ent.status=args.status
        ent.assignee=args.assignee
        syn.store(ent)


# --------------------- Util functions ----------------------------
def argsort(seq):
    # http://stackoverflow.com/questions/3071415/efficient-method-to-calculate-the-rank-vector-of-a-list-in-python
    return sorted(range(len(seq)), key = seq.__getitem__)


def build_parser():
    """Builds the argument parser and returns the result."""
    
    parser = argparse.ArgumentParser(
            description='Interfaces with the Synapse repository for sample tracking')
    parser.add_argument('--debug', dest='debug', action='store_true')
 
    subparsers = parser.add_subparsers( title='commands',
                                        description='The following commands are available:',
                                        help='For additional help: "synapseICGCMonitor <COMMAND> -h"')

    parser_get = subparsers.add_parser('getBamForSplit',
                                       help='Returns a unaligned un-split TCGA bam file UUID as stored on CGHub')
    parser_get.add_argument('assignee', metavar='assignee', type=str,
            help='Center processing file for example UCSC or EBI')
    parser_get.set_defaults(func=getBamForSplit)

    parser_reset = subparsers.add_parser('resetStatus',
                                       help='Given an UUID accession resets the status')
    parser_reset.add_argument('accession', metavar='accession', type=str,
            help='accession identifier to reset the status')
    parser_reset.add_argument('--assignee', metavar='assignee', type=str, default = None,
            help='Center processing file for example UCSC or EBI (defaults to None)')
    parser_reset.add_argument('--status', metavar='status', type=str, default = 'unassigned',
            help='status of file processing {unassigned, splitting, split, aligning, aligned}\n defaults to unassigned')
    parser_reset.set_defaults(func=resetStatus)

    parser_addFile = subparsers.add_parser('addSplitBamFiles',
                                           help='Adds the split bam files for monitoring and alignment')
    parser_addFile.add_argument('accession', metavar='accession', type=str,
                                 help='accession identifier from which files were derived')
    parser_addFile.add_argument('host', metavar='host', type=str,
                                help='VM host or ip address where files are being stored temporarily.')
    parser_addFile.add_argument('paths', metavar='paths', type=str,  nargs='*',
            help='space separated list of paths to split bam files.')
    parser_addFile.set_defaults(func=addSplitBamFiles)

    parser_getAlign = subparsers.add_parser('getBamForAlignment',
                                       help='Returns a unaligned lane level TCGA bam file location as a triple of accession ip address and file path')
    parser_getAlign.add_argument('assignee', metavar='assignee', type=str,
            help='Computer or process id processing the file')
    parser_getAlign.set_defaults(func=getBamForAlignment)

    parser_setAlign = subparsers.add_parser('submitAlignedBam',
                                       help='Marks alignment as done and stores UUID of CGHub File.')
    parser_setAlign.add_argument('synapseId', metavar='id', type=str,
            help='Synapse Id (as returned by getBamForAlignment to update.')
    parser_setAlign.add_argument('UUID', metavar='uuid', type=str,
            help='UUID that identifies the aligned bam in CGHub')
    parser_setAlign.set_defaults(func=submitAlignedBam)


    return parser



if __name__ == "__main__":
    args = build_parser().parse_args()
    syn = synapseclient.Synapse(debug=args.debug)
    syn.login(silent=True)
    if 'func' in args:
        args.func(args, syn)


