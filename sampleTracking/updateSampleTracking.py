import synapseclient
from synapseclient import File, Folder
import gdata.docs
import gdata.docs.service
import gdata.spreadsheet.service
import re, os
import string
import sys

PROJECT='syn2351328'
THEMES =['Novel somatic mutation calling methods',
         'Analysis of mutations in regulatory regions',
         'Integration of transcriptome and genome',
         'Integration of epigenome and genome',
         'Consequences of somatic mutations on pathway and network activity',
         'Patterns of structural variations, signatures, genomic correlations, retrotransposones, mobile elements',
         'Mutation signatures and processes',
         'Germline cancer genome',
         'Inferring driver mutations and identifying cancer genes and pathways',
         'Translating cancer genomes to the clinic',
         'Evolution and heterogeneity',
         'Portals, visualization and software infrastructure',
         'Molecular subtypes and classification',
         'Analysis of mutations in non-coding RNA',
         'Exploratory',
         'Pathogens']



syn=synapseclient.Synapse()
syn.login() 


#Set up sample tracking      
USERNAME='larsson.omberg@sagebase.org'
PASSWORD=sys.argv[1]
DOCNAME='PanCancer sample-tracking Master List 2013-02-21'
FAKE_RECORDSTORE_ID='syn2364746'
BASE_URL='https://cghub.ucsc.edu/cghub/data/analysis/download/'
#SPREADSHEET = 'https://docs.google.com/a/sagebase.org/spreadsheet/ccc?key=0ApWzavEDzSJddEhIRjQ1X05MVE1oLWIwT1l3Z2xsOXc&usp=sharing#gid=0'

# Connect to Google
gd_client = gdata.spreadsheet.service.SpreadsheetsService()
gd_client.source = 'sagebase_createRecordStoreFromGoogleDoc'
gd_client.email = USERNAME
gd_client.password = PASSWORD
gd_client.ProgrammaticLogin()
#gd_client.SetClientLoginToken(TOKEN)

## Find the right spreadsheet and open the document for reading
q = gdata.spreadsheet.service.DocumentQuery()
q['title'] = DOCNAME
q['title-exact'] = 'true'
feed = gd_client.GetSpreadsheetsFeed(query=q)
spreadsheet_id = feed.entry[0].id.text.rsplit('/',1)[1]
feed = gd_client.GetWorksheetsFeed(spreadsheet_id)
worksheet_id = feed.entry[0].id.text.rsplit('/',1)[1]

rows = gd_client.GetListFeed(spreadsheet_id, worksheet_id).entry
for i, row in enumerate(rows[3000:]):
    print i+3000, row.custom['projectcode'].text, '%s_%s' %(row.custom['accessionidentifier'].text, row.custom['sampleidentifier'].text)
    if 'TCGA' in row.custom['study'].text:
        path = '%s%s' %(BASE_URL, row.custom['accessionidentifier'].text)
        location='CGHub'
    else:
        path = row.custom['accessionidentifier'].text
        path = 'None' if path is None else path
        location=None

    record = File(path=path,
                  name = '%s_%s' %(row.custom['accessionidentifier'].text, row.custom['sampleidentifier'].text),
                  parentId=FAKE_RECORDSTORE_ID, synapseStore=False)
    record['location'] = location
    record['Study'] = row.custom['study'].text
    record['project_code']=row.custom['projectcode'].text
    record['accession_identifier'] = row.custom['accessionidentifier'].text
    record['donor_identifier'] = row.custom['donoridentifier'].text
    record['speciment_identifier'] = row.custom['specimenidentifier'].text
    record['sample_identifier'] = row.custom['sampleidentifier'].text
    record['sample_type_name']  = row.custom['normaltumourdesignation'].text
    record['matching_sample_identifier']  = row.custom['matchingnormalortumoursampleidentifier'].text
    record['sequencing_strategy'] =  row.custom['sequencingstrategy'].text
    record['number_of_bam_files'] =  row.custom['numberofbamfilessample'].text
    record['raw_data_filename'] =  row.custom['rawdatafilename'].text
    record['assignee'] =  row.custom['assignee'].text
    record['status'] = 'unassigned'


    record['aligning_center'] = ' '
    record['vcf'] = ' '

    syn.store(record, forceVersion=False)
 # specimenidentifiersampleid: 62bff77e-4fe6-4a9f-a867-345584608e7d
 # normaltumordesignationsampletypename: Primary Solid Tumor
 # donoridentifierparticipantid: 9205c164-7975-421a-90c3-edfe8def595c
 # rawdatafilenamefilename: 9e0aa323dd137c62bd3ba6626357862a.bam
 
# for row in rows:
#     for key in row.custom:
#         print " %s: %s" % (key, row.custom[key].text)
#     print

# for row in rows:
#     sampleName = row.custom['decoratedname'].text
#     record = synapseclient.Folder(name=sampleName, parentId=FAKE_RECORDSTORE_ID)
#     for key in row.custom:
#         if key == 'decoratedname':
#             record['decoratedName'] = sampleName
#             record['fastqId'] = syn._findEntityIdByNameAndParent('%s.fastq' %sampleName, FASTQ_ID)
#         else:
#             val = row.custom[key].text
#             val = None if val=='na' else val
#             if val is not None:
#                 try:
#                     val = int(val)
#                 except ValueError:
#                     try:
#                         val = float(val)
#                     except ValueError:
#                         pass
#             record[key.replace('-', '_')] = val
#     print record
#     syn.store(record)


    


