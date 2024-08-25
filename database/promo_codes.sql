CREATE TABLE
  `promo_codes` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `code` varchar(50) DEFAULT NULL,
    `type` varchar(255) DEFAULT 'single_use',
    PRIMARY KEY (`id`)
  )