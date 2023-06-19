import json
from config import url_suffix
import bcrypt
from credentials import url_suffix
from cryptography.fernet import Fernet


class EncryptionHelper:
    def __init__(self):
        self.key = self.get_key()

    def create_new_key(self):
        key = Fernet.generate_key()
        with open('encryptionkey.json', 'w') as f:
            json.dump({'key': key.decode()}, f)

    def get_key(self):
        try:
            if url_suffix == "/gruettechat":
                path = "/home/jan/wwwroot/gruettechat/gruettechat/app/encryptionkey.json"
            else:
                path = "encryptionkey.json"
            with open(path, 'r') as f:
                data = json.load(f)
                return data['key']

        except FileNotFoundError:
            self.create_new_key()
            with open('encryptionkey.json', 'r') as f:
                data = json.load(f)
                return data['key']

    def encrypt_message(self, message):
        cipher_suite = Fernet(self.key)
        encrypted_message = cipher_suite.encrypt(message.encode())
        encrypted_message_number = self.string_to_number(encrypted_message)
        return encrypted_message_number

    def decrypt_message(self, encrypted_message_number):
        try:
            cipher_suite = Fernet(self.key)
            encrypted_message = self.number_to_string(encrypted_message_number)
            decrypted_message = cipher_suite.decrypt(bytes(encrypted_message, 'utf-8')).decode()
            return decrypted_message
        except Exception as e:
            return False
    
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

    # Hashes and salts the provided password
    def hash_password(self, password):
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        return hashed_password.decode('utf-8')

    # Verifies if the provided password matches the hashed password
    def check_password(self, password, hashed_password):
        return bcrypt.checkpw(password.encode(), hashed_password.encode())


if __name__ == "__main__":
    eh = EncryptionHelper()

    my_test_message = "This is a test message"
    encrypted_message = eh.encrypt_message(my_test_message)
    print(encrypted_message)
    decrypted_message = eh.decrypt_message(encrypted_message)
    print(decrypted_message)

    password = "mysecretpassword"
    hashed_password = eh.hash_password(password)
    print(hashed_password)
    is_password_correct = eh.check_password(password, hashed_password)
    print(is_password_correct)
