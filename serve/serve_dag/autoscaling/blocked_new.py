from ray import serve

@serve.deployment
class Blocked:
    async def __call__(self):
        signal = serve.get_deployment_handle("SignalDeployment", app_name="signal")
        await signal.wait.remote()
        return "hello"

app = Blocked.bind()
