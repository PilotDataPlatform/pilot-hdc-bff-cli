# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import time

import httpx
import jwt as pyjwt
from fastapi import Request

from app.clients.lineage import LineageClient
from app.components.user.models import CurrentUser
from app.config import ConfigClass
from app.logger import logger
from app.models.base_models import APIResponse
from app.models.base_models import EAPIResponseCode
from app.resources.error_handler import APIException

api_response = APIResponse()


async def jwt_required(request: Request) -> CurrentUser:
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    try:
        payload = pyjwt.decode(token, options={'verify_signature': False})
    except Exception:
        raise APIException(
            error_msg='Invalid token',
            status_code=EAPIResponseCode.unauthorized.value,
        )

    username: str = payload.get('preferred_username')
    realm_roles = payload['realm_access']['roles']
    exp = payload.get('exp')
    if time.time() - exp > 0:
        raise APIException(
            error_msg='Token expired',
            status_code=EAPIResponseCode.unauthorized.value,
        )
    if username is None:
        raise APIException(
            error_msg='User not found',
            status_code=EAPIResponseCode.unauthorized.value,
        )

    async with httpx.AsyncClient() as client:
        payload = {
            'username': username,
        }
        res = await client.get(ConfigClass.AUTH_SERVICE + '/v1/admin/user', params=payload)
    if res.status_code != 200:
        raise APIException(
            error_msg='Auth Service: ' + str(res.json()),
            status_code=EAPIResponseCode.forbidden.value,
        )

    user = res.json().get('result', None)
    if not user:
        raise APIException(
            error_msg=f'Auth service: {username} does not exist.',
            status_code=EAPIResponseCode.forbidden.value,
        )

    return CurrentUser(
        {
            'code': 200,
            'user_id': user.get('id'),
            'username': username,
            'email': user.get('email'),
            'role': user.get('role'),
            'token': token,
            'realm_roles': realm_roles,
        }
    )


def get_project_role(current_identity, project_code):
    logger.info('get_project_role'.center(80, '='))
    logger.info(f'Received identity: {current_identity}, project_code: {project_code}')
    if current_identity['role'] == 'admin':
        role = 'platform-admin'
    else:
        # intersection set between the <project>-roles and user realms
        possible_roles = {project_code + '-' + i for i in ['admin', 'contributor', 'collaborator']}
        # the value is either empty list [] or [<project>-role]
        role = possible_roles.intersection(current_identity['realm_roles'])
        role = role.pop() if len(role) else None

    return role


async def has_permission(identity, project_code, resource, zone, operation):

    if identity['role'] == 'admin':
        role = 'platform_admin'
    else:
        if not project_code:
            logger.info('No project code and not a platform admin, permission denied')
            return False
        role = get_project_role(identity, project_code)
        if not role:
            logger.info(
                'Unable to get project role in permissions check, \
                    user might not belong to project'
            )
            return False

    try:
        payload = {
            'role': role,
            'resource': resource,
            'zone': zone,
            'operation': operation,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(ConfigClass.AUTH_SERVICE + '/v1/authorize', params=payload)
        if response.status_code != 200:
            error_msg = f'Error calling authorize API - {response.json()}'
            raise APIException(status_code=response.status_code, error_msg=error_msg)
        if response.json()['result'].get('has_permission'):
            return True
        else:
            return False
    except Exception as e:
        error_msg = str(e)
        logger.info(f'Exception on authorize call: {error_msg}')
        raise APIException(status_code=EAPIResponseCode.internal_error, error_msg=error_msg)


def select_url_by_zone(zone):
    if zone == ConfigClass.CORE_ZONE_LABEL.lower():
        url = ConfigClass.UPLOAD_SERVICE_CORE + '/v1/files/jobs'
    else:
        url = ConfigClass.UPLOAD_SERVICE_GREENROOM + '/v1/files/jobs'
    return url


async def transfer_to_pre(data, project_code, header):
    try:
        logger.info('transfer_to_pre'.center(80, '-'))
        payload = {
            'current_folder_node': data.current_folder_node,
            'parent_folder_id': data.parent_folder_id,
            'project_code': project_code,
            'operator': data.operator,
            'data': data.data,
            'job_type': data.job_type,
        }
        headers = {'Session-ID': header.get('Session-ID'), 'authorization': header.get('authorization')}
        url = select_url_by_zone(data.zone)
        async with httpx.AsyncClient() as client:
            result = await client.post(url, headers=headers, json=payload, timeout=None)
            logger.info(f'pre response: {result.text}')
        return result
    except Exception as e:
        logger.info(f'Upload service error: {e}')
        raise e


async def get_lineage_client() -> LineageClient:
    """Create a callable dependency for Lineage client instance."""
    client = LineageClient()
    yield client
