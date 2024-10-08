# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import ClassVar
from typing import Mapping

import fastapi
import httpx
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi_utils.cbv import cbv
from starlette.datastructures import MultiDict

from app.components.user.models import CurrentUser
from app.logger import logger
from app.models.base_models import EAPIResponseCode
from app.models.dataset_models import DatasetDetailResponse
from app.models.dataset_models import DatasetListResponse
from app.resources.dependencies import jwt_required
from app.resources.error_handler import APIException
from app.resources.error_handler import ECustomizedError
from app.resources.error_handler import catch_internal
from app.resources.error_handler import customized_error_template
from app.resources.helpers import get_dataset
from app.resources.helpers import get_dataset_versions
from app.services.dataset.client import DatasetServiceClient
from app.services.dataset.client import get_dataset_service_client
from app.services.project.client import ProjectServiceClient
from app.services.project.client import get_project_service_client

router = APIRouter(tags=['V1 dataset'])

_API_NAMESPACE = 'api_dataset'


class ProxyPass:

    request_allowed_parameters: ClassVar[set[str]]

    response_allowed_headers: ClassVar[set[str]]

    async def __call__(self, request: Request) -> fastapi.Response:
        """Main method that will be called to process request into route."""

        filtered_parameters = await self.filter_request_parameters(request)
        parameters = await self.modify_request_parameters(filtered_parameters)
        raw_response = await self.proxy_request(parameters)
        response = await self.process_response(raw_response)

        return response

    async def filter_request_parameters(self, request: Request) -> MultiDict[str]:
        """Iterate over query parameters and keep only allowed."""

        parameters = MultiDict()

        for allowed_parameter in self.request_allowed_parameters:
            if allowed_parameter in request.query_params:
                for value in request.query_params.getlist(allowed_parameter):
                    parameters.append(allowed_parameter, value)

        return parameters

    async def modify_request_parameters(self, parameters: MultiDict[str]) -> MultiDict[str]:
        """Perform modification over the query parameters."""

        return MultiDict(parameters)

    async def proxy_request(self, parameters: MultiDict[str]) -> httpx.Response:
        """Perform request to the underlying service."""

        return httpx.Response(status_code=100)

    async def raise_for_response_status(self, response: httpx.Response) -> None:
        """Raise exception when received response is not successful."""

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.error(
                f'Received "{response.status_code}" status code in response when calling "{response.request.url}" url'
            )
            raise APIException(error_msg='Unhandled Exception', status_code=EAPIResponseCode.internal_error.value)

    async def filter_response_headers(self, headers: httpx.Headers) -> Mapping[str, str]:
        """Iterate over response headers and keep only allowed."""

        processed_headers = {}

        for header in self.response_allowed_headers:
            if header in headers:
                processed_headers[header] = headers[header]

        return processed_headers

    async def process_response(self, response: httpx.Response) -> fastapi.Response:
        """Take the response from the underlying service and process it, so it can be returned to initial caller."""

        await self.raise_for_response_status(response)

        headers = await self.filter_response_headers(response.headers)

        return fastapi.Response(content=response.content, status_code=response.status_code, headers=headers)


@cbv(router)
class ListDatasets(ProxyPass):
    request_allowed_parameters: ClassVar[set[str]] = {
        'creator',
        'project_code',
        'sort_by',
        'sort_order',
        'page',
        'page_size',
    }
    response_allowed_headers: ClassVar[set[str]] = {'Content-Type'}

    current_user: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)
    dataset_service_client: DatasetServiceClient = Depends(get_dataset_service_client)

    @router.get('/datasets', summary='List all Datasets user can access.')
    async def __call__(self, request: Request) -> fastapi.Response:
        return await super().__call__(request)

    async def modify_request_parameters(self, parameters: MultiDict[str]) -> MultiDict[str]:
        """Replace parameters with appropriate for Dataset Service and check permissions.

        - If the creator parameter is specified it is set with the current username.
        - If the project_code parameter is specified it is part of projects to which the current user has access.
        - If neither creator nor project_code parameters are specified filtering by projects where user has admin roles or where user is the creator.
        """

        modified_parameters = MultiDict(parameters)

        creator_parameter = modified_parameters.pop('creator', None)
        project_code_parameter = modified_parameters.pop('project_code', None)

        user_projects_with_admin_role = self.current_user.get_projects_with_role('admin')

        if not creator_parameter and not project_code_parameter and user_projects_with_admin_role:
            project_ids = []
            for project_code in user_projects_with_admin_role:
                project = await self.project_service_client.get(code=project_code)
                project_ids.append(project.id)
            modified_parameters['project_id_any'] = ','.join(project_ids)
            modified_parameters['or_creator'] = self.current_user.username

            return modified_parameters

        if creator_parameter or not user_projects_with_admin_role:
            modified_parameters['creator'] = self.current_user.username

        if project_code_parameter:
            user_projects = list(self.current_user.get_project_roles().keys())
            if project_code_parameter not in user_projects:
                raise APIException(error_msg='Permission denied', status_code=EAPIResponseCode.forbidden.value)

            project = await self.project_service_client.get(code=project_code_parameter)
            modified_parameters['project_id'] = project.id

        return modified_parameters

    async def proxy_request(self, parameters: MultiDict[str]) -> httpx.Response:
        return await self.dataset_service_client.list_datasets(parameters)

    async def process_response(self, response: httpx.Response) -> fastapi.Response:
        api_response = DatasetListResponse(code=EAPIResponseCode.success)

        try:
            api_response.result = response.json().get('result')
        except Exception:
            api_response.result = None

        return api_response.json_response()


@cbv(router)
class GetDataset:
    current_identity: CurrentUser = Depends(jwt_required)
    project_service_client: ProjectServiceClient = Depends(get_project_service_client)

    @router.get(
        '/dataset/{dataset_code}',
        response_model=DatasetDetailResponse,
        summary='Get dataset detail based on the dataset code',
    )
    @catch_internal(_API_NAMESPACE)
    async def get_dataset(self, dataset_code, page=0, page_size=10):
        """
        Summary:
            The api will integrate with dataset detail and versions
            api to have a joint response for cli tool.
        Path Parameter:
            - dataset_code(str): unique identifier of dataset
        Parameter:
            - page(int): page number
            - page_size(str): page size
        return:
            - result(dict): dataset detail info
        """

        logger.info('API get_dataset'.center(80, '-'))
        api_response = DatasetDetailResponse()

        logger.info(f'User request with identity: {self.current_identity}')
        dataset = await get_dataset(dataset_code)
        logger.info(f'Getting user dataset node: {dataset}')
        if not dataset:
            api_response.code = EAPIResponseCode.not_found
            api_response.error_msg = customized_error_template(ECustomizedError.DATASET_NOT_FOUND)
            return api_response.json_response()

        if not await self.current_identity.can_access_dataset(dataset, self.project_service_client):
            api_response.code = EAPIResponseCode.forbidden
            api_response.error_msg = customized_error_template(ECustomizedError.PERMISSION_DENIED)
            return api_response.json_response()

        node_geid = dataset.get('id')
        dataset_query_event = {'dataset_geid': node_geid, 'page': page, 'page_size': page_size}
        logger.info(f'Dataset query: {dataset_query_event}')

        versions = await get_dataset_versions(dataset_query_event)
        logger.info(f'Dataset versions: {versions}')
        dataset_detail = {'general_info': dataset, 'version_detail': versions, 'version_no': len(versions)}
        api_response.result = dataset_detail
        api_response.code = EAPIResponseCode.success
        return api_response.json_response()
