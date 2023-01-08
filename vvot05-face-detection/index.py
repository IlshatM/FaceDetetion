import base64
import boto3
import requests
import json
import os

ACCESS_KEY = os.environ['access_key']
SECRET_KEY = os.environ['secret_key']
QUEUE_URL = os.environ['queue_url']


def handler(event, context):
    bucket_id = event['messages'][0]['details']['bucket_id']
    object_id = event['messages'][0]['details']['object_id']
    token = context.token['access_token']

    session = boto3.session.Session(region_name='ru-central1')
    s3 = session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )

    photo = s3.get_object(Bucket=bucket_id, Key=object_id)
    encoded_photo = encode_file(photo['Body'])
    print('Content')
    print(encoded_photo)

    headers = {'Authorization': 'Bearer ' + token}
    stt_url = 'https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze'

    r = requests.post(
        url = stt_url,
        headers = headers,
        data = json.dumps(body_json(encoded_photo), indent=4)
    )

    print('Content')
    print(r.content)
    faces = json.loads(r.content.decode('utf-8'))['results'][0]['results'][0]['faceDetection']
    print('Faces')
    print(faces)

    if 'faces' in faces:
        sqs_session = boto3.session.Session(region_name='ru-central1', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
        sqs_client = sqs_session.client(
            service_name='sqs',
            endpoint_url='https://message-queue.api.cloud.yandex.net',
            region_name='ru-central1'
        )

        for face in faces['faces']:
            message = json.dumps({
                'origin_key': object_id,
                'vertices': face['boundingBox']['vertices']
            })
            sqs_client.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=message
            )

def encode_file(file):
    file_content = file.read()
    return base64.b64encode(file_content)

def body_json(encoded_photo):
    body_json = {
        'analyze_specs': [{
            'content': encoded_photo.decode('utf-8'),
            'features': [{
            'type': "FACE_DETECTION"
            }]
        }]
    }
    return body_json