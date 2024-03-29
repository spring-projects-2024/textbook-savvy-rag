#REF: https://pythonhosted.org/refextract/
#magic-bin is required:  pip install python-magic-bin

from refextract import extract_references_from_url

def get_references(id):
    """Extract list of references from an ArXiv paper. Given the ArXiv ID of the paper, builds the url of pdf version (required for the retrieval)"""
    reference = extract_references_from_url("http://arxiv.org/pdf/"+str(id)+".pdf")
    return reference






