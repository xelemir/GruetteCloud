CREATE TABLE
  `finance_receipts` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `user_id` int(10) unsigned,
    `date` datetime DEFAULT NULL,
    `total` varchar(25) DEFAULT NULL,
    `merchant_name` varchar(255) DEFAULT NULL,
    `receipt_id` varchar(255) DEFAULT NULL,
    `note` varchar(255) DEFAULT NULL,
    `payment_method` varchar(255) DEFAULT NULL,
    `is_income` tinyint(1) DEFAULT 0,
    `add_to_budget` tinyint(1) DEFAULT 0,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
  )