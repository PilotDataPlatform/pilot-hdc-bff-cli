# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LoggerFactory
from common import has_file_permission
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi_utils.cbv import cbv

from app.config import ConfigClass

from ...models.file_models import ItemStatus
from ...models.manifest_models import ManifestAttachPost
from ...models.manifest_models import ManifestAttachResponse
from ...models.manifest_models import ManifestExportResponse
from ...models.manifest_models import ManifestListResponse
from ...resources.dependencies import jwt_required
from ...resources.error_handler import EAPIResponseCode
from ...resources.error_handler import ECustomizedError
from ...resources.error_handler import catch_internal
from ...resources.error_handler import customized_error_template
from ...resources.helpers import Annotations
from ...resources.helpers import get_attribute_templates
from ...resources.helpers import get_user_projects
from ...resources.helpers import get_zone
from ...resources.helpers import query_file_folder
from ...resources.helpers import separate_rel_path
from ...resources.validation_service import ManifestValidator

router = APIRouter()


@cbv(router)
class APIManifest:
    _API_TAG = 'V1 Manifest'
    _API_NAMESPACE = 'api_manifest'

    def __init__(self):
        self._logger = LoggerFactory(
            self._API_NAMESPACE,
            level_default=ConfigClass.LOG_LEVEL_DEFAULT,
            level_file=ConfigClass.LOG_LEVEL_FILE,
            level_stdout=ConfigClass.LOG_LEVEL_STDOUT,
            level_stderr=ConfigClass.LOG_LEVEL_STDERR,
        ).get_logger()

    @router.get(
        '/manifest',
        tags=[_API_TAG],
        response_model=ManifestListResponse,
        summary='Get manifest list by project code',
    )
    @catch_internal(_API_NAMESPACE)
    async def list_manifest(self, project_code: str, current_identity: dict = Depends(jwt_required)):
        api_response = ManifestListResponse()
        try:
            _ = current_identity['username']
        except (AttributeError, TypeError):
            return current_identity

        project_list = await get_user_projects(current_identity)
        if project_code not in [x.get('code') for x in project_list]:
            api_response.code = EAPIResponseCode.forbidden
            api_response.error_msg = 'User is not the member of the project'
            return api_response.json_response()

        self._logger.info('API list_manifest'.center(80, '-'))
        self._logger.info(f'User request with identity: {current_identity}')
        self._logger.info(f'User request information: project_code: {project_code}')
        try:
            response = await get_attribute_templates(project_code)
            manifest_list = response.get('result')
            status_code = response.get('code')
            if status_code != 200:
                api_response.error_msg = 'Cannot get manifest'
                api_response.code = EAPIResponseCode.internal_error
                return api_response.json_response()

            self._logger.info(f'Getting manifest list: {manifest_list}')
            api_response.result = manifest_list
            api_response.code = EAPIResponseCode.success
            return api_response.json_response()
        except Exception as e:
            self._logger.error(f'Error listing manifest: {e}')
            api_response.code = EAPIResponseCode.internal_error
            api_response.error_msg = str(e)
            return api_response.json_response()

    @router.post(
        '/manifest/attach',
        tags=[_API_TAG],
        response_model=ManifestAttachResponse,
        summary='Attach manifest to file',
    )
    @catch_internal(_API_NAMESPACE)
    async def attach_manifest(
        self, data: ManifestAttachPost, request: Request, current_identity: dict = Depends(jwt_required)
    ):
        """CLI will call manifest validation API before attach manifest to file after uploading process."""
        api_response = ManifestAttachResponse()
        manifest_name = data.manifest_name
        project_code = data.project_code
        attributes = data.attributes
        zone = data.zone
        file_path = data.file_name
        try:
            _ = current_identity['username']
        except (AttributeError, TypeError):
            return current_identity
        self._logger.info('API attach_manifest'.center(80, '-'))
        self._logger.info(f'User request with identity: {current_identity}')

        parent_path, file_name = separate_rel_path(file_path)
        file_info = {
            'container_code': project_code,
            'container_type': 'project',
            'parent_path': parent_path,
            'recursive': False,
            'zone': get_zone(zone),
            'status': ItemStatus.ACTIVE,
            'name': file_name,
        }
        file_response = await query_file_folder(file_info, request)
        self._logger.info(f'Query result: {file_response.text}')
        file_node = file_response.json().get('result')
        if not file_node:
            api_response.error_msg = customized_error_template(ECustomizedError.FILE_NOT_FOUND)
            api_response.code = EAPIResponseCode.not_found
            return api_response.json_response()
        else:
            global_entity_id = file_node[0].get('id')
            file_type = file_node[0].get('type')

        try:
            if not await has_file_permission(
                ConfigClass.AUTH_SERVICE + '/v1/', file_node[0], 'annotate', current_identity
            ):
                api_response.error_msg = 'Permission denied'
                api_response.code = EAPIResponseCode.forbidden
                return api_response.json_response()
        except KeyError as e:
            self._logger.error(f'Missing information error: {str(e)}')
            api_response.error_msg = customized_error_template(ECustomizedError.MISSING_INFO) % str(e)
            api_response.code = EAPIResponseCode.bad_request
            api_response.result = str(e)
            return api_response.json_response()

        self._logger.info(f'Globale entity id for {file_name}: {global_entity_id}')
        self._logger.info(f'File {file_name} file_type by {file_type}')
        annotation_func = getattr(Annotations, f'attach_manifest_to_{file_type}')
        filter_template_res = await get_attribute_templates(project_code, manifest_name)

        self._logger.info(f'filter_template_res: {filter_template_res}')
        target_manifest = filter_template_res.get('result')
        if target_manifest:
            target_attribute = target_manifest[0].get('attributes')
            self._logger.info(f'target_attribute: {target_attribute}')
            validator = ManifestValidator(attributes, target_attribute)
            attribute_validation_error_msg = await validator.has_valid_attributes()
            if attribute_validation_error_msg:
                self._logger.error(f'attribute_validation_error_msg: {attribute_validation_error_msg}')
                api_response.error_msg = attribute_validation_error_msg
                api_response.result = ''
                api_response.code = EAPIResponseCode.bad_request
                return api_response.json_response()
        else:
            self._logger.error(f'Invalid manifest: {target_manifest}')
            api_response.error_msg = f'Manifest Not Exist {manifest_name}'
            api_response.result = ''
            api_response.code = EAPIResponseCode.bad_request
            return api_response.json_response()
        manifest_id = filter_template_res.get('result')[0].get('id')
        self._logger.info(f'manifest_id: {manifest_id}')
        annotation_event = {
            'global_entity_id': global_entity_id,
            'manifest_id': manifest_id,
            'attributes': attributes,
        }
        response = await annotation_func(annotation_event)
        self._logger.info(f'Attach manifest result: {response}')
        if not response:
            api_response.error_msg = customized_error_template(ECustomizedError.FILE_NOT_FOUND)
            api_response.code = EAPIResponseCode.not_found
            return api_response.json_response()
        else:
            api_response.result = response
            api_response.code = EAPIResponseCode.success
            return api_response.json_response()

    @router.get(
        '/manifest/export',
        tags=[_API_TAG],
        response_model=ManifestExportResponse,
        summary='Export manifest from project',
    )
    @catch_internal(_API_NAMESPACE)
    async def export_manifest(
        self,
        project_code,
        name,
        current_identity: dict = Depends(jwt_required),
    ):
        """Export manifest from the project."""
        api_response = ManifestExportResponse()
        try:
            _ = current_identity['username']
        except (AttributeError, TypeError):
            return current_identity
        self._logger.info('API export_manifest'.center(80, '-'))
        self._logger.info(f'User request with identity: {current_identity}')

        project_list = await get_user_projects(current_identity)
        if project_code not in [x.get('code') for x in project_list]:
            api_response.code = EAPIResponseCode.forbidden
            api_response.error_msg = 'User is not the member of the project'
            return api_response.json_response()

        manifest_res = await get_attribute_templates(project_code, name)
        manifest = manifest_res.get('result')
        self._logger.info(f'Matched manifest: {manifest}')
        self._logger.info(f'not manifest: {not manifest}')
        if not manifest:
            api_response.code = EAPIResponseCode.not_found
            api_response.error_msg = customized_error_template(ECustomizedError.MANIFEST_NOT_FOUND) % name
            return api_response.json_response()
        else:
            self._logger.debug(f'Attributes result {manifest}')
            self._logger.info(f'Attributes result {manifest}')
            api_response.code = EAPIResponseCode.success
            api_response.result = manifest
            return api_response.json_response()
