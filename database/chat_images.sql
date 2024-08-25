create table
  `chat_images` (
    `id` int unsigned NOT NULL AUTO_INCREMENT,
    `created_at` timestamp not null default CURRENT_TIMESTAMP,
    `filename` varchar(255) null,
		`author_id` int(10) unsigned DEFAULT NULL,
    `recipient_id` int(10) unsigned DEFAULT NULL,
    `last_accessed_by_author` timestamp null default CURRENT_TIMESTAMP,
    `last_accessed_by_recipient` timestamp null default CURRENT_TIMESTAMP,
    `chat_message_id` int(10) unsigned DEFAULT NULL,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`recipient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`chat_message_id`) REFERENCES `chats` (`id`) ON DELETE CASCADE
  );