-- USER Table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    default_mpesa_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('ACTIVE','INACTIVE','SUSPENDED') DEFAULT 'ACTIVE'
);

-- CATEGORY Table

CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_name VARCHAR(50) NOT NULL,
    category_type ENUM('PREDEFINED','CUSTOM') DEFAULT 'CUSTOM',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ACCOUNT Table (Digital Envelopes + Primary Account)
CREATE TABLE accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_name VARCHAR(50) NOT NULL,
    account_type ENUM('PRIMARY','DIGITAL','SAVINGS') DEFAULT 'DIGITAL',
    category_id INT,
    balance DECIMAL(12,2) DEFAULT 0.00,
    start_date DATE,
    end_date DATE,
    overspend_rule ENUM('BLOCK','WARN','ALLOW') DEFAULT 'BLOCK',
    rollover_rule ENUM('ROLLOVER','RETURN','REALLOCATE') DEFAULT 'ROLLOVER',
    status ENUM('ACTIVE','FROZEN','EXPIRED','CLOSED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
);

-- INCOME_SOURCE Table
CREATE TABLE income_sources (
    income_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    source_name VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    frequency ENUM('MONTHLY','WEEKLY','IRREGULAR') DEFAULT 'MONTHLY',
    next_payment_date DATE,
    target_account_id INT NOT NULL,
    status ENUM('ACTIVE','INACTIVE') DEFAULT 'ACTIVE',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (target_account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
);

-- TRANSACTION Table
CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    source_account_id INT NOT NULL,
    destination_account_id INT,
    category_id INT,
    transaction_type ENUM('ALLOCATION','TRANSFER','PAYMENT','INCOME') NOT NULL,
    payment_type ENUM('SEND_MONEY','PAYBILL','TILL','NONE') DEFAULT 'NONE',
    amount DECIMAL(12,2) NOT NULL,
    status ENUM('PENDING','SUCCESS','FAILED') DEFAULT 'PENDING',
    reference_code VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (source_account_id) REFERENCES accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (destination_account_id) REFERENCES accounts(account_id) ON DELETE SET NULL,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
);

-- MPESA_REQUEST Table
CREATE TABLE mpesa_requests (
    mpesa_request_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NOT NULL,
    from_number VARCHAR(20) NOT NULL,
    to_number VARCHAR(20) NOT NULL,
    payment_type ENUM('SEND_MONEY','PAYBILL','TILL') NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    checkout_request_id VARCHAR(50),
    response_code VARCHAR(20),
    response_description VARCHAR(255),
    status ENUM('PENDING','SUCCESS','FAILED') DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE
);

-- NOTIFICATION Table
CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    notification_type ENUM('PAYMENT','LOW_BALANCE','EXPIRY','GENERAL') DEFAULT 'GENERAL',
    message VARCHAR(255) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
