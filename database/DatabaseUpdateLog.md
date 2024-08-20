# Database Update Log

This file contains the update logs for the current database update on GrütteCloud

## Logs

### gruttechat_users

1. Renamed table `gruttechat_users` to `users`

### gruttechat_messages

1. Rename table `gruttechat_messages` to `chats`
2. Rename column `username_send` to `content` to `author_id`
3. Change data type of column `author_id` from `VARCHAR(500)` to `int(10) unsigned`
4. Rename column `username_receive` to `content` to `receipient_id`
5. Change data type of column `receipient_id` from `VARCHAR(500)` to `int(10) unsigned`
6. Add Foreign Key `author_id` referencing `users(id)`
7. Add Foreign Key `receipient_id` referencing `users(id)`
