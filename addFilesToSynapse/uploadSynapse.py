import synapseclient 
from synapseclient import File
import synapseHelpers
import pandas as pd
import os, urllib, urlparse
import multiprocessing.dummy as mp
from collections import Counter

import synapseHelpers
BASE = '/tcgapancan/pancan/variant_calling_pilot_64/'
URLBASE = 'sftp://tcgaftps.nci.nih.gov'
DATATYPES = ['snv_mnv', 'snv', 'mnv', 'indel', 'sv', 'cnv', 'binnedReadCounts', 'verifyBamId']
DIRS = {'broad': 'syn3165121',
        'BSC': 'syn3165143',
        'wustl': 'syn3165146',
        'yale':'syn3165120', 
        'mda_kchen': 'syn3165149', 
        'MDA_HGSC': 'syn3167886', 
        'mcgill_popsv': 'syn3165151',
        'oicr_sga': 'syn3167076',
        'sfu': 'syn3165152', 
        'LOHcomplete': 'syn3168451',
        'Synteka_pgm21': 'syn3206414',
        'oicr_bl': 'syn3206415', 
        'crg_clindel': 'syn3206417'}

syn = synapseclient.Synapse(skip_checks=True)
syn.login(silent=True)

def url2path(str):
    return urllib.unquote(urlparse.urlparse(str).path)


def findFilesAlreadyInSynapse():
    """Determine the files already stored in Synapse"""
    allFiles= synapseHelpers.query2df(syn.chunkedQuery("select * from file where benefactorId=='syn2351328'"), False)
    print 'Found', len(allFiles), 'files in Synapse.  Fetching urls...'
    def get(id):
        print id
        return syn.get(id, downloadFile=False)
    entities = p.map(get,  allFiles.id)
    return entities


def findMissingSangerFiles(entities, files):
    savedURLs = [e.externalURL for e in entities if e.parentId in ('syn3155834')]
    #Create a data frame
    sangerfiles_in_synapse = [s.replace('sftp://tcgaftps.nci.nih.gov', '').strip() for s in savedURLs]
    dfSynapse = pd.DataFrame(sangerfiles_in_synapse, columns= ['synapse_path'])
    dfSynapse.index = [s.split('/')[-1]  for s in dfSynapse.synapse_path]

    #Filter out Sanger files out of all files in Jamboree
    sangerfiles_in_jamboree = [f.strip() for f in files if 'Sanger' in f]
    dfJamboree = pd.DataFrame(sangerfiles_in_jamboree, columns= ['jamboree_path'])
    dfJamboree.index = [s.split('/')[-1]  for s in dfJamboree.jamboree_path]

    #Merge the dataframse to find differences
    df = dfSynapse.merge(dfJamboree, 'outer', left_index=True, right_index=True)
    df.ix[df.synapse_path.isnull() | df.jamboree_path.isnull(), :].to_csv('missing_files.csv')


def findFilesNotInJamboreeButInSynapse(entities):
    """
    """
    savedURLs = [e.externalURL for e in entities if 
                 e.externalURL is not None and 
                 e.externalURL.startswith('sftp://tcgaftps.nci.nih.gov')]
    urls = set([url2path(y) for y in savedURLs ])
    
    with open('jamboree_only_files.txt') as fp:
        files = fp.readlines()
        files = [f.strip() for f in files]
    files = set(files)
    print list(files)[0]
    print list(urls)[0]
    print len(urls), len(files), len(urls - files)
    return urls-files

def uploadToSynapse(f):
    """Given a filepath extracts metadata and uploads to Synapse"""
    center, sample_id, workflow_name, date, call_type, dataType, fileType = ['']*7
    url = URLBASE+f
    if   'OICR_BL' in f: center = 'oicr_bl'
    elif 'CRG/clindel/somatic' in f:  center = 'crg_clindel'
    else: center = f.split('/')[4]
    filename =  f.split('/')[-1]
    if center in ('yale', 'wustl', 'LOHcomplete'):
        if filename =='bd829214-f230-4331-b234-def10bbe7938CNV.vcf.gz':
            sample_id, dataType, fileType='bd829214-f230-4331-b234-def10bbe7938', 'cnv', 'vcf'
        else:
            sample_id, dataType = filename.lower().split('.')[:2]
            fileType =  [i for i in filename.split('.')[2:] if i != 'gz'][-1]
    elif center in ('broad', 'BSC', 'oicr_sga', 'mda_kchen', 'MDA_HGSC', 'mcgill_popsv', 'sfu', 'UCSC', 'oicr_bl', 'Synteka_pgm21', 'crg_clindel'):
        sample_id, workflow_name, date, call_type, dataType  =  filename.replace('indels', 'indel', split('.')[:5])
        fileType =  [i for i in filename.split('.')[5:] if i != 'gz'][-1]
    else:
        print 'Not uploading:', f
        return 
    print center, workflow_name, date, call_type, dataType, fileType
    file = File(url, parentId=DIRS[center], synapseStore=False)
    file.center = center.lower()
    file.sample_id = sample_id
    file.workflow_name = workflow_name
    file.date = date
    file.call_type = call_type
    file.dataType = 'DNA'
    file.disease = 'Cancer'
    file.dataSubType = dataType
    file.fileType = fileType
    #file.analysis_id_tumor = ?????
    syn.store(file, forceVersion=False)


if __name__ == '__main__':
    p = mp.Pool(9)
    #Files in Jamboree to add
    with open('jamboree_pilot_64.txt') as fp:
        files = fp.readlines()
        files = [f.strip() for f in files]

    #Files already uploaded to Synapse
    entities = findFilesAlreadyInSynapse()
    savedURLs = [e.externalURL for e in entities if e.externalURL is not None]
    #findMissingSangerFiles(entities, files) #Used to inform OICR 
    #missing =  findFilesNotInJamboreeButInSynapse(entities)
    #print Counter([f[:40] for f in missing]).most_common()
    
    ###REMOVE files already uploaded or for other reasons
    urls = set([url2path(y) for y in savedURLs ])
    files = [y for y in files if y not in urls]
    files = [y for y in files if not y.endswith('md5\n')]     #Remove md5 sum files
    files = [f for f in files if 'dkfz' not in f] #Remove DKFZ uploaded twice
    files = [f for f in files if 'OICR_Sanger_Core' not in f] #Remove Sanger 
    files = [f for f in files if 'OICR_staging' not in f] #Remove Staging
    files = [f for f in files if 'embl' not in f]  #Remove embl files (md5 and lowconf)

    #Not permanent filters
    files = [f for f in files if 'germline' not in f]  #Remove germline samples
    files = [f for f in files if '1000Genome' not in f and '1KG' not in f] #Remove 1000Genomes
    files = [f for f in files if 'HALLYM/GATK/tumor' not in f] #Remove
    #Upload the remaining files to Synapse
    p.map(uploadToSynapse, files)

    #Counter([os.path.dirname(f.replace(BASE, '')) for f in files]).most_common()



