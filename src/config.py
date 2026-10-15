from pyDataverse.api import NativeApi, DataAccessApi
import json
from pathlib import Path

class Config:

    def __init__(self):
        config_file_path = Path(__file__).resolve().parent / 'config.json'

        with open(config_file_path) as f:
            conf = json.load(f)
        self.dv_origin_url = conf['biocultural']['origin_url']
        self.dv_origin_api_token = conf['biocultural']['origin_api_token']
        self.dataverse_names = conf['biocultural']['dataverse_names']
        self.doi_prefix = conf['biocultural']['doi_prefix']
        self.dv_metadata_directory = conf['biocultural']['metadata_directory']
        self.dv_files_directory = conf['biocultural']['files_directory']

        self.api_origin = NativeApi(self.dv_origin_url, self.dv_origin_api_token)
