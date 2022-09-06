from locust import HttpUser, task


class UserBehavior(HttpUser):
    max_wait = 5000
    min_wait = 1000

    @task(1)
    def index(self):
        self.client.get('http://localhost/')
    

    @task(2)
    def predict(self):
        file = [("file", ("dog.jpeg", open("dog.jpeg", "rb"), "image/jpeg"))]
        self.client.post('http://localhost/predict', headers = {}, data = {}, files = file)
