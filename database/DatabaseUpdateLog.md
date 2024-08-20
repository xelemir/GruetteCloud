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

### gruttechat_blocked_users

1. Rename table `gruttechat_blocked_users` to `blocked_users`
2. Rename column `username` to `user_id`
3. Change data type of column `user_id` from `VARCHAR(500)` to `int(10) unsigned`
4. Rename column `blocked_username` to `blocked_user_id`
5. Change data type of column `blocked_user_id` from `VARCHAR(500)` to `int(10) unsigned`
6. Add Foreign Key `user_id` referencing `users(id)`
7. Add Foreign Key `blocked_user_id` referencing `users(id)`

### gruettecloud_receipts

1. Rename table `gruettecloud_receipts` to `finance_receipts`
2. Rename column `username` to `user_id`
3. Change data type of column `user_id` from `VARCHAR(500)` to `int(10) unsigned`
4. Add Foreign Key `user_id` referencing `users(id)`

    **TODO**: Currently, column `id` and `receipt_id` are used. Receipt_ID should be deleted.

### gruettecloud_receipt_items

1. Rename table `gruettecloud_receipt_items` to `finance_receipt_items`

    **TODO**: Currently, column `receipt_id` references `gruettecloud_receipts(receipt_id)`. This should be changed to `finance_receipts(id)` in the future.

### gruttechat_platform_messages

1. Rename table `gruttechat_platform_messages` to `platform_notifications`

### gruttecloud_tickets

1. Rename table `gruttecloud_tickets` to `tickets`

### gruttedrive_files_shared

1. Rename table `gruttedrive_files_shared` to `drive_links`
2. Rename column `owner` to `user_id`
3. Change data type of column `user_id` from `VARCHAR(500)` to `int(10) unsigned`
4. Add Foreign Key `user_id` referencing `users(id)`

### reset_password

1. Rename table `reset_password` to `password_resets`
2. Rename column `username` to `user_id`
3. Change data type of column `user_id` from `VARCHAR(500)` to `int(10) unsigned`
4. Add Foreign Key `user_id` referencing `users(id)`

## Status

| Table Name | Created | Data Migrated |
|------------|---------|---------------|
| `users` | 2024-08-20 | - |
| `chats` | 2024-08-20 | - |
| `blocked_users` | 2024-08-20 | - |
| `finance_receipts` | 2024-08-20 | - |
| `finance_receipt_items` | 2024-08-20 | - |
| `platform_notifications` | 2024-08-20 | - |
| `tickets` | 2024-08-20 | - |
| `drive_links` | 2024-08-20 | - |
| `password_resets` | 2024-08-20 | - |

| Python File Name | Code Updated |
|------------------|--------------|
| `flask_app.py` | 2024-08-20 |
| `loginSignUp_routes.py` | 2024-08-20 |
| `chat_routes.py` | 2024-08-20 |
| `expense_tracker_routes.py` | - |
| `drive_routes.py` | - |
| `settingss_routes.py` | - |
| `tool_routes.py` | - |
| `dashboard_routes.py` | - |
| Folder: pythonHelper | - |

## Notes