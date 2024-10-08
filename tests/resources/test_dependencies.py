# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import time

import jwt
import pytest
from fastapi import Request

from app.models.project_models import POSTProjectFile
from app.resources.dependencies import jwt_required
from app.resources.dependencies import transfer_to_pre
from app.resources.error_handler import APIException

pytestmark = pytest.mark.asyncio
project_code = 'test_project'


async def test_jwt_required_should_return_successed(httpx_mock):
    mock_request = Request(scope={'type': 'http'})
    encoded_jwt = jwt.encode(
        {'realm_access': {'roles': ['platform_admin']}, 'preferred_username': 'test_user', 'exp': time.time() + 3},
        key='unittest',
        algorithm='HS256',
    )
    mock_request._headers = {'Authorization': 'Bearer ' + encoded_jwt}
    httpx_mock.add_response(
        method='GET',
        url='http://auth/v1/admin/user?username=test_user',
        json={'result': {'id': 1, 'role': 'admin'}},
        status_code=200,
    )
    test_result = await jwt_required(mock_request)
    assert test_result['code'] == 200
    assert test_result['user_id'] == 1
    assert test_result['username'] == 'test_user'


async def test_jwt_required_without_token_should_return_unauthorized():
    mock_request = Request(scope={'type': 'http'})
    mock_request._headers = {}
    with pytest.raises(APIException) as e:
        _ = await jwt_required(mock_request)
        assert e.value.status_code == 401
        assert e.value.error_msg == 'Invalid token'


async def test_jwt_required_with_token_expired_should_return_unauthorized():
    mock_request = Request(scope={'type': 'http'})
    encoded_jwt = jwt.encode(
        {'realm_access': {'roles': ['platform_admin']}, 'preferred_username': 'test_user', 'exp': time.time() - 3},
        key='unittest',
        algorithm='HS256',
    )
    mock_request._headers = {'Authorization': 'Bearer ' + encoded_jwt}

    try:
        await jwt_required(mock_request)
    except APIException as e:
        assert e.status_code == 401
    except Exception:
        raise AssertionError()


async def test_jwt_required_without_username_return_not_found(httpx_mock):
    mock_request = Request(scope={'type': 'http'})

    encoded_jwt = jwt.encode(
        {'realm_access': {'roles': ['platform_admin']}, 'preferred_username': 'test_user', 'exp': time.time() + 3},
        key='unittest',
        algorithm='HS256',
    )
    mock_request._headers = {'Authorization': 'Bearer ' + encoded_jwt}
    httpx_mock.add_response(
        method='GET',
        url='http://auth/v1/admin/user?username=test_user',
        json={'result': None},
        status_code=404,
    )
    try:
        await jwt_required(mock_request)
    except APIException as e:
        assert e.status_code == 403
    except Exception:
        raise AssertionError()


async def test_transfer_to_pre_success(httpx_mock):
    mock_post_model = POSTProjectFile
    mock_post_model.current_folder_node = 'current_folder_node'
    mock_post_model.parent_folder_id = 'parent_folder_id'
    mock_post_model.operator = 'operator'
    mock_post_model.data = 'data'
    mock_post_model.zone = 'cr'
    mock_post_model.job_type = 'job_type'
    httpx_mock.add_response(
        method='POST',
        url='http://data_upload_cr/v1/files/jobs',
        json={},
        status_code=200,
    )
    headers = {'Session-ID': 'session_id', 'authorization': 'fake-token'}
    result = await transfer_to_pre(mock_post_model, project_code, headers)
    assert result.json() == {}


async def test_transfer_to_pre_with_external_service_fail():
    mock_post_model = POSTProjectFile
    mock_post_model.current_folder_node = 'current_folder_node'
    mock_post_model.parent_folder_id = 'parent_folder_id'
    mock_post_model.operator = 'operator'
    mock_post_model.data = 'data'
    mock_post_model.zone = 'cr'
    mock_post_model.job_type = 'job_type'

    try:
        await transfer_to_pre(mock_post_model, project_code, 'session_id')
        raise AssertionError()
    except Exception:
        assert True
