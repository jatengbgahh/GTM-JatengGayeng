CREATE DATABASE IF NOT EXISTS `gtm-jateng-gayeng`;

USE `gtm-jateng-gayeng`;

CREATE TABLE IF NOT EXISTS `event` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `telegram_user_id` BIGINT NOT NULL,
    `telegram_username` VARCHAR(255) NULL,
    `nama_event` VARCHAR(255) NOT NULL,
    `branch` VARCHAR(255) NOT NULL,
    `wok` VARCHAR(255) NOT NULL,
    `latitude` DECIMAL(10, 8) NOT NULL,
    `longitude` DECIMAL(11, 8) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
