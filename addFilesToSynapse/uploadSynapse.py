import synapseclient 
from synapseclient import File
import pandas as pd
import os, urllib
import multiprocessing.dummy as mp

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
        'LOHComplete': 'syn3168451'}

syn = synapseclient.Synapse(skip_checks=True)
syn.login(silent=True)


def findFilesAlreadyInSynapse():
    """Determine the files already stored in Synapse"""
    allFiles= synapseHelpers.query2df(syn.chunkedQuery("select * from file where benefactorId=='syn2351328'"), False)
    entities = p.map(lambda id: syn.get(id, downloadFile=False), allFiles.id)
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


def uploadToSynapse(f):
    """Given a filepath extracts metadata and uploads to Synapse"""
    center, sample_id, workflow_name, date, call_type, dataType, fileType = ['']*7
    url = URLBASE+f
    if len(f.split('/')) >6:
        #TODO add 
        #  center = OICR_BL/sv and OICR_BL/snv as center
        #  center = LOHcomplete
        return
    center= f.split('/')[4]
    filename =  f.split('/')[-1]
    if center in ('yale', 'wustl', 'LOHcomplete'):
        if filename =='bd829214-f230-4331-b234-def10bbe7938CNV.vcf.gz':
            sample_id, dataType, fileType='bd829214-f230-4331-b234-def10bbe7938', 'cnv', 'vcf'
        else:
            sample_id, dataType = filename.lower().split('.')[:2]
            fileType =  [i for i in filename.split('.')[2:] if i != 'gz'][-1]
    elif center in ('broad', 'BSC', 'oicr_sga', 'mda_kchen', 'MDA_HGSC', 'mcgill_popsv', 'sfu'):
        sample_id, workflow_name, date, call_type, dataType  =  filename.split('.')[:5]
        fileType =  [i for i in filename.split('.')[5:] if i != 'gz'][-1]
    else:
        print f
        return 
    #TODO uncomment frome here on.
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
    syn.store(file, forceVersion=False)



if __name__ == '__main__':
    p = mp.Pool(9)
    #Files in Jamboree to add
    with open('jamboree_pilot_64.txt') as fp:
        files = fp.readlines()
        files = [f.strip() for f in files]

    #Files already uploaded to Synapse
    entities = findFilesAlreadyInSynapse()
    savedURLs = [e.externalURL for e in entities if e.externalURL is not None]# if e.parentId in ('syn3155834', 'syn3049523', 'syn2898426', 'syn3153526', 'syn3107237', 'syn3104289', 'syn3060776', 'syn3049525', 'syn3153529')]
    #findMissingSangerFiles(entities, files) #Used to inform OICR 

    ###REMOVE files already uploaded or for other reasons
    #Remove all already uploaded
    urls = set([urllib.unquote(y[27:]) for y in savedURLs ])
    files = [y for y in files if y not  in urls]
    #Remove md5 sum files
    files = [y for y in files if not y.endswith('md5\n')]
    #Remove already uploaded DKFZ files
    files = [y for y in files if 'dkfz' not in y]
    #Remove already uploaded embl files 
    files = [y for y in files if 'embl' not in y] #skips somatic_lowconf.sv.vcf
    #Remove already uploaded Sanger files 
    sangerSaved = set([y.split('/')[-1] for y in savedURLs if 'Sanger' in y])
    files = [y for y in files if (y.split('/')[-1] not in sangerSaved and 'OICR_Sanger_Core' in y) or 'OICR_Sanger_Core' not in y]

    #Upload the remaining files to Synapse
    p.map(uploadToSynapse, files)

    #Counter([os.path.dirname(f.replace(BASE, '')) for f in files]).most_common()
    # [('OICR_Sanger_Core', 913),
    #  ('HALLYM/GATK/germline', 252),
    #  ('HALLYM/GATK/tumor', 224),
    #  ('CRG/pesvfisher/germline', 150),
    #  ('LOHcomplete', 136),
    #  ('OICR_BL/snv', 126),
    #  ('Synteka_pgm21', 126),
    #  ('CRG/clindel/somatic', 126),
    #  ('CRG/clindel/germline', 118),
    #  ('OICR_BL/sv', 98),
    #  ('HALLYM/GATK/1000Genome_original', 24),
    #  ('HALLYM/GATK/1000Genome_platinum', 24),
    #  ('yale/1KG', 12)]
    #yale = [f for f in files if 'sfu' in f] 

#4326
#2437
#1528
#2329
