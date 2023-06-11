// Connect to the database
db = db.getSiblingDB('grutteChatDB');

// Create user collection
db.createCollection('gruttechat_users');
// Create index for id and username
db.gruttechat_users.createIndex({ id: 1 }, { unique: true });
db.gruttechat_users.createIndex({ username: 1 }, { unique: true });

// Create messages collection
db.createCollection('gruttechat_messages');
// Create index for id
db.gruttechat_messages.createIndex({ id: 1 }, { unique: true });
// Create indexes for username_send and username_receive
db.gruttechat_messages.createIndex({ username_send: 1 });
db.gruttechat_messages.createIndex({ username_receive: 1 });
