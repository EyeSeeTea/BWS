from datetime import datetime, timedelta
import logging
import os
import time
from urllib.parse import urljoin
import requests
from django.core.management.base import BaseCommand
from api.models import (
    EmdbEntry,
    HybridModel,
    PdbEntry,
    RefinedModel,
    RefinedModelMethod,
    RefinedModelSource,
)

# from api.dataPaths import URL_CERES
from api.utils import save_json, updateRefinedModel
from api.dataPaths import URL_PHENIX_STATUS

# PHENIX

HTTP_TIMEOUT = 15

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)


def log_info(message):
    logger.info(message)
    print(message)


class Command(BaseCommand):
    """
    Update CERES entries (RefinedModels)
    """

    requires_migrations_checks = True

    def handle(self, *args, **options):
        log_info("** Updating CERES entries **")
        mapping_entries = HybridModel.objects.filter(
            emdbId_id__isnull=False
        ).values_list("emdbId_id", "pdbId_id")
        mapping_entries_list = list(mapping_entries)
        log_info("Fetching CERES entries")
        success, not_found = get_refined_model_ceres(mapping_entries_list)
        log_info("Success: " + str(len(success)))
        log_info("Not found: " + str(len(not_found)))
        save_entries(success, not_found)
        update_ceres_entries(success, not_found)
        log_info("** Finished updating CERES entries **")


def fetch_and_execute(url, func):
    try:
        response = requests.get(url, timeout=HTTP_TIMEOUT)
        if func(response):
            return url
        else:
            return False
    except Exception as e:
        log_info(f"Error while fetching URL {url}: {repr(e)}")
        return False


def ceres_exists(res):
    if res.status_code != 200:
        log_info(f"Error fetching CERES model: {res.status_code}")
        return False
    return "Does not exist" not in res.text


def ceres_model_exists(res):
    return res.status_code == 200


def get_first_url_matching_criteria(urls, func):
    for url in urls:
        result = fetch_and_execute(url, func)
        if result:
            return url
    return False


def fetch_ceres(pdbId, emdbId):
    entry_date = datetime.today().strftime("%m_%Y")  # 0 padded, i.e.: 04_2022
    previous_month = (datetime.today().replace(day=1) - timedelta(days=1)).strftime(
        "%m_%Y"
    )
    entry_date_2 = previous_month
    urls = [
        urljoin(URL_PHENIX_STATUS, f"goto_entry/{pdbId}_{emdbId}/{entry_date}/"),
        urljoin(URL_PHENIX_STATUS, f"goto_entry/{pdbId}_{emdbId}/{entry_date_2}/"),
    ]

    return get_first_url_matching_criteria(urls, ceres_exists)


def map_possible_filename_urls(pdbId, emdbId, url):
    possible_filenames = [
        "real_space_refined_000.pdb",
        "neut_real_space_refined_000.pdb",
        "trim_real_space_refined_000.pdb",
        "neut_trim_real_space_refined_000.pdb",
    ]
    # https://cci.lbl.gov/static/data/9m0s_63562/04_2025/9m0s_63562_real_space_refined_000.pdb
    base_url = url.replace(
        "https://cci.lbl.gov/ceres/goto_entry/", "https://cci.lbl.gov/static/data/"
    )
    mapped_filenames = [
        f"{base_url}{pdbId}_{emdbId}_{filename}" for filename in possible_filenames
    ]
    return mapped_filenames


def get_ceres_filename(pdbId, emdbId, url):
    mapped_filename_urls = map_possible_filename_urls(pdbId, emdbId, url)
    return get_first_url_matching_criteria(mapped_filename_urls, ceres_model_exists)


def get_refined_model_ceres(mapping_entries_list):
    success = []
    not_found = []
    start_time = time.time()

    for index, (emdb_id, pdb_id) in enumerate(mapping_entries_list):
        pdbId = pdb_id.lower()
        emdbId = emdb_id.replace("EMD-", "")
        url = fetch_ceres(pdbId, emdbId)
        if url:
            filename_url = get_ceres_filename(pdbId, emdbId, url)
            if filename_url:
                log_info(f"Found CERES model file: {filename_url}")
            success.append(
                {
                    "pdbId": pdb_id,  # lowercase
                    "emdbId": emdb_id,  # lowercase
                    "url": url,
                    "filename_url": filename_url,
                }
            )
        else:
            not_found.append(
                (
                    pdb_id,  # lowercase
                    emdb_id,  # lowercase
                )
            )
        if time.time() - start_time >= 30:
            progress = (index + 1) / len(mapping_entries_list) * 100
            log_info(
                f"Progress: {progress:.2f}% - Success: {len(success)} - Not found: {len(not_found)}"
            )
            start_time = time.time()
        time.sleep(1)  # Avoiding DDoS

    return success, not_found


def save_entries(success, not_found):
    json = {"success": success, "not_found": not_found}
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"ceres_{timestamp}.json"
    save_json(json, "/data/ceres_entries", filename)
    log_info(f"Saved to {filename}")


def get_refined_models():
    refModelSource = RefinedModelSource.objects.get(name="CERES")
    refModelMethod = RefinedModelMethod.objects.get(
        source=refModelSource, name="PHENIX"
    )
    ceres_refined_models = RefinedModel.objects.filter(
        method=refModelMethod, source=refModelSource
    )

    return ceres_refined_models


def update_ceres_entries(success, not_found):
    updated = []
    refined_models = get_refined_models()
    refined_model_pdb_ids = refined_models.values_list("pdbId_id", flat=True)
    refModelSource = RefinedModelSource.objects.get(name="CERES")
    refModelMethod = RefinedModelMethod.objects.get(
        source=refModelSource, name="PHENIX"
    )

    # Add new refined models (not present yet)
    for item in success:
        pdb_id = item["pdbId"]
        emdb_id = item["emdbId"]
        url = item["url"]
        filename_url = item["filename_url"]
        refined_model = refined_models.get(pdbId_id=pdb_id, emdbId_id=emdb_id)
        needs_update = False
        external_link = url
        query_link = ""
        if refined_model is not None:
            needs_update = (
                refined_model.filename != filename_url
                or refined_model.external_link != url
            )
        if needs_update:
            updated.append(
                {
                    "pdbId": pdb_id,
                    "emdbId": emdb_id,
                    "url": url,
                    "filename_url": filename_url,
                }
            )
        if pdb_id not in refined_model_pdb_ids or needs_update:
            pdbObj = PdbEntry.objects.get(dbId=pdb_id)
            emdbObj = EmdbEntry.objects.get(dbId=emdb_id)
            updateRefinedModel(
                emdbObj,
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
        [
            item["pdbId"]
            for item in success
            if item["pdbId"] not in refined_model_pdb_ids
        ]
    )
    log_info(f"Added refined models: {added_count}")

    # Log deleted refined models
    deleted_count = len(
        [pdb_id for pdb_id, _ in not_found if pdb_id in refined_model_pdb_ids]
    )
    log_info(f"Deleted refined models: {deleted_count}")

    # Log updated refined models
    updated_count = len(updated)
    log_info(f"Updated refined models: {updated_count}")
