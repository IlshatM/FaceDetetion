import os
import json
import ydb
import ydb.iam
import requests

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'
DB_PATH = os.environ['DB_PATH']
DB_ENDPOINT = os.environ['DB_ENDPOINT']
API_GATEWAY = os.environ.get("API_GATEWAY")

def response(code = 200, body = ''):
    return {'statusCode': code, 'body': body }


def driver():
    credentials = ydb.iam.MetadataUrlCredentials()
    driver_config = ydb.DriverConfig(
        DB_ENDPOINT, DB_PATH, credentials=credentials
    )
    return ydb.Driver(driver_config)


def updateName(ydb_driver):
    query = f"""
        PRAGMA TablePathPrefix("{DB_PATH}");
        UPDATE photo_faces
        SET user_chat_id = {user_chat_id}
        WHERE id = {entry_id};
    """
    session = ydb_driver.table_client.session().create()
    session.transaction().execute(query, commit_tx=True)
    session.closing()


def emptyFace(ydb_driver):
    query = f"""
        PRAGMA TablePathPrefix("{DB_PATH}");
        SELECT id, face_key from photo_faces
        WHERE name IS NULL LIMIT 1;
    """
    session = ydb_driver.table_client.session().create()
    result_set = session.transaction().execute(query, commit_tx=True)
    session.closing()
    if not result_set or not result_set[0].rows:
        return None

    return result_set[0].rows[0]


def setUserChatId(ydb_driver, entry_id, message_in):
    user_chat_id = message_in['chat']['id']
    query = f"""
        PRAGMA TablePathPrefix("{DB_PATH}");
        UPDATE photo_faces
        SET user_chat_id = {user_chat_id}
        WHERE id = {entry_id};
    """
    session = ydb_driver.table_client.session().create()
    session.transaction().execute(query, commit_tx=True)
    session.closing()


def sendMessage(text, message):
    message_id = message['message_id']
    chat_id = message['chat']['id']
    reply_message = {'chat_id': chat_id,
                     'text': text,
                     'reply_to_message_id': message_id}
    requests.post(url=f'{TELEGRAM_API_URL}/sendMessage', json=reply_message)


def sendPhoto(photo_url, message):
    message_id = message['message_id']
    chat_id = message['chat']['id']
    reply_message = {'chat_id': chat_id,
                     'photo': photo_url,
                     'reply_to_message_id': message_id}
    requests.post(url=f'{TELEGRAM_API_URL}/sendPhoto', json=reply_message)

def find(name, ydb_driver, message_in):
    query = f"""
        PRAGMA TablePathPrefix("{DB_PATH}");
        SELECT id, photo_key from photo_faces
        WHERE name = '{name}';
    """
    session = ydb_driver.table_client.session().create()
    result_set = session.transaction().execute(query, commit_tx=True)
    session.closing()

    if not result_set or not result_set[0].rows:
        sendMessage('Фотографии с {name} не найдены', message_in)
        return None

    for i in result_set[0].rows:
        photo_url = f'{API_GATEWAY}/photo?id={i["photo_key"].decode("utf-8")}'
        sendPhoto(photo_url, message_in)


def face(ydb_driver, message_in):
    entry = emptyFace(ydb_driver)

    if entry:
        setUserChatId(ydb_driver, entry['id'], message_in)
        photo_url = f'{API_GATEWAY}/?face={entry["face_key"].decode("utf-8")}'
        sendPhoto(photo_url, message_in)
    else:
        sendMessage("There's no photo with unknown face", message_in)


def setName(ydb_driver, message_in, name):
    user_chat_id = message_in['chat']['id']

    query = f"""
        PRAGMA TablePathPrefix("{DB_PATH}");
        SELECT id from photo_faces
        WHERE name IS NULL AND user_chat_id = {user_chat_id} LIMIT 1;
    """
    session = ydb_driver.table_client.session().create()
    result_set = session.transaction().execute(query, commit_tx=True)
    if not result_set or not result_set[0].rows:
        session.closing()
        return None

    entry_id = result_set[0].rows[0]['id']
    mutation = f"""
        PRAGMA TablePathPrefix("{DB_PATH}");
        UPDATE photo_faces
        SET name = '{name}'
        WHERE id = {entry_id};
    """
    session.transaction().execute(mutation, commit_tx=True)
    session.closing()


def handler(event, context):
    ydb_driver = driver()
    ydb_driver.wait(timeout=5)
    try:
        if TELEGRAM_BOT_TOKEN is None:
            return response()

        message_in = json.loads(event['body'])['message']
        message_txt = message_in["text"]

        if message_txt == None or len(message_txt) == 0:
            return response()

        if "entities" in message_in:
            match message_txt.split()[0]:
                case "/find":
                    find(" ".join(message_txt.split()[1:]), ydb_driver, message_in)
                    return
                case "/getface":
                    face(ydb_driver, message_in)
                    return
        else:
            setName(ydb_driver, message_in, message_txt)
        
        return response()
    except Exception as err:
        print("Error")
        print(err)
        return response(body = err)
