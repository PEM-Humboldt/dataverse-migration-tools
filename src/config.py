from dotenv import load_dotenv
from pyDataverse.api import NativeApi
import os

load_dotenv()

class Config:

    def __init__(self):
        self.metadata_dir = os.getenv('METADATA_DIR')
        self.files_dir = os.getenv('FILES_DIR')

        self.dv_origin_url = os.getenv('BIOCULTURAL_ORIGIN_URL')
        self.dv_origin_api_token = os.getenv('BIOCULTURAL_ORIGIN_API_TOKEN')
        self.dv_data_dir = os.getenv('BIOCULTURAL_DATA_DIR')
        
        self.api_origin = NativeApi(self.dv_origin_url, self.dv_origin_api_token)

        self.ceiba_origin_path = conf['ceiba']['origin_path']
        self.ceiba_metadata_directory = conf['ceiba']['metadata_directory']
        self.ceiba_files_directory = conf['ceiba']['files_directory']
