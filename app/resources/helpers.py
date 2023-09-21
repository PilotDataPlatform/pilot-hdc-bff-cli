# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from common import LoggerFactory
from common.project.project_client import ProjectClient

from app.config import ConfigClass
from app.models.file_models import ItemStatus

_logger = LoggerFactory(
    'Helpers',
    level_default=ConfigClass.LOG_LEVEL_DEFAULT,
    level_file=ConfigClass.LOG_LEVEL_FILE,
    level_stdout=ConfigClass.LOG_LEVEL_STDOUT,
    level_stderr=ConfigClass.LOG_LEVEL_STDERR,
).get_logger()


def get_zone(namespace):
    return {
        ConfigClass.GREEN_ZONE_LABEL.lower(): 0,
        ConfigClass.CORE_ZONE_LABEL.lower(): 1,
    }.get(namespace.lower(), 0)


async def get_item_by_id(item_id: str) -> dict:
    '''
    Summary:
         the helper function to get the item by id
    Parameter:
        - item_id(str): the unique identifier for item
    Return:
        - item detail(dict)
    '''
    async with httpx.AsyncClient() as client:
        response = await client.get(
            ConfigClass.METADATA_SERVICE + f'/v1/item/{item_id}/',
            follow_redirects=True,
        )

    return response.json().get('result')


async def batch_query_node_by_geid(geid_list):
    _logger.info('batch_query_node_by_geid'.center(80, '-'))
    params = {'ids': geid_list}
    _logger.info(f'params: {params}')
    async with httpx.AsyncClient() as client:
        response = await client.get(
            ConfigClass.METADATA_SERVICE + '/v1/items/batch/',
            params=params,
            follow_redirects=True,
        )
    _logger.info(response.url)
    _logger.info(f'query response: {response.text}')
    res_json = response.json()
    _logger.info(f'res_json: {res_json}')
    result = res_json.get('result')
    located_geid = []
    query_result = {}
    for node in result:
        geid = node.get('id', '')
        status = node.get('status')
        if geid in geid_list and status != ItemStatus.ARCHIVED:
            located_geid.append(geid)
            query_result[geid] = node
    _logger.info(f'returning located_geid: {located_geid}')
    _logger.info(f'returning query_result: {query_result}')
    return located_geid, query_result


async def get_dataset(dataset_code):
    """get dataset node information."""
    _logger.info('get_dataset'.center(80, '-'))
    try:
        url = ConfigClass.DATASET_SERVICE + f'/v1/datasets/{dataset_code}'
        _logger.info(f'Getting dataset url: {url}')
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        _logger.info(f'Getting dataset response: {response.text}')
        result = response.json()
        return result
    except Exception as e:
        _logger.error(f'Error when get dataset {dataset_code}: {e}')
        return None


async def list_datasets(user, page, page_size):
    """List all datasets."""
    _logger.info('list_datasets'.center(80, '-'))
    try:
        params = {
            'creator': user,
            'page': page,
            'page_size': page_size,
            'filter': {},
            'order_type': 'desc',
            'order_by': 'created_at',
        }
        _logger.info(f'Listing dataset payload: {params}')
        async with httpx.AsyncClient() as client:
            response = await client.get(ConfigClass.DATASET_SERVICE + '/v1/datasets/', params=params)
        result = response.json().get('result')
        _logger.info(f'Listing dataset result: {result}')
        return result
    except Exception:
        return None


async def get_user_projects(current_identity, page=0, page_size=100, order='desc', order_by='created_at'):
    _logger.info('get_user_projects'.center(80, '-'))
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

    _logger.info(f'project_res: {project_res}')
    projects = project_res.get('result')
    _logger.info(f'projects: {projects}')
    for p in projects:
        res_projects = {'name': p.name, 'code': p.code, 'geid': p.id}
        projects_list.append(res_projects)
    _logger.info(f'Number of projects found: {len(projects_list)}')
    return projects_list


async def get_attribute_templates(project_code, manifest_name=None):
    _logger.info('get_attribute_templates'.center(80, '-'))
    url = ConfigClass.METADATA_SERVICE + '/v1/template/'
    params = {'project_code': project_code}
    _logger.info(f'Getting: {url}')
    _logger.info(f'PARAMS: {params}')
    if manifest_name:
        params['name'] = manifest_name
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, params=params)
    _logger.info(f'RESPONSE: {response.text}')
    if not response.json():
        return None
    return response.json()


async def query_file_folder(params, request):
    _logger.info('query_file_folder'.center(80, '-'))
    try:
        _logger.info(f'query params: {params}')
        headers = {'Authorization': request.headers.get('Authorization')}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                ConfigClass.METADATA_SERVICE + '/v1/items/search/',
                params=params,
                headers=headers,
                follow_redirects=True,
            )
        _logger.info(f'query response: {response.url}')
        _logger.info(f'query response: {response.text}')
        return response
    except Exception as e:
        _logger.error(f'Error file/folder: {e}')


async def get_dataset_versions(event):
    _logger.info('get_dataset_versions'.center(80, '-'))
    _logger.info(f'Query event: {event}')
    try:
        url = ConfigClass.DATASET_SERVICE + '/v1/dataset/versions'
        _logger.info(f'url: {url}')
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
        _logger.info(f'Query result: {res.text}')
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
        _logger.error(f'Error getting dataset version: {e}')


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
        _logger.info('attach_manifest_to_file'.center(80, '-'))
        url = ConfigClass.METADATA_SERVICE + '/v1/item/'
        params = {'id': event.get('global_entity_id')}
        payload = {
            'type': 'file',
            'attribute_template_id': event.get('manifest_id'),
            'attributes': event.get('attributes'),
        }
        _logger.info(f'PUT: {url}')
        _logger.info(f'PAYLOAD: {payload}')
        _logger.info(f'PARAMS: {params}')
        async with httpx.AsyncClient() as client:
            response = await client.put(url=url, params=params, json=payload)
        _logger.info(f'RESPONSE: {response.text}')
        result = response.json().get('result')
        return result

    @staticmethod
    async def attach_manifest_to_folder(event):
        _logger.info('attach_manifest_to_folder'.center(80, '-'))
        url = ConfigClass.METADATA_SERVICE + '/v1/items/batch/bequeath/'
        params = {'id': event.get('global_entity_id')}
        payload = {'attribute_template_id': event.get('manifest_id'), 'attributes': event.get('attributes')}
        _logger.info(f'PUT: {url}')
        _logger.info(f'PAYLOAD: {payload}')
        _logger.info(f'PARAMS: {params}')
        async with httpx.AsyncClient() as client:
            response = await client.put(url=url, params=params, json=payload)
        _logger.info(f'RESPONSE: {response.text}')
        result = response.json().get('result')
        return result
