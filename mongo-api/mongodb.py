import pprint
import pymongo
import datetime


class MyMongo(object):
    def __init__(self, ip, port):
        self._client = pymongo.MongoClient(ip, port)
        self.db = self._client.mlta
        self.coll = self._client.mlta.transactions

    def insert(self, body):
        self.coll.insert_one(body)

    def document_exists(self, filter):
        return bool(self.coll.count_documents(filter, limit=1))

    def update(self, filter, body, upsert=False):
        self.coll.update_one(filter, body, upsert)

    def get(self, filter, attr):
        return self.coll.find_one(filter, attr)

    def get_all(self, filter, attr):
        return self.coll.find(filter, attr)



if __name__ == '__main__':

    client = MyMongo('172.18.0.80', 27017)


    filter = {'name': 'Caleb'}
    if client.document_exists(filter):
        body = {
            '$push': {
                'data': {'acc': 84.54, 'err': 53.54, 'timestamp': datetime.datetime.now()}
            }
        }
        client.update(filter, body)
    else:
        print('Document does not exist')
        body = {
            'name': 'Caleb',
            'first_commit': datetime.datetime.now(),
            'data': []
        }
        client.insert(body)

    history = client.get(filter)['data']
    
    print(history)

    
            
