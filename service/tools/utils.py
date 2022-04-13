import json
import os
import requests
from bs4 import BeautifulSoup


def download_file(url, path):
    """
    Download the file from `url` and save it locally under `filename`:
    """
    local_filename = url.split('/')[-1]
    full_path = os.path.join(path, local_filename)
    print("- download file:", url, full_path)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        os.makedirs(path, exist_ok=True)
        with open(full_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return full_path


def save_json(data,  path, filename, createIfNotExist=True):
    """
    Save the data as json file
    """
    print("- save json:", path, filename)
    # print(json.dumps(data, indent=2))
    if path and createIfNotExist:
        os.makedirs(path, exist_ok=True)
    full_path = os.path.join(path, filename)
    with open(full_path, 'w') as f:
        json.dump(data, f)
    return f.name


def getGitHubFileList(url, ext=''):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    files = [node.get('href').split('/')[-1]
             for node in soup.find_all('a') if node.get('href').endswith(ext)]
    return files
