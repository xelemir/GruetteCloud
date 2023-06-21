rs.initiate(
  {
     _id: "rs0",
     members: [
        { _id: 0, host : "mongodb1:27017", priority: 1},
        { _id: 1, host : "mongodb2:27017", priority: 0.5 },
        { _id: 2, host : "mongodb3:27017", priority: 0.5 }
     ]
  }
);


db = db.getSiblingDB('gruetteChatDB');

db.createUser({
  user: 'mainUser',
  pwd: 'pwd',
  roles: [{ role: 'readWrite', db: 'gruetteChatDB' }],
  passwordDigestor: 'server',
  mechanisms: ["SCRAM-SHA-1"]
});