# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from pytest_httpx import HTTPXMock

test_dataset_api = '/v1/datasets'
dataset_code = 'testdataset'
dataset_geid = 'test-dataset-geid'
test_dataset_detailed_api = '/v1/dataset/testdataset'
pytestmark = pytest.mark.asyncio


async def test_list_dataset_without_token(test_async_client):
    res = await test_async_client.get(test_dataset_api)
    res_json = res.json()
    assert res_json.get('code') == 401
    assert res_json.get('error_msg') == 'Invalid token'


async def test_list_dataset_should_successed(test_async_client_auth, httpx_mock: HTTPXMock):
    header = {'Authorization': 'fake token'}
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://dataset_service/v1/datasets/'
            '?creator=testuser&filter=%7B%7D&order_by=created_at&order_type=desc&page=0&page_size=10'
        ),
        json={
            'code': 200,
            'error_msg': '',
            'page': 0,
            'total': 1,
            'num_of_pages': 1,
            'result': [
                {
                    'id': 'fake-geid',
                    'source': '',
                    'authors': ['user1', 'user2'],
                    'code': dataset_code,
                    'type': 'GENERAL',
                    'modality': [],
                    'collection_method': [],
                    'license': '',
                    'tags': [],
                    'description': 'my description',
                    'size': 0,
                    'total_files': 0,
                    'title': 'test dataset',
                    'creator': 'testuser',
                    'project_id': 'None',
                    'created_at': '2022-03-31T15:00:04',
                    'updated_at': '2022-03-31T15:00:04',
                }
            ],
        },
        status_code=200,
    )
    res = await test_async_client_auth.get(test_dataset_api, headers=header)
    res_json = res.json()
    assert res_json.get('code') == 200
    datasets = []
    for d in res_json.get('result'):
        datasets.append(d.get('code'))
    assert dataset_code in datasets


async def test_list_empty_dataset(test_async_client_auth, httpx_mock: HTTPXMock):
    header = {'Authorization': 'fake token'}
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://dataset_service/v1/datasets/'
            '?creator=testuser&filter=%7B%7D&order_by=created_at&order_type=desc&page=0&page_size=10'
        ),
        json={'code': 200, 'error_msg': '', 'page': 0, 'total': 1, 'num_of_pages': 1, 'result': []},
        status_code=200,
    )
    res = await test_async_client_auth.get(test_dataset_api, headers=header)
    res_json = res.json()
    assert res_json.get('code') == 200
    assert res_json.get('result') == []


async def test_get_dataset_detail_without_token(test_async_client):
    res = await test_async_client.get(test_dataset_detailed_api)
    res_json = res.json()
    assert res_json.get('code') == 401
    assert res_json.get('error_msg') == 'Invalid token'


async def test_get_dataset_detail_should_successed(test_async_client_auth, httpx_mock):
    header = {'Authorization': 'fake token'}
    httpx_mock.add_response(
        method='GET',
        url=f'http://dataset_service/v1/datasets/{dataset_code}',
        json={
            'id': dataset_geid,
            'source': '',
            'authors': ['user1', 'user2'],
            'code': dataset_code,
            'type': 'GENERAL',
            'modality': [],
            'collection_method': [],
            'license': '',
            'tags': [],
            'description': 'my description',
            'size': 0,
            'total_files': 0,
            'title': 'my title',
            'creator': 'testuser',
            'project_id': 'None',
            'created_at': '2022-03-31T15:00:04',
            'updated_at': '2022-03-31T15:00:04',
        },
        status_code=200,
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://dataset_service/v1/dataset/versions'
            '?dataset_id=test-dataset-geid&page=0&page_size=10&order=desc&sorting=created_at'
        ),
        json={
            'code': 200,
            'error_msg': '',
            'page': 0,
            'total': 3,
            'num_of_pages': 1,
            'result': [
                {
                    'id': '1',
                    'dataset_code': dataset_code,
                    'dataset_id': dataset_geid,
                    'version': '2.0',
                    'created_by': 'testuser',
                    'created_at': '2022-06-07T22:10:29',
                    'location': 'fake-minio-zip-path2',
                    'notes': 'test release version 2',
                },
                {
                    'id': '2',
                    'dataset_code': dataset_code,
                    'dataset_id': dataset_geid,
                    'version': '1.1',
                    'created_by': 'testuser',
                    'created_at': '2022-03-17T13:53:27',
                    'location': 'fakie-minio-zip-path1-1',
                    'notes': 'test release version 1.1',
                },
                {
                    'id': '82',
                    'dataset_code': dataset_code,
                    'dataset_id': dataset_geid,
                    'version': '1.0',
                    'created_by': 'testuser',
                    'created_at': '2022-03-10T18:37:41',
                    'location': 'fake-minio-zip-path-1',
                    'notes': 'test release version 1.0',
                },
            ],
        },
        status_code=200,
    )
    res = await test_async_client_auth.get(test_dataset_detailed_api, headers=header)
    res_json = res.json()
    assert res_json.get('code') == 200
    result = res_json.get('result')
    _dataset_info = result.get('general_info')
    assert _dataset_info['creator'] == 'testuser'
    _version_info = result.get('version_detail')
    assert _version_info[0]['dataset_code'] == dataset_code
    _version_no = result.get('version_no')
    assert _version_no == 3


async def test_get_dataset_detail_no_access(test_async_client_auth, httpx_mock):
    header = {'Authorization': 'fake token'}
    httpx_mock.add_response(
        method='GET',
        url=f'http://dataset_service/v1/datasets/{dataset_code}',
        json={
            'id': 'fake_geid',
            'source': '',
            'authors': ['user1', 'user2'],
            'code': dataset_code,
            'type': 'GENERAL',
            'modality': [],
            'collection_method': [],
            'license': '',
            'tags': [],
            'description': 'my description',
            'size': 0,
            'total_files': 0,
            'title': 'my title',
            'creator': 'fakeuser',
            'project_id': 'None',
            'created_at': '2022-03-31T15:00:04',
            'updated_at': '2022-03-31T15:00:04',
        },
        status_code=200,
    )
    res = await test_async_client_auth.get(test_dataset_detailed_api, headers=header)
    res_json = res.json()
    assert res_json.get('code') == 403
    assert res_json.get('error_msg') == 'Permission Denied'


async def test_get_dataset_detail_not_exist(test_async_client_auth, httpx_mock):
    header = {'Authorization': 'fake token'}
    httpx_mock.add_response(
        method='GET',
        url=f'http://dataset_service/v1/datasets/{dataset_code}',
        json={'error': {'code': 'global.not_found', 'details': 'Requested resource is not found'}},
        status_code=200,
    )
    res = await test_async_client_auth.get(test_dataset_detailed_api, headers=header)
    res_json = res.json()
    assert res_json.get('code') == 403
    assert res_json.get('error_msg') == 'Permission Denied'
