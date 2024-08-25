CREATE TABLE
  `finance_receipt_items` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `receipt_id` varchar(255) DEFAULT NULL,
    `item` varchar(255) DEFAULT NULL,
    `price` varchar(25) DEFAULT NULL,
    PRIMARY KEY (`id`)
  )