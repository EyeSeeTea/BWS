#! /usr/bin/env python3

import json
import requests
import unittest

def _load_config(file):
    data = json.load(file)
    return data

def _format_url(server, port, data):
    endpoint = data["endpoint"].format(**data)
    url = "http://{ip}:{port}{endpoint}".format(ip=server, port=port, endpoint=endpoint)
    return url 

def _get_needed_data_from_config(config, id):
    server = config["bws-server-ip"]
    port = config["bws-server-port"]
    endpoint = config[id]["endpoint"]
    result = config[id]["result"]
    status_code = config[id]["status_code"]
    element_id = config[id]["name"]
    url = _format_url(server, port, config[id])
    return url, element_id, result, status_code

def _general_test_case(config, id):
    url, id, result, status_code = _get_needed_data_from_config(config,id)
    response = requests.get(url)
    print(response.status_code, status_code)
    assert int(response.status_code) == int(status_code)
    response_text = response.text
    #if (response.status_code == 200):
    #    assert json.loads(response_text) == json.loads(result)
    return response_text, result, id

class TestAnnotationAPI(unittest.TestCase):

    config = _load_config(open("config.json"))

    def test_non_existent_PDB_redo(self):
        # 1. Test non existent element in PDB redo DB
        _general_test_case(self.config, "bws-PDB-redo-API-invalid")

    def test_existent_PDB_redo(self):
        # 2. Test existent element in PDB redo DB
        _general_test_case(self.config, "bws-PDB-redo-API-valid")

    def test_empty_PDB_redo(self):
        # 3. Empty string given: due to django internals, this 
        # redirects to the previous element Eg: to /api/annotation/PDB_REDO/
        _general_test_case(self.config, "bws-PDB-redo-API-empty")

    def test_non_existent_EBI(self):
        # 4.
        _general_test_case(self.config, "bws-EBI-invalid")

    def test_existent_EBI(self):
        # 5.
        _general_test_case(self.config, "bws-EBI-valid")

    def test_empty_EBI(self):
        # 6.
        _general_test_case(self.config, "bws-EBI-empty")

    def test_non_existent_IEDB(self):
        # 7. 
        _general_test_case(self.config, "bws-IEDB-invalid")

    def test_existent_IEDB(self):
        # 8.
        _general_test_case(self.config, "bws-IEDB-valid")

    def test_empty_IEDB(self):
        # 9.
        _general_test_case(self.config, "bws-IEDB-empty")

    def test_non_existent_Phosphosite(self):
        # 10.
        _general_test_case(self.config, "bws-phosphosite-invalid")

    def test_existent_phosposite(self):
        # 11.
        _general_test_case(self.config, "bws-phosphosite-valid")

    def test_empty_phosposite(self):
        # 12.
        _general_test_case(self.config, "bws-phosphosite-empty")

    def test_non_existent_DBPTM(self):
        # 13.
        _general_test_case(self.config, "bws-DBPTM-valid")

    def test_existent_DBPTM(self):
        # 14.
        _general_test_case(self.config, "bws-DBPTM-invalid")

    def test_empty_DBPTM(self):
        # 15
        _general_test_case(self.config, "bws-DBPTM-empty")

    def test_non_existent_BIOMUTA(self):
        # 16
        _general_test_case(self.config, "bws-BIOMUTA-invalid")

    def test_existent_BIOMUTA(self):
        # 17
        _general_test_case(self.config, "bws-BIOMUTA-valid")

    def test_empty_BIOMUTA(self):
        # 18
        _general_test_case(self.config, "bws-BIOMUTA-empty")

    def test_non_existent_EBI(self):
        # 19
        _general_test_case(self.config, "bws-DSYSMAP-invalid")

    def test_existent_DSYSMAP(self):
        # 20.
        _general_test_case(self.config, "bws-DSYSMAP-valid")

    def test_empty_DSYSMAP(self):
        # 21
        _general_test_case(self.config, "bws-DSYSMAP-empty")

    def test_non_existent_ELMDB(self):
        # 22
        _general_test_case(self.config, "bws-ELMDB-invalid")

    def test_existent_ELMDB(self):
        # 23
        _general_test_case(self.config, "bws-ELMDB-valid")

    def test_empty_ELMDB(self):
        # 24
        _general_test_case(self.config, "bws-ELMDB-empty")

    def test_non_existent_PFAM(self):
        # 25.
        _general_test_case(self.config, "bws-PFAM-invalid")

    def test_existent_PFAM(self):
        # 26
        _general_test_case(self.config, "bws-PFAM-valid")

    def test_empty_PFAM(self):
        # 27
        _general_test_case(self.config, "bws-PFAM-empty")

    def test_non_existent_SMART(self):
        # 28
        _general_test_case(self.config, "bws-SMART-invalid")

    def test_existent_SMART(self):
        # 29
        _general_test_case(self.config, "bws-SMART-valid")

    def test_empty_SMART(self):
        # 30.
        _general_test_case(self.config, "bws-SMART-empty")

    def test_non_existent_MOBI(self):
        # 31
        _general_test_case(self.config, "bws-MOBI-invalid")

    def test_existent_MOBI(self):
        # 32
        _general_test_case(self.config, "bws-MOBI-valid")

    def test_empty_MOBI(self):
        # 33
        _general_test_case(self.config, "bws-MOBI-empty")

    def test_non_existent_INTERPRO(self):
        # 34
        _general_test_case(self.config, "bws-INTERPRO-invalid")

    def test_existent_INTERPRO(self):
        # 35.
        _general_test_case(self.config, "bws-INTERPRO-valid")

    def test_empty_INTERPRO(self):
        # 36
        _general_test_case(self.config, "bws-INTERPRO-empty")

    def test_non_existent_ENSEMBL_VARIATION(self):
        # 37
        _general_test_case(self.config, "bws-ENSEMBLE-VARIATION-invalid")

    def test_existent_ENSEMBL_VARIATION(self):
        # 38
        _general_test_case(self.config, "bws-ENSEMBLE-VARIATION-valid")

    def test_empty_ENSEMBL_VARIATION(self):
        # 39
        _general_test_case(self.config, "bws-ENSEMBL-VARIATION-empty")

    def test_non_existent_ENSEMBL_ANNOTATION(self):
        # 40.
        _general_test_case(self.config, "bws-ENSEMBL-ANNOTATION-invalid")

    def test_existent_ENSEMBL_ANNOTATION(self):
        # 41
        _general_test_case(self.config, "bws-ENSEMBL-ANNOTATION-valid")

    def test_empty_ENSEMBL_ANNOTATION(self):
        # 42
        _general_test_case(self.config, "bws-ENSEMBL-ANNOTATION-empty")

    def test_non_existent_LENGTH(self):
        # 43
        _general_test_case(self.config, "bws-LENGTHS-invalid")

    def test_existent_LENGTH(self):
        # 44
        _general_test_case(self.config, "bws-LENGTHS-valid")

    def test_empty_LENGTH(self):
        # 45.
        _general_test_case(self.config, "bws-LENGTHS-empty")

    def test_non_existent_MULTI(self):
        # 46
        _general_test_case(self.config, "bws-LENGTHS-MULTI-invalid")

    def test_existent_MULTI(self):
        # 47
        _general_test_case(self.config, "bws-LENGTHS-MULTI-invalid")

    def test_empty_MULTI(self):
        # 48
        _general_test_case(self.config, "bws-LENGTHS-MULTI-invalid")

if __name__ == '__main__':
    unittest.main()

