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

        self.gn_origin_url = os.getenv('GN_URL')
        self.gn_user = os.getenv('GN_USER')
        self.gn_password = os.getenv('GN_PASSWORD')
        self.gn_data_dir = os.getenv('GN_DATA_DIR')
