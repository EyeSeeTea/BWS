import logging
import time
from urllib.parse import urljoin
import requests
from django.core.management.base import BaseCommand
from api.models import PdbEntry, RefinedModel, RefinedModelMethod, RefinedModelSource
from api.dataPaths import URL_PDB_REDO
from api.utils import save_json, updateRefinedModel
from .update_utils import log_info, save_entries, log_progress, HTTP_TIMEOUT


class Command(BaseCommand):
    """
    Update PDB Redo entries (RefinedModels)
    """

    requires_migrations_checks = True

    def handle(self, *args, **options):
        log_info("** Updating PDB Redo entries **")
        pdb_entries = PdbEntry.objects.all().values_list("dbId", flat=True)
        pdb_entries_list = list(pdb_entries)
        log_info("Fetching PDB Redo entries")
        success, not_found = get_refined_model_pdb_redo(pdb_entries_list)
        log_info("Success: " + str(len(success)))
        log_info("Not found: " + str(len(not_found)))
        save_entries(
            success, not_found, "pdb_redo", save_json, "/data/pdb_redo_entries"
        )
        update_pdb_redo_entries(success, not_found)
        log_info("** Finished updating PDB Redo entries **")


def fetch_pdb_redo(pdb_id):
    url = urljoin(URL_PDB_REDO, f"db/{pdb_id}/pdbe.json")
    try:
        resp = requests.get(url, timeout=HTTP_TIMEOUT)
        return resp.status_code == 200
    except Exception as e:
        log_info(f"Can't find PDB-Redo model: {repr(e)}", url)


def get_refined_model_pdb_redo(list):
    success = []
    not_found = []
    start_time = time.time()

    for index, pdb_id in enumerate(list):
        if fetch_pdb_redo(pdb_id.lower()):
            success.append(pdb_id)
        else:
            not_found.append(pdb_id)
        log_progress(index, len(list), success, not_found, start_time)
        time.sleep(1)  # Avoiding DDoS

    return success, not_found


def get_refined_models():
    refModelSource = RefinedModelSource.objects.get(name="PDB-REDO")
    refModelMethod = RefinedModelMethod.objects.get(
        source=refModelSource, name="PDB-Redo"
    )
    pdb_redo_refined_models = RefinedModel.objects.filter(
        method=refModelMethod, source=refModelSource
    )

    return pdb_redo_refined_models


def update_pdb_redo_entries(success, not_found):
    updated = []
    refined_models = get_refined_models()
    refined_model_pdb_ids = refined_models.values_list("pdbId_id", flat=True)
    refModelSource = RefinedModelSource.objects.get(name="PDB-REDO")
    refModelMethod = RefinedModelMethod.objects.get(
        source=refModelSource, name="PDB-Redo"
    )

    # Add new refined models (not present yet)
    for pdb_id in success:
        pdb_id_lower = pdb_id.lower()
        filename_url = f"https://pdb-redo.eu/db/{pdb_id_lower}/{pdb_id_lower}_final.cif"
        external_link = urljoin(URL_PDB_REDO, f"db/{pdb_id}")
        query_link = ""
        refined_model = refined_models.get(pdbId_id=pdb_id)
        needs_update = False

        if refined_model is not None:
            needs_update = (
                refined_model.filename != filename_url
                or refined_model.queryLink != query_link
            )
        if needs_update:
            updated.append(
                {
                    "pdbId": pdb_id,
                    "filename_url": filename_url,
                }
            )

        if pdb_id not in refined_model_pdb_ids or needs_update:
            pdbObj = PdbEntry.objects.get(dbId=pdb_id)
            updateRefinedModel(
                None,
                pdbObj,
                refModelSource,
                refModelMethod,
                filename_url,
                external_link,
                query_link,
                "",
            )

    # Delete not found refined models (that were present)
    for pdb_id in not_found:
        if pdb_id in refined_model_pdb_ids:
            RefinedModel.objects.filter(pdbId_id=pdb_id).delete()

    # Log added refined models
    added_count = len(
        [pdb_id for pdb_id in success if pdb_id not in refined_model_pdb_ids]
    )
    log_info(f"Added refined models: {added_count}")

    # Log deleted refined models
    deleted_count = len(
        [pdb_id for pdb_id in not_found if pdb_id in refined_model_pdb_ids]
    )
    log_info(f"Deleted refined models: {deleted_count}")

    # Log updated refined models
    updated_count = len(updated)
    log_info(f"Updated refined models: {updated_count}")
