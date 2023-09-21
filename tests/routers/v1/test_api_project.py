# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from pytest_httpx import HTTPXMock
from requests.models import Response

from app.config import ConfigClass
from app.models.file_models import ItemStatus

pytestmark = pytest.mark.asyncio
test_project_api = '/v1/projects'
project_code = 'test_project'
test_get_project_file_api = f'/v1/project/{project_code}/files'
test_get_project_resume_api = f'/v1/project/{project_code}/files/resumable'
test_get_project_file_download_api = f'/v1/project/{project_code}/files/download'
test_get_project_item_api = f'/v1/project/{project_code}/search'


@pytest.fixture
def mock_get_item_by_id(httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.METADATA_SERVICE + '/v1/item/test_id/',
        json={
            'code': 200,
            'error_msg': '',
            'page': 0,
            'total': 0,
            'num_of_pages': 1,
            'result': {
                'id': 'item-id',
                'parent': 'parent-id',
                'parent_path': 'testuser',
                'restore_path': None,
                'status': False,
                'type': 'file',
                'zone': 0,
                'name': 'fake_file',
                'size': 0,
                'owner': 'testuser',
                'container_code': project_code,
                'container_type': 'project',
                'created_time': '2022-04-13 18:17:51.008212',
                'last_updated_time': '2022-04-13 18:17:51.008227',
            },
        },
        status_code=200,
    )


async def test_get_project_list_should_return_200(test_async_client_auth, mocker):
    test_project = ['project1', 'project2', 'project3']
    mocker.patch(
        'app.routers.v1.api_project.get_user_projects',
        return_value=test_project,
    )
    header = {'Authorization': 'fake token'}
    res = await test_async_client_auth.get(test_project_api, headers=header)
    res_json = res.json()
    projects = res_json.get('result')
    assert res.status_code == 200
    assert len(projects) == len(test_project)


async def test_get_project_list_without_token_should_return_401(
    test_async_client,
):
    res = await test_async_client.get(test_project_api)
    res_json = res.json()
    assert res_json.get('code') == 401
    assert res_json.get('error_msg') == 'Invalid token'


async def test_upload_files_into_project_should_return_200(
    test_async_client_auth, mocker, httpx_mock, mock_get_item_by_id, has_permission_true
):
    payload = {
        'operator': 'test_user',
        'upload_message': 'test',
        'type': 'processed',
        'zone': 'gr',
        'filename': 'fake.png',
        'job_type': 'AS_FILE',
        'current_folder_node': 'folder1',
        'parent_folder_id': 'test_id',
        'data': [{'resumable_filename': 'fake.png', 'resumable_relative_path': 'folder1'}],
    }

    mock_response = Response()
    mock_response.status_code = 200
    mock_response._content = b'{ "result" : "SUCCESSED" }'
    mocker.patch('app.routers.v1.api_project.transfer_to_pre', return_value=mock_response)
    header = {'Authorization': 'fake token'}
    response = await test_async_client_auth.post(test_get_project_file_api, headers=header, json=payload)
    assert response.status_code == 200
    assert response.json()['result'] == 'SUCCESSED'


async def test_upload_files_with_invalid_upload_event_should_return_400(test_async_client_auth, mocker):
    payload = {
        'operator': 'test_user',
        'upload_message': 'test',
        'type': 'processed',
        'zone': 'zone',
        'filename': 'fake.png',
        'job_type': 'AS_FILE',
        'current_folder_node': '',
        'parent_folder_id': 'test_id',
        'data': [{'resumable_filename': 'fake.png', 'resumable_relative_path': ''}],
    }
    header = {'Authorization': 'fake token'}
    response = await test_async_client_auth.post(test_get_project_file_api, headers=header, json=payload)
    res_json = response.json()
    assert res_json.get('code') == 400
    assert res_json.get('error_msg') == 'Invalid zone: zone'


async def test_upload_to_core_outside_vm(test_async_client_project_member_auth, mocker):

    payload = {
        'operator': 'test_user',
        'upload_message': 'test',
        'type': 'processed',
        'zone': 'cr',
        'filename': 'fake.png',
        'job_type': 'AS_FILE',
        'current_folder_node': '',
        'parent_folder_id': 'test_id',
        'data': [{'resumable_filename': 'fake.png', 'resumable_relative_path': ''}],
    }
    header = {'Authorization': 'fake token'}
    response = await test_async_client_project_member_auth.post(test_get_project_file_api, headers=header, json=payload)
    res_json = response.json()

    assert res_json.get('code') == 403
    assert res_json.get('error_msg') == 'Cannot upload to cr zone'


async def test_upload_with_conflict_should_return_409(
    test_async_client_auth, mocker, has_permission_true, mock_get_item_by_id, httpx_mock
):
    payload = {
        'operator': 'test_user',
        'upload_message': 'test',
        'type': 'processed',
        'zone': 'gr',
        'filename': 'fake.png',
        'job_type': 'AS_FILE',
        'current_folder_node': '',
        'parent_folder_id': 'test_id',
        'data': [{'resumable_filename': 'fake.png', 'resumable_relative_path': ''}],
    }

    mock_response = Response()
    mock_response.status_code = 409
    mock_response._content = b'{ "error_msg" : "File with that name already exists" }'
    mocker.patch('app.routers.v1.api_project.transfer_to_pre', return_value=mock_response)

    header = {'Authorization': 'fake token'}
    response = await test_async_client_auth.post(test_get_project_file_api, headers=header, json=payload)
    res_json = response.json()
    assert res_json.get('code') == 409
    assert res_json.get('error_msg') == 'File with that name already exists'


async def test_upload_files_into_project_with_tag_permission_should_return_200(
    test_async_client_auth, mocker, httpx_mock, mock_get_item_by_id, has_permission_true
):
    payload = {
        'operator': 'test_user',
        'upload_message': 'test',
        'type': 'processed',
        'zone': 'gr',
        'filename': 'fake.png',
        'job_type': 'AS_FILE',
        'current_folder_node': 'folder1',
        'parent_folder_id': 'test_id',
        'folder_tags': ['tag1', 'tag2'],
        'data': [{'resumable_filename': 'fake.png', 'resumable_relative_path': 'folder1'}],
    }

    mock_response = Response()
    mock_response.status_code = 200
    mock_response._content = b'{ "result" : "SUCCESSED" }'
    mocker.patch('app.routers.v1.api_project.transfer_to_pre', return_value=mock_response)
    header = {'Authorization': 'fake token'}
    response = await test_async_client_auth.post(test_get_project_file_api, headers=header, json=payload)
    assert response.status_code == 200
    assert response.json()['result'] == 'SUCCESSED'


async def test_upload_files_into_project_without_tag_should_return_403(
    test_async_client_auth, mocker, httpx_mock, mock_get_item_by_id
):
    url = (
        ConfigClass.AUTH_SERVICE + '/v1/authorize?role=platform_admin&resource=file_in_own_namefolder&'
        'zone=greenroom&operation=upload&project_code=test_project'
    )
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
    url = (
        ConfigClass.AUTH_SERVICE + '/v1/authorize?role=platform_admin&resource=file_in_own_namefolder&'
        'zone=greenroom&operation=annotate&project_code=test_project'
    )
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': False}})

    payload = {
        'operator': 'test_user',
        'upload_message': 'test',
        'type': 'processed',
        'zone': 'gr',
        'filename': 'fake.png',
        'job_type': 'AS_FILE',
        'current_folder_node': 'folder1',
        'parent_folder_id': 'test_id',
        'folder_tags': ['tag1', 'tag2'],
        'data': [{'resumable_filename': 'fake.png', 'resumable_relative_path': 'folder1'}],
    }

    mock_response = Response()
    mock_response.status_code = 200
    mock_response._content = b'{ "result" : "SUCCESSED" }'
    mocker.patch('app.routers.v1.api_project.transfer_to_pre', return_value=mock_response)
    header = {'Authorization': 'fake token'}
    response = await test_async_client_auth.post(test_get_project_file_api, headers=header, json=payload)
    assert response.status_code == 403


async def test_upload_with_internal_error_should_return_500(
    test_async_client_auth, mocker, httpx_mock, mock_get_item_by_id, has_permission_true
):
    payload = {
        'operator': 'test_user',
        'upload_message': 'test',
        'type': 'processed',
        'zone': 'gr',
        'filename': 'fake.png',
        'job_type': 'AS_FILE',
        'current_folder_node': '',
        'parent_folder_id': 'test_id',
        'data': [{'resumable_filename': 'fake.png', 'resumable_relative_path': ''}],
    }

    mock_response = Response()
    mock_response.status_code = 400
    mock_response._content = b'{ "error_msg" : "mock_internal_error" }'
    mocker.patch('app.routers.v1.api_project.transfer_to_pre', return_value=mock_response)

    header = {'Authorization': 'fake token'}
    response = await test_async_client_auth.post(test_get_project_file_api, headers=header, json=payload)
    res_json = response.json()
    assert res_json.get('code') == 500
    assert res_json.get('error_msg') == 'Upload Error: mock_internal_error'


async def test_resume_upload_files_success(
    test_async_client_auth, mocker, httpx_mock, mock_get_item_by_id, has_permission_true
):
    httpx_mock.add_response(
        method='POST',
        url='http://data_upload_gr/v1/files/resumable',
        json={
            'code': 200,
            'result': [],
        },
        status_code=200,
    )

    payload = {
        'bucket': project_code,
        'zone': 'gr',
        'object_infos': [{'item_id': 'test_id', 'object_path': 'test_path', 'resumable_id': 'test_resumable_id'}],
    }
    header = {'Authorization': 'fake token'}
    res = await test_async_client_auth.post(test_get_project_resume_api, headers=header, json=payload)

    assert res.status_code == 200


# project download test


async def test_download_with_403_wrong_permission(
    test_async_client_auth, mocker, mock_get_item_by_id, httpx_mock, has_permission_false
):
    payload = {
        'operator': 'test_user',
        'zone': 'gr',
        'container_code': project_code,
        'container_type': 'project',
        'files': [{'id': 'test_id'}],
    }

    header = {'Authorization': 'fake token'}
    response = await test_async_client_auth.post(test_get_project_file_download_api, headers=header, json=payload)
    res_json = response.json()
    assert response.status_code == 403
    assert res_json.get('error_msg') == f'Unauthorized download action on project {project_code}'


async def test_download_with_400_bad_request(
    test_async_client_auth, mocker, mock_get_item_by_id, httpx_mock, has_permission_true
):
    payload = {
        'operator': 'test_user',
        'zone': 'gr',
        'container_code': project_code,
        'container_type': 'project',
        'files': [{'id': 'test_id'}],
    }

    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.DOWNLOAD_SERVICE_GREENROOM + '/v2/download/pre/',
        json={'code': 400, 'error_msg': 'Error', 'page': 0, 'total': 0, 'num_of_pages': 1, 'result': []},
        status_code=400,
    )

    header = {'Authorization': 'fake token', 'Session-ID': 'fake session'}
    response = await test_async_client_auth.post(test_get_project_file_download_api, headers=header, json=payload)

    res_json = response.json()
    assert response.status_code == 400
    assert res_json.get('error_msg') == 'Download service error: Error'


async def test_download_with_200_pass(
    test_async_client_auth, mocker, mock_get_item_by_id, httpx_mock, has_permission_true
):
    payload = {
        'operator': 'test_user',
        'zone': 'gr',
        'container_code': project_code,
        'container_type': 'project',
        'files': [{'id': 'test_id'}],
    }

    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.DOWNLOAD_SERVICE_GREENROOM + '/v2/download/pre/',
        json={'code': 200, 'error_msg': '', 'page': 0, 'total': 0, 'num_of_pages': 1, 'result': []},
        status_code=200,
    )

    header = {'Authorization': 'fake token', 'Session-ID': 'fake session'}
    response = await test_async_client_auth.post(test_get_project_file_download_api, headers=header, json=payload)

    assert response.status_code == 200


# project search test
async def test_get_folder_in_project_should_return_200(test_async_client_auth, mocker, httpx_mock: HTTPXMock):
    param = {
        'zone': 'zone',
        'project_code': project_code,
        'path': 'testuser/fake_folder',
        'item_type': 'folder',
        'container_type': 'project',
    }
    mocker.patch('app.routers.v1.api_project.get_zone', return_value='zone')
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/'
            '?container_code=test_project'
            '&container_type=project'
            '&parent_path=testuser'
            '&recursive=false'
            '&zone=zone'
            '&status=ACTIVE'
            '&name=fake_folder'
            '&type=folder'
        ),
        json={
            'code': 200,
            'result': [
                {
                    'id': 'item-id',
                    'parent': 'parent-id',
                    'parent_path': 'testuser',
                    'restore_path': None,
                    'status': ItemStatus.ACTIVE,
                    'type': 'folder',
                    'zone': 0,
                    'name': 'fake_folder',
                    'size': 0,
                    'owner': 'testuser',
                    'container_code': project_code,
                    'container_type': 'project',
                    'created_time': '2022-04-13 18:17:51.008212',
                    'last_updated_time': '2022-04-13 18:17:51.008227',
                    'storage': {
                        'id': '8cd8cef7-2603-4ec3-b5a0-479e58e4c9d9',
                        'location_uri': '',
                        'version': '1.0',
                    },
                    'extended': {
                        'id': '96510da0-22f4-4487-ac88-71cd48967c8d',
                        'extra': {'tags': [], 'attributes': {}},
                    },
                },
                {'id': 'item-id2', 'parent': 'parent-id2'},
            ],
        },
        status_code=200,
    )
    header = {'Authorization': 'fake token'}
    res = await test_async_client_auth.get(test_get_project_item_api, headers=header, query_string=param)
    res_json = res.json()
    assert res_json.get('code') == 200
    result = res_json.get('result')
    assert result.get('type') == 'folder'
    assert result.get('name') == 'fake_folder'
    assert result.get('zone') == 0
    assert result.get('container_code') == project_code


async def test_get_file_in_project_should_return_200(test_async_client_auth, mocker, httpx_mock: HTTPXMock):
    param = {
        'zone': 'zone',
        'project_code': project_code,
        'path': 'testuser/fake_file',
        'item_type': 'file',
        'container_type': 'project',
    }
    mocker.patch('app.routers.v1.api_project.get_zone', return_value='zone')
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/'
            '?container_code=test_project'
            '&container_type=project'
            '&parent_path=testuser'
            '&recursive=false'
            '&zone=zone'
            '&status=ACTIVE'
            '&name=fake_file'
            '&type=file'
        ),
        json={
            'code': 200,
            'result': [
                {
                    'id': 'item-id',
                    'parent': 'parent-id',
                    'parent_path': 'testuser',
                    'restore_path': None,
                    'status': ItemStatus.ACTIVE,
                    'type': 'file',
                    'zone': 0,
                    'name': 'fake_file',
                    'size': 0,
                    'owner': 'testuser',
                    'container_code': project_code,
                    'container_type': 'project',
                    'created_time': '2022-04-13 18:17:51.008212',
                    'last_updated_time': '2022-04-13 18:17:51.008227',
                    'storage': {
                        'id': '8cd8cef7-2603-4ec3-b5a0-479e58e4c9d9',
                        'location_uri': '',
                        'version': '1.0',
                    },
                    'extended': {
                        'id': '96510da0-22f4-4487-ac88-71cd48967c8d',
                        'extra': {'tags': [], 'attributes': {}},
                    },
                },
                {'id': 'item-id2', 'parent': 'parent-id2'},
            ],
        },
        status_code=200,
    )
    header = {'Authorization': 'fake token'}
    res = await test_async_client_auth.get(test_get_project_item_api, headers=header, query_string=param)
    res_json = res.json()
    assert res_json.get('code') == 200
    result = res_json.get('result')
    assert result.get('type') == 'file'
    assert result.get('name') == 'fake_file'
    assert result.get('zone') == 0
    assert result.get('container_code') == project_code


async def test_get_folder_in_project_without_token_should_return_401(
    test_async_client,
):
    param = {
        'zone': 'zone',
        'project_code': project_code,
        'path': 'testuser/fake_folder',
        'item_type': 'folder',
        'container_type': 'project',
    }
    res = await test_async_client.get(test_get_project_item_api, query_string=param)
    res_json = res.json()
    assert res_json.get('code') == 401
    assert res_json.get('error_msg') == 'Invalid token'


async def test_get_folder_in_project_without_permission_should_return_404(test_async_client_auth, httpx_mock, mocker):
    param = {
        'zone': 'zone',
        'project_code': project_code,
        'path': 'testuser/fake_folder',
        'item_type': 'folder',
        'container_type': 'project',
    }

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/'
            '?container_code=test_project'
            '&container_type=project'
            '&parent_path=testuser'
            '&recursive=false'
            '&zone=zone'
            '&status=ACTIVE'
            '&name=fake_folder'
            '&type=folder'
        ),
        json={},
        status_code=404,
    )

    mocker.patch('app.routers.v1.api_project.get_zone', return_value='zone')
    header = {'Authorization': 'fake token'}
    res = await test_async_client_auth.get(test_get_project_item_api, headers=header, query_string=param)
    res_json = res.json()
    assert res.status_code == 404
    assert res_json.get('error_msg') == 'Error Getting Folder: not found'


async def test_get_folder_fail_when_query_node_should_return_500(test_async_client_auth, mocker, httpx_mock):
    param = {
        'zone': 'zone',
        'project_code': project_code,
        'path': 'testuser/fake_folder',
        'item_type': 'folder',
        'container_type': 'project',
    }

    mocker.patch('app.routers.v1.api_project.get_zone', return_value='zone')
    mock_response = Response()
    mock_response.status_code = 500
    mock_response._content = b'{"result": [], "error_msg":"mock error"}'
    mocker.patch(
        'app.routers.v1.api_project.query_file_folder',
        return_value=mock_response,
    )
    header = {'Authorization': 'fake token'}
    res = await test_async_client_auth.get(test_get_project_item_api, headers=header, query_string=param)
    res_json = res.json()
    assert res_json.get('code') == 500
    assert res_json.get('error_msg') == 'Error Getting Folder: mock error'


async def test_get_project_list_2nd_page_should_return_200(test_async_client_auth, mocker):
    test_project = [
        {'name': 'project 1', 'code': 'project1', 'geid': 'fake-geid-1'},
        {'name': 'project 2', 'code': 'project2', 'geid': 'fake-geid-2'},
        {'name': 'project 3', 'code': 'project3', 'geid': 'fake-geid-3'},
        {'name': 'project 4', 'code': 'project4', 'geid': 'fake-geid-4'},
        {'name': 'project 5', 'code': 'project5', 'geid': 'fake-geid-5'},
        {'name': 'project 6', 'code': 'project6', 'geid': 'fake-geid-6'},
        {'name': 'project 7', 'code': 'project7', 'geid': 'fake-geid-7'},
        {'name': 'project 8', 'code': 'project8', 'geid': 'fake-geid-8'},
        {'name': 'project 9', 'code': 'project9', 'geid': 'fake-geid-9'},
        {'name': 'project 10', 'code': 'project10', 'geid': 'fake-geid-10'},
    ]
    mocker.patch(
        'app.routers.v1.api_project.get_user_projects',
        return_value=test_project,
    )
    header = {'Authorization': 'fake token'}
    params = {'page': 0, 'page_size': 10, 'order': 'created_at', 'order_by': 'desc'}
    res = await test_async_client_auth.get(test_project_api, headers=header, query_string=params)
    res_json = res.json()
    projects = res_json.get('result')
    assert res.status_code == 200
    assert len(projects) == len(test_project)


async def test_get_project_list_20_per_page_should_return_200(test_async_client_auth, mocker):
    test_project = [
        {'name': 'project 1', 'code': 'project1', 'geid': 'fake-geid-1'},
        {'name': 'project 2', 'code': 'project2', 'geid': 'fake-geid-2'},
        {'name': 'project 3', 'code': 'project3', 'geid': 'fake-geid-3'},
        {'name': 'project 4', 'code': 'project4', 'geid': 'fake-geid-4'},
        {'name': 'project 5', 'code': 'project5', 'geid': 'fake-geid-5'},
        {'name': 'project 6', 'code': 'project6', 'geid': 'fake-geid-6'},
        {'name': 'project 7', 'code': 'project7', 'geid': 'fake-geid-7'},
        {'name': 'project 8', 'code': 'project8', 'geid': 'fake-geid-8'},
        {'name': 'project 9', 'code': 'project9', 'geid': 'fake-geid-9'},
        {'name': 'project 10', 'code': 'project10', 'geid': 'fake-geid-10'},
        {'name': 'project 11', 'code': 'project11', 'geid': 'fake-geid-11'},
        {'name': 'project 12', 'code': 'project12', 'geid': 'fake-geid-12'},
        {'name': 'project 13', 'code': 'project13', 'geid': 'fake-geid-13'},
        {'name': 'project 14', 'code': 'project14', 'geid': 'fake-geid-14'},
        {'name': 'project 15', 'code': 'project15', 'geid': 'fake-geid-15'},
        {'name': 'project 16', 'code': 'project16', 'geid': 'fake-geid-16'},
        {'name': 'project 17', 'code': 'project17', 'geid': 'fake-geid-17'},
        {'name': 'project 18', 'code': 'project18', 'geid': 'fake-geid-18'},
        {'name': 'project 19', 'code': 'project19', 'geid': 'fake-geid-19'},
        {'name': 'project 20', 'code': 'project20', 'geid': 'fake-geid-20'},
    ]
    mocker.patch(
        'app.routers.v1.api_project.get_user_projects',
        return_value=test_project,
    )
    header = {'Authorization': 'fake token'}
    params = {'page': 0, 'page_size': 10, 'order': 'created_at', 'order_by': 'desc'}
    res = await test_async_client_auth.get(test_project_api, headers=header, query_string=params)
    res_json = res.json()
    projects = res_json.get('result')
    assert res.status_code == 200
    assert len(projects) == len(test_project)


async def test_get_project_list_desc_order_by_code_should_return_200(test_async_client_auth, mocker):
    test_project = [
        {'name': 'project1', 'code': 'zproject', 'geid': 'fake-geid1'},
        {'name': 'project2', 'code': 'xproject', 'geid': 'fake-geid2'},
        {'name': 'project3', 'code': 'wproject', 'geid': 'fake-geid3'},
        {'name': 'project4', 'code': 'uproject', 'geid': 'fake-geid4'},
        {'name': 'project5', 'code': 'kproject', 'geid': 'fake-geid5'},
        {'name': 'project6', 'code': 'jproject', 'geid': 'fake-geid6'},
        {'name': 'project7', 'code': 'gproject', 'geid': 'fake-geid7'},
        {'name': 'project8', 'code': 'cproject', 'geid': 'fake-geid8'},
        {'name': 'project9', 'code': 'bproject', 'geid': 'fake-geid9'},
        {'name': 'project10', 'code': 'aproject', 'geid': 'fake-geid10'},
    ]
    mocker.patch(
        'app.routers.v1.api_project.get_user_projects',
        return_value=test_project,
    )
    header = {'Authorization': 'fake token'}
    params = {'page': 0, 'page_size': 10, 'order': 'created_at', 'order_by': 'desc'}
    res = await test_async_client_auth.get(test_project_api, headers=header, query_string=params)
    res_json = res.json()
    projects = res_json.get('result')
    assert res.status_code == 200
    assert len(projects) == len(test_project)
    assert projects == test_project
