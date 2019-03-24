
# REST API for face recognition

import flask
from flask import request

app = flask.Flask(__name__)

# home page
@app.route("/", methods=['GET'])
def home():
	output = ""
	output += "Available Methods:\n"
	output += "\t\t/add_faces: adds faces from a given S3 bucket into a collection.\n"
	output += "\t\t/detect_faces: detects faces from a given image against faces indexed in a given collection.\n"
	output += "\t\t/detect_celebrities: detects famous celebrities in a given image.\n"
	output += "\t\t/list_collections: lists collections of previously indexed faces.\n"
	output += "\t\t/delete_collection: deletes a specific collection.\n"

	return output

# training face recognition
# adds faces from a given S3 bucket into a collection
@app.route("/add_faces", methods=['POST'])
def add_faces():

	import boto3
	import re

	if 'bucket' in request.args:
		bucket_name = request.args['bucket']
	else:
		return "Please provide the S3 bucket name.."

	# if collection name is not given, use 'global' as default
	if 'collection' in request.args:
		collection_name = request.args['collection']
	else:
		collection_name = "global"

	# create boto3 rekognition client
	rekog_client = boto3.client('rekognition')

	# create a new collection, if it doesn't exist already
	response = rekog_client.list_collections()
	if not collection_name in response['CollectionIds']:
		rekog_client.create_collection(CollectionId=collection_name)

	# create boto3 s3 client
	s3_client = boto3.client('s3')

	# list images in s3 bucket
	response = s3_client.list_objects(Bucket=bucket_name)

	# add faces detected in the images to given collection
	for item in response['Contents']:

		image_file = item['Key']
		star_name = re.sub(r'(-\d+)?\.(jpg|jpeg|png)', r'', image_file)

		response = rekog_client.index_faces(CollectionId=collection_name, Image={'S3Object': {'Bucket': bucket_name, 'Name': image_file}}, DetectionAttributes=['ALL'], ExternalImageId=star_name)

	return "Done"

# detects faces in the given image file by matching against the collection of previously indexed faces
@app.route("/detect_faces", methods=['GET'])
def detect_faces():

	import boto3

	# create rekognition client
	rekog_client = boto3.client('rekognition')

	# check if the collection name is provided
	if 'collection' in request.args:
		collection_name = request.args['collection']
	# otherwise, use 'global' as default
	else:
		collection_name = "global"

	# picture from which faces are to be detected
	if 'image' not in request.files:
		return "Please provide the image file to detect faces.."

	# download and save the test image
	from datetime import datetime

	file = request.files['image']
	extn = file.filename.rsplit(".")[1]
	test_image = "test-images/image-" + datetime.now().strftime("%d%m%Y-%H%M%S") + "." + extn
	file.save(test_image)

	output = ""
	# pass image to aws rekognition
	with open(test_image, 'rb') as image:
		result = rekog_client.search_faces_by_image(CollectionId=collection_name, Image={'Bytes': image.read()}, MaxFaces=1)
		output = result['FaceMatches'][0]['Face']['ExternalImageId'] 
	return output

# detects celebrities in the given image
@app.route("/detect_celebrities", methods=['GET'])
def detect_celebrities():

	import boto3

	# create rekognition client
	rekog_client = boto3.client('rekognition')

	# picture from which faces are to be detected
	if 'image' not in request.files:
		return "Please provide the image file to detect faces.."

	# download and save the test image
	from datetime import datetime

	file = request.files['image']
	extn = file.filename.rsplit(".")[1]
	test_image = "test-images/image-" + datetime.now().strftime("%d%m%Y-%H%M%S") + "." + extn
	file.save(test_image)
	
	output = ""
	# pass input image to aws rekognition
	with open(test_image, "rb") as image:
		result = rekog_client.recognize_celebrities(Image={'Bytes': image.read()})
		for celebrity in result['CelebrityFaces']:
			output += celebrity['Name'] + "\n"
	return output

# deletes a given collection of previously indexed faces
@app.route("/delete_collection", methods=['GET'])
def delete_collection():

	import boto3

	# create rekognition client
	rekog_client = boto3.client('rekognition')

	if 'collection' not in request.args:
		return "Please provide the collection name to be deleted.."

	collection_name = request.args['collection']

	result = rekog_client.delete_collection(CollectionId=collection_name)
	return "Done"

# lists available collections of previously indexed faces
@app.route("/list_collections", methods=['GET'])
def list_collections():

	import boto3

	# create rekognition client
	rekog_client = boto3.client('rekognition')

	result = rekog_client.list_collections()
	output = ""
	for collection in result['CollectionIds']:
		output += collection + "\n"

	return output

# run the python flask app
import sys
if len(sys.argv) > 1:
	port_no = sys.argv[1]
else:
	port_no = 5000
app.run(host='127.0.0.1', port=port_no, debug=True)
