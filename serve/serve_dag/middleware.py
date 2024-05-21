import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

import logging

logger = logging.getLogger("ray.serve")


class Middleware(BaseHTTPMiddleware):

    def __init__(
            self,
            app,
            some_attribute: str,
    ):
        super().__init__(app)
        logger.info("------------{}------------".format(some_attribute))

    async def dispatch(self, request: Request, call_next):
        # do something with the request object, for example
        start_time = time.perf_counter()
        # process the request and get the response
        response = await call_next(request)
        logger.info(f"Total time {time.perf_counter() - start_time}")

        return response
