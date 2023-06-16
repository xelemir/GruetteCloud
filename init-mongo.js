conn = new Mongo('mongodb://mongodb:27017/');

// Access the gruetteChatDB database

db = conn.getDB('gruetteChatDB');

// Create the user in the gruetteChatDB database
db.createUser(
    {
      user: "mainUser",
      pwd: "pwd",
      roles: [ { role: "readWrite", db: "gruetteChatDB" } ]
    }
)

// Create the collections in the gruetteChatDB database
db.createCollection('users');
db.createCollection('messages');
