from xml.dom.minidom import parseString
import requests


def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
    
    
def dom_scan(node, query):
    stack = query.split("/")
    if node.localName == stack[0]:
        return dom_scan_iter(node, stack[1:], [stack[0]])
    return []

def dom_scan_iter(node, stack, prefix):
    if len(stack):
        for child in node.childNodes:
                if child.nodeType == child.ELEMENT_NODE:
                    if child.localName == stack[0]:
                        for out in dom_scan_iter(child, stack[1:], prefix + [stack[0]]):
                            yield out
                    elif '*' == stack[0]:
                        for out in dom_scan_iter(child, stack[1:], prefix + [child.localName]):
                            yield out
    else:
        if node.nodeType == node.ELEMENT_NODE:
            yield node, prefix, dict(node.attributes.items()), getText( node.childNodes )
        elif node.nodeType == node.TEXT_NODE:
            yield node, prefix, None, getText( node.childNodes )
            

#build the cghub info tables

#req = requests.get("https://cghub.ucsc.edu/cghub/metadata/analysisDetail?study=*")
#dom = parseString(req.text)

name_map = {}
md5_map = {}
size_map = {}
for node, prefix, attr, text in (dom_scan(dom.childNodes[0], "ResultSet/Result")):
    filename = None
    file_md5 = None
    filesize = None
    for res in dom_scan(node, "Result/files/file"):
        for res_barcorde in dom_scan(res[0], "Result/legacy_sample_id"):
            barcode = res_md5[3]
        for res_name in dom_scan(res[0], "file/filename"):
            if not res_name[3].endswith(".bai"):
                filename = res_name[3]
                for res_md5 in dom_scan(res[0], "file/checksum"):
                    file_md5 = res_md5[3]
                for res_md5 in dom_scan(res[0], "file/filesize"):
                    filesize = res_md5[3]

    analysis_id = None
    for res in dom_scan(node, "Result/analysis_id"):
        analysis_id = res[3]
    name_map[analysis_id] = filename
    md5_map[analysis_id] = file_md5
    size_map[analysis_id] = int(filesize)
    #barcode_map[analysis_id] = barcode

    #participant_id

#########################
#Add file annotation for 
#########################
import synapseclient
syn=synapseclient.login() 

for val in  syn.chunkedQuery("select accession_identifier, fileSize from file where parentId=='syn2364746' and location=='CGHub'"):
    id = val['file.id']
    accession = val['file.accession_identifier'][0]
    if val['file.fileSize'] is None:
        print id, size_map[accession], md5_map[accession]
        print syn.setAnnotations(id, syn.getAnnotations(id), 
                                 fileSize=size_map[accession], 
                                 fileMD5=md5_map[accession])
