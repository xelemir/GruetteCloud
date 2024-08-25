CREATE TABLE
  `drive_links` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `file_path` varchar(5000) DEFAULT NULL,
    `user_id` int(10) unsigned,
    `short_code` varchar(255) DEFAULT NULL,
    `name` varchar(1000) DEFAULT NULL,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
  )