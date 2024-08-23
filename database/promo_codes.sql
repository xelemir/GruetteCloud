CREATE TABLE
  `promo_codes` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `code` varchar(50) DEFAULT NULL,
    `type` varchar(255) DEFAULT 'single_use',
    PRIMARY KEY (`id`)
  ) ENGINE = InnoDB AUTO_INCREMENT = 29 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci