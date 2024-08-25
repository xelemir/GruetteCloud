CREATE TABLE
  `platform_notifications` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `content` varchar(5000) DEFAULT NULL,
    `subject` varchar(255) DEFAULT NULL,
    `color` varchar(255) DEFAULT NULL,
    `link` varchar(1000) DEFAULT NULL,
    `decorator` varchar(255) DEFAULT NULL,
    PRIMARY KEY (`id`)
  )