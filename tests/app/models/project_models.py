# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict
from typing import List

from pydantic import BaseModel
from pydantic import Field

from .base_models import APIResponse


class ProjectListResponse(APIResponse):
    """Project list response class."""

    result: dict = Field(
        {},
        example={
            'code': 200,
            'error_msg': '',
            'result': [
                {'name': 'Sample project 1', 'code': 'sampleproject1'},
                {'name': 'Sample Project 2', 'code': 'sampleproject2'},
            ],
        },
    )


class POSTProjectFileResponse(APIResponse):
    result: dict = Field({}, example={'code': 200, 'error_msg': '', 'result': {}})


class ResumableResponse(APIResponse):
    result: dict


class POSTProjectFile(BaseModel):
    operator: str
    job_type: str
    zone: str
    current_folder_node: str
    parent_folder_id: str
    data: List[Dict[str, Any]]
    folder_tags: List[str] = []


class ResumableUploadPOST(BaseModel):
    """Pre upload payload model."""

    class ObjectInfo(BaseModel):
        object_path: str
        resumable_id: str
        item_id: str

    bucket: str
    zone: str
    object_infos: List[ObjectInfo]


class PreDownloadProjectFile(BaseModel):
    class DownloadFileList(BaseModel):
        id: str

    files: List[DownloadFileList]
    zone: str
    operator: str
    container_code: str
    container_type: str


class GetProjectRoleResponse(APIResponse):
    result: dict = Field({}, example={'code': 200, 'error_msg': '', 'result': 'role'})


class GetProjectFolder(BaseModel):
    project_code: str
    zone: str
    folder: str
    relative_path: str


class GetProjectFolderResponse(APIResponse):
    result: dict = Field(
        {},
        example={
            'code': 200,
            'error_msg': '',
            'result': {
                'id': 1552,
                'labels': ['Greenroom', 'Folder'],
                'global_entity_id': 'bc8b4239-b22a-47dd-9d23-36ade331ebbf',
                'folder_level': 1,
                'list_priority': 10,
                'folder_relative_path': 'cli_folder_test23',
                'time_lastmodified': '2021-05-10T22:18:29',
                'uploader': 'admin',
                'name': 'folder_test',
                'time_created': '2021-05-10T22:18:29',
                'project_code': 'sampleproject',
                'tags': [],
            },
        },
    )
