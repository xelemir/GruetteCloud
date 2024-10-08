CREATE TABLE
  `users` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `username` varchar(500) NOT NULL,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `password` varchar(4000) NOT NULL,
    `email` varchar(2000) NOT NULL,
    `is_email_verified` tinyint(1) NOT NULL,
    `has_premium` tinyint(1) NOT NULL,
    `ai_personality` varchar(255) NOT NULL,
    `verification_code` varchar(255) DEFAULT NULL,
    `is_2fa_enabled` tinyint(1) DEFAULT 0,
    `2fa_secret_key` varchar(100) DEFAULT '0',
    `is_admin` tinyint(1) DEFAULT 0,
    `is_verified` tinyint(1) DEFAULT 0,
    `receive_emails` tinyint(1) DEFAULT 1,
    `profile_picture` varchar(255) DEFAULT 'purple',
    `default_app` varchar(255) DEFAULT 'chat',
    `phone` varchar(255) DEFAULT '0',
    `first_name` varchar(100) DEFAULT '0',
    `last_name` varchar(200) DEFAULT '0',
    `advanced_darkmode` tinyint(1) DEFAULT 0,
    `finance_budget` int(11) DEFAULT 0,
    `ai_model` varchar(255) DEFAULT 'gpt-4o-mini',
    PRIMARY KEY (`id`)
  )

