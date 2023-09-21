# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from aioredis import StrictRedis
from common import LoggerFactory

from ..config import ConfigClass

logger = LoggerFactory(
    'api_health',
    level_default=ConfigClass.LOG_LEVEL_DEFAULT,
    level_file=ConfigClass.LOG_LEVEL_FILE,
    level_stdout=ConfigClass.LOG_LEVEL_STDOUT,
    level_stderr=ConfigClass.LOG_LEVEL_STDERR,
).get_logger()


async def redis_check():
    try:
        res = await StrictRedis(
            host=ConfigClass.REDIS_HOST,
            port=ConfigClass.REDIS_PORT,
            db=ConfigClass.REDIS_DB,
            password=ConfigClass.REDIS_PASSWORD,
        ).ping()
        logger.info(f'Redis health check result: {res}')
        if res:
            return True
    except Exception as e:
        logger.error(f'Redis health check failed: {e}')
        return False
