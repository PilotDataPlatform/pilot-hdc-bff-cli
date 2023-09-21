# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum

from pydantic import BaseModel
from pydantic import Field

from .base_models import APIResponse


class ItemStatus(str, Enum):
    """The new enum type for file status
        - REGISTERED means file is created by upload service but not complete yet. either in progress or fail.
        - ACTIVE means file uploading is complete.
        - ARCHIVED means the file has been deleted."""

    REGISTERED = 'REGISTERED'
    ACTIVE = 'ACTIVE'
    ARCHIVED = 'ARCHIVED'

    def __str__(self):
        return '%s' % self.name


class GetProjectFileList(BaseModel):
    project_code: str
    zone: str
    folder: str
    source_type: str


class GetProjectFileListResponse(APIResponse):
    result: dict = Field(
        {},
        example={
            'code': 200,
            'error_msg': '',
            'result': [
                {
                    'id': 6127,
                    'labels': ['File', 'Greenroom'],
                    'global_entity_id': 'baee1ca0-37a5-4c9b-afcb-1b2d4b2447aa',
                    'project_code': 'sampleproject',
                    'operator': 'admin',
                    'file_size': 1048576,
                    'tags': [],
                    'list_priority': 20,
                    'status': ItemStatus.ARCHIVED,
                    'path': '/data/core-storage/sampleproject/raw/folders1',
                    'time_lastmodified': '2021-05-18T14:34:21',
                    'process_pipeline': '',
                    'uploader': 'admin',
                    'parent_folder_geid': 'c1c3766f-36bd-42db-8ca5-9040726cbc03',
                    'name': 'Testdateiäöüßs2',
                    'time_created': '2021-05-18T14:34:21',
                    'guid': '4e06b8c5-8235-476e-b818-1ea5b0f0043c',
                    'full_path': '/data/core-storage/sampleproject/...',
                },
                {
                    'id': 2842,
                    'labels': ['Greenroom', 'Folder'],
                    'folder_level': 1,
                    'global_entity_id': '7a71ed22-9cd0-465e-a18e-b66fda2c4e04',
                    'list_priority': 10,
                    'folder_relative_path': 'folders1',
                    'time_lastmodified': '2021-05-11T20:17:51',
                    'uploader': 'admin',
                    'name': 'folders',
                    'time_created': '2021-05-11T20:17:51',
                    'project_code': 'sampleproject',
                    'tags': [],
                },
            ],
        },
    )


class QueryDataInfo(BaseModel):
    geid: list


class QueryDataInfoResponse(APIResponse):
    result: dict = Field(
        {},
        example={
            'code': 200,
            'error_msg': '',
            'result': [
                {'status': 'Permission Denied', 'result': [], 'geid': '2b60f036-9642-44e7-883b-c8ed247b1152'},
                {
                    'status': 'success',
                    'result': [
                        {
                            'id': 23279,
                            'labels': ['Greenroom', 'File'],
                            'global_entity_id': '3586fa29-4a68-b833-...',
                            'display_path': 'admin/Testdateiäöüßs14',
                            'project_code': 'sampleproject',
                            'version_id': '08cac0b1-75cf-4c2e-8bed-c43fa99d682f',
                            'operator': 'admin',
                            'file_size': 1048576,
                            'tags': [],
                            'status': ItemStatus.ARCHIVED,
                            'list_priority': 20,
                            'path': '/data/core-storage/sampleproject/admin',
                            'time_lastmodified': '2021-07-29T18:18:00',
                            'process_pipeline': '',
                            'uploader': 'admin',
                            'parent_folder_geid': '22508bda-4a76-...',
                            'name': 'Testdateiäöüßs14',
                            'time_created': '2021-07-29T18:18:00',
                            'guid': '12e23fb5-51d5-4ee9-8fb4-78fe9f9810d9',
                            'location': 'minio://http://minio.minio:...',
                            'full_path': '/data/core-storage/sampleproject/...',
                        }
                    ],
                    'geid': '3586fa29-18ef-4a68-b833-5c04d3c2831c',
                },
                {'status': 'Permission Denied', 'result': [], 'geid': 'a17fcf3a-179c-4099-a607-1438464527e2'},
                {'status': 'File Not Exist', 'result': [], 'geid': '80c08693-9ac8-4b94-bb02-9aebe0ec9f20'},
            ],
        },
    )
