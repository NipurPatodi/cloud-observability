from locust import HttpUser, task, constant
import random

class WebSiteUser(HttpUser):
    host="http://ec2-34-228-20-81.compute-1.amazonaws.com:8000"
    wait_time= constant(0.1)

    @task
    def create_post(self):
        random_pan= random.randint(-1, 1000000)
        self.client.post("/model/payuk-opt", json={"pan":random_pan, "product":f"random Product {random_pan}"})