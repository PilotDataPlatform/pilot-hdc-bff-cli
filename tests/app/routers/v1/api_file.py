# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import has_file_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi_utils.cbv import cbv

from app.components.user.models import CurrentUser
from app.config import ConfigClass
from app.logger import logger

from ...models.file_models import GetProjectFileListResponse
from ...models.file_models import ItemStatus
from ...models.file_models import QueryDataInfo
from ...models.file_models import QueryDataInfoResponse
from ...resources.dependencies import get_project_role
from ...resources.dependencies import jwt_required
from ...resources.error_handler import EAPIResponseCode
from ...resources.error_handler import ECustomizedError
from ...resources.error_handler import catch_internal
from ...resources.error_handler import customized_error_template
from ...resources.helpers import batch_query_node_by_geid
from ...resources.helpers import get_zone
from ...resources.helpers import query_file_folder

router = APIRouter()
_API_TAG = 'V1 files'
_API_NAMESPACE = 'api_files'


@cbv(router)
class APIFile:
    current_identity: CurrentUser = Depends(jwt_required)

    @router.post(
        '/query/geid',
        tags=[_API_TAG],
        response_model=QueryDataInfoResponse,
        summary='Query file/folder information by geid',
    )
    @catch_internal(_API_NAMESPACE)
    async def query_file_folders_by_geid(self, data: QueryDataInfo):
        """Get file/folder information by geid."""
        file_response = QueryDataInfoResponse()

        geid_list = data.geid
        logger.info('API /query/geid'.center(80, '-'))
        logger.info(f'Received information geid: {geid_list}')
        logger.info(f'User identity: {self.current_identity}')
        response_list = []
        located_geid, query_result = await batch_query_node_by_geid(geid_list)
        for global_entity_id in geid_list:
            logger.info(f'Query geid: {global_entity_id}')
            result = {}
            if global_entity_id not in located_geid:
                status = customized_error_template(ECustomizedError.FILE_NOT_FOUND)
                logger.info(f'status: {status}')
            elif query_result[global_entity_id].get('status') == ItemStatus.ARCHIVED:
                status = customized_error_template(ECustomizedError.FILE_FOLDER_ONLY)
                logger.info(f'status: {status}')
            else:
                logger.info(f'Query result: {query_result[global_entity_id]}')

                permission = await has_file_permission(
                    ConfigClass.AUTH_SERVICE + '/v1/', query_result[global_entity_id], 'view', self.current_identity
                )
                if not permission:
                    status = customized_error_template(ECustomizedError.PERMISSION_DENIED)
                else:
                    status = 'success'
                    result = query_result[global_entity_id]
            response_list.append({'status': status, 'result': result, 'geid': global_entity_id})

        logger.info(f'Query file/folder result: {response_list}')
        file_response.result = response_list
        file_response.code = EAPIResponseCode.success
        return file_response.json_response()

    @router.get(
        '/{project_code}/files/query',
        tags=[_API_TAG],
        response_model=GetProjectFileListResponse,
        summary='Get files and folders in the project/folder',
    )
    @catch_internal(_API_NAMESPACE)
    async def get_file_folders(self, project_code, zone, folder, source_type, page, page_size, request: Request):
        """List files and folders in project."""
        logger.info('API file_list_query'.center(80, '-'))
        file_response = GetProjectFileListResponse()

        zone = get_zone(zone)
        project_role = get_project_role(self.current_identity, project_code)
        logger.info(
            f'project_role in ["admin", "platform-admin"]: \
                {project_role in ["admin", "platform-admin"]}'
        )

        params = {
            'container_code': project_code,
            'container_type': source_type.lower(),
            'recursive': False,
            'zone': zone,
            'status': ItemStatus.ACTIVE,
            'page': page,
            'page_size': page_size,
            'order': 'desc',
        }
        if folder:
            params['parent_path'] = folder
        logger.info(f'Query node payload: {params}')
        folder_info = await query_file_folder(params, request)
        logger.info(f'folder_info: {folder_info}')
        response = folder_info.json()
        logger.info(f'folder_response: {response}')
        if response.get('code') != 200:
            file_response.result = response.get('result')
            file_response.code = EAPIResponseCode.internal_error
            file_response.error_msg = 'Error Getting Folder: ' + response.get('error_msg')
            return file_response.json_response()
        else:
            file_response.result = response.get('result')
            file_response.code = EAPIResponseCode.success
            file_response.error_msg = response.get('error_msg')
            return file_response.json_response()
