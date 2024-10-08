# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from common.project.project_client import ProjectClient

from app.config import ConfigClass
from app.logger import logger
from app.models.file_models import ItemStatus


def get_zone(namespace):
    return {
        ConfigClass.GREEN_ZONE_LABEL.lower(): 0,
        ConfigClass.CORE_ZONE_LABEL.lower(): 1,
    }.get(namespace.lower(), 0)


async def get_item_by_id(item_id: str) -> dict:
    """
    Summary:
         the helper function to get the item by id
    Parameter:
        - item_id(str): the unique identifier for item
    Return:
        - item detail(dict)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            ConfigClass.METADATA_SERVICE + f'/v1/item/{item_id}/',
            follow_redirects=True,
        )

    return response.json().get('result')


async def batch_query_node_by_geid(geid_list):
    logger.info('batch_query_node_by_geid'.center(80, '-'))
    params = {'ids': geid_list}
    logger.info(f'params: {params}')
    async with httpx.AsyncClient() as client:
        response = await client.get(
            ConfigClass.METADATA_SERVICE + '/v1/items/batch/',
            params=params,
            follow_redirects=True,
        )
    logger.info(response.url)
    logger.info(f'query response: {response.text}')
    res_json = response.json()
    logger.info(f'res_json: {res_json}')
    result = res_json.get('result')
    located_geid = []
    query_result = {}
    for node in result:
        geid = node.get('id', '')
        status = node.get('status')
        if geid in geid_list and status != ItemStatus.ARCHIVED:
            located_geid.append(geid)
            query_result[geid] = node
    logger.info(f'returning located_geid: {located_geid}')
    logger.info(f'returning query_result: {query_result}')
    return located_geid, query_result


async def get_dataset(dataset_code):
    """get dataset node information."""
    logger.info('get_dataset'.center(80, '-'))
    try:
        url = ConfigClass.DATASET_SERVICE + f'/v1/datasets/{dataset_code}'
        logger.info(f'Getting dataset url: {url}')
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        logger.info(f'Getting dataset response: {response.text}')
        response.raise_for_status()
        result = response.json()
        return result
    except Exception as e:
        logger.error(f'Error when get dataset {dataset_code}: {e}')
        return None


async def get_user_projects(current_identity, page=0, page_size=100, order='desc', order_by='created_at'):
    logger.info('get_user_projects'.center(80, '-'))
    projects_list = []
    project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URI)

    if current_identity['role'] != 'admin':
        roles = current_identity['realm_roles']
        project_codes = [i.split('-')[0] for i in roles]
        project_codes = ','.join(project_codes)
    else:
        project_codes = ''
    project_res = await project_client.search(
        code_any=project_codes, page=page, page_size=page_size, order_type=order, order_by=order_by
    )

    logger.info(f'project_res: {project_res}')
    projects = project_res.get('result')
    logger.info(f'projects: {projects}')
    for p in projects:
        res_projects = {'name': p.name, 'code': p.code, 'geid': p.id}
        projects_list.append(res_projects)
    logger.info(f'Number of projects found: {len(projects_list)}')
    return projects_list


async def get_attribute_templates(project_code, manifest_name=None):
    logger.info('get_attribute_templates'.center(80, '-'))
    url = ConfigClass.METADATA_SERVICE + '/v1/template/'
    params = {'project_code': project_code}
    logger.info(f'Getting: {url}')
    logger.info(f'PARAMS: {params}')
    if manifest_name:
        params['name'] = manifest_name
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, params=params)
    logger.info(f'RESPONSE: {response.text}')
    if not response.json():
        return None
    return response.json()


async def query_file_folder(params, request):
    logger.info('query_file_folder'.center(80, '-'))
    try:
        logger.info(f'query params: {params}')
        headers = {'Authorization': request.headers.get('Authorization')}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                ConfigClass.METADATA_SERVICE + '/v1/items/search/',
                params=params,
                headers=headers,
                follow_redirects=True,
            )
        logger.info(f'query response: {response.url}')
        logger.info(f'query response: {response.text}')
        return response
    except Exception as e:
        logger.error(f'Error file/folder: {e}')


async def get_dataset_versions(event):
    logger.info('get_dataset_versions'.center(80, '-'))
    logger.info(f'Query event: {event}')
    try:
        url = ConfigClass.DATASET_SERVICE + '/v1/dataset/versions'
        logger.info(f'url: {url}')
        params = {
            'dataset_id': event.get('dataset_geid'),
            'page': event.get('page'),
            'page_size': event.get('page_size'),
            'order': 'desc',
            'sorting': 'created_at',
        }
        async with httpx.AsyncClient() as client:
            res = await client.get(url, params=params)
        res_json = res.json()

        dataset_versions = []
        result = res_json.get('result')
        logger.info(f'Query result: {res.text}')
        if not result:
            return []
        for attr in result:
            result = {
                'dataset_code': attr['dataset_code'],
                'dataset_id': attr['dataset_id'],
                'version': attr['version'],
                'created_by': attr['created_by'],
                'created_at': str(attr['created_at']),
                'location': attr['location'],
                'notes': attr['notes'],
            }
            dataset_versions.append(result)
        return dataset_versions
    except Exception as e:
        logger.error(f'Error getting dataset version: {e}')


def separate_rel_path(folder_path):
    folder_layers = folder_path.strip('/').split('/')
    if len(folder_layers) > 1:
        rel_path = '/'.join(folder_layers[:-1])
        folder_name = folder_layers[-1]
    else:
        rel_path = ''
        folder_name = folder_path
    return rel_path, folder_name


class Annotations:
    @staticmethod
    async def attach_manifest_to_file(event):
        logger.info('attach_manifest_to_file'.center(80, '-'))
        url = ConfigClass.METADATA_SERVICE + '/v1/item/'
        params = {'id': event.get('global_entity_id')}
        payload = {
            'type': 'file',
            'attribute_template_id': event.get('manifest_id'),
            'attributes': event.get('attributes'),
        }
        logger.info(f'PUT: {url}')
        logger.info(f'PAYLOAD: {payload}')
        logger.info(f'PARAMS: {params}')
        async with httpx.AsyncClient() as client:
            response = await client.put(url=url, params=params, json=payload)
        logger.info(f'RESPONSE: {response.text}')
        result = response.json().get('result')
        return result

    @staticmethod
    async def attach_manifest_to_folder(event):
        logger.info('attach_manifest_to_folder'.center(80, '-'))
        url = ConfigClass.METADATA_SERVICE + '/v1/items/batch/bequeath/'
        params = {'id': event.get('global_entity_id')}
        payload = {'attribute_template_id': event.get('manifest_id'), 'attributes': event.get('attributes')}
        logger.info(f'PUT: {url}')
        logger.info(f'PAYLOAD: {payload}')
        logger.info(f'PARAMS: {params}')
        async with httpx.AsyncClient() as client:
            response = await client.put(url=url, params=params, json=payload)
        logger.info(f'RESPONSE: {response.text}')
        result = response.json().get('result')
        return result
