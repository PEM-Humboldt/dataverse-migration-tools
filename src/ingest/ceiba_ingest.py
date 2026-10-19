from src.config import Config
from pathlib import Path
import xml.etree.ElementTree as ET
import json
import xmltodict
from src.utilitarios.storage import save_file, save_json_metadata
import os

config = Config()

def read_resources():
    return [name for name in os.listdir(config.ceiba_origin_path) if os.path.isdir(os.path.join(config.ceiba_origin_path, name))]

def get_latest_version(r_dir):
    # Comparar todas las versiones y saca solo la última
    mayor_version = 0
    mayor_mversion = 0
    vm = 0
    for file in os.listdir(r_dir):
        filename = os.fsdecode(file)
        if filename.endswith(".xml") and filename.startswith("eml"):
            filename = os.path.splitext(filename)[0]
            try:
                version = filename.split("-")[1]
                v = version.split(".")[0]
                if int(v) >= mayor_version:
                    mayor_version = int(v)
            except:
                pass
        

    for file in os.listdir(r_dir):
        filename = os.fsdecode(file)
        if filename.startswith(f"eml-{mayor_version}"):
            try:
                filename = os.path.splitext(filename)[0]
                vm = filename.split(".")[1]
                if int(vm) >= mayor_mversion:
                    mayor_mversion = int(vm)
            except:
                pass

    print("MAYOR VERIOSN IS", mayor_version, " AND MINOR VERSION IS ", mayor_mversion)
    if mayor_version != 0 and mayor_mversion != 0:
        latest_version = str(mayor_version) + "." + str(mayor_mversion)
    elif mayor_version != 0 and mayor_mversion == 0:
        latest_version = str(mayor_version) + "." + str(mayor_mversion)
    elif mayor_version == 0:
        latest_version = mayor_version

    return latest_version

def read_xml(resource):
    r_dir = config.ceiba_origin_path + '/' + resource
    print("Im r_dis is ", r_dir)

    latest = get_latest_version(r_dir)
    print("The latest version for this resource is: ", latest)
    if latest != 0:
        resource_name = "eml-" + latest
    else:
        resource_name = "eml"

    files = ["resource", resource_name]
    for f in files:
        filepath = r_dir + '/' + f + ".xml"
        print("Final filepath is ", filepath)
        with open(filepath, 'r', encoding="UTF-8") as xml_file:
            data_dict = xmltodict.parse(xml_file.read())

        write_dir = config.ceiba_metadata_directory + '/' + resource
        save_json_metadata(data_dict, write_dir, f, "")

def main():
    resources = read_resources()
    #resource = 'colombia_magnoliophyta_2014'
    #read_xml(resource)
    for r in resources:
        read_xml(r)

if __name__ == '__main__':
    main()