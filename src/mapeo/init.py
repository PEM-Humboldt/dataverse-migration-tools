# Parse JSON to python dict
from pathlib import Path

import openpyxl

from src.mapeo.reconstruct_mapping import load_dv_schemas, unflatten_dataset
from src.mapeo.biocultural_mapping_example import migrate_access, migrate_altered, migrate_bounding_boxes, migrate_contractors, migrate_data_collection_situation, migrate_data_collectors, migrate_date, migrate_external_references, migrate_geographic_coverage, migrate_geographic_unit, migrate_grant_numbers, migrate_institute_parties, migrate_institutional_projects, migrate_keywords, migrate_language, migrate_operations, migrate_periods, migrate_release_date, migrate_vocabulary, state_table, vocabulary_table
from src.formato.utilitarios.mapping import normalize_string
from src.utilitarios.files import read_json, read_xlsx, write_json
from src.config import Config
from src.utilitarios.logger import logger

config = Config()

def clean_value(valor):
    # A single compound field (multiple = false) is a dict of subfield objects: keeps the values only
    if isinstance(valor, dict):
        return {sub_key: sub_dict["value"] for sub_key, sub_dict in valor.items()}

    # If value is NOT a list, returns value
    if not isinstance(valor, list):
        return valor  # Lo devuelve tal cual, no hay nada que limpiar

    # If value IS a list, then it loops over it and checks wether if is a list of values or list of dicts
    clean_list = []
    
    for elemento in valor:
        # If is a list of values
        if not isinstance(elemento, dict):
            clean_list.append(elemento)
            
        # If is a list of dictionaries
        else:
            clean_dict = {}
            for sub_key, sub_dict in elemento.items():
                # Returns the value only
                clean_dict[sub_key] = sub_dict["value"]
            
            clean_list.append(clean_dict)

    return clean_list

def flatten_dataset(data: dict) -> dict:
    """Turns field list into a clean dict with just key-value(typeName)."""
    flat_map = {}
    
    for block_name, block_content in data.items():
        flat_map[block_name] = {
            field["typeName"]: clean_value(field["value"])
            for field in block_content.get("fields", [])
        }
    return flat_map

def citation_block_mapping(final_dict, flat_data):
    # Citation block

    citation_block = flat_data.get('citation') or {}

    direct_copy_fields = ['subtitle', 'alternativeTitle', 'subject', 'distributionDate', 'depositor', 'dateOfDeposit', 'kindOfData']
    for field in direct_copy_fields:
        if citation_block.get(field):
            final_dict['citation'][field] = citation_block.get(field)

    institute_parties_fields = ['producer', 'distributor']
    for field in institute_parties_fields:
        if citation_block.get(field):
            final_dict['citation'][field] = migrate_institute_parties(citation_block.get(field), field)

    transform_fields = {
        'title': normalize_string,
        'keyword': migrate_keywords,
        'language': migrate_language,
        'productionDate': migrate_date,
        'grantNumber': migrate_grant_numbers
    }

    for field, func in transform_fields.items():
        if citation_block.get(field):
            final_dict['citation'][field] = func(citation_block.get(field))

    # Compound fields
    final_dict['citation']['author'] = []
    author_block = citation_block.get('author') or []
    for author in author_block:
        final_dict['citation']['author'].append({
            'authorName' : author.get('authorName'),
            'authorAffiliation': author.get('authorAffiliation'),
            'authorIdentifierScheme': author.get('authorIdentifierScheme'),
            'authorIdentifier': author.get('authorIdentifier')
            }
        )


    final_dict['citation']['datasetContact'] = []
    contact_block = citation_block.get('datasetContact') or []
    for contact in contact_block:
        final_dict['citation']['datasetContact'].append({
            'datasetContactName': contact.get('datasetContactName'),
            'datasetContactAffiliation': contact.get('datasetContactAffiliation'),
            'datasetContactEmail': str(contact.get('datasetContactEmail')).strip().lower() if contact.get('datasetContactEmail') else None,
        })


    final_dict['citation']['dsDescription'] = []
    dsDescription_block = citation_block.get('dsDescription') or []
    for desc in dsDescription_block:
        final_dict['citation']['dsDescription'].append({
            'dsDescriptionValue': desc.get('dsDescriptionValue'),
            'dsDescriptionDate': migrate_date(desc.get('dsDescriptionDate'))
        })

    final_dict['citation']['contributor'] = []
    contributor_block = citation_block.get('contributor') or []
    for contributor in contributor_block:
        final_dict['citation']['contributor'].append({
            'contributorType': contributor.get('contributorType'),
            'contributorName': contributor.get('contributorName')
        })

def geospatial_block_mapping(final_dict, flat_data, states):
    geospatial_block = flat_data.get('geospatial') or {}

    if geospatial_block.get('geographicCoverageDescription'):
        final_dict['geospatial']['geographicCoverageDescription'] = geospatial_block.get('geographicCoverageDescription')

    final_dict['geospatial']['geographicCoverage'] = migrate_geographic_coverage(geospatial_block.get('geographicCoverage'), states)

    geographicUnit_value = migrate_geographic_unit(geospatial_block.get('geographicUnit'))
    if geographicUnit_value is not None:
        final_dict['geospatial']['geographicUnit'] = geographicUnit_value

    final_dict['geospatial']['geographicBoundingBox'] = migrate_bounding_boxes(geospatial_block.get('geographicBoundingBox'))

def socialscience_block_mapping(final_dict, flat_data, vocabulary):
    socialscience_block = flat_data.get('socialscience') or {}
    citation_block = flat_data.get('citation') or {}

    sc_direct_copy_fields = ['unitOfAnalysis', 'universe', 'timeMethod', 'collectorTraining', 'samplingProcedure', 'targetSampleSize', 'actionsToMinimizeLoss', 'weighting', 'responseRate', 'samplingErrorEstimates', 'otherDataAppraisal']
    for field in sc_direct_copy_fields:
        value = socialscience_block.get(field)
        if value:
            final_dict['socialscience'][field] = value
    
    sc_from_citation_fields = ['timePeriodCovered', 'dateOfCollection']
    for field in sc_from_citation_fields:
        value = migrate_periods(citation_block.get(field), field, f"soc_{field}")
        if value:
            final_dict['socialscience'][f"soc_{field}"] = value

    dataCollector_value = migrate_data_collectors(socialscience_block.get('dataCollector'))
    if dataCollector_value:
        final_dict['socialscience']['dataCollector'] = dataCollector_value

    vocab_fields = ['collectionMode', 'researchInstrument']
    for field in vocab_fields:
        table = vocabulary_table(vocabulary, f"socialscience/{field}")
        value = migrate_vocabulary(socialscience_block.get(field), table)
        if value:
            final_dict['socialscience'][field] = value

    situation_value = migrate_data_collection_situation(socialscience_block.get('dataCollectionSituation'), socialscience_block.get('collectionMode'))
    if situation_value:
        final_dict["socialscience"]["dataCollectionSituation"] = situation_value

    operations_fields = ['controlOperations', 'cleaningOperations']
    for field in operations_fields:
        value = migrate_operations(socialscience_block.get(field))
        if value:
            final_dict['socialscience'][field] = value

def institutional_block_mapping(final_dict, flat_data, raw_data, socioecologic_data):
    availabilityStatus = raw_data['datasetVersion'].get('availabilityStatus')
    termsOfUse = raw_data['datasetVersion'].get('termsOfUse')
    persistentId = raw_data['datasetVersion'].get('datasetPersistentId')
    files_dict = raw_data['datasetVersion'].get('files')
    inventory_data = raw_data.get('inventory_data') or {}

    row = next(
        (row for row in socioecologic_data if row.get("persistent_id") == persistentId),
        None
    )

    grant_number_value = final_dict['citation'].get('grantNumber')

    inv = inventory_data.get("inventory", {})
    i2d_row = inv.get("sociocultural")
    detalle_macro = inv.get("proyecto_macro_detalle")

    macro_projects = {}
    if i2d_row and i2d_row.get("proyecto_macro") and detalle_macro:
        macro_projects[i2d_row["proyecto_macro"]] = detalle_macro

    project_value = migrate_institutional_projects(grant_number_value, row, macro_projects)
    if project_value:
        final_dict['institutional']['project'] = project_value

    contractor_value = migrate_contractors(flat_data, i2d_row)
    if contractor_value:
        final_dict['institutional']['contractor'] = contractor_value

    final_dict['institutional']['access'] = {}
    accessType_value, _ = migrate_access(termsOfUse)
    if accessType_value:
        final_dict['institutional']['access']['accessType'] = accessType_value

    altered_value = migrate_altered(files_dict)
    if altered_value:
        final_dict['institutional']['access']['altered'] = altered_value

    restricted_value = migrate_release_date(availabilityStatus)
    if restricted_value:
        final_dict['institutional']['access']['restrictedUntil'] = restricted_value

def external_ref_block_mapping(final_dict, flat_data, raw_data):
    persistentId = raw_data['datasetVersion']['datasetPersistentId']
    citation_block = flat_data.get('citation') or {}

    if "localhost" in str(config.dv_origin_url):
        temp_url = "http://example.com"
    else:
        temp_url = config.dv_origin_url
    value = migrate_external_references(persistentId, citation_block.get('publication') or [], temp_url)
    if value:
        final_dict['externalReferences']['externalReference'] = value   

def mapping_main(raw_data, catalogs):
    # Start looping over each metadatablock
    final_dict = {
        'citation': {},
        'geographic': {},
        'geospatial': {},
        'institutional': {},
        'socialscience': {},
        'externalReferences': {}
    }

    vocabulary = catalogs['vocabulary']
    states = catalogs['states']
    socioecologic_data = catalogs['socioecologic_data']

    metadata_dict = raw_data['datasetVersion']['metadataBlocks']
    flat_data = flatten_dataset(metadata_dict)

    # Citation block
    citation_block_mapping(final_dict, flat_data)

    # Geographic block
    geospatial_block_mapping(final_dict, flat_data, states)

    # Social science block
    socialscience_block_mapping(final_dict, flat_data, vocabulary)

    # Institutional block
    institutional_block_mapping(final_dict, flat_data, raw_data, socioecologic_data)

    # External references block
    external_ref_block_mapping(final_dict, flat_data, raw_data)

    return final_dict

def main():
    files = Path(config.dv_data_dir) / config.metadata_dir

    wb = openpyxl.load_workbook(config.vocabularies, data_only=True)
    vocabulary = read_xlsx(wb, "vocabularies")
    states = state_table(vocabulary)

    socioecologic_data = read_xlsx(wb, "socioecologico")

    catalogs = {
        "vocabulary": vocabulary,
        "states": states,
        "socioecologic_data": socioecologic_data,
    }

    schema = load_dv_schemas()
    count = 0
    for file in list(files.iterdir()):
        raw_data = read_json(file)
        mapped_dict = mapping_main(raw_data, catalogs)
        dv_blocks = unflatten_dataset(mapped_dict, schema)

        raw_data['datasetVersion']['metadataBlocks'] = dv_blocks

        identifier = file.name.split("-")[0]
        dir_path = Path(config.dv_data_dir) / 'final_mapped' / identifier
        dir_path.mkdir(parents=True, exist_ok=True)
        write_json(raw_data, dir_path , file.name)
        count += 1 

    logger.info(f"Finished {count}")
if __name__ == "__main__":
    main()