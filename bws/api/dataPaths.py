import os

from django.conf import settings

LOCAL_DATA_DIR = os.path.join(settings.BASE_DIR, 'data')
LOCAL_DATA_DIR = 'data'
EMDB_BASEDIR='emdbs'
EMDB_DATA_DIR=  os.path.join(LOCAL_DATA_DIR, EMDB_BASEDIR)

THORN_BASEDIR="coronavirus_structural_task_force/"
THORN_DATA_DIR=  os.path.join(LOCAL_DATA_DIR, THORN_BASEDIR)

MODIFIED_PDBS_ANN_BASEDIR="pdbRemodelAnn/"
MODIFIED_PDBS_ANN_DIR=  os.path.join(LOCAL_DATA_DIR, MODIFIED_PDBS_ANN_BASEDIR)

COMPUT_MODELS_BASEDIR="computModels/"
COMPUT_MODELS_DIR=  os.path.join(LOCAL_DATA_DIR, COMPUT_MODELS_BASEDIR)

MODEL_AND_LIGAND_BASEDIR="ligandModels/"
MODEL_AND_LIGAND_DIR=  os.path.join(LOCAL_DATA_DIR, MODEL_AND_LIGAND_BASEDIR)

EMV_WS_URL="http://finlay.cnb.csic.es:8010"
EMV_WS_PATH="emv"