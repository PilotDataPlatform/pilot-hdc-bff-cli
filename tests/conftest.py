# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re

import jwt
import pytest
import pytest_asyncio
from async_asgi_testclient import TestClient as TestAsyncClient
from cryptography.hazmat.backends import default_backend as crypto_default_backend

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Request
from pydantic import BaseModel

from app.config import ConfigClass
from app.main import create_app
from app.resources.dependencies import jwt_required

key = rsa.generate_private_key(backend=crypto_default_backend(), public_exponent=65537, key_size=2048)


CLI_PRIVATE_KEY = key.private_bytes(
    crypto_serialization.Encoding.PEM, crypto_serialization.PrivateFormat.PKCS8, crypto_serialization.NoEncryption()
)


ConfigClass.CLI_PUBLIC_KEY = key.public_key().public_bytes(
    crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
)


@pytest_asyncio.fixture
async def test_async_client():
    app = create_app()
    app.dependency_overrides[jwt_required] = jwt_required
    async with TestAsyncClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def test_async_client_auth():
    """Create client with mock auth token."""
    app = create_app()
    app.dependency_overrides[jwt_required] = override_jwt_required
    client = TestAsyncClient(app)
    return client


@pytest.fixture
def test_async_client_project_member_auth():
    """Create client with mock auth token for project api only."""
    from run import app

    client = TestAsyncClient(app)
    security = HTTPAuthorizationCredentials
    app.dependency_overrides[jwt_required] = override_member_jwt_required
    return client


@pytest.fixture
def mock_cli_rules_app():
    """Create a test client for cli rules ONLY."""
    from fastapi import FastAPI

    from app.models.project_models import POSTProjectFile
    from app.resources.authorization.decorator import cli_rules_enforcement
    from app.resources.authorization.models import ValidAction

    test_cli_rules_app = FastAPI()

    @test_cli_rules_app.post('/v1/test/{project_code}/files/upload')
    @cli_rules_enforcement(ValidAction.UPLOAD)
    async def test_func_upload(project_code: str, request: Request, data: POSTProjectFile):
        return True

    @test_cli_rules_app.post('/v1/test/{project_code}/files/download')
    @cli_rules_enforcement(ValidAction.DOWNLOAD)
    async def test_func_download(project_code: str, request: Request, data: POSTProjectFile):
        return True

    return TestAsyncClient(test_cli_rules_app)


@pytest.fixture
async def mock_VM_info():
    vm_info_gr = {'ip': '', 'project_code': 'test_project', 'zone': ConfigClass.GREEN_ZONE_LABEL}
    vm_info_cr = {'ip': '', 'project_code': 'test_project', 'zone': ConfigClass.CORE_ZONE_LABEL}
    hash_code_gr = jwt.encode(vm_info_gr, key=CLI_PRIVATE_KEY, algorithm='RS256')
    hash_code_cr = jwt.encode(vm_info_cr, key=CLI_PRIVATE_KEY, algorithm='RS256')

    vm_info_gr_ip = {'ip': 'some_ip', 'project_code': 'test_project', 'zone': ConfigClass.GREEN_ZONE_LABEL}
    vm_info_cr_ip = {'ip': 'some_ip', 'project_code': 'test_project', 'zone': ConfigClass.CORE_ZONE_LABEL}
    hash_code_gr_ip = jwt.encode(vm_info_gr_ip, key=CLI_PRIVATE_KEY, algorithm='RS256')
    hash_code_cr_ip = jwt.encode(vm_info_cr_ip, key=CLI_PRIVATE_KEY, algorithm='RS256')

    hash_code = {
        ConfigClass.GREEN_ZONE_LABEL: hash_code_gr,
        ConfigClass.CORE_ZONE_LABEL: hash_code_cr,
        ConfigClass.GREEN_ZONE_LABEL + '_ip': hash_code_gr_ip,
        ConfigClass.CORE_ZONE_LABEL + '_ip': hash_code_cr_ip,
    }
    return hash_code


# Mock for the permission
async def override_jwt_required(request: Request):
    return {
        'code': 200,
        'user_id': 1,
        'username': 'testuser',
        'role': 'admin',
        'token': 'fake token',
        'realm_roles': ['platform-admin'],
    }


async def override_member_jwt_required(request: Request):
    return {
        'code': 200,
        'user_id': 1,
        'username': 'testuser',
        'role': 'contributor',
        'token': 'fake token',
        'realm_roles': ['testproject-contributor'],
    }


class HTTPAuthorizationCredentials(BaseModel):
    credentials: str = 'fake_token'


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    monkeypatch.setattr(ConfigClass, 'GREEN_ZONE_LABEL', 'gr')
    monkeypatch.setattr(ConfigClass, 'CORE_ZONE_LABEL', 'cr')
    monkeypatch.setattr(ConfigClass, 'UPLOAD_SERVICE_CORE', 'http://data_upload_cr')
    monkeypatch.setattr(ConfigClass, 'UPLOAD_SERVICE_GREENROOM', 'http://data_upload_gr')
    monkeypatch.setattr(ConfigClass, 'AUTH_SERVICE', 'http://auth')
    monkeypatch.setattr(ConfigClass, 'METADATA_SERVICE', 'http://metadata_service')
    monkeypatch.setattr(ConfigClass, 'DATASET_SERVICE', 'http://dataset_service')


@pytest.fixture
def has_permission_true(httpx_mock):
    url = re.compile('^http://auth/v1/authorize.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})


@pytest.fixture
def has_permission_false(httpx_mock):
    url = re.compile('^http://auth/v1/authorize.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': False}})
