import json
from config import flask_app_path, encryption_key
from cryptography.fernet import Fernet


class EncryptionHelper:
    def __init__(self):
        #self.key = self.get_key()
        self.key = encryption_key

    def create_new_key(self):
        key = Fernet.generate_key()
        with open('encryptionkey.json', 'w') as f:
            json.dump({'key': key.decode()}, f)

    def get_key(self):
        try:
            path = flask_app_path + "encryptionkey.json"
            
            with open(path, 'r') as f:
                data = json.load(f)
                return data['key']

        except FileNotFoundError:
            return False
            """self.create_new_key()
            with open('encryptionkey.json', 'r') as f:
                data = json.load(f)
                return data['key']"""

    def encrypt_message(self, message):
        cipher_suite = Fernet(self.key)
        encrypted_message = cipher_suite.encrypt(message.encode())
        encrypted_message_number = self.string_to_number(encrypted_message)
        return encrypted_message_number

    def decrypt_message(self, encrypted_message_number):
        #try:
            cipher_suite = Fernet(self.key)
            encrypted_message = self.number_to_string(encrypted_message_number)
            decrypted_message = cipher_suite.decrypt(bytes(encrypted_message, 'utf-8')).decode()
            return decrypted_message
        #except Exception as e:
            #return False
    
    def string_to_number(self, string):    
        encoded_string = string.decode('utf-8')
        bytes_representation = bytes(encoded_string, 'utf-8')
        hex_representation = bytes_representation.hex()
        return hex_representation


    def number_to_string(self, hex_string):
        if len(hex_string) % 2 != 0:
            hex_string = '0' + hex_string
        encoded_bytes = bytes.fromhex(hex_string)
        string = encoded_bytes.decode('utf-8')
        return string


if __name__ == "__main__":
    eh = EncryptionHelper()