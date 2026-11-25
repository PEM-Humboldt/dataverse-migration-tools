from dotenv import load_dotenv
from pyDataverse.api import NativeApi
import os

load_dotenv()

class Config:

    def __init__(self):
        self.metadata_dir = os.getenv('METADATA_DIR')
        self.files_dir = os.getenv('FILES_DIR')
        self.i2d_inventory = os.getenv('INVENTORY_PATH')
        self.vocabularies = os.getenv('VOCABULARIES_PATH')
        self.tsv_files = os.getenv('TSV_FILES_PATH')
        self.prefix_DOI = os.getenv('PREFIX_DOI')

        self.dv_target_url = os.getenv('DV_TARGET_URL')
        self.dv_target_api_token = os.getenv('DV_TARGET_API_TOKEN')
        self.dv_socioecologico_alias = os.getenv('DV_SOCIOECOLOGICO_ALIAS')
        self.dv_biologico_alias = os.getenv('DV_BIOLOGICO_ALIAS')
        self.dv_goegrafico_alias = os.getenv('DV_GEOGRAFICO_ALIAS')

        self.dv_origin_url = os.getenv('BIOCULTURAL_ORIGIN_URL')
        self.dv_origin_api_token = os.getenv('BIOCULTURAL_ORIGIN_API_TOKEN')
        self.dv_data_dir = os.getenv('BIOCULTURAL_DATA_DIR')
        
        self.api_origin = NativeApi(self.dv_origin_url, self.dv_origin_api_token)
        self.api_target = NativeApi(self.dv_target_url, self.dv_target_api_token)

        self.dv_target_url = os.getenv('DV_TARGET_URL')
        self.dv_target_api_token = os.getenv('DV_TARGET_API_TOKEN')

        self.ceiba_origin_path = os.getenv('CEIBA_ORIGIN_PATH')
        self.ceiba_data_dir = os.getenv('CEIBA_DATA_DIR')
        
        self.gn_origin_url = os.getenv('GN_URL')
        self.gn_user = os.getenv('GN_USER')
        self.gn_password = os.getenv('GN_PASSWORD')
        self.gn_data_dir = os.getenv('GN_DATA_DIR')
