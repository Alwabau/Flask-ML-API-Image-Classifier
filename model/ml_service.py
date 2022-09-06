import time
import json
import redis
import settings
import os
import numpy as np
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image




# Connecting to Redis and assign to variable `db`

db = redis.Redis(
    host= settings.REDIS_IP, 
    port= settings.REDIS_PORT, 
    db= settings.REDIS_DB_ID
)


model = ResNet50(weights='imagenet')


def predict(image_name):
    """
    Load image from the corresponding folder based on the image name
    received, then, run our ML model to get predictions.

    Parameters
    ----------
    image_name : str
        Image filename.

    Returns
    -------
    class_name, pred_probability : tuple(str, float)
        Model predicted class as a string and the corresponding confidence
        score as a number.
    """
    img = image.load_img(os.path.join(settings.UPLOAD_FOLDER, image_name), target_size=(224, 224))
    
    pic = image.img_to_array(img)
    pic = np.expand_dims(pic, axis=0)
    pic = preprocess_input(pic)

    predictions = model.predict(pic)
    prediction = decode_predictions(predictions, top=1)[0]
    predicted_class = prediction[0][1] 

    score = round(float(prediction[0][2]), 4)

    return tuple([predicted_class , score])


def classify_process():
    """
    Loop indefinitely asking Redis for new jobs.
    When a new job arrives, takes it from the Redis queue, uses the loaded ML
    model to get predictions and stores the results back in Redis using
    the original job ID so other services can see it was processed and access
    the results.

    Load image from the corresponding folder based on the image name
    received, then, run our ML model to get predictions.
    """
    while True:

        _, msg = db.brpop(settings.REDIS_QUEUE)
        msg = json.loads(msg)
        name_image = msg['image_name']
        class_name, pred_probability = predict(name_image)
        output_model = {
            "prediction": class_name,
            "score": pred_probability,
            }
        db.set(msg['id'], json.dumps(output_model))

        time.sleep(settings.SERVER_SLEEP)


if __name__ == "__main__":
    # Now launch process
    print("Launching ML service...")
    classify_process()
