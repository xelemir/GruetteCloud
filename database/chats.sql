CREATE TABLE
  `chats` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `author_id` int(10) unsigned,
    `recipient_id` int(10) unsigned,
    `message_content` varchar(5000),
    `is_read` tinyint(1) DEFAULT 0,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`recipient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
  ) ENGINE = InnoDB AUTO_INCREMENT = 272 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci