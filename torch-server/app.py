import os 
import io
import sys
import time
import flask
import tarfile
import logging
import datetime
import requests
import subprocess 
from MyLogger import logger
from api import get_model_api



############### Define Logger ###################

logger.setLevel(logging.INFO)
logger = logger.getChild(__name__)

############## Define Model API ###############

model_api = get_model_api()
print('Model is ready to be used.')

###############################################


app = flask.Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    logger.info('File received')

    username    = flask.request.form['username']
    uuid        = flask.request.form['uuid']
    
    s1 = time.time()
    good = has_remaining_quota(username)
    e1 = time.time()
    logger.info(f'Time checking quota: {e1-s1:.4f}')

    if not has_remaining_quota(username):
        logger.info(f'user {username} has no remaining quota')
        return flask.jsonify({'status': 'bad', 'description': 'NoRemainingQuota'})

    ss = time.time()
    
    s1 = time.time()
    logger.info(flask.request.form)
    byte_array  = flask.request.files['file'].read()
    e1 = time.time()
    logger.info(f'Time reading byte stream: {e1-s1:.4}')

    s1 = time.time()
    file_like_obj = io.BytesIO(byte_array)
    e1 = time.time()
    logger.info(f'Time transfering to file obj: {e1-s1:.4}')
    
    payload = safe_untar(file_like_obj, username, uuid)
    return flask.jsonify(payload)

def safe_untar(file_like_obj, username, uuid):
    logger.info('============================================')
    try:
        logger.info('Try opening tar file')
        tar = tarfile.open(fileobj=file_like_obj, mode='r:gz')
        
        container_id = os.environ['HOSTNAME']
        tmp_file = f'tmp-{container_id}'
        logger.info('Try Extracting file')
        tar.extractall(tmp_file)

        logger.info('Cleaning up redundant files')
        subprocess.call(('sh', 'cleanup.sh'))

        imgs = [f'{tmp_file}/{f}' for f in os.listdir(tmp_file)]
        assert (len(imgs) == 200)

        logger.info('Loading into api...')
        acc, err = model_api(imgs)
        acc, err = f'{acc:.3f}', f'{err:.4f}'
        write_to_db(username, uuid, acc, err)
        tar.close()
        
        logger.info('Done!')
        
        return {'status': 'good', 'description': 'UploadSuccess', 'acc':acc, 'error': err}

    except tarfile.ReadError:
        logger.info('Error: FileFormatError')
        return {'status': 'bad', 'description': 'FileFormatError'}
    except tarfile.ExtractError:
        logger.info('Error: ExtractionError')
        logger.info('Closing tarfile...')
        tar.close()
        return {'status': 'bad', 'description': 'ExtractionError'}
    except AssertionError:
        logger.info('Error: FileNumberError')
        logger.info('Closing tarfile...')
        tar.close()
        return {'status': 'bad', 'description': 'FileNumberError'}
    except Exception as error:
        logger.info('----------')
        logger.info(error)
        logger.info('----------')
        logger.info('Closing tarfile...')
        tar.close()
        
        return {'status': 'bad', 'description': str(error)}
    finally:
        if os.path.exists(tmp_file):
            logger.info(f'Deleting {tmp_file} folder')
            subprocess.call(('rm', '-rf', tmp_file))
        logger.info('==========================================')



def has_remaining_quota(user):
    response = requests.get(f'http://mongoapi:3386/internal/user/quota?username={user}')
    response = response.json()
    
    return response['available']

def write_to_db(user, uuid, acc, err):
    r = requests.get(f'http://mongoapi:3386/internal/user/check?username={user}')
    r = r.json()

    if r['exists']:
        requests.post(f'http://mongoapi:3386/internal/user/update?username={user}&acc={acc}&err={err}')
    else:
        requests.post(f'http://mongoapi:3386/internal/user/create?username={user}&uuid={uuid}')
        requests.post(f'http://mongoapi:3386/internal/user/update?username={user}&acc={acc}&err={err}')


if __name__ == '__main__':
    app.run('0.0.0.0')
