import os
import ray
from ray import serve

class AntiControllerException(Exception):
    """This exception cannot be initialized in the Serve controller."""

    def __init__(self, *args):
        controller = serve.context.get_global_client()._controller
        controller_pid = ray.get(controller.get_pid.remote())
        if os.getpid() == controller_pid:
            raise RuntimeError("Exception failed to initialize!")

raise AntiControllerException("This is the custom exception info!")

@serve.deployment
def f(*args):
    return "Hi there!"

app = f.bind()
