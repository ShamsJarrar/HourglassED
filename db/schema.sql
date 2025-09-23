CREATE DATABASE IF NOT EXISTS hourglassed_db;
USE hourglassed_db;

CREATE TABLE IF NOT EXISTS users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  name VARCHAR(100) NOT NULL,
  is_verified BOOLEAN DEFAULT FALSE,
  otp_code VARCHAR(6),
  otp_expiration DATETIME
);

CREATE TABLE IF NOT EXISTS event_classes (
  class_id INT AUTO_INCREMENT PRIMARY KEY,
  class_name VARCHAR(255) NOT NULL,
  is_builtin BOOLEAN DEFAULT FALSE,
  created_by INT DEFAULT NULL,
  FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
  UNIQUE (class_name, created_by)
);


CREATE TABLE IF NOT EXISTS recurrence_series (
  series_id INT AUTO_INCREMENT PRIMARY KEY,
  recurrence_pattern VARCHAR(255) NOT NULL,
  recurrence_end DATETIME NULL,
  user_id INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS events (
  event_id INT AUTO_INCREMENT PRIMARY KEY,
  event_type INT NOT NULL,
  header VARCHAR(255),
  title VARCHAR(255) NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  color VARCHAR(20) DEFAULT '#FFD700',
  notes TEXT,
  user_id INT NOT NULL,
  series_id INT DEFAULT NULL,
  is_exception BOOLEAN NOT NULL DEFAULT FALSE,
  timezone VARCHAR(64) DEFAULT 'UTC', 
  FOREIGN KEY (event_type) REFERENCES event_classes(class_id) ON DELETE RESTRICT,
  FOREIGN KEY (series_id) REFERENCES recurrence_series(series_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);



CREATE TABLE IF NOT EXISTS friend_requests (
  request_id INT AUTO_INCREMENT PRIMARY KEY,
  sender_id INT NOT NULL,
  receiver_id INT NOT NULL,
  status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS friends (
  user_id INT NOT NULL,
  friend_id INT NOT NULL,
  PRIMARY KEY (user_id, friend_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (friend_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_invitations (
  invitation_id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  invited_user_id INT NOT NULL,
  status ENUM('pending', 'accepted', 'rejected', 'withdrawn', 'removed', 'expired') NOT NULL DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
  FOREIGN KEY (invited_user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_proposals (
  proposal_id       BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id           INT NOT NULL,
  proposal_type     ENUM('create_event','update_event','delete_event','batch_plan') NOT NULL,
  target_event_id   INT NULL,                         -- for update/delete; NULL for create/batch
  payload_json      JSON NOT NULL,                    -- data needed to perform the change on approval
  diff_json         JSON NOT NULL,                    -- before → after (for UI)
  reasoning_summary VARCHAR(255) NOT NULL,            -- short human-readable reason
  status            ENUM('pending','committed','rejected','expired') NOT NULL DEFAULT 'pending',
  expires_at        DATETIME NOT NULL,                -- store in UTC
  created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_agent_proposals_user
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_agent_proposals_event
    FOREIGN KEY (target_event_id) REFERENCES events(event_id) ON DELETE SET NULL,

  INDEX idx_agent_proposals_user_status (user_id, status),
  INDEX idx_agent_proposals_expires (expires_at)
);

CREATE TABLE IF NOT EXISTS agent_audit_log (
  log_id       BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id      INT NOT NULL,
  proposal_id  BIGINT NULL,
  event        VARCHAR(120) NOT NULL,   -- e.g., 'propose_update_event', 'approve_proposal'
  payload_json JSON NULL,               -- trimmed args/outputs (no secrets/tokens)
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_audit_user
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_audit_proposal
    FOREIGN KEY (proposal_id) REFERENCES agent_proposals(proposal_id) ON DELETE SET NULL,

  INDEX idx_audit_user_created (user_id, created_at)
);

CREATE TABLE IF NOT EXISTS agent_user_prefs (
  user_id        INT PRIMARY KEY,
  timezone       VARCHAR(64) NOT NULL DEFAULT 'UTC',
  study_windows  JSON NULL,        -- e.g. [{"dow":["Mon","Wed","Thu"],"start":"19:00","end":"21:00"}]
  no_go_windows  JSON NULL,        -- e.g. [{"dow":["Fri"],"start":"12:00","end":"14:00"}]
  session_len_m  INT NOT NULL DEFAULT 90,   -- preferred study session length (minutes)
  buffer_min     INT NOT NULL DEFAULT 10,   -- min buffer between sessions (minutes)
  naming_rules   JSON NULL,        -- e.g. {"study_prefix":"Study: "}
  course_prefs   JSON NULL,        -- e.g. {"Algorithms":{"difficulty":4,"target_hours":12}}
  updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_prefs_user
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);