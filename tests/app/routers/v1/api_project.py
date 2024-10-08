# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import httpx
from common import has_file_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi_utils.cbv import cbv

from app.components.user.models import CurrentUser
from app.config import ConfigClass
from app.logger import logger
from app.models.base_models import EAPIResponseCode
from app.models.file_models import ItemStatus
from app.models.project_models import GetProjectFolderResponse
from app.models.project_models import POSTProjectFile
from app.models.project_models import POSTProjectFileResponse
from app.models.project_models import PreDownloadProjectFile
from app.models.project_models import ProjectListResponse
from app.models.project_models import ResumableResponse
from app.models.project_models import ResumableUploadPOST
from app.resources.authorization.decorator import cli_rules_enforcement
from app.resources.authorization.models import ValidAction
from app.resources.dependencies import jwt_required
from app.resources.dependencies import transfer_to_pre
from app.resources.error_handler import catch_internal
from app.resources.helpers import get_item_by_id
from app.resources.helpers import get_user_projects
from app.resources.helpers import get_zone
from app.resources.helpers import query_file_folder

router = APIRouter()
_API_TAG = 'V1 Projects'
_API_NAMESPACE = 'api_project'


@cbv(router)
class APIProject:

    current_identity: CurrentUser = Depends(jwt_required)

    @router.get(
        '/projects',
        tags=[_API_TAG],
        response_model=ProjectListResponse,
        summary='Get project list that user have access to',
    )
    @catch_internal(_API_NAMESPACE)
    async def list_project(self, page=0, page_size=10, order='created_at', order_by='desc'):
        """Get the project list that user have access to."""
        logger.info('API list_project'.center(80, '-'))
        api_response = ProjectListResponse()

        logger.info(f'User request with identity: {self.current_identity}')
        project_list = await get_user_projects(self.current_identity, page, page_size, order, order_by)

        logger.info(f'Getting user projects: {project_list}')
        logger.info(f'Number of projects: {len(project_list)}')
        api_response.result = project_list
        api_response.code = EAPIResponseCode.success
        return api_response.json_response()

    @router.post(
        '/project/{project_code}/files',
        response_model=POSTProjectFileResponse,
        summary='pre upload file to the target zone',
        tags=['V1 Files'],
    )
    @catch_internal(_API_NAMESPACE)
    @cli_rules_enforcement(ValidAction.UPLOAD)
    async def project_file_preupload(
        self,
        project_code,
        request: Request,
        data: POSTProjectFile,
    ):
        """PRE upload and check existence of file in project."""
        api_response = POSTProjectFileResponse()
        logger.info('API project_file_preupload'.center(80, '-'))

        item = await get_item_by_id(data.parent_folder_id)
        if not item:
            api_response.error_msg = 'Item not found'
            api_response.code = EAPIResponseCode.not_found
            return api_response

        if not await has_file_permission(ConfigClass.AUTH_SERVICE + '/v1/', item, 'upload', self.current_identity):
            error_msg = f'Unauthorized upload action on project {project_code}'
            logger.error(error_msg)
            api_response.error_msg = error_msg
            api_response.code = EAPIResponseCode.forbidden
            return api_response.json_response()

        elif len(data.folder_tags) > 0 and not await has_file_permission(
            ConfigClass.AUTH_SERVICE + '/v1/', item, 'annotate', self.current_identity
        ):
            error_msg = f'Unauthorized annotation action on project {project_code}'
            logger.error(error_msg)
            api_response.error_msg = error_msg
            api_response.code = EAPIResponseCode.forbidden
            return api_response.json_response()

        try:
            logger.info('Tansfering to pre upload')
            result = await transfer_to_pre(data, project_code, request.headers)
            logger.info(result.text)
            if result.status_code == 409:
                api_response.error_msg = result.json()['error_msg']
                api_response.code = EAPIResponseCode.conflict
                return api_response.json_response()
            elif result.status_code != 200:
                api_response.error_msg = 'Upload Error: ' + result.json()['error_msg']
                api_response.code = EAPIResponseCode.internal_error
                return api_response.json_response()
            else:
                api_response.result = result.json()['result']

            return api_response.json_response()
        except Exception as e:
            logger.error(f'Preupload error: {e}')
            raise e

    @router.post(
        '/project/{project_code}/files/resumable',
        response_model=ResumableResponse,
        summary='resumable upload check',
        tags=['V1 Files'],
    )
    @catch_internal(_API_NAMESPACE)
    @cli_rules_enforcement(ValidAction.UPLOAD)
    async def project_file_resumable(
        self,
        project_code,
        request: Request,
        data: ResumableUploadPOST,
    ):
        """
        Summary:
            the api to check the uploaded chunk in the object
            storage. Afterwards, cli will resume the previous
            upload.
        Parameter:
            - bucket(str): the unique code of bucket
            - zone(str): the greenromm or core
            - object_infos(List[ObjectInfo]): the list of pairs contains following:
                - object_path(str): the unique path in object storage
                - resumable_id(str): the unique identifier for resumable upload
        return:
            - result(list):
                - object_path(str): the unique path in object storage
                - resumable_id(str): the unique identifier for resumable upload
                - chunks_info(dict[str: str]): the pair of chunk_number: etag
        """
        api_response = POSTProjectFileResponse()
        logger.info('API project file resumable upload'.center(80, '-'))

        for x in data.object_infos:
            item = await get_item_by_id(x.item_id)
            if not await has_file_permission(ConfigClass.AUTH_SERVICE + '/v1/', item, 'upload', self.current_identity):
                error_msg = f'Unauthorized upload action on project {project_code}'
                logger.error(error_msg)
                api_response.error_msg = error_msg
                api_response.code = EAPIResponseCode.forbidden

                return api_response.json_response()

        try:
            logger.info('Tansfering to pre upload')
            async with httpx.AsyncClient() as client:
                url = ConfigClass.UPLOAD_SERVICE_GREENROOM + '/v1/files/resumable'
                payload = await request.json()
                headers = {
                    'authorization': request.headers.get('authorization'),
                }
                res = await client.post(url, headers=headers, json=payload, timeout=None)
                api_response.result = res.json().get('result', [])

            return api_response.json_response()
        except Exception as e:
            logger.error(f'resumable error: {e}')
            raise e

    @router.post(
        '/project/{project_code}/files/download',
        response_model=POSTProjectFileResponse,
        summary='pre download file from the target zone',
        tags=['V1 Files'],
    )
    @cli_rules_enforcement(ValidAction.DOWNLOAD)
    @catch_internal(_API_NAMESPACE)
    async def project_file_predownload(
        self,
        project_code,
        request: Request,
        data: PreDownloadProjectFile,
    ):
        """PRE upload and check existence of file in project."""
        api_response = POSTProjectFileResponse()

        logger.info('API project_file_preupload'.center(80, '-'))
        logger.info(
            f'User request with identity: \
            {self.current_identity}'
        )

        for x in data.files:
            item = await get_item_by_id(x.id)
            if not await has_file_permission(
                ConfigClass.AUTH_SERVICE + '/v1/', item, 'download', self.current_identity
            ):
                error_msg = f'Unauthorized download action on project {project_code}'
                logger.error(error_msg)
                api_response.error_msg = error_msg
                api_response.code = EAPIResponseCode.forbidden
                return api_response.json_response()

        try:
            if data.zone == ConfigClass.GREEN_ZONE_LABEL.lower():
                url = ConfigClass.DOWNLOAD_SERVICE_GREENROOM + '/v2/download/pre/'
            else:
                url = ConfigClass.DOWNLOAD_SERVICE_CORE + '/v2/download/pre/'
            async with httpx.AsyncClient() as client:
                headers = {
                    'Session-ID': request.headers.get('Session-ID'),
                    'authorization': request.headers.get('authorization'),
                }
                payload = {
                    'files': [dict(x) for x in data.files],
                    'zone': data.zone,
                    'operator': data.operator,
                    'container_code': data.container_code,
                    'container_type': data.container_type,
                }
                result = await client.post(url, headers=headers, json=payload)
                if result.status_code != 200:
                    raise Exception(result.json().get('error_msg'))

            return result.json()
        except Exception as e:
            api_response.error_msg = f'Download service error: {e}'
            api_response.code = EAPIResponseCode.bad_request
            return api_response.json_response()

    @router.get(
        '/project/{project_code}/search',
        tags=[_API_TAG],
        response_model=GetProjectFolderResponse,
        summary='Get item in the project',
    )
    @catch_internal(_API_NAMESPACE)
    async def get_project_item(self, project_code, zone, path, item_type, container_type, request: Request):
        """Get item in project."""
        api_response = GetProjectFolderResponse()

        logger.info('API get_project_item'.center(80, '-'))
        logger.info(f'User request identity: {self.current_identity}')

        folder_path = path.strip('/').split('/')
        parent_path = '/'.join(folder_path[0:-1])
        folder_name = folder_path[-1]

        folder_check_event = {
            'container_code': project_code,
            'container_type': container_type,
            'parent_path': parent_path,
            'recursive': False,
            'zone': get_zone(zone),
            'status': ItemStatus.ACTIVE,
            'name': folder_name,
        }
        if item_type:
            folder_check_event['type'] = item_type
        logger.info(f'Folder check event: {folder_check_event}')
        folder_response = await query_file_folder(folder_check_event, request)
        logger.info(f'Folder check response: {folder_response.text}')
        response = folder_response.json()

        if folder_response.status_code == 500:
            error = response.get('error_msg')
            error_msg = f'Error Getting Folder: {error}'
            response_code = EAPIResponseCode.internal_error
            result = ''
        elif folder_response.status_code == 404:
            error_msg = 'Error Getting Folder: not found'
            response_code = EAPIResponseCode.not_found
            result = ''
        else:
            res = response.get('result')
            logger.info(f'res: {res}')

            if res:
                result = res[0]
                response_code = EAPIResponseCode.success
                error_msg = ''
            else:
                result = res
                response_code = EAPIResponseCode.not_found
                error_msg = 'Folder not exist'

        logger.info(f'error_msg: {error_msg}')
        api_response.result = result
        api_response.code = response_code
        api_response.error_msg = error_msg
        return api_response.json_response()
