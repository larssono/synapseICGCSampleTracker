import synapseclient 
from synapseclient import File
import synapseHelpers
import pandas as pd
import os, urllib, urlparse
import multiprocessing.dummy as mp
from collections import Counter

QUERY = "select * from file where projectId=='syn2351328' and dataType=='DNA' and call_type=='somatic'"

syn = synapseclient.Synapse(skip_checks=True)
syn.login(silent=True)


if __name__ == '__main__':
    df= synapseHelpers.query2df(syn.chunkedQuery(QUERY), True, ['name', 'id', 'parentId'])
    df = df[[x in ('snv_mnv', 'sv', 'indel', 'cnv') for x in df.dataSubType]]

    #Pretyify Source names:
    df['source'] = [c.split('_')[0].upper() if isinstance(c, basestring) else '' for c in df.center]
    df.source[df.workflow_name =='SangerPancancerCgpCnIndelSnvStr'] = 'Sanger'
    
    #Summarize number of samples
    counts = pd.pivot_table(df, 'sample_id', 
                            rows=['source', 'workflow_name'], 
                            cols = ['dataSubType'], 
                            aggfunc=lambda x: len(set(x)))

    #Display number of samples
    #counts.plot(kind='bar')
    #Attempt at getting rid of missing bars
    #pd.melt(counts.reset_index(), id_vars=['source', 'workflow_name']).plot(kind='bar')

    counts[counts.isnull()] =''
    print synapseHelpers.df2markdown(counts)
    

    #Create summary table of all VCF files
    vcfdf = df[df.fileType=='vcf'][['sample_id', 'workflow_name', 'dataSubType', 'id']]
    vcfdf['name'] = [x.workflow_name+'_'+x.dataSubType for i,x in vcfdf.iterrows()]
    vcfdf.pivot('sample_id', 'name', 'id')
    table = vcfdf.pivot('sample_id', 'name', 'id')
    table[table.isnull()]=''
    print synapseHelpers.df2markdown(table)
