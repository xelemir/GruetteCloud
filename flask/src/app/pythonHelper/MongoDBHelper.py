from pymongo import MongoClient
import logging

class MongoDBHelper:
    def __init__(self):
        try:
            username = "mainUser"
            password = "pwd"
            self.client = MongoClient(f"mongodb://{username}:{password}@mongodb:27017/gruetteChatDB?authSource=gruetteChatDB&authMechanism=SCRAM-SHA-1")
            self.db = self.client["gruetteChatDB"]

        except Exception as e:
            logging.error(f"The error '{e}' occurred")

    def write(self, collection_name, document):
        try:
            self.db[collection_name].insert_one(document)
        except Exception as e:
            logging.error(f"The error '{e}' occurred")

    def read(self, collection_name, query, sort=None):
        collection = self.db[collection_name]
        if sort:
            result = collection.find(query).sort(sort)
        else:
            result = collection.find(query)
        return [doc for doc in result]
        
    def update(self, collection_name, query, new_values):
        try:
            self.db[collection_name].update_one(query, new_values)
        except Exception as e:
            print(f"An error occurred while updating the document: {e}")

    def delete(self, collection_name, query):
        try:
            self.db[collection_name].delete_one(query)
        except Exception as e:
            print(f"An error occurred while deleting the document: {e}")


if __name__ == "__main__":
    db = MongoDBHelper()
