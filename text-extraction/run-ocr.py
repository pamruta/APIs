
# function to run OCR on a given input file
# using the selected choice of service
def run_ocr(choice, filename):

	if choice == "aws":
		result = run_aws(filename)

	elif choice == "google-vision":
		result = run_google(filename)

	elif choice == "tesseract":
		result = run_tesseract(filename)
	else:
		result = "Choice " + choice + " not supported."

	return result

# run OCR using aws
def run_aws(filename):

	# import AWS boto3 SDK
	import boto3
	client = boto3.client('rekognition')

	result = ""
	with open(filename, "rb") as image:
		ocr_output = client.detect_text(Image = {'Bytes': image.read()})
		for text in ocr_output['TextDetections']:
			if text['Type'] == "LINE":
				result = result + "\n" + text['DetectedText'] 
	return result

# run OCR using google-vision
def run_google(filename):

	# import google vision sdk

	from google.cloud import vision
	client = vision.ImageAnnotatorClient()

	result = ""
	with open(filename, "rb") as image:
		image_object = vision.types.Image(content=image.read())
		ocr_output = client.document_text_detection(image=image_object)
		result = ocr_output.full_text_annotation.text

	return result

# run OCR using tesseract
def run_tesseract(filename):

	# import required packages
	import pytesseract
	from PIL import Image

	result = ""
	ocr_output = pytesseract.image_to_string(Image.open(filename))
	for text in ocr_output.split("\n"):
		# omit blank lines
		if text.strip():
			result = result + "\n" + text 

	return result

# create python flask app

import flask
from flask import request

app = flask.Flask(__name__)

# runs OCR service with given parameters
@app.route("/ocr", methods=['GET'])
def ocr():

	# handling utf-8 encodings
	import sys
	reload(sys)
	sys.setdefaultencoding('utf-8')

	# there are many options to run OCR, here are few choices
	available_choices = ['aws', 'google-vision', 'tesseract']

	# if no choice is given, use google-vision by default
	if 'choice' not in request.args:
		choice = "google-vision"
	else:
		choice = request.args['choice']

		# check if the choice is valid
		if choice not in available_choices:
			response = "Please select choice from: " + str(available_choices)
			return response

        # input image
        if 'image' not in request.files:
                response = "Please provide the input image to run OCR."
                return response

        file = request.files['image']

        # get file extension
        extn = file.filename.rsplit(".")[1]

        # create unique file name
	from datetime import datetime
        file_name = "image-" + datetime.now().strftime("%d%m%Y-%H%M%S") + "." + extn

        # save file in input directory for further processing
        file_path = "input/" + file_name
        file.save(file_path)

	ocr_result = run_ocr(choice, file_path)
	return ocr_result

# running the app on specified port number
import sys
if len(sys.argv) > 1:
	port_no = sys.argv[1]
else:
	# default port number 
	port_no = 5000

app.run(host='0.0.0.0', port=port_no, debug=True)
