import ray
from ray import serve

from ray.serve.metrics import Counter, Gauge, Histogram
import logging
import time
import psutil
import aias
from fastapi import FastAPI, Request, Response

from ray.serve.handle import DeploymentHandle
from middleware import Middleware

logger = logging.getLogger("ray.serve")

app = FastAPI()
app.add_middleware(Middleware, some_attribute="logger middleware")


@serve.deployment
class MetricPublisher:
    def __init__(self):
        logger.info("---------- INIT Metric Publisher -----------")
        name = 'PAY_UK_MODEL'
        logger.info("Initializing Logs for Ray serve... setting up Metrics")
        self.metrics_dict = dict()
        for i in range(1, 5):
            good_request_ctr = Counter(
                f"mp_payuk_num_good_requests_{i}",
                description=f"Number of good pay uk request processed by the serving. {i}",
                tag_keys=("deployment_name",),
            )
            good_request_ctr.set_default_tags({"deployment_name": name})

            bad_request_ctr = Counter(
                f"mp_payuk_num_bad_requests_{i}",
                description=f"Improper requests received by the serving because of bad PAN number or missing pan number. {i}",
                tag_keys=("deployment_name",),
            )
            bad_request_ctr.set_default_tags({"deployment_name": name})

            req_mem_gauge = Gauge(
                f"mp_payuk_curr_request_mem_usage_{i}",
                description=f"Current pay uk request memory usage. Goes up and down. _{i}",
                tag_keys=("deployment_name",),
            )
            req_mem_gauge.set_default_tags({"deployment_name": name})

            req_lat_histogram = Histogram(
                f"mp_payuk_curr_request_latency_{i}",
                description=f"Latencies of prime requests in ms._{i}",
                boundaries=[0.1, 1],
                tag_keys=("deployment_name",),
            )
            req_lat_histogram.set_default_tags({"deployment_name": name})
            self.metrics_dict.update({f"good_request_ctr_{i}": good_request_ctr.inc,
                                      f"bad_request_ctr_{i}": bad_request_ctr.inc,
                                      f"req_mem_gauge_{i}": req_mem_gauge.set,
                                      f"req_lat_histogram_{i}": req_lat_histogram.observe})

    def publish_metrics(self, metric_lst: list):
        logger.info("---------- INIT publish_metrics -----------")
        for item in metric_lst:
            try:
                logger.info("---- publishing metrics: {} -----".format(item))
                self.metrics_dict[item['metric']](value=item['value'])

            except Exception as e:
                logger.info("Exception while publishing", exc_info=e)


@serve.deployment(num_replicas=1)
@serve.ingress(app)
class RtpPayUK:
    def __init__(self, metric_responder: DeploymentHandle):
        name = 'PAY_UK_MODEL'
        logger.info("Initializing Logs for Ray serve... setting up Metrics")
        self.metrics_dict = {}
        for i in range(1, 5):
            good_request_ctr = Counter(
                f"payuk_num_good_requests_{i}",
                description=f"Number of good pay uk request processed by the serving {i}.",
                tag_keys=("deployment_name",),
            )
            good_request_ctr.set_default_tags({"deployment_name": name})

            bad_request_ctr = Counter(
                f"payuk_num_bad_requests_{i}",
                description=f"Improper requests received by the serving because of bad PAN number or missing pan number {i}.",
                tag_keys=("deployment_name",),
            )
            bad_request_ctr.set_default_tags({"deployment_name": name})

            req_mem_gauge = Gauge(
                f"payuk_curr_request_mem_usage_{i}",
                description=f"Current pay uk request memory usage. Goes up and down {i}.",
                tag_keys=("deployment_name",),
            )
            req_mem_gauge.set_default_tags({"deployment_name": name})

            req_lat_histogram = Histogram(
                f"payuk_curr_request_latency_{i}",
                description=f"Latencies of prime requests in ms {i}.",
                boundaries=[0.1, 1],
                tag_keys=("deployment_name",),
            )
            req_lat_histogram.set_default_tags({"deployment_name": name})
            self.metrics_dict.update({f"good_request_ctr_{i}": good_request_ctr.inc,
                                 f"bad_request_ctr_{i}": bad_request_ctr.inc,
                                 f"req_mem_gauge_{i}": req_mem_gauge.set,
                                 f"req_lat_histogram_{i}": req_lat_histogram.observe})
        self.metric_responder = metric_responder

    def __hamming_weight(self, n):
        count = 0
        while n:
            n &= n - 1
            count += 1
        return count

    def check_hamming_weight(self, pan: int) -> int:
        start = time.perf_counter()
        if pan <= 0:
            logger.warning(f"Pan `{pan}` is improper, defaulting it to 0 score")
            # Increment the request count.
            request_metric = 'bad_request_ctr'
            hw = 0
        else:
            hw = self.__hamming_weight(pan)
            # Increment the request count.
            request_metric = 'good_request_ctr'
        end = time.perf_counter()
        for i in range(1, 5):
            process = psutil.Process()
            self.metrics_dict[f'req_mem_gauge_{i}'](value=process.memory_info().rss)
            self.metrics_dict[f'{request_metric}_{i}'](value=1)
            self.metrics_dict[f'req_lat_histogram_{i}'](value=start - end)
        logger.info(f"Metric exposer time with no optimization = { time.perf_counter()- end}")
        return hw

    def check_hamming_weight_optimized(self, pan: int) -> (int, list):
        start = time.perf_counter()
        q = list()
        if pan <= 0:
            logger.warning(f"Pan `{pan}` is improper, defaulting it to 0 score")
            # Increment the request count.
            request_metric = 'bad_request_ctr'

            hw = 0
        else:
            hw = self.__hamming_weight(pan)
            # Increment the request count.
            request_metric = 'good_request_ctr'
        end = time.perf_counter()
        for i in range(1, 5):
            process = psutil.Process()
            q.append({'metric': f"{request_metric}_{i}", "value": 1})
            q.append({'metric': f"req_mem_gauge_{i}", "value": process.memory_info().rss})
            q.append({'metric': f"req_lat_histogram_{i}", "value": 1000 * (end - start)})
        # Async call metrics
        return (hw, q)

    @app.post("/payuk-unopt")
    @aias.transaction(model_name="payuk", model_version="0.0.1")
    async def payuk_unopt_endpoint(self, request: Request, data: dict, response: Response) -> dict:
        response.headers["response-type"] = "mock"
        hw = (100 - self.check_hamming_weight(data.get('pan', -1)))
        return {
            "explainability_reason_codes": "['1a', '1b', '9']",
            "rskind": [
                "11:8.0"
            ],
            "scores": f"[{hw}]"
        }

    @app.post("/payuk-opt")
    @aias.transaction(model_name="payuk", model_version="0.0.1")
    async def payuk_opt_endpoint(self, request: Request, data: dict, response: Response) -> dict:
        response.headers["response-type"] = "mock"
        bhw, lst = self.check_hamming_weight_optimized(data.get('pan', -1))
        start = time.perf_counter()
        self.metric_responder.publish_metrics.remote(lst)
        logger.info(f"Metric exposer time with optimization = {time.perf_counter() - start}")
        hw = 100 - bhw
        return {
            "explainability_reason_codes": "['1a', '1b', '9']",
            "rskind": [
                "11:8.0"
            ],
            "scores": f"[{hw}]"
        }


metric_deployment = MetricPublisher.bind()
deployment_graph = RtpPayUK.bind(metric_deployment)
