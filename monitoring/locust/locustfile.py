from locust import HttpUser, task, between
import random


class PrimeApiUser(HttpUser):
    """
    Locust user that simulates clients submitting compute tasks and polling
    the API for status. Also polls the metrics endpoint occasionally.
    """
    wait_time = between(1, 3)

    def on_start(self):
        # store the last submitted request id so this user can poll it
        self.last_request_id = None

    @task(6)
    def submit_task(self):
        # Submit a compute request — adjust n as needed
        with self.client.post("/tasks", json={"n": random.randint(1, 1000)}, catch_response=True) as resp:
            if resp.status_code == 202:
                try:
                    body = resp.json()
                    self.last_request_id = body.get("request_id")
                except Exception:
                    # ignore parsing errors, keep going
                    self.last_request_id = None
            else:
                resp.failure(f"Unexpected status code: {resp.status_code}")

    @task(3)
    def poll_task_status(self):
        # If we have a pending request, poll its status
        if not self.last_request_id:
            return
        url = f"/tasks/{self.last_request_id}"
        with self.client.get(url, catch_response=True) as r:
            if r.status_code == 200:
                try:
                    data = r.json()
                    status = data.get("status")
                    # clear stored id when task is no longer pending
                    if status and status != "pending":
                        self.last_request_id = None
                except Exception:
                    r.failure("Invalid JSON in task status response")
            elif r.status_code == 404:
                # task not found -> clear and move on
                self.last_request_id = None
            else:
                r.failure(f"Unexpected status code polling task: {r.status_code}")

    @task(1)
    def poll_metrics(self):
        # Lightweight poll of the metrics endpoint
        self.client.get("/metrics")

