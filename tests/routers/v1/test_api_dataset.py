# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Callable

import pytest
from pytest_httpx import HTTPXMock
from starlette.requests import Request

from app.components.user.models import CurrentUser
from app.components.user.models import UserRole
from app.resources.dependencies import jwt_required

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
        url='http://dataset_service/v1/datasets/?creator=testuser',
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
        url='http://dataset_service/v1/datasets/?creator=testuser',
        json={'code': 200, 'error_msg': '', 'page': 0, 'total': 1, 'num_of_pages': 1, 'result': []},
        status_code=200,
    )
    res = await test_async_client_auth.get(test_dataset_api, headers=header)
    res_json = res.json()
    assert res_json.get('code') == 200
    assert res_json.get('result') == []


async def test_list_datasets_with_creator_parameter_returns_200(test_async_client, httpx_mock):
    test_async_client.application.dependency_overrides[jwt_required]: Callable[[Request], None] = lambda: CurrentUser(
        {'username': 'any', 'realm_roles': []}
    )

    httpx_mock.add_response(
        method='GET',
        url='http://dataset_service/v1/datasets/?creator=any',
        json={},
    )

    params = {'creator': 'any'}
    response = await test_async_client.get('/v1/datasets', query_string=params)

    assert response.status_code == 200


async def test_list_datasets_with_creator_parameter_replaces_creator_value_with_current_identity(
    test_async_client, httpx_mock, fake
):
    test_async_client.application.dependency_overrides[jwt_required]: Callable[[Request], None] = lambda: CurrentUser(
        {'username': 'any', 'realm_roles': []}
    )
    httpx_mock.add_response(
        method='GET',
        url='http://dataset_service/v1/datasets/?creator=any',
        json={},
    )

    params = {'creator': fake.user_name()}
    response = await test_async_client.get('/v1/datasets', query_string=params)

    assert response.status_code == 200


async def test_list_datasets_without_creator_parameter_adds_project_id_any_and_or_creator_parameters(
    test_async_client, httpx_mock, fake, project_factory
):
    """When current user has the project admin role in any project."""

    username = fake.user_name()
    project_1 = project_factory.mock_retrieval_by_code()
    project_2 = project_factory.mock_retrieval_by_code()
    realm_roles = [
        f'{fake.project_code()}-{UserRole.CONTRIBUTOR.value}',
        f'{fake.project_code()}-{UserRole.COLLABORATOR.value}',
        f'{project_1.code}-{UserRole.ADMIN.value}',
        f'{project_2.code}-{UserRole.ADMIN.value}',
    ]
    test_async_client.application.dependency_overrides[jwt_required]: Callable[[Request], None] = lambda: CurrentUser(
        {'username': username, 'realm_roles': realm_roles}
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://dataset_service/v1/datasets/?' f'project_id_any={project_1.id},{project_2.id}&or_creator={username}'
        ),
        json={},
    )

    response = await test_async_client.get('/v1/datasets')

    assert response.status_code == 200


async def test_list_datasets_without_creator_parameter_adds_only_creator_parameter(test_async_client, httpx_mock, fake):
    """When current user doesn't have the project admin role in any project."""

    username = fake.user_name()
    realm_roles = [f'{fake.project_code()}-{UserRole.CONTRIBUTOR.value}']
    test_async_client.application.dependency_overrides[jwt_required]: Callable[[Request], None] = lambda: CurrentUser(
        {'username': username, 'realm_roles': realm_roles}
    )
    httpx_mock.add_response(
        method='GET',
        url=f'http://dataset_service/v1/datasets/?creator={username}',
        json={},
    )

    response = await test_async_client.get('/v1/datasets')

    assert response.status_code == 200


async def test_list_datasets_with_project_code_parameter_replaces_it_with_project_id_and_adds_creator_parameter(
    test_async_client, httpx_mock, fake, project_factory
):
    """When current user has no admin role in the specified project code."""

    username = fake.user_name()
    project = project_factory.mock_retrieval_by_code()
    realm_roles = [f'{project.code}-{UserRole.CONTRIBUTOR.value}']
    test_async_client.application.dependency_overrides[jwt_required]: Callable[[Request], None] = lambda: CurrentUser(
        {'username': username, 'realm_roles': realm_roles}
    )
    httpx_mock.add_response(
        method='GET',
        url=f'http://dataset_service/v1/datasets/?creator={username}&project_id={project.id}',
        json={},
    )

    params = {'project_code': project.code}
    response = await test_async_client.get('/v1/datasets', query_string=params)

    assert response.status_code == 200


async def test_list_datasets_with_project_code_parameter_returns_forbidden(test_async_client, fake):
    """When current user doesn't have any roles in the specified project code."""

    username = fake.user_name()
    realm_roles = [f'{fake.project_code()}-{UserRole.ADMIN.value}']
    test_async_client.application.dependency_overrides[jwt_required]: Callable[[Request], None] = lambda: CurrentUser(
        {'username': username, 'realm_roles': realm_roles}
    )

    params = {'project_code': fake.project_code()}
    response = await test_async_client.get('/v1/datasets', query_string=params)

    assert response.status_code == 403


async def test_list_datasets_with_project_code_and_creator_parameters_replaces_project_code_with_project_id_parameter(
    test_async_client, httpx_mock, fake, project_factory
):
    username = fake.user_name()
    project = project_factory.mock_retrieval_by_code()
    realm_roles = [f'{project.code}-{UserRole.CONTRIBUTOR.value}']
    test_async_client.application.dependency_overrides[jwt_required]: Callable[[Request], None] = lambda: CurrentUser(
        {'username': username, 'realm_roles': realm_roles}
    )
    httpx_mock.add_response(
        method='GET',
        url=f'http://dataset_service/v1/datasets/?creator={username}&project_id={project.id}',
        json={},
    )

    params = {'creator': username, 'project_code': project.code}
    response = await test_async_client.get('/v1/datasets', query_string=params)

    assert response.status_code == 200


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


async def test_get_dataset_detail_no_access(test_async_client_auth, dataset_factory):
    header = {'Authorization': 'fake token'}
    dataset = dataset_factory.generate(code='testdataset')
    dataset_factory.mock_retrieval_by_code(dataset)
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
        status_code=404,
    )
    res = await test_async_client_auth.get(test_dataset_detailed_api, headers=header)
    res_json = res.json()
    assert res_json.get('code') == 404
    assert res_json.get('error_msg') == 'Cannot found given dataset code'
