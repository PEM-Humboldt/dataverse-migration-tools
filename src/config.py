from dotenv import load_dotenv
from pyDataverse.api import NativeApi
import os

load_dotenv()

class Config:

    def __init__(self):
        self.dv_origin_url = os.getenv('BIOCULTURAL_ORIGIN_URL')
        self.dv_origin_api_token = os.getenv('BIOCULTURAL_ORIGIN_API_TOKEN')
        self.dv_metadata_directory = os.getenv('BIOCULTURAL_METADATA_DIR')
        self.dv_files_directory = os.getenv('BIOCULTURAL_FILES_DIR')

        self.api_origin = NativeApi(self.dv_origin_url, self.dv_origin_api_token)
