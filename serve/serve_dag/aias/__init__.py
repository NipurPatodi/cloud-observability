from functools import wraps
from typing import Callable
from fastapi import Request, Response


def transaction(model_name, model_version, **deco_kwargs):

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
                self, request: Request, data: dict, response: Response
        ) -> dict:
            # use decorator_args and decorator_kwargs if required
            # update response headers
            aip_trace_id = request.headers["x-request-id"]
            response.headers["aip-trace-id"] = aip_trace_id
            response.headers["model-name"] = model_name
            response.headers["model-version"] = model_version
            # response.headers.update(self.metadata)
            # run func
            return await func(self, request, data, response)

        return wrapper

    return decorator
