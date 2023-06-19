db = db.getSiblingDB('gruetteChatDB'); // switch to your db

// Create the user in the gruetteChatDB database
db.createUser({
  user: 'mainUser',
  pwd: 'pwd',
  roles: [{ role: 'readWrite', db: 'gruetteChatDB' }],
  passwordDigestor: 'server',
  mechanisms: ["SCRAM-SHA-1"]
});
