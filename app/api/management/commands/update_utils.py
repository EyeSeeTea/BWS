import logging
import time

HTTP_TIMEOUT = 15

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)


def log_info(message):
    logger.info(message)
    print(message)


def save_entries(success, not_found, prefix, save_json_func, save_dir):
    json = {"success": success, "not_found": not_found}
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{prefix}_{timestamp}.json"
    save_json_func(json, save_dir, filename)
    log_info(f"Saved to {filename}")


def log_progress(index, total, success, not_found, start_time, interval=30):
    if time.time() - start_time >= interval:
        progress = (index + 1) / total * 100
        log_info(
            f"Progress: {progress:.2f}% - Success: {len(success)} - Not found: {len(not_found)}"
        )
        return time.time()
    return start_time
