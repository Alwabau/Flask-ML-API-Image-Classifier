import time
import uuid
import redis
import settings
import json
import redis

db = redis.Redis(
    host= settings.REDIS_IP, 
    port= settings.REDIS_PORT, 
    db= settings.REDIS_DB_ID
)


def model_predict(image_name):
    """
    Receives an image name and queues the job into Redis.
    Will loop until getting the answer from our ML service.

    Parameters
    ----------
    image_name : str
        Name for the image uploaded by the user.

    Returns
    -------
    prediction, score : tuple(str, float)
        Model predicted class as a string and the corresponding confidence
        score as a number.
    """

    job_id = str(uuid.uuid4())
    job_data = {"id": job_id, "image_name": image_name}
    db.rpush(settings.REDIS_QUEUE, json.dumps(job_data))

    while True:

        if db.get(job_id):
            output = json.loads(db.get(job_id))
            db.delete(job_id)
            break

        time.sleep(settings.API_SLEEP)

    return tuple([output['prediction'], output['score']])
