from sanic import Sanic
from sanic.response import text
from sanic import response
import json
import os
import ydb
import ydb.iam
import requests
import random
import boto3
import io
from PIL import Image, ImageDraw

app = Sanic(__name__)
ydb_driver: ydb.Driver

DB_ENDPOINT = os.environ['DB_ENDPOINT']
DB_PATH = os.environ['DB_PATH']
PHOTO_BUCKET_ID = os.environ['PHOTO_BUCKET_ID']
FACES_BUCKET_ID = os.environ['FACES_BUCKET_ID']
PORT = os.environ['PORT']

def driver():
    credentials = ydb.iam.MetadataUrlCredentials()
    driver_config = ydb.DriverConfig(DB_ENDPOINT, DB_PATH, credentials=credentials)
    return ydb.Driver(driver_config)

def photoKeyAndTitle(body):
  params = json.loads(json.loads(body.decode('utf-8'))['messages'][0]['details']['message']['body'])
  origin_key = params['origin_key']
  vertices0 = (int(params['vertices'][0]['x']), int(params['vertices'][0]['y']))
  vertices2 = (int(params['vertices'][2]['x']), int(params['vertices'][2]['y']))

  photo_data = io.BytesIO()

  photo_session = boto3.session.Session(
    region_name='ru-central1'
  )
  s3_photo_client = photo_session.client(
      service_name='s3',
      endpoint_url='https://storage.yandexcloud.net'
  )
  s3_photo_client.download_fileobj(PHOTO_BUCKET_ID, origin_key, photo_data)

  photo_image = Image.open(photo_data)

  img1 = ImageDraw.Draw(photo_image)
  img1.rectangle([vertices0, vertices2],outline ="blue", width=5)
  face_photo_title = "{0}_{1}.jpg".format(
    origin_key.replace(".", ""),
    random.getrandbits(64)
  )

  in_mem_file = io.BytesIO()
  photo_image.save(in_mem_file, format='JPEG')
  in_mem_file.seek(0)

  s3_photo_client.upload_fileobj(in_mem_file, FACES_BUCKET_ID, face_photo_title, ExtraArgs={'ContentType': 'image/jpeg'})
  return [origin_key, face_photo_title]

def insertEntry(photo_key, photo_face_key):
    query = f"""
        PRAGMA TablePathPrefix("{DB_PATH}");
        INSERT INTO photo_faces (id, photo_key, face_key)
        VALUES ({random.getrandbits(32)}, '{photo_key}', '{photo_face_key}');
    """
    session = ydb_driver.table_client.session().create()
    session.transaction().execute(query, commit_tx=True)
    session.closing()


@app.after_server_start
async def afterServerStart(app, loop):
    global ydb_driver
    ydb_driver = driver()
    ydb_driver.wait(timeout=5)

@app.route("/", methods=["POST"],)
async def index(request):
    result = photoKeyAndTitle(request.body)
    insertEntry(result[0], result[1])
    return text("Hello!")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(PORT), motd=False, access_log=False)

