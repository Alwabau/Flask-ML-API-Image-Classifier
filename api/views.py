import utils
import settings
import os
import json
import hashlib
import re
from middleware import model_predict


from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

router = Blueprint("app_router", __name__, template_folder="templates")


@router.route("/", methods=["GET"])
def index():
    """
    Index endpoint, renders our HTML code.
    """
    return render_template("index.html")


@router.route("/", methods=["POST"])
def upload_image():
    """
    Function used in our frontend so we can upload and show an image.
    When it receives an image from the UI, it also calls our ML model to
    get and display the predictions.
    """
    # No file received, show basic UI
    if "file" not in request.files:
        flash("No file part")
        return redirect(request.url)

    # File received but no filename is provided, show basic UI
    file = request.files["file"]
    if file.filename == "":
        flash("No image selected for uploading")
        return redirect(request.url)

    # File received and it's an image, we must show it and get predictions
    if file and utils.allowed_file(file.filename):

        unique_file_name = utils.get_file_hash(file)
        file.save(os.path.join(settings.UPLOAD_FOLDER, unique_file_name))

        model_prediction = model_predict(unique_file_name)

        predicted_class = model_prediction[0] 
        predicted_class = re.sub('_', ' ', predicted_class)
        predicted_class = predicted_class.title()

        score = round(float(model_prediction[1]  * 100), 2)
    
        context = {
            "prediction": predicted_class,
            "score": score,
            "filename": unique_file_name
        }

        # Updating render template
        return render_template(
            "index.html", filename=unique_file_name, context= context
        )
    # File received and but it isn't an image
    else:
        flash("Allowed image types are -> png, jpg, jpeg, gif")
        return redirect(request.url)


@router.route("/display/<filename>")
def display_image(filename):
    """
    Display uploaded image in our UI.
    """
    return redirect(
        url_for("static", filename="uploads/" + filename), code=301
    )


@router.route("/predict", methods=["POST"])
def predict():
    """
    Endpoint used to get predictions without need to access the UI.

    Parameters
    ----------
    file : str
        Input image we want to get predictions from.

    Returns
    -------
    flask.Response
        JSON response from our API having the following format:
            {
                "success": bool,
                "prediction": str,
                "score": float,
            }

        - "success" will be True if the input file is valid and we get a
          prediction from our ML model.
        - "prediction" model predicted class as string.
        - "score" model confidence score for the predicted class as float.
    """
 
    if "file" in request.files: 
        
        file = request.files["file"]
        
        if file and utils.allowed_file(file.filename):

            unique_file_name_noui = utils.get_file_hash(file)
            file.save(settings.UPLOAD_FOLDER + unique_file_name_noui)
            model_prediction_noui = model_predict(unique_file_name_noui)
            

            rpse = {"success": True, "prediction": model_prediction_noui[0], "score": model_prediction_noui[1]}

            return jsonify(rpse)

        
    rpse = {"success": False, "prediction": None, "score": None}
    
    return jsonify(rpse), 400



@router.route("/feedback", methods=["GET", "POST"])
def feedback():
    """
    Store feedback from users about wrong predictions on a text file.

    Parameters
    ----------
    report : request.form
        Feedback given by the user with the following JSON format:
            {
                "filename": str,
                "prediction": str,
                "score": float
            }

        - "filename" corresponds to the image used stored in the uploads
          folder.
        - "prediction" is the model predicted class as string reported as
          incorrect.
        - "score" model confidence score for the predicted class as float.
    """
    report = request.form.get("report")

    if report:
        with open(settings.FEEDBACK_FILEPATH, "a+") as f:
            f.write(report + "\n")

    return render_template("index.html")
