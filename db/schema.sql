CREATE DATABASE IF NOT EXISTS hourglassed_db;
USE hourglassed_db;

CREATE TABLE IF NOT EXISTS users (  user_id INT AUTO_INCREMENT PRIMARY KEY,     email VARCHAR(255) NOT NULL UNIQUE,     password VARCHAR(255) NOT NULL,     name VARCHAR(100) NOT NULL);

CREATE TABLE IF NOT EXISTS event_classes (  class_id INT AUTO_INCREMENT PRIMARY KEY,     class_name VARCHAR(255) NOT NULL UNIQUE,     is_builtin BOOLEAN DEFAULT FALSE);

CREATE TABLE IF NOT EXISTS events (  event_id INT AUTO_INCREMENT PRIMARY KEY,     event_type INT,     header VARCHAR(255),     title VARCHAR(255),     start_time DATETIME NOT NULL,     end_time DATETIME NOT NULL,     recurrence_pattern VARCHAR(255),     color VARCHAR(20),     notes TEXT,     linked_event_id INT,     user_id INT NOT NULL,     FOREIGN KEY (event_type) REFERENCES event_classes(class_id) ON DELETE SET NULL,     FOREIGN KEY (linked_event_id) REFERENCES events(event_id) ON DELETE SET NULL,     FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE );

CREATE TABLE IF NOT EXISTS shared_events (  id INT AUTO_INCREMENT PRIMARY KEY,     event_id INT NOT NULL,     user_id INT NOT NULL,     FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,     FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE );





