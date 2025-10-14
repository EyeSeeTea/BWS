import logging
import os
import time
from urllib.parse import urljoin
import requests
import sqlite3
from django.core.management.base import BaseCommand
from api.models import PdbEntry, RefinedModel, RefinedModelMethod, RefinedModelSource
from api.dataPaths import CSTF_LOCAL_PATH, URL_CSTF
from api.utils import save_json, updateRefinedModel

CSTF_DB = "https://raw.githubusercontent.com/thorn-lab/coronavirus_structural_task_force/refs/heads/master/utils/database/stats.db"
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
    Update CSTF entries (RefinedModels)
    """

    requires_migrations_checks = True

    def handle(self, *args, **options):
        log_info("** Updating CSTF entries **")
        download_database()
        refinement_items = select_refinements_from_database()
        log_info(f"Found {len(refinement_items)} refinements in CSTF database")
        log_info("Fetching CSTF entries...")
        refinement_models = retrieve_refinement_models(refinement_items)
        save_entries(refinement_models)
        update_cstf_entries(refinement_models)
        log_info("** Finished updating CERES entries **")


def retrieve_refinement_models(refinement_items):
    picked_files = []
    for item in refinement_items:
        path = item["path"].replace("\\", "/").replace("../", "")
        files = get_repository_files(item["pdbId"], path, item["github"])
        if len(files) == 0:
            log_info(f"Info: No files found for {item['pdbId']} at path {path}")
            continue
        picked = pick_one_from_refinement(files)
        time.sleep(1)  # Avoid hitting GitHub API rate limits
        if picked:
            picked_files.append(picked)
    return picked_files


def download_database():
    log_info("Downloading CSTF database...")
    response = requests.get(CSTF_DB, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    os.makedirs(os.path.join(os.path.dirname(__file__), CSTF_LOCAL_PATH), exist_ok=True)
    db_path = os.path.join(os.path.dirname(__file__), CSTF_LOCAL_PATH + "/stats.db")
    with open(db_path, "wb") as f:
        f.write(response.content)
    log_info("CSTF database downloaded successfully.")


def select_refinements_from_database():
    db_path = os.path.join(os.path.dirname(__file__), CSTF_LOCAL_PATH + "/stats.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        SELECT ID, datapath, github FROM General WHERE hasRerefinement = 1
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    return [
        {"pdbId": row[0].upper(), "path": row[1], "github": row[2]} for row in results
    ]


def get_repository_files(pdbId, path, github):
    OWNER = "thorn-lab"
    REPO = "coronavirus_structural_task_force"
    API_REQUEST = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"

    files = get_github_response(API_REQUEST)
    items = []
    for f in files:
        if f["type"] == "dir" and f["name"] in ("isolde", "refmac"):

            subdir_files = get_github_response(f["url"])
            for subfile in subdir_files:
                ext = os.path.splitext(subfile["name"])[1].lower()
                if ext in [".cif", ".mmcif", ".pdb"]:
                    items.append(
                        {
                            "pdbId": pdbId,
                            "name": subfile["name"],
                            "extension": ext,
                            "filename_url": subfile["download_url"],
                            "external_url": github,
                            "type": f["name"],  # "isolde" or "refmac"
                        }
                    )
    return items


# TODO: This will only maintain isolde or refmac files, not both. If both are present, both should prioritize and be returned.
# But overlap meanwhile is not happening at least.
def pick_one_from_refinement(files):
    """
    Select a single file from the refinement files, prioritizing by extension:
    .mmcif > .cif > .pdb. Returns the first file found for the highest priority extension.
    """
    # Maintain only one file per refinement item by extension priority: mmcif > cif > pdb
    priority = {".mmcif": 0, ".cif": 1, ".pdb": 2}
    # Sort files by priority and pick the one with the highest priority (lowest value)
    sorted_files = sorted(
        (f for f in files if f["extension"] in priority),
        key=lambda f: priority[f["extension"]],
    )
    selected = sorted_files[0] if sorted_files else None
    if selected:
        return selected


def get_github_response(url):
    """
    Fetch response from a given GitHub URL.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",  # Ensure GITHUB_TOKEN is set in your environment
        "User-Agent": "BWS-API",
    }
    return get_json_response(url, headers=headers)


# TODO: Move this function to the common utils module
def get_json_response(url, headers=None):
    """
    Fetch JSON response from a given URL, with optional headers.
    """
    try:
        response = requests.get(url, timeout=HTTP_TIMEOUT, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log_info(f"Error fetching JSON from {url}: {repr(e)}")
        log_info(f"Response content: {getattr(response, 'text', '')}")
        return None


def save_entries(entries):
    json = {"entries": entries}
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"cstf_{timestamp}.json"
    save_json(json, "/data/cstf_entries", filename)
    log_info(f"Saved to {filename}")


def get_refined_models():
    refModelSource = RefinedModelSource.objects.get(name="CSTF")
    refModelMethodIsolde = RefinedModelMethod.objects.get(
        source=refModelSource, name="Isolde"
    )
    refModelMethodRefmac = RefinedModelMethod.objects.get(
        source=refModelSource, name="Refmac"
    )

    isolde_refined_models = RefinedModel.objects.filter(
        method=refModelMethodIsolde, source=refModelSource
    )
    refmac_refined_models = RefinedModel.objects.filter(
        method=refModelMethodRefmac, source=refModelSource
    )

    return (isolde_refined_models, refmac_refined_models)


# TODO: divide and repeat separately for Isolde and Refmac
def update_cstf_entries(items):
    updated = []
    added = []
    refined_models = get_refined_models()
    isolde_refined_model = refined_models[0]
    refmac_refined_model = refined_models[1]
    isolde_refined_model_pdb_ids = refined_models[0].values_list("pdbId_id", flat=True)
    refmac_refined_model_pdb_ids = refined_models[1].values_list("pdbId_id", flat=True)

    refModelSource = RefinedModelSource.objects.get(name="CSTF")
    refModelMethodIsolde = RefinedModelMethod.objects.get(
        source=refModelSource, name="Isolde"
    )
    refModelMethodRefmac = RefinedModelMethod.objects.get(
        source=refModelSource, name="Refmac"
    )

    # Add new refined models (not present yet and ones that need update)
    for item in items:
        if item["type"] == "isolde":
            refModelMethod = refModelMethodIsolde
        elif item["type"] == "refmac":
            refModelMethod = refModelMethodRefmac
        pdb_id = item["pdbId"]
        external_url = item["external_url"]
        filename_url = item["filename_url"]

        try:
            refined_model = isolde_refined_model.get(pdbId_id=pdb_id)
        except RefinedModel.DoesNotExist:
            refined_model = None
        except Exception as e:
            log_info(f"Error fetching refined model for pdbId={pdb_id}: {repr(e)}")
            refined_model = None

        if refined_model is None:
            try:
                refined_model = refmac_refined_model.get(pdbId_id=pdb_id)
            except RefinedModel.DoesNotExist:
                refined_model = None
            except Exception as e:
                log_info(f"Error fetching refined model for pdbId={pdb_id}: {repr(e)}")
                refined_model = None

        needs_update = False
        query_link = ""
        if refined_model is not None:
            log_info(
                f"RefinedModel found for pdbId={pdb_id}: refinedmodel={refined_model}"
            )
            needs_update = (
                refined_model.filename != filename_url
                or refined_model.externalLink != external_url
            )
        if needs_update:
            updated.append(
                {
                    "pdbId": pdb_id,
                    "url": external_url if external_url else None,
                    "filename_url": filename_url if filename_url else None,
                }
            )
        if (
            pdb_id not in isolde_refined_model_pdb_ids
            and pdb_id not in refmac_refined_model_pdb_ids
        ):
            added.append(
                {
                    "pdbId": pdb_id,
                    "url": external_url if external_url else None,
                    "filename_url": filename_url if filename_url else None,
                }
            )
        if (
            pdb_id not in isolde_refined_model_pdb_ids
            and pdb_id not in refmac_refined_model_pdb_ids
        ) or needs_update:
            try:
                pdbObj = PdbEntry.objects.get(dbId=pdb_id)
            except Exception as e:
                log_info(
                    f"PDB ID {pdb_id} not found in BWS database, therefore, unable to append the refined model: {repr(e)}"
                )
                continue

            updateRefinedModel(
                None,
                pdbObj,
                refModelSource,
                refModelMethod,
                filename_url,
                external_url,
                query_link,
                "",
            )

    # TODO: not found should be the ones that are now in the database but aren't in the CSTF database
    # # Delete not found refined models (that were present)
    # for pdb_id in not_found:
    #     if pdb_id in refined_model_pdb_ids:
    #         RefinedModel.objects.filter(pdbId_id=pdb_id).delete()

    # Log deleted refined models
    # deleted_count = len(
    #     [pdb_id for pdb_id, _ in not_found if pdb_id in refined_model_pdb_ids]
    # )
    # log_info(f"Deleted refined models: {deleted_count}")

    # Log updated refined models
    updated_count = len(updated)
    log_info(f"Updated refined models: {updated_count}")

    # Log added refined models
    added_count = len(added)
    log_info(f"Added refined models: {added_count}")
