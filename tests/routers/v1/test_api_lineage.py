# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest

pytestmark = pytest.mark.asyncio
test_lineage_api = '/v1/lineage'


async def test_create_lineage_return_200(test_async_client_auth, mocker):
    payload = {
        'project_code': 'test_project',
        'input_id': 'fake_input_id',
        'output_id': 'fake_output_id',
        'input_path': 'fake/path/test.txt',
        'output_path': 'fake/path/destination/test.txt',
        'action_type': 'copy',
        'description': 'Test lineage',
    }
    header = {'Authorization': 'fake token'}
    mocker.patch('app.clients.lineage.LineageClient.create_lineage', return_value=None)
    res = await test_async_client_auth.post(test_lineage_api, headers=header, json=payload)
    assert res.status_code == 200


async def test_create_lineage_with_internal_error_return_500(test_async_client_auth, mocker):
    payload = {
        'project_code': 'test_project',
        'input_id': 'fake_input_id',
        'output_id': 'fake_output_id',
        'input_path': 'fake/path/test.txt',
        'output_path': 'fake/path/destination/test.txt',
        'action_type': 'copy',
        'description': 'Test lineage',
    }
    header = {'Authorization': 'fake token'}
    mocker.patch('app.clients.lineage.LineageClient.create_lineage', side_effect=Exception('ID not found'))
    res = await test_async_client_auth.post(test_lineage_api, headers=header, json=payload)
    assert res.status_code == 500
