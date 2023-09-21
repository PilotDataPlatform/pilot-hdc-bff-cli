# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest

from app.config import ConfigClass
from app.models.project_models import POSTProjectFile
from app.resources.authorization.decorator import VM_info_enforcement
from app.resources.authorization.decorator import zone_enforcement
from app.resources.authorization.exceptions import InvalidAction
from app.resources.authorization.exceptions import ProjectCodeMismacthed
from app.resources.authorization.exceptions import SourceIpMismatched
from app.resources.authorization.models import ValidAction


@pytest.mark.asyncio
async def test_cli_rules_enforcement_greenroom_pass(mock_VM_info, mock_cli_rules_app, mocker):

    # test on upload to greenroom
    project_code = 'test_project'
    headers = {'vm-info': mock_VM_info.get(ConfigClass.GREEN_ZONE_LABEL)}
    data_gr = POSTProjectFile(
        operator='',
        job_type='',
        parent_folder_id='parent_folder_id',
        filename='test_file',
        current_folder_node='admin',
        zone=ConfigClass.GREEN_ZONE_LABEL,
        data=[],
    )

    try:
        res = await mock_cli_rules_app.post(
            f'/v1/test/{project_code}/files/upload', json=dict(data_gr), headers=headers
        )
        assert res.status_code == 200
    except Exception:
        raise AssertionError()

    # test on download from greenroom
    try:
        res = await mock_cli_rules_app.post(
            f'/v1/test/{project_code}/files/download', json=dict(data_gr), headers=headers
        )
        assert res.status_code == 200
    except Exception:
        raise AssertionError()


@pytest.mark.asyncio
async def test_cli_rules_enforcement_core_pass(mock_VM_info, mock_cli_rules_app, mocker):

    # test on upload to core
    project_code = 'test_project'
    headers = {'vm-info': mock_VM_info.get(ConfigClass.CORE_ZONE_LABEL)}
    data_gr = POSTProjectFile(
        operator='',
        job_type='',
        parent_folder_id='parent_folder_id',
        filename='test_file',
        current_folder_node='admin',
        zone=ConfigClass.CORE_ZONE_LABEL,
        data=[],
    )

    try:
        res = await mock_cli_rules_app.post(
            f'/v1/test/{project_code}/files/upload', json=dict(data_gr), headers=headers
        )
        assert res.status_code == 200
    except Exception:
        raise AssertionError()

    # test on download from greenroom
    try:
        res = await mock_cli_rules_app.post(
            f'/v1/test/{project_code}/files/download', json=dict(data_gr), headers=headers
        )
        assert res.status_code == 200
    except Exception:
        raise AssertionError()


@pytest.mark.asyncio
async def test_cli_rules_enforcement_block_wrong_ip(mock_VM_info, mock_cli_rules_app, mocker):

    # test on upload to core
    project_code = 'test_project'
    headers = {'vm-info': mock_VM_info.get(ConfigClass.GREEN_ZONE_LABEL + '_ip')}
    data_gr = POSTProjectFile(
        operator='',
        job_type='',
        parent_folder_id='parent_folder_id',
        filename='test_file',
        current_folder_node='admin',
        zone=ConfigClass.GREEN_ZONE_LABEL,
        data=[],
    )

    try:
        res = await mock_cli_rules_app.post(
            f'/v1/test/{project_code}/files/upload', json=dict(data_gr), headers=headers
        )
        assert res.status_code == 403
        assert res.json().get('error_msg') == 'The ip of VM does not matched with source ip'
    except Exception:
        raise AssertionError()


@pytest.mark.asyncio
async def test_cli_rules_enforcement_block_wrong_project(mock_VM_info, mock_cli_rules_app, mocker):

    # test on upload to core
    project_code = 'test_wrong_project'
    headers = {'vm-info': mock_VM_info.get(ConfigClass.GREEN_ZONE_LABEL)}
    data_gr = POSTProjectFile(
        operator='',
        job_type='',
        parent_folder_id='parent_folder_id',
        filename='test_file',
        current_folder_node='admin',
        zone=ConfigClass.GREEN_ZONE_LABEL,
        data=[],
    )

    try:
        res = await mock_cli_rules_app.post(
            f'/v1/test/{project_code}/files/upload', json=dict(data_gr), headers=headers
        )
        assert res.status_code == 403
        assert res.json().get('error_msg') == 'The project of VM does not matched with query'
    except Exception:
        raise AssertionError()


# zone_enforcement test


@pytest.mark.asyncio
async def test_zone_enforcement_greenroom_download():
    # greenroom should able to only download from greenroom
    try:
        await zone_enforcement(ConfigClass.GREEN_ZONE_LABEL, ValidAction.DOWNLOAD, ConfigClass.GREEN_ZONE_LABEL)
    except Exception:
        raise AssertionError()

    try:
        await zone_enforcement(ConfigClass.GREEN_ZONE_LABEL, ValidAction.DOWNLOAD, ConfigClass.CORE_ZONE_LABEL)
    except InvalidAction:
        assert True
    except Exception:
        raise AssertionError()


@pytest.mark.asyncio
async def test_zone_enforcement_greenroom_upload():
    # greenroom should able to only upload to greenroom
    try:
        await zone_enforcement(ConfigClass.GREEN_ZONE_LABEL, ValidAction.UPLOAD, ConfigClass.GREEN_ZONE_LABEL)
    except Exception:
        raise AssertionError()

    try:
        await zone_enforcement(ConfigClass.GREEN_ZONE_LABEL, ValidAction.UPLOAD, ConfigClass.CORE_ZONE_LABEL)
    except InvalidAction:
        assert True
    except Exception:
        raise AssertionError()


@pytest.mark.asyncio
async def test_zone_enforcement_core_download():
    # core should able to only download from core
    try:
        await zone_enforcement(ConfigClass.CORE_ZONE_LABEL, ValidAction.DOWNLOAD, ConfigClass.GREEN_ZONE_LABEL)
    except InvalidAction:
        assert True
    except Exception:
        raise AssertionError()

    try:
        await zone_enforcement(ConfigClass.CORE_ZONE_LABEL, ValidAction.DOWNLOAD, ConfigClass.CORE_ZONE_LABEL)
    except Exception:
        raise AssertionError()


@pytest.mark.asyncio
async def test_zone_enforcement_core_upload():
    # core should able to upload greenroom zone
    try:
        await zone_enforcement(ConfigClass.CORE_ZONE_LABEL, ValidAction.UPLOAD, ConfigClass.GREEN_ZONE_LABEL)
    except Exception:
        raise AssertionError()

    # core should able to upload core zone
    try:
        await zone_enforcement(ConfigClass.CORE_ZONE_LABEL, ValidAction.UPLOAD, ConfigClass.CORE_ZONE_LABEL)
    except Exception:
        raise AssertionError()


#


@pytest.mark.asyncio
async def test_VM_info_enforcement_pass():
    vm_info = {'ip': 'test_ip', 'project_code': 'test_project', 'zone': ConfigClass.GREEN_ZONE_LABEL}
    try:
        await VM_info_enforcement(vm_info, 'test_ip', 'test_project')
    except Exception:
        raise AssertionError()


@pytest.mark.asyncio
async def test_VM_info_enforcement_ip_mismatch():
    vm_info = {'ip': 'test_ip', 'project_code': 'test_project', 'zone': ConfigClass.GREEN_ZONE_LABEL}
    try:
        await VM_info_enforcement(vm_info, 'test_ip_not_matched', 'test_project')
    except SourceIpMismatched:
        assert True
    except Exception:
        raise AssertionError()


@pytest.mark.asyncio
async def test_VM_info_enforcement_project_code_mismatch():
    vm_info = {'ip': 'test_ip', 'project_code': 'test_project', 'zone': ConfigClass.GREEN_ZONE_LABEL}
    try:
        await VM_info_enforcement(vm_info, 'test_ip', 'test_project_not_matched')
    except ProjectCodeMismacthed:
        assert True
    except Exception:
        raise AssertionError()
