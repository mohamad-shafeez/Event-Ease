-- ============================================
-- EventEase Database Schema
-- Version: 1.0 (Combined & Consolidating All Phases)
-- ============================================

CREATE DATABASE IF NOT EXISTS eventease_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE eventease_db;

-- ============================================
-- 1. USERS
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(100) NOT NULL,
    email             VARCHAR(150) NOT NULL UNIQUE,
    password_hash     VARCHAR(255) NOT NULL,
    role              ENUM('admin','creator','user') NOT NULL DEFAULT 'user',
    avatar            VARCHAR(255) DEFAULT NULL,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_banned         TINYINT(1) DEFAULT 0,
    phone             VARCHAR(20) DEFAULT NULL,
    bio               TEXT DEFAULT NULL,
    organization_name VARCHAR(255) DEFAULT NULL,
    website_url       VARCHAR(255) DEFAULT NULL,
    preferences       TEXT DEFAULT NULL,
    city              VARCHAR(100) DEFAULT NULL,
    INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB;

-- ============================================
-- 2. EVENTS
-- ============================================
CREATE TABLE IF NOT EXISTS events (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    creator_id      INT NOT NULL,
    title           VARCHAR(255) NOT NULL,
    type            ENUM('concert','tech_conference','workshop','sports',
                         'wedding','exhibition','webinar','food_festival',
                         'charity','comedy') NOT NULL,
    description     TEXT,
    date_start      DATETIME NOT NULL,
    date_end        DATETIME DEFAULT NULL,
    venue           VARCHAR(255) DEFAULT NULL,
    city            VARCHAR(100) DEFAULT NULL,
    capacity        INT DEFAULT 0,
    price           DECIMAL(10,2) DEFAULT 0.00,
    banner          VARCHAR(255) DEFAULT NULL,
    status          ENUM('draft','published','cancelled','upcoming','live','ended') DEFAULT 'draft',
    registered      INT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_events_type (type),
    INDEX idx_events_status (status),
    INDEX idx_events_date_start (date_start),
    INDEX idx_events_creator (creator_id)
) ENGINE=InnoDB;

-- ============================================
-- 3. EVENT DETAILS (type-specific config)
-- ============================================
CREATE TABLE IF NOT EXISTS event_details (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    event_id        INT NOT NULL,
    field_key       VARCHAR(100) NOT NULL,
    field_value     TEXT,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    INDEX idx_ed_event (event_id)
) ENGINE=InnoDB;

-- ============================================
-- 4. REGISTRATIONS
-- ============================================
CREATE TABLE IF NOT EXISTS registrations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    event_id        INT NOT NULL,
    ticket_code     VARCHAR(50) NOT NULL UNIQUE,
    qr_path         VARCHAR(255) DEFAULT NULL,
    status          ENUM('confirmed','pending','cancelled','checked_in') DEFAULT 'pending',
    paid_at         TIMESTAMP NULL DEFAULT NULL,
    checked_in      TINYINT(1) DEFAULT 0,
    checked_in_at   DATETIME DEFAULT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    INDEX idx_reg_user (user_id),
    INDEX idx_reg_event (event_id),
    INDEX idx_reg_ticket (ticket_code)
) ENGINE=InnoDB;

-- ============================================
-- 5. REGISTRATION ANSWERS (form responses)
-- ============================================
CREATE TABLE IF NOT EXISTS registration_answers (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    registration_id   INT NOT NULL,
    question_key      VARCHAR(100) NOT NULL,
    answer            TEXT,
    FOREIGN KEY (registration_id) REFERENCES registrations(id) ON DELETE CASCADE,
    INDEX idx_ra_reg (registration_id)
) ENGINE=InnoDB;

-- ============================================
-- 6. PAYMENTS
-- ============================================
CREATE TABLE IF NOT EXISTS payments (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    registration_id   INT NOT NULL,
    amount            DECIMAL(10,2) NOT NULL,
    method            VARCHAR(50) DEFAULT 'online',
    txn_id            VARCHAR(100) DEFAULT NULL,
    status            ENUM('success','pending','failed','refunded') DEFAULT 'pending',
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (registration_id) REFERENCES registrations(id) ON DELETE CASCADE,
    INDEX idx_pay_reg (registration_id),
    INDEX idx_pay_status (status)
) ENGINE=InnoDB;

-- ============================================
-- 7. ANALYTICS
-- ============================================
CREATE TABLE IF NOT EXISTS analytics (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    event_id        INT NOT NULL,
    views           INT DEFAULT 0,
    date            DATE NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    INDEX idx_ana_event (event_id),
    INDEX idx_ana_date (date)
) ENGINE=InnoDB;

-- ============================================
-- 8. AI LOGS
-- ============================================
CREATE TABLE IF NOT EXISTS ai_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    prompt          TEXT NOT NULL,
    response        TEXT,
    model_used      VARCHAR(50),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_ai_user (user_id)
) ENGINE=InnoDB;

-- ============================================
-- 9. PLATFORM SETTINGS
-- ============================================
CREATE TABLE IF NOT EXISTS platform_settings (
  setting_key   VARCHAR(100) PRIMARY KEY,
  setting_value TEXT,
  updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Initialize default settings
INSERT IGNORE INTO platform_settings (setting_key, setting_value) VALUES
('platform_name', 'EventEase'),
('tagline', 'Discover & Host Amazing Events'),
('support_email', 'support@eventease.com'),
('max_tickets_per_user', '5'),
('allow_guest_browsing', 'true'),
('maintenance_mode', 'false');

-- ============================================
-- 10. WAITLIST
-- ============================================
CREATE TABLE IF NOT EXISTS waitlist (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    event_id   INT NOT NULL,
    email      VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- 11. PASSWORD RESETS
-- ============================================
CREATE TABLE IF NOT EXISTS password_resets (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  token      VARCHAR(64) NOT NULL UNIQUE,
  expires_at DATETIME NOT NULL,
  used       TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- 12. CONVERSATIONS
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  user_id         INT NOT NULL,
  creator_id      INT NOT NULL,
  event_id        INT DEFAULT NULL,
  last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================
-- 13. MESSAGES
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  conversation_id INT NOT NULL,
  sender_id       INT NOT NULL,
  message_text    TEXT NOT NULL,
  is_read         TINYINT(1) DEFAULT 0,
  sent_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
  FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- 14. REVIEWS
-- ============================================
CREATE TABLE IF NOT EXISTS reviews (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  event_id     INT NOT NULL,
  user_id      INT NOT NULL,
  rating       TINYINT NOT NULL,
  review_text  TEXT DEFAULT NULL,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- 15. SAVED EVENTS
-- ============================================
CREATE TABLE IF NOT EXISTS saved_events (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  user_id  INT NOT NULL,
  event_id INT NOT NULL,
  saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  UNIQUE KEY unique_save (user_id, event_id)
) ENGINE=InnoDB;

-- ============================================
-- 16. CREATOR FOLLOWS
-- ============================================
CREATE TABLE IF NOT EXISTS creator_follows (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  follower_id INT NOT NULL,
  creator_id  INT NOT NULL,
  followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY unique_follow (follower_id, creator_id)
) ENGINE=InnoDB;

-- ============================================
-- 17. NOTIFICATIONS
-- ============================================
CREATE TABLE IF NOT EXISTS notifications (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  message    TEXT NOT NULL,
  link       VARCHAR(255) DEFAULT NULL,
  is_read    TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;
