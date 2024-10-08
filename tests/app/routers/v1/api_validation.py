# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi_utils.cbv import cbv

from app.components.user.models import CurrentUser
from app.config import ConfigClass
from app.logger import logger
from app.models.error_model import InvalidEncryptionError
from app.resources.helpers import get_attribute_templates
from app.resources.helpers import get_user_projects

from ...models.validation_models import EnvValidatePost
from ...models.validation_models import EnvValidateResponse
from ...models.validation_models import ManifestValidatePost
from ...models.validation_models import ManifestValidateResponse
from ...resources.dependencies import jwt_required
from ...resources.error_handler import EAPIResponseCode
from ...resources.error_handler import ECustomizedError
from ...resources.error_handler import catch_internal
from ...resources.error_handler import customized_error_template
from ...resources.validation_service import ManifestValidator
from ...resources.validation_service import decryption

router = APIRouter()


@cbv(router)
class APIValidation:
    _API_TAG = 'V1 Validate'
    _API_NAMESPACE = 'api_validation'

    @router.post(
        '/validate/manifest',
        tags=[_API_TAG],
        response_model=ManifestValidateResponse,
        summary='Validate manifest for project',
    )
    @catch_internal(_API_NAMESPACE)
    async def validate_manifest(
        self,
        request_payload: ManifestValidatePost,
        current_identity: CurrentUser = Depends(jwt_required),
    ):
        """Validate the manifest based on the project."""
        logger.info('API validate_manifest'.center(80, '-'))
        api_response = ManifestValidateResponse()
        try:
            manifests = request_payload.manifest_json
            manifest_name = manifests['manifest_name']
            project_code = manifests['project_code']
            attributes = manifests.get('attributes', {})

            project_list = await get_user_projects(current_identity)
            if project_code not in [x.get('code') for x in project_list]:
                api_response.code = EAPIResponseCode.forbidden
                api_response.error_msg = 'User is not the member of the project'
                return api_response.json_response()

            response = await get_attribute_templates(project_code, manifest_name)
            manifest_list = response.get('result')
            logger.info(f'manifest_info: {manifest_list}')
            if not manifest_list:
                api_response.error_msg = customized_error_template(ECustomizedError.MANIFEST_NOT_FOUND) % manifest_name
                api_response.result = 'invalid'
                api_response.code = EAPIResponseCode.not_found
                return api_response.json_response()

            target_attribute = manifest_list[0].get('attributes')
            logger.info(f'attributes: {attributes}')
            logger.info(f'target_attribute: {target_attribute}')
            validator = ManifestValidator(attributes, target_attribute)
            attribute_validation_error_msg = await validator.has_valid_attributes()
            if attribute_validation_error_msg:
                logger.error(f'attribute_validation_error_msg: {attribute_validation_error_msg}')
                api_response.error_msg = attribute_validation_error_msg
                api_response.result = 'invalid'
                api_response.code = EAPIResponseCode.bad_request
                return api_response.json_response()
            api_response.code = EAPIResponseCode.success
            api_response.result = 'valid'
            return api_response.json_response()
        except Exception as e:
            logger.error(f'Error validate_manifest: {e}')
            raise e

    @router.post(
        '/validate/env', tags=[_API_TAG], response_model=EnvValidateResponse, summary='Validate env for CLI commands'
    )
    @catch_internal(_API_NAMESPACE)
    async def validate_env(self, request: Request, request_payload: EnvValidatePost):
        """Validate the environment accessible zone."""
        logger.info('API validate_env'.center(80, '-'))
        logger.info(request_payload)
        api_response = EnvValidateResponse()
        encrypted_msg = request_payload.environ
        zone = request_payload.zone
        action = request_payload.action
        logger.info(f'msg: {encrypted_msg}')
        logger.info(request_payload)

        valid_zones = [ConfigClass.GREEN_ZONE_LABEL.lower(), ConfigClass.CORE_ZONE_LABEL.lower()]
        if zone not in valid_zones:
            logger.debug(f'Invalid zone value: {zone}')
            api_response.code = EAPIResponseCode.bad_request
            api_response.error_msg = customized_error_template(ECustomizedError.INVALID_ZONE)
            api_response.result = 'Invalid'
            return api_response.json_response()

        greenroom = ConfigClass.GREEN_ZONE_LABEL.lower()
        core = ConfigClass.CORE_ZONE_LABEL.lower()
        restrict_zone = {
            greenroom: {'upload': [greenroom], 'download': [greenroom]},
            core: {'upload': [greenroom, core], 'download': [core]},
        }

        if encrypted_msg:
            try:
                current_zone = decryption(encrypted_msg, ConfigClass.CLI_SECRET)
            except InvalidEncryptionError as e:
                logger.error(f'Invalid encryption: {e}')
                api_response.code = EAPIResponseCode.bad_request
                api_response.error_msg = customized_error_template(ECustomizedError.INVALID_VARIABLE)
                api_response.result = 'Invalid'
                return api_response.json_response()
        else:
            current_zone = ConfigClass.CORE_ZONE_LABEL.lower()

        permit_action = restrict_zone.get(current_zone)
        permit_zone = permit_action.get(action)
        logger.info(f'Current zone: {current_zone}')
        logger.info(f'Accessing zone: {zone}')
        logger.info(f'Action: {action}')
        logger.info(f'permit_action: {permit_action}')
        logger.info(f'permit_zone: {permit_zone}')
        if zone in permit_zone:
            result = 'valid'
            error = ''
            code = EAPIResponseCode.success
        else:
            result = 'Invalid'
            attempt = 'upload to' if action == 'upload' else 'download from'
            error = f'Invalid action: {attempt} {zone} in {current_zone}'
            code = EAPIResponseCode.forbidden
        api_response.code = code
        api_response.error_msg = error
        api_response.result = result
        return api_response.json_response()
