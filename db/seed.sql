USE hourglassed_db;

INSERT IGNORE INTO event_classes (class_name, is_builtin) VALUES
('exam', TRUE),
('subject', TRUE),
('study_session', TRUE),
('work', TRUE),
('personal', TRUE),
('extracurricular', TRUE);