# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import FastAPI
from fastapi_health import health

from app.resources.health_check import redis_check

from .routers import api_root
from .routers.v1 import api_dataset
from .routers.v1 import api_file
from .routers.v1 import api_lineage
from .routers.v1 import api_manifest
from .routers.v1 import api_project
from .routers.v1 import api_validation


def api_registry(app: FastAPI):
    prefix = '/v1'
    app.add_api_route('/v1/health', health([redis_check], success_status=204, failure_status=503), tags=['Health'])
    app.include_router(api_root.router)
    app.include_router(api_project.router, prefix=prefix)
    app.include_router(api_manifest.router, prefix=prefix)
    app.include_router(api_validation.router, prefix=prefix)
    app.include_router(api_file.router, prefix=prefix)
    app.include_router(api_dataset.router, prefix=prefix)
    app.include_router(api_lineage.router, prefix=prefix)
