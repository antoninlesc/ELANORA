-- *********************************************
-- * PROJECT ELANORA V4 - IMPROVED VERSION                   
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
    userId INT PRIMARY KEY AUTO_INCREMENT,
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
    instanceId INT PRIMARY KEY AUTO_INCREMENT,
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
    projectId INT PRIMARY KEY AUTO_INCREMENT,
    project_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    instanceId INT NOT NULL,
    FOREIGN KEY (instanceId) REFERENCES INSTANCE(instanceId) ON DELETE CASCADE
);

CREATE TABLE ELAN_FILE (
    elanId INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT NOT NULL,
    userId INT NOT NULL,
    FOREIGN KEY (userId) REFERENCES USER(userId) ON DELETE CASCADE
);

CREATE TABLE ANNOTATION_STANTARD (
    standardId VARCHAR(50) PRIMARY KEY,
    standard_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    regex VARCHAR(500) NOT NULL
);

CREATE TABLE TIER (
    tierId VARCHAR(50) PRIMARY KEY,
    tier_name VARCHAR(100) NOT NULL,
    parent_tierId VARCHAR(50) NULL,
    FOREIGN KEY (parent_tierId) REFERENCES TIER(tierId) ON DELETE CASCADE
);

CREATE TABLE ANNOTATION (
    annotationId VARCHAR(50) PRIMARY KEY,
    annotation_value TEXT NOT NULL,
    start_time DECIMAL(10,3) NOT NULL,
    end_time DECIMAL(10,3) NOT NULL,
    tierId VARCHAR(50) NOT NULL,
    FOREIGN KEY (tierId) REFERENCES TIER(tierId) ON DELETE CASCADE
);

CREATE TABLE CONFLICT (
    conflictId VARCHAR(50) PRIMARY KEY,
    conflict_type ENUM('annotation_overlap', 'tier_mismatch', 'value_difference', 'structural', 'other') NOT NULL,
    conflict_description TEXT NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL DEFAULT 'medium',
    status ENUM('detected', 'in_progress', 'resolved', 'dismissed') NOT NULL DEFAULT 'open',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    resolved_by INT NULL,
    projectId INT NOT NULL,
    FOREIGN KEY (resolved_by) REFERENCES USER(userId) ON DELETE SET NULL,
    FOREIGN KEY (projectId) REFERENCES PROJECT(projectId) ON DELETE CASCADE
);

CREATE TABLE COMMENT (
    commentId VARCHAR(50) PRIMARY KEY,
    content TEXT NOT NULL,
    target_type ENUM('project', 'elan_file', 'conflict', 'tier', 'annotation') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    userId INT NOT NULL,
    parent_commentId VARCHAR(50) NULL,
    FOREIGN KEY (userId) REFERENCES USER(userId) ON DELETE CASCADE,
    FOREIGN KEY (parent_commentId) REFERENCES COMMENT(commentId) ON DELETE CASCADE
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
    projectId INT NOT NULL,
    FOREIGN KEY (sender) REFERENCES USER(userId) ON DELETE CASCADE,
    FOREIGN KEY (receiver) REFERENCES USER(userId) ON DELETE CASCADE,
    FOREIGN KEY (projectId) REFERENCES PROJECT(projectId) ON DELETE CASCADE
);

-- Junction Tables
-- _______________

CREATE TABLE ELAN_FILE_TO_PROJECT (
    elanId INT NOT NULL,
    projectId INT NOT NULL,
    PRIMARY KEY (elanId, projectId),
    FOREIGN KEY (elanId) REFERENCES ELAN_FILE(elanId) ON DELETE CASCADE,
    FOREIGN KEY (projectId) REFERENCES PROJECT(projectId) ON DELETE CASCADE
);

CREATE TABLE ELAN_FILE_TO_TIER (
    elanId INT NOT NULL,
    tierId VARCHAR(50) NOT NULL,
    PRIMARY KEY (tierId, elanId),
    FOREIGN KEY (tierId) REFERENCES TIER(tierId) ON DELETE CASCADE,
    FOREIGN KEY (elanId) REFERENCES ELAN_FILE(elanId) ON DELETE CASCADE
);

CREATE TABLE PROJECT_ANNOT_STANDARD (
    standardId VARCHAR(50) NOT NULL,
    projectId INT NOT NULL,
    PRIMARY KEY (projectId, standardId),
    FOREIGN KEY (projectId) REFERENCES PROJECT(projectId) ON DELETE CASCADE,
    FOREIGN KEY (standardId) REFERENCES ANNOTATION_STANTARD(standardId) ON DELETE CASCADE
);

CREATE TABLE USER_TO_PROJECT (
    projectId INT NOT NULL,
    userId INT NOT NULL,
    permission ENUM('read', 'write', 'admin', 'owner') NOT NULL DEFAULT 'read',
    PRIMARY KEY (userId, projectId),
    FOREIGN KEY (userId) REFERENCES USER(userId) ON DELETE CASCADE,
    FOREIGN KEY (projectId) REFERENCES PROJECT(projectId) ON DELETE CASCADE
);

CREATE TABLE USER_WORK_ON_CONFLICT (
    conflictId VARCHAR(50) NOT NULL,
    userId INT NOT NULL,
    PRIMARY KEY (userId, conflictId),
    FOREIGN KEY (userId) REFERENCES USER(userId) ON DELETE CASCADE,
    FOREIGN KEY (conflictId) REFERENCES CONFLICT(conflictId) ON DELETE CASCADE
);

CREATE TABLE CONFLICT_OF_ELAN_FILE (
    conflictId VARCHAR(50) NOT NULL,
    elanId INT NOT NULL,
    PRIMARY KEY (elanId, conflictId),
    FOREIGN KEY (elanId) REFERENCES ELAN_FILE(elanId) ON DELETE CASCADE,
    FOREIGN KEY (conflictId) REFERENCES CONFLICT(conflictId) ON DELETE CASCADE
);

-- Comment Association Tables
-- __________________________

CREATE TABLE COMMENT_PROJECT (
    commentId VARCHAR(50) PRIMARY KEY,
    projectId INT NOT NULL,
    FOREIGN KEY (commentId) REFERENCES COMMENT(commentId) ON DELETE CASCADE,
    FOREIGN KEY (projectId) REFERENCES PROJECT(projectId) ON DELETE CASCADE
);

CREATE TABLE COMMENT_ELAN_FILE (
    commentId VARCHAR(50) PRIMARY KEY,
    elanId INT NOT NULL,
    FOREIGN KEY (commentId) REFERENCES COMMENT(commentId) ON DELETE CASCADE,
    FOREIGN KEY (elanId) REFERENCES ELAN_FILE(elanId) ON DELETE CASCADE
);

CREATE TABLE COMMENT_CONFLICT (
    commentId VARCHAR(50) PRIMARY KEY,
    conflictId VARCHAR(50) NOT NULL,
    FOREIGN KEY (commentId) REFERENCES COMMENT(commentId) ON DELETE CASCADE,
    FOREIGN KEY (conflictId) REFERENCES CONFLICT(conflictId) ON DELETE CASCADE
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
CREATE INDEX idx_project_instance ON PROJECT(instanceId);

-- ELAN File indexes
CREATE INDEX idx_elan_filename ON ELAN_FILE(filename);
CREATE INDEX idx_elan_user ON ELAN_FILE(userId);

-- Annotation indexes
CREATE INDEX idx_annotation_tier ON ANNOTATION(tierId);
CREATE INDEX idx_annotation_time ON ANNOTATION(start_time, end_time);

-- Tier indexes
CREATE INDEX idx_tier_name ON TIER(tier_name);
CREATE INDEX idx_tier_parent ON TIER(parent_tierId);

-- Conflict indexes
CREATE INDEX idx_conflict_project ON CONFLICT(projectId);
CREATE INDEX idx_conflict_status ON CONFLICT(status);
CREATE INDEX idx_conflict_severity ON CONFLICT(severity);
CREATE INDEX idx_conflict_type ON CONFLICT(conflict_type);
CREATE INDEX idx_conflict_resolved_by ON CONFLICT(resolved_by);

-- Comment indexes
CREATE INDEX idx_comment_user ON COMMENT(userId);
CREATE INDEX idx_comment_parent ON COMMENT(parent_commentId);
CREATE INDEX idx_comment_target_type ON COMMENT(target_type);
CREATE INDEX idx_comment_created ON COMMENT(created_at);

-- Invitation indexes
CREATE INDEX idx_invitation_sender ON INVITATION(sender);
CREATE INDEX idx_invitation_receiver ON INVITATION(receiver);
CREATE INDEX idx_invitation_project ON INVITATION(projectId);
CREATE INDEX idx_invitation_status ON INVITATION(status);
CREATE INDEX idx_invitation_expires ON INVITATION(expires_at);

-- Junction table indexes
CREATE INDEX idx_user_project_permission ON USER_TO_PROJECT(permission);
CREATE INDEX idx_elan_project_project ON ELAN_FILE_TO_PROJECT(projectId);
CREATE INDEX idx_elan_tier_elan ON ELAN_FILE_TO_TIER(elanId);

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
    u.userId,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    u.is_active,
    p.projectId,
    p.project_name,
    p.description as project_description,
    utp.permission as project_permission
FROM USER u
JOIN USER_TO_PROJECT utp ON u.userId = utp.userId
JOIN PROJECT p ON utp.projectId = p.projectId
WHERE u.is_active = TRUE;

CREATE VIEW project_files AS
SELECT 
    p.projectId,
    p.project_name,
    ef.elanId,
    ef.filename,
    ef.file_path,
    ef.file_size,
    u.username as uploaded_by
FROM PROJECT p
JOIN ELAN_FILE_TO_PROJECT efp ON p.projectId = efp.projectId
JOIN ELAN_FILE ef ON efp.elanId = ef.elanId
JOIN USER u ON ef.userId = u.userId;

CREATE VIEW active_conflicts AS
SELECT 
    c.conflictId,
    c.conflict_type,
    c.conflict_description,
    c.severity,
    c.status,
    c.detected_at,
    p.project_name,
    u.username as resolved_by_user
FROM CONFLICT c
JOIN PROJECT p ON c.projectId = p.projectId
LEFT JOIN USER u ON c.resolved_by = u.userId
WHERE c.status IN ('open', 'in_progress');

-- Stored Procedures Section
-- ________________________

DELIMITER //

CREATE PROCEDURE AddUserToProject(
    IN p_userId INT,
    IN p_projectId INT,
    IN p_permission ENUM('read', 'write', 'admin')
)
BEGIN
    INSERT INTO USER_TO_PROJECT (userId, projectId, permission)
    VALUES (p_userId, p_projectId, p_permission)
    ON DUPLICATE KEY UPDATE 
        permission = p_permission;
END //

CREATE PROCEDURE RemoveUserFromProject(
    IN p_userId INT,
    IN p_projectId INT
)
BEGIN
    DELETE FROM USER_TO_PROJECT 
    WHERE userId = p_userId AND projectId = p_projectId;
END //

CREATE PROCEDURE AcceptInvitation(
    IN p_invitationID VARCHAR(50)
)
BEGIN
    DECLARE v_userId INT;
    DECLARE v_projectId INT;
    DECLARE v_permission ENUM('read', 'write', 'admin', 'owner');
    
    SELECT receiver, projectId, project_permission 
    INTO v_userId, v_projectId, v_permission
    FROM INVITATION 
    WHERE invitationID = p_invitationID AND status = 'pending';
    
    IF v_userId IS NOT NULL THEN
        UPDATE INVITATION 
        SET status = 'accepted', 
            responded_at = CURRENT_TIMESTAMP
        WHERE invitationID = p_invitationID;
        
        INSERT INTO USER_TO_PROJECT (userId, projectId, permission)
        VALUES (v_userId, v_projectId, v_permission)
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