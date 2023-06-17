conn = new Mongo('mongodb://mongodb:27017/');

// Access the gruetteChatDB database

db = conn.getDB('gruetteChatDB');

// Create the user in the gruetteChatDB database
db.createUser({
  user: 'mainUser',
  pwd: 'pwd',
  roles: [{ role: 'readWrite', db: 'gruetteChatDB' }],
  passwordDigestor: 'server',
  mechanisms: ["SCRAM-SHA-1"]
});
