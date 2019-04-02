import time
import uuid
import flask
from flask_cors import *
import datetime
from dateutil import parser
from mongodb import MyMongo

mongo = MyMongo('mongo', 27017)
app = flask.Flask(__name__)
CORS(app, supports_credentials=True)

def get_time():
    now = datetime.datetime.now()
    offset = datetime.timedelta(hours=8)

    return (now+offset).isoformat()


def iso_to_datetime(isostr):
    return parser.parse(isostr)


def is_next_day(d):
    d = iso_to_datetime(d)
    now = iso_to_datetime(get_time())

    return True if now.date() > d.date() else False


@app.route('/internal/user/check', methods=['GET'])
def check_user():
    username = flask.request.args.get('username')

    print(f'Checking if user {username} exists in database...')
    filter = {'name': username}

    exists = mongo.document_exists(filter)

    if exists:
        print(f'{username} is in database')
    else:
        print(f'{username} is not in database')
    
    return flask.jsonify({'exists':exists})
    

@app.route('/internal/user/create', methods=['POST'])
def create_user():
    username = flask.request.args.get('username')
    uuid     = flask.request.args.get('uuid')
    print(f'Adding user {username} to database...')
    
    # note to self: use $set if 'data' is {}, else if 'data' is [], use $push 
    body = {
        'name': username,
        'uuid': uuid,
        'first_commit': get_time(),
        'data': [],
        'selected': '',
        'numEntry': 0,
        'last':'',
        'remaining_uploads': 5
    }

    mongo.insert(body)

    return flask.jsonify({'status': 'good'})


@app.route('/internal/user/quota', methods=['GET'])
def get_quota():
    username = flask.request.args.get('username')
    filter = {'name': username}

    body = {'_id':0, 'last':1, 'remaining_uploads':1}
    
    record = mongo.get(filter, body)
    if not record:
        return flask.jsonify({'available': True})
    remaining = int(record['remaining_uploads'])
    last = record['last']
    
    if last: # 'last' is not an empty string
        print(f'Remaining uploads for {username}: {remaining}')

        if is_next_day(last): # Next day
            print('Next day. Renewing quota.')
            body = {
                '$set': {'remaining_uploads': 5}
            }
            mongo.update(filter, body)
            
        elif remaining > 0:  # same day and has remaining quota
            print(f'Still has quota: {remaining}')

        else:  # same day but no remaining quota
            print('No remaining quota')
            return flask.jsonify({'available': False})

        return flask.jsonify({'available': True})
            
    else: # 'last' = '', user has not yet uploaded any files
        print(f'User {username} has not yet uploaded any files')
        return flask.jsonify({'available': True})


@app.route('/internal/user/update', methods=['POST'])
def user_update():
    username = flask.request.args.get('username')
    acc      = flask.request.args.get('acc')
    err      = flask.request.args.get('err')
    rid      = str(uuid.uuid4())[-12:]

    filter = {'name': username}
 
    body = {
        '$push': {
            f'data': { 'rid': rid, 'acc': acc, 'err': err, 'timestamp': get_time() }
        },
        '$inc': {'numEntry': 1, 'remaining_uploads': -1},
        '$set': {'last': get_time()}
    }
    
    print(f'Updating transaction for user {username}')
    mongo.update(filter, body, True)

    return flask.jsonify({'status':'good'})


@app.route('/api/db/user/select', methods=['POST'])
def select_transaction():
    print('Selecting transaction...')
    #username = flask.request.args.get('username')
    uuid     = flask.request.args.get('id') 
    rid      = flask.request.args.get('rid')

    filter = {'uuid': uuid}
    body = {'data':1, '_id':0}
    
    record = mongo.get(filter, body)
    for r in record['data']:
        if r['rid'] == rid:
            record = r
            break

    body = {'$set': {'selected': record} }

    mongo.update(filter, body)

    print(f'Transaction {rid} selected for user {uuid}')

    return flask.jsonify({'records': record})


@app.route('/api/db/user/history', methods=['GET'])
def get_history():

    uuid = flask.request.args.get('id')    
    filter = {'uuid': uuid}
    body = {'name':1, 'uuid':1, 'data':1, '_id':0, 'selected':1}
    
    data = mongo.get(filter, body)

    if data is None:
        return (flask.jsonify({'status': 'NoSubmission'}))

    payload = {
        'name': data['name'],
        'uuid': data['uuid'],
        'records': data['data'],
        'selected': data['selected']
    }

    return flask.jsonify(payload)

@app.route('/api/db/user/remain', methods=['GET'])
def get_remain():
    
    uuid = flask.request.args.get('id')
    filter = {'uuid': uuid}

    body = {'_id': 0, 'remaining_uploads': 1, 'uuid':1, 'last':1}

    record = mongo.get(filter, body)

    if not record:
        return flask.jsonify({'id':uuid, 'remain': 5})
    elif is_next_day(record['last']):
        print('Next day. Renewing quota')
        body = {'$set': {'remaining_uploads': 5} }
        mongo.update(filter, body)
        
    remain = record['remaining_uploads']

    return flask.jsonify({'id': uuid, 'remain': remain})

@app.route('/api/db/users/selected', methods=['GET'])
def get_all():
    ss = time.time()
    filter, attr = {}, {
                        'name':1,
                        'data':{'$slice':1},
                        'selected':1,
                        'numEntry':1,
                        'last':1,
                        '_id':0
                        }
    body = mongo.get_all(filter, attr)
        
    payload = {
        'records': []
    }
    
    for r in body:
        record = {}
            
        record['name'] = r['name']
        record['acc'] = r['selected']['acc'] if r['selected'] else r['data'][0]['acc']
        record['err'] = r['selected']['err'] if r['selected'] else r['data'][0]['err']
        record['timestamp'] = r['selected']['timestamp'] if r['selected'] else r['data'][0]['timestamp']
        record['numEntry'] = r['numEntry']

        payload['records'].append(record)
                    
    ee = time.time()
    print(f'Time getting all: {ee-ss:.4}')

    return flask.jsonify(payload)


