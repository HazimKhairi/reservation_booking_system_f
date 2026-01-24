-- Library Room Reservation System - Database Migration
-- Run this script to add payment functionality to an existing database

USE library_reservation;

-- Add price_per_hour to rooms if it doesn't exist
SET @dbname = DATABASE();
SET @tablename = 'rooms';
SET @columnname = 'price_per_hour';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname) > 0,
  'SELECT 1',
  'ALTER TABLE rooms ADD COLUMN price_per_hour DECIMAL(10, 2) NOT NULL DEFAULT 10.00 AFTER equipment'
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Update rooms with default prices if null
UPDATE rooms SET price_per_hour = 10.00 WHERE price_per_hour IS NULL;
UPDATE rooms SET price_per_hour = 5.00 WHERE name LIKE '%Study%' AND price_per_hour = 10.00;
UPDATE rooms SET price_per_hour = 15.00 WHERE name LIKE '%Conference%' AND price_per_hour = 10.00;
UPDATE rooms SET price_per_hour = 3.00 WHERE name LIKE '%Pod%' AND price_per_hour = 10.00;
UPDATE rooms SET price_per_hour = 20.00 WHERE name LIKE '%Media%' AND price_per_hour = 10.00;

-- Add bank details to users if they don't exist
SET @columnname = 'bank_name';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'users' AND COLUMN_NAME = @columnname) > 0,
  'SELECT 1',
  'ALTER TABLE users ADD COLUMN bank_name VARCHAR(100) AFTER role'
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'bank_account_number';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'users' AND COLUMN_NAME = @columnname) > 0,
  'SELECT 1',
  'ALTER TABLE users ADD COLUMN bank_account_number VARCHAR(50) AFTER bank_name'
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'bank_account_holder';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'users' AND COLUMN_NAME = @columnname) > 0,
  'SELECT 1',
  'ALTER TABLE users ADD COLUMN bank_account_holder VARCHAR(100) AFTER bank_account_number'
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Modify reservations status to include 'pending'
ALTER TABLE reservations MODIFY COLUMN status ENUM('pending', 'confirmed', 'cancelled') NOT NULL DEFAULT 'pending';

-- Create payments table if it doesn't exist
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reservation_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    bank_name VARCHAR(100),
    account_number VARCHAR(50),
    account_holder VARCHAR(100),
    transaction_id VARCHAR(100) UNIQUE,
    status ENUM('pending', 'completed', 'failed', 'refunded') NOT NULL DEFAULT 'pending',
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create index for faster payment lookups
CREATE INDEX IF NOT EXISTS idx_payments_transaction ON payments(transaction_id);

-- Update admin password (password: admin123)
UPDATE users SET password_hash = '$2b$12$vyUfLVObe3wMChv9rtH4B.gpjgoongW.a0HARvhpsenzE7rnDjIWC' WHERE username = 'admin';

-- Delete test patron if exists (for clean re-testing)
DELETE FROM users WHERE username = 'testpatron';

SELECT 'Migration completed successfully!' AS status;
