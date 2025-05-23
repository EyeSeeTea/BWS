import os

from django.conf import settings

PATH_DATA = os.path.join(settings.BASE_DIR, 'data')
PATH_APP = "/app"
PATH_DATA = "/data"
PATH_TOOLS = "/tools"

EMDB_BASEDIR = 'emdbs'
EMDB_DATA_DIR = os.path.join(PATH_DATA, EMDB_BASEDIR)

EMV_BASEDIR = 'emv'
EMV_DATA_DIR = os.path.join(PATH_DATA, EMV_BASEDIR)

FUNPDBE_BASEDIR = "funpdbe"
FUNPDBE_DATA_PATH = os.path.join(PATH_DATA, FUNPDBE_BASEDIR)

THORN_BASEDIR = "coronavirus_structural_task_force/"
THORN_DATA_DIR = os.path.join(PATH_DATA, THORN_BASEDIR)

MODIFIED_PDBS_ANN_BASEDIR = "pdbRemodelAnn/"
MODIFIED_PDBS_ANN_DIR = os.path.join(PATH_DATA, MODIFIED_PDBS_ANN_BASEDIR)

COMPUT_MODELS_BASEDIR = "computModels/"
COMPUT_MODELS_DIR = os.path.join(PATH_DATA, COMPUT_MODELS_BASEDIR)

MODEL_AND_LIGAND_BASEDIR = "ligandModels/"
MODEL_AND_LIGAND_DIR = os.path.join(PATH_DATA, MODEL_AND_LIGAND_BASEDIR)

BIONOTES_URL = "https://3dbionotes.cnb.csic.es"
MAPPINGS_WS_PATH = "api/mappings"
EMV_WS_URL = "http://finlay.cnb.csic.es:8010"
EMV_WS_PATH = "emv"

# https://github.com/thorn-lab/coronavirus_structural_task_force/tree/master/pdb/nsp3/SARS-CoV-2/6vxs/isolde
CSTF_GITHUB_URL = "https://github.com/thorn-lab/coronavirus_structural_task_force/tree/master/pdb/"
# https://raw.githubusercontent.com/thorn-lab/coronavirus_structural_task_force/master/pdb/isolde_refinements.txt
CSTF_GITHUB_RAW_URL = "https://raw.githubusercontent.com/thorn-lab/coronavirus_structural_task_force/master/pdb/"
ISOLDE_REF_FNAME = "isolde_refinements.txt"
ISOLDE_JSON_FNAME = "isolde_entries.json"
CSTF_LOCAL_PATH = PATH_DATA + "/" + "cstf"
ISOLDE_LOCAL_DATA_PATH = CSTF_LOCAL_PATH + "/" + "isolde"
URL_ISOLDE_QUERY = "/isolde"
URL_UNIPROT = "https://www.uniprot.org/uniprot/"
URL_NCBI_TAXONOMY = "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id="
URL_PDB_REDO = 'https://pdb-redo.eu/'
URL_PDB_REDO_QUERY = '/pdb_redo/'
URL_CSTF = 'https://insidecorona.net/'
URL_PHENIX_STATUS = 'https://cci.lbl.gov/ceres/'
URL_PHENIX_CERES = 'https://cci.lbl.gov/ceres'
URL_PHENIX_CERES_QUERY = ''
URL_LIGAND_IMAGE_EBI = "https://www.ebi.ac.uk/pdbe/static/files/pdbechem_v2/"
URL_LIGAND_EBI = "https://www.ebi.ac.uk/pdbe-srv/pdbechem/chemicalCompound/show/"

# IDR_BASEDIR = "IDR/"
# IDR_DIR = os.path.join(LOCAL_DATA_DIR, IDR_BASEDIR)
URL_SCREEN_TABLE = 'https://idr.openmicroscopy.org/webgateway/table/Screen/{screenId}/query/?query=*'
URL_IDR_INDEX_PAGE = "https://idr.openmicroscopy.org/webclient/?experimenter=-1"
URL_SCREENS_PROJECTS = "https://idr.openmicroscopy.org/mapr/api/{key}/?value={value}"
URL_SHOW_KEY = 'https://idr.openmicroscopy.org/webclient/?show={key}-{keyId}'
URL_ATTR_KEY = 'https://idr.openmicroscopy.org/api/v0/m/{key}s/{keyId}/'
URL_THUMBNAIL = 'https://idr.openmicroscopy.org/webclient/render_thumbnail/{imageId}'
