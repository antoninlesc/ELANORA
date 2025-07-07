-- *********************************************
-- * PROJECT ELANORA V7
-- *--------------------------------------------
-- * Enhanced with better data types, constraints, and structure
-- * Based on sourceV2 best practices
-- * Generation date: Mon Jul  7 2025 
-- ********************************************* 

-- Database Section
-- ________________ 

-- CREATE DATABASE `anto-schema-relationnal`;
-- USE `anto-schema-relationnal`;

-- Tables Section
-- _____________ 

CREATE TABLE USER (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP NULL
);

CREATE TABLE INSTANCE (
    instance_id INT PRIMARY KEY AUTO_INCREMENT,
    instance_name VARCHAR(100) NOT NULL,
    institution_name VARCHAR(100) NOT NULL,
    contact_email VARCHAR(100) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    default_language VARCHAR(10) NOT NULL DEFAULT 'en',
    max_file_size_mb DECIMAL(10,2) NOT NULL DEFAULT 100.00,
    max_users INT NOT NULL DEFAULT 1000,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE PROJECT (
    project_id INT PRIMARY KEY AUTO_INCREMENT,
    project_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    instance_id INT NOT NULL,
    FOREIGN KEY (instance_id) REFERENCES INSTANCE(instance_id) ON DELETE CASCADE
);

CREATE TABLE ELAN_FILE (
    elan_id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE
);

CREATE TABLE ANNOTATION_STANDARD (
    standard_id VARCHAR(50) PRIMARY KEY,
    standard_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    regex VARCHAR(500) NOT NULL
);

CREATE TABLE TIER (
    tier_id VARCHAR(50) PRIMARY KEY,
    tier_name VARCHAR(100) NOT NULL,
    parent_tier_id VARCHAR(50) NULL,
    FOREIGN KEY (parent_tier_id) REFERENCES TIER(tier_id) ON DELETE CASCADE
);

CREATE TABLE ANNOTATION (
    annotation_id VARCHAR(50) PRIMARY KEY,
    annotation_value TEXT NOT NULL,
    start_time DECIMAL(10,3) NOT NULL,
    end_time DECIMAL(10,3) NOT NULL,
    tier_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (tier_id) REFERENCES TIER(tier_id) ON DELETE CASCADE
);

CREATE TABLE CONFLICT (
    conflict_id VARCHAR(50) PRIMARY KEY,
    conflict_type ENUM('annotation_overlap', 'tier_mismatch', 'value_difference', 'structural', 'other') NOT NULL,
    conflict_description TEXT NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL DEFAULT 'medium',
    status ENUM('detected', 'in_progress', 'resolved', 'dismissed') NOT NULL DEFAULT 'detected',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    resolved_by INT NULL,
    project_id INT NOT NULL,
    FOREIGN KEY (resolved_by) REFERENCES USER(user_id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES PROJECT(project_id) ON DELETE CASCADE
);

CREATE TABLE COMMENT (
    comment_id VARCHAR(50) PRIMARY KEY,
    content TEXT NOT NULL,
    target_type ENUM('project', 'elan_file', 'conflict', 'tier', 'annotation') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INT NOT NULL,
    parent_comment_id VARCHAR(50) NULL,
    FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES COMMENT(comment_id) ON DELETE CASCADE
);

CREATE TABLE INVITATION (
    invitationID VARCHAR(50) PRIMARY KEY,
    project_permission ENUM('read', 'write', 'admin', 'owner') NOT NULL DEFAULT 'read',
    status ENUM('pending', 'accepted', 'rejected', 'expired') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    responded_at TIMESTAMP NULL,
    sender INT NOT NULL,
    receiver INT NOT NULL,
    project_id INT NOT NULL,
    FOREIGN KEY (sender) REFERENCES USER(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver) REFERENCES USER(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES PROJECT(project_id) ON DELETE CASCADE
);

-- Junction Tables
-- _______________

CREATE TABLE ELAN_FILE_TO_PROJECT (
    elan_id INT NOT NULL,
    project_id INT NOT NULL,
    PRIMARY KEY (elan_id, project_id),
    FOREIGN KEY (elan_id) REFERENCES ELAN_FILE(elan_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES PROJECT(project_id) ON DELETE CASCADE
);

CREATE TABLE ELAN_FILE_TO_TIER (
    elan_id INT NOT NULL,
    tier_id VARCHAR(50) NOT NULL,
    PRIMARY KEY (tier_id, elan_id),
    FOREIGN KEY (tier_id) REFERENCES TIER(tier_id) ON DELETE CASCADE,
    FOREIGN KEY (elan_id) REFERENCES ELAN_FILE(elan_id) ON DELETE CASCADE
);

CREATE TABLE PROJECT_ANNOT_STANDARD (
    standard_id VARCHAR(50) NOT NULL,
    project_id INT NOT NULL,
    PRIMARY KEY (project_id, standard_id),
    FOREIGN KEY (project_id) REFERENCES PROJECT(project_id) ON DELETE CASCADE,
    FOREIGN KEY (standard_id) REFERENCES ANNOTATION_STANDARD(standard_id) ON DELETE CASCADE
);

CREATE TABLE USER_TO_PROJECT (
    project_id INT NOT NULL,
    user_id INT NOT NULL,
    permission ENUM('read', 'write', 'admin', 'owner') NOT NULL DEFAULT 'read',
    PRIMARY KEY (user_id, project_id),
    FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES PROJECT(project_id) ON DELETE CASCADE
);

CREATE TABLE USER_WORK_ON_CONFLICT (
    conflict_id VARCHAR(50) NOT NULL,
    user_id INT NOT NULL,
    PRIMARY KEY (user_id, conflict_id),
    FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE,
    FOREIGN KEY (conflict_id) REFERENCES CONFLICT(conflict_id) ON DELETE CASCADE
);

CREATE TABLE CONFLICT_OF_ELAN_FILE (
    conflict_id VARCHAR(50) NOT NULL,
    elan_id INT NOT NULL,
    PRIMARY KEY (elan_id, conflict_id),
    FOREIGN KEY (elan_id) REFERENCES ELAN_FILE(elan_id) ON DELETE CASCADE,
    FOREIGN KEY (conflict_id) REFERENCES CONFLICT(conflict_id) ON DELETE CASCADE
);

-- Comment Association Tables
-- __________________________

CREATE TABLE COMMENT_PROJECT (
    comment_id VARCHAR(50) PRIMARY KEY,
    project_id INT NOT NULL,
    FOREIGN KEY (comment_id) REFERENCES COMMENT(comment_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES PROJECT(project_id) ON DELETE CASCADE
);

CREATE TABLE COMMENT_ELAN_FILE (
    comment_id VARCHAR(50) PRIMARY KEY,
    elan_id INT NOT NULL,
    FOREIGN KEY (comment_id) REFERENCES COMMENT(comment_id) ON DELETE CASCADE,
    FOREIGN KEY (elan_id) REFERENCES ELAN_FILE(elan_id) ON DELETE CASCADE
);

CREATE TABLE COMMENT_CONFLICT (
    comment_id VARCHAR(50) PRIMARY KEY,
    conflict_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (comment_id) REFERENCES COMMENT(comment_id) ON DELETE CASCADE,
    FOREIGN KEY (conflict_id) REFERENCES CONFLICT(conflict_id) ON DELETE CASCADE
);

-- Indexes Section
-- _____________ 

-- User indexes
CREATE INDEX idx_user_email ON USER(email);
CREATE INDEX idx_user_username ON USER(username);
CREATE INDEX idx_user_active ON USER(is_active);
CREATE INDEX idx_user_last_login ON USER(last_login);

-- Instance indexes
CREATE INDEX idx_instance_name ON INSTANCE(instance_name);
CREATE INDEX idx_instance_active ON INSTANCE(is_active);

-- Project indexes
CREATE INDEX idx_project_name ON PROJECT(project_name);
CREATE INDEX idx_project_instance ON PROJECT(instance_id);

-- ELAN File indexes
CREATE INDEX idx_elan_filename ON ELAN_FILE(filename);
CREATE INDEX idx_elan_user ON ELAN_FILE(user_id);

-- Annotation indexes
CREATE INDEX idx_annotation_tier ON ANNOTATION(tier_id);
CREATE INDEX idx_annotation_time ON ANNOTATION(start_time, end_time);

-- Tier indexes
CREATE INDEX idx_tier_name ON TIER(tier_name);
CREATE INDEX idx_tier_parent ON TIER(parent_tier_id);

-- Conflict indexes
CREATE INDEX idx_conflict_project ON CONFLICT(project_id);
CREATE INDEX idx_conflict_status ON CONFLICT(status);
CREATE INDEX idx_conflict_severity ON CONFLICT(severity);
CREATE INDEX idx_conflict_type ON CONFLICT(conflict_type);
CREATE INDEX idx_conflict_resolved_by ON CONFLICT(resolved_by);

-- Comment indexes
CREATE INDEX idx_comment_user ON COMMENT(user_id);
CREATE INDEX idx_comment_parent ON COMMENT(parent_comment_id);
CREATE INDEX idx_comment_target_type ON COMMENT(target_type);
CREATE INDEX idx_comment_created ON COMMENT(created_at);

-- Invitation indexes
CREATE INDEX idx_invitation_sender ON INVITATION(sender);
CREATE INDEX idx_invitation_receiver ON INVITATION(receiver);
CREATE INDEX idx_invitation_project ON INVITATION(project_id);
CREATE INDEX idx_invitation_status ON INVITATION(status);
CREATE INDEX idx_invitation_expires ON INVITATION(expires_at);

-- Junction table indexes
CREATE INDEX idx_user_project_permission ON USER_TO_PROJECT(permission);
CREATE INDEX idx_elan_project_project ON ELAN_FILE_TO_PROJECT(project_id);
CREATE INDEX idx_elan_tier_elan ON ELAN_FILE_TO_TIER(elan_id);

-- Triggers Section
-- _______________

DELIMITER //

CREATE TRIGGER update_user_timestamp
    BEFORE UPDATE ON USER
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //

CREATE TRIGGER update_instance_timestamp
    BEFORE UPDATE ON INSTANCE
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //

CREATE TRIGGER check_invitation_expiry
    BEFORE UPDATE ON INVITATION
    FOR EACH ROW
BEGIN
    IF NEW.expires_at < CURRENT_TIMESTAMP AND OLD.status = 'pending' THEN
        SET NEW.status = 'expired';
    END IF;
END //

CREATE TRIGGER update_conflict_resolved_time
    BEFORE UPDATE ON CONFLICT
    FOR EACH ROW
BEGIN
    IF NEW.status = 'resolved' AND OLD.status != 'resolved' THEN
        SET NEW.resolved_at = CURRENT_TIMESTAMP;
    END IF;
END //

DELIMITER ;

-- Views Section
-- ____________

CREATE VIEW user_projects AS
SELECT 
    u.user_id,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    u.is_active,
    p.project_id,
    p.project_name,
    p.description as project_description,
    utp.permission as project_permission
FROM USER u
JOIN USER_TO_PROJECT utp ON u.user_id = utp.user_id
JOIN PROJECT p ON utp.project_id = p.project_id
WHERE u.is_active = TRUE;

CREATE VIEW project_files AS
SELECT 
    p.project_id,
    p.project_name,
    ef.elan_id,
    ef.filename,
    ef.file_path,
    ef.file_size,
    u.username as uploaded_by
FROM PROJECT p
JOIN ELAN_FILE_TO_PROJECT efp ON p.project_id = efp.project_id
JOIN ELAN_FILE ef ON efp.elan_id = ef.elan_id
JOIN USER u ON ef.user_id = u.user_id;

CREATE VIEW active_conflicts AS
SELECT 
    c.conflict_id,
    c.conflict_type,
    c.conflict_description,
    c.severity,
    c.status,
    c.detected_at,
    p.project_name,
    u.username as resolved_by_user
FROM CONFLICT c
JOIN PROJECT p ON c.project_id = p.project_id
LEFT JOIN USER u ON c.resolved_by = u.user_id
WHERE c.status IN ('detected', 'in_progress');

-- Stored Procedures Section
-- ________________________

DELIMITER //

CREATE PROCEDURE AddUserToProject(
    IN p_user_id INT,
    IN p_project_id INT,
    IN p_permission ENUM('read', 'write', 'admin')
)
BEGIN
    INSERT INTO USER_TO_PROJECT (user_id, project_id, permission)
    VALUES (p_user_id, p_project_id, p_permission)
    ON DUPLICATE KEY UPDATE 
        permission = p_permission;
END //

CREATE PROCEDURE RemoveUserFromProject(
    IN p_user_id INT,
    IN p_project_id INT
)
BEGIN
    DELETE FROM USER_TO_PROJECT 
    WHERE user_id = p_user_id AND project_id = p_project_id;
END //

CREATE PROCEDURE AcceptInvitation(
    IN p_invitationID VARCHAR(50)
)
BEGIN
    DECLARE v_user_id INT;
    DECLARE v_project_id INT;
    DECLARE v_permission ENUM('read', 'write', 'admin', 'owner');
    
    SELECT receiver, project_id, project_permission 
    INTO v_user_id, v_project_id, v_permission
    FROM INVITATION 
    WHERE invitationID = p_invitationID AND status = 'pending';
    
    IF v_user_id IS NOT NULL THEN
        UPDATE INVITATION 
        SET status = 'accepted', 
            responded_at = CURRENT_TIMESTAMP
        WHERE invitationID = p_invitationID;
        
        INSERT INTO USER_TO_PROJECT (user_id, project_id, permission)
        VALUES (v_user_id, v_project_id, v_permission)
        ON DUPLICATE KEY UPDATE 
            permission = v_permission;
    END IF;
END //

CREATE PROCEDURE RejectInvitation(
    IN p_invitationID VARCHAR(50)
)
BEGIN
    UPDATE INVITATION 
    SET status = 'rejected', 
        responded_at = CURRENT_TIMESTAMP
    WHERE invitationID = p_invitationID AND status = 'pending';
END //

DELIMITER ;