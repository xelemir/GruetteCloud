CREATE TABLE
  `finance_receipt_items` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `receipt_id` varchar(255) DEFAULT NULL,
    `item` varchar(255) DEFAULT NULL,
    `price` varchar(25) DEFAULT NULL,
    PRIMARY KEY (`id`)
  ) ENGINE = InnoDB AUTO_INCREMENT = 468 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci