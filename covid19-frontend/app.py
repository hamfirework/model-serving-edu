# Import Libraries and setup
from flask import Flask, request, jsonify, g, redirect, url_for, flash, render_template, make_response
from flask_cors import CORS, cross_origin
import requests
import os
import datetime
#import random
from pathlib import Path
import shutil
import numpy as np

from PIL import Image
from io import BytesIO
import base64
from imageio import imread
import json
import time
import uuid
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger()

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

UPLOAD_FOLDER = os.path.join('static', 'source')
OUTPUT_FOLDER = os.path.join('static', 'result')
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'PDF', 'PNG', 'JPG', 'JPEG'])

app = Flask(__name__)
CORS(app)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

prediction=' '
confidence=0
filename='Image_Prediction.png'
image_name = filename


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def hello_world():
	return render_template('index.html', prediction='INCONCLUSIVE', confidence=0, filename='no image')

# Service healthchecks
@app.route('/covid19/api/v1/healthcheck', methods=['GET', 'POST'])
def liveness():
    logging.info("===========liveness=========")
    return 'Covid19 detector API is live!'

@app.route("/query", methods=["POST"])
def query():
    logging.info("===========query=========")
    if request.method == 'POST':
        # RECIBIR DATA DEL POST
        if 'file' not in request.files:
            return render_template('index.html', prediction='INCONCLUSIVE', confidence=0, filename='no image')
        file = request.files['file']
        # image_data = file.read()
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return render_template('index.html', prediction='INCONCLUSIVE', confidence=0, filename='no image')
        if file and allowed_file(file.filename):

            filename = str(file.filename)
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(img_path)
            image_name = filename

            logging.info("===== os.environ['COVID_SERVER_URL'] ====")
            logging.info(os.environ['COVID_SERVER_URL'])

            # detection covid
            try:
                COVID_SERVER_URL = os.environ['COVID_SERVER_URL']
                domain_url = COVID_SERVER_URL + '/covid19/api/v1/predict'
                logging.info(domain_url)
                data={ "img_path" : img_path, "filename" : filename}
                json_response = requests.post(domain_url, json=data, verify=False)
                res = json.loads(json_response.text)

                prediction = res['prediction']
                prob = res['prob']
                img_pred_name = res['img_pred_name']

                output_path = os.path.join(app.config['OUTPUT_FOLDER'], img_pred_name)
                return render_template('index.html', prediction=prediction, confidence=prob, filename=image_name, xray_image=img_path, xray_image_with_heatmap=output_path)
            except Exception as e:
                logging.warning(e)
                return render_template('index.html', prediction='INCONCLUSIVE', confidence=0, filename=image_name, xray_image=img_path)
        else:
            return render_template('index.html', name='FILE NOT ALOWED', confidence=0, filename=image_name, xray_image=img_path)


# No caching at all for API endpoints.
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

if __name__ == '__main__':
    app.run('0.0.0.0', 6000)
