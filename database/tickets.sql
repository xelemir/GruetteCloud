CREATE TABLE
  `tickets` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `name` varchar(1000) DEFAULT NULL,
    `email` varchar(200) DEFAULT NULL,
    `username` varchar(500) DEFAULT NULL,
    `message` varchar(5000) DEFAULT NULL,
    `status` varchar(255) DEFAULT 'opened',
    `assigned_to` varchar(255) DEFAULT NULL,
    PRIMARY KEY (`id`)
  )