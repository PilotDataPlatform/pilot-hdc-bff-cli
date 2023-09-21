# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging
from functools import lru_cache
from typing import Any
from typing import Dict
from typing import Optional

from common import VaultClient
from pydantic import BaseSettings
from pydantic import Extra


class VaultConfig(BaseSettings):
    """Store vault related configuration."""

    APP_NAME: str = 'bff-cli'
    CONFIG_CENTER_ENABLED: bool = False

    VAULT_URL: Optional[str]
    VAULT_CRT: Optional[str]
    VAULT_TOKEN: Optional[str]

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


def load_vault_settings(settings: BaseSettings) -> Dict[str, Any]:
    config = VaultConfig()

    if not config.CONFIG_CENTER_ENABLED:
        return {}

    client = VaultClient(config.VAULT_URL, config.VAULT_CRT, config.VAULT_TOKEN)
    return client.get_from_vault(config.APP_NAME)


class Settings(BaseSettings):
    version = '2.2.0a0'
    port: int = 5080
    host: str = '0.0.0.0'

    ATLAS_API: str = 'http://127.0.0.1:21000'
    ATLAS_ADMIN: str = ''
    ATLAS_PASSWD: str = ''
    ATLAS_ENTITY_TYPE: str = ''

    CLI_SECRET: str = ''
    CLI_PUBLIC_KEY_PATH: str = ''
    CLI_PUBLIC_KEY: str = ''

    OPEN_TELEMETRY_HOST: str = '0.0.0.0'
    OPEN_TELEMETRY_PORT: int = 6831
    OPEN_TELEMETRY_ENABLED: bool = False

    CORE_ZONE_LABEL: str = ''
    GREEN_ZONE_LABEL: str = ''

    AUTH_SERVICE: str = 'http://127.0.0.1:5061'
    UPLOAD_SERVICE_GREENROOM: str = 'http://127.0.0.1:5079'
    UPLOAD_SERVICE_CORE: str = 'http://127.0.0.1:5079'
    DOWNLOAD_SERVICE_CORE: str = 'http://127.0.0.1:5077'
    DOWNLOAD_SERVICE_GREENROOM: str = 'http://127.0.0.1:5077'
    DATASET_SERVICE: str = 'http://127.0.0.1:5081'
    METADATA_SERVICE: str = 'http://127.0.0.1:5065'
    PROJECT_SERVICE: str = 'http://127.0.0.1:5064'

    REDIS_HOST: str = '127.0.0.1'
    REDIS_PASSWORD: str = ''
    REDIS_DB: int = 0
    REDIS_PORT: int = 6379

    LOG_LEVEL_DEFAULT = logging.WARN
    LOG_LEVEL_FILE = logging.WARN
    LOG_LEVEL_STDOUT = logging.WARN
    LOG_LEVEL_STDERR = logging.ERROR

    def modify_values(self, settings):
        if settings.CLI_PUBLIC_KEY_PATH:
            settings.CLI_PUBLIC_KEY = open(settings.CLI_PUBLIC_KEY_PATH).read().encode('ascii')
        settings.REDIS_URI = f'redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}'
        return settings

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = Extra.allow

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                env_settings,
                load_vault_settings,
                init_settings,
                file_secret_settings,
            )


@lru_cache(1)
def get_settings():
    settings = Settings()
    settings = settings.modify_values(settings)
    return settings


ConfigClass = get_settings()
