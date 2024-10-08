# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv

from app.components.user.models import CurrentUser
from app.logger import logger

from ...clients.lineage import LineageClient
from ...models.base_models import EAPIResponseCode
from ...models.lineage_models import LineageCreatePost
from ...models.lineage_models import LineageCreateResponse
from ...resources.dependencies import get_lineage_client
from ...resources.dependencies import jwt_required
from ...resources.error_handler import catch_internal

router = APIRouter()


@cbv(router)
class APILineage:
    _API_TAG = 'V1 Lineage'
    _API_NAMESPACE = 'api_lineage'

    @router.post(
        '/lineage',
        tags=[_API_TAG],
        response_model=LineageCreateResponse,
        summary='[PENDING] Create lineage for given input and output id',
    )
    @catch_internal(_API_NAMESPACE)
    async def create_lineage(
        self,
        request_payload: LineageCreatePost,
        current_identity: CurrentUser = Depends(jwt_required),
        get_lineage: LineageClient = Depends(get_lineage_client),
    ) -> JSONResponse:
        response = LineageCreateResponse()
        try:
            logger.info('API Lineage'.center(80, '-'))
            proxy_payload = request_payload.__dict__
            logger.info(f'payload: {proxy_payload}')
            await get_lineage.create_lineage(
                input_id=proxy_payload['input_id'],
                output_id=proxy_payload['output_id'],
                input_path=proxy_payload['input_path'],
                output_path=proxy_payload['output_path'],
                container_code=proxy_payload['project_code'],
                action_type=proxy_payload['action_type'],
                description=proxy_payload['description'],
            )
            response.code = EAPIResponseCode.success
        except Exception:
            logger.exception('Failure to create lineage')
            response.code = EAPIResponseCode.internal_error
            response.error_msg = 'Lineage creation failed'
        return response.json_response()
