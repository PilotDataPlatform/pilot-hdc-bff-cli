# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from functools import wraps
from typing import Dict

import jwt

from app.config import ConfigClass
from app.models.base_models import APIResponse
from app.models.base_models import EAPIResponseCode

from .exceptions import InvalidAction
from .exceptions import ProjectCodeMismacthed
from .exceptions import SourceIpMismatched
from .models import ValidAction


def cli_rules_enforcement(action: ValidAction):
    """
    Summary:
    """

    def decorator(func):
        @wraps(func)
        async def inner(*arg, **kwargs):

            api_response = APIResponse()
            request = kwargs.get('request')
            project_code = kwargs.get('project_code', None)
            target_zone = kwargs.get('data').zone

            greenroom = ConfigClass.GREEN_ZONE_LABEL.lower()
            core = ConfigClass.CORE_ZONE_LABEL.lower()
            if target_zone not in [greenroom, core]:
                api_response.error_msg = f'Invalid zone: {target_zone}'
                api_response.code = EAPIResponseCode.bad_request
                return api_response.json_response()

            vm_info = request.headers.get('vm-info', None)
            if vm_info:
                vm_info = jwt.decode(vm_info, ConfigClass.CLI_PUBLIC_KEY, algorithms=['RS256'])
                ip_pairs = request.headers.get('x-forwarded-for', ', ')
                incoming_ip = ip_pairs.split(', ')[0]
                try:
                    await VM_info_enforcement(vm_info, incoming_ip, project_code)
                except (SourceIpMismatched, ProjectCodeMismacthed) as e:
                    api_response.error_msg = str(e)
                    api_response.code = EAPIResponseCode.forbidden
                    return api_response.json_response()

                try:
                    await zone_enforcement(vm_info.get('zone'), action, target_zone)
                except InvalidAction as e:
                    api_response.error_msg = str(e)
                    api_response.code = EAPIResponseCode.forbidden
                    return api_response.json_response()
            else:
                if target_zone == core and action == ValidAction.UPLOAD:
                    api_response.error_msg = f'Cannot upload to {core} zone'
                    api_response.code = EAPIResponseCode.forbidden
                    return api_response.json_response()

            return await func(*arg, **kwargs)

        return inner

    return decorator


async def VM_info_enforcement(vm_info: Dict[str, str], incoming_ip: str, project_code: str) -> None:
    """
    Summary:
        the function will check the following attribute in the signed
        jwt:
         - ip in the jwt should be same as source ip of request
         - project_code specify in vm info should be same as payload
    Parameter:
        - vm_info(dict): vm infomation
        - incoming_ip(str): the ip address of source
        - project_code(str): the target project
    """

    if vm_info.get('ip') != incoming_ip:
        raise SourceIpMismatched('The ip of VM does not matched with source ip')

    elif project_code not in vm_info.get('project_code'):
        raise ProjectCodeMismacthed('The project of VM does not matched with query')


async def zone_enforcement(current_zone: str, action: ValidAction, target_zone: str) -> None:
    """
    Summary:
        the function will check the following rules between zones
         - greenroom can ONLY make operation in greenroom. Cannot
         - upload/download in core
         - core can do anything except download from greenroom
    Parameter:
        - current_zone(dict): the zone that current vm is on
        - action(ValidAction): the action that user initiates (eg. upload/download)
        - target_zone(str): the zone that user want to operate
    """

    greenroom = ConfigClass.GREEN_ZONE_LABEL.lower()
    core = ConfigClass.CORE_ZONE_LABEL.lower()
    restrict_zone = {
        greenroom: {ValidAction.UPLOAD: [greenroom], ValidAction.DOWNLOAD: [greenroom]},
        core: {ValidAction.UPLOAD: [greenroom, core], ValidAction.DOWNLOAD: [core]},
    }

    permit_action = restrict_zone.get(current_zone)
    permit_zone = permit_action.get(action)
    if target_zone not in permit_zone:
        attempt = 'upload to' if action == ValidAction.UPLOAD else 'download from'
        error = f'Invalid action: {attempt} {target_zone} in {current_zone}'
        raise InvalidAction(error)
