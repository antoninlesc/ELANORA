-- SQL DUMP FOR ELAN PROJECT MANAGEMENT SYSTEM
-- Database: erl-schema-relationnel
-- Version: 2.0 Enhanced
-- Created: 2025-07-04

-- CREATE DATABASE erl_schema_relationnel;


-- Tables Section

CREATE TABLE User (
    userId INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone_number VARCHAR(20),
    website VARCHAR(255),
    written_language VARCHAR(20) NOT NULL DEFAULT 'en',
    affiliation VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    activation_code VARCHAR(100) NOT NULL,
    is_verified_account BOOLEAN NOT NULL DEFAULT FALSE,
    has_used_condition BOOLEAN NOT NULL DEFAULT FALSE,
    street_number VARCHAR(100) NOT NULL,
    street_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Project (
    projectID INT PRIMARY KEY AUTO_INCREMENT,
    project_name VARCHAR(100) NOT NULL,
    description VARCHAR(250) NOT NULL,
    status ENUM('active', 'inactive', 'completed', 'archived') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE ELAN_Files (
    elanId INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT NOT NULL,
    projectID INT NOT NULL,
    FOREIGN KEY (projectID) REFERENCES Project(projectID) ON DELETE CASCADE
);

CREATE TABLE user_to_project (
    projectID INT NOT NULL,
    userId INT NOT NULL,
    project_permission ENUM('read', 'write', 'admin') DEFAULT 'read',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (userId, projectID),
    FOREIGN KEY (userId) REFERENCES User(userId) ON DELETE CASCADE,
    FOREIGN KEY (projectID) REFERENCES Project(projectID) ON DELETE CASCADE
);

CREATE TABLE Invitations (
    invitationID INT PRIMARY KEY AUTO_INCREMENT,
    projet_permission ENUM('read', 'write', 'admin') DEFAULT 'read',
    status ENUM('pending', 'accepted', 'rejected', 'expired') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    responded_at TIMESTAMP NULL,
    projectID INT NOT NULL,
    userId INT NOT NULL,
    Sen_userId INT NOT NULL,
    FOREIGN KEY (projectID) REFERENCES Project(projectID) ON DELETE CASCADE,
    FOREIGN KEY (userId) REFERENCES User(userId) ON DELETE CASCADE,
    FOREIGN KEY (Sen_userId) REFERENCES User(userId) ON DELETE CASCADE
);


-- Indexes Section

CREATE INDEX idx_user_email ON User(email);
CREATE INDEX idx_user_username ON User(username);
CREATE INDEX idx_user_active ON User(is_active);
CREATE INDEX idx_user_verified ON User(is_verified_account);
CREATE INDEX idx_user_department ON User(department);
CREATE INDEX idx_user_country ON User(country);

CREATE INDEX idx_project_name ON Project(project_name);
CREATE INDEX idx_project_status ON Project(status);
CREATE INDEX idx_project_created ON Project(created_at);

CREATE INDEX idx_elan_filename ON ELAN_Files(filename);
CREATE INDEX idx_elan_project ON ELAN_Files(projectID);

CREATE INDEX idx_user_project_user ON user_to_project(userId);
CREATE INDEX idx_user_project_project ON user_to_project(projectID);
CREATE INDEX idx_user_project_permission ON user_to_project(project_permission);

CREATE INDEX idx_invitation_user ON Invitations(userId);
CREATE INDEX idx_invitation_project ON Invitations(projectID);
CREATE INDEX idx_invitation_sender ON Invitations(Sen_userId);
CREATE INDEX idx_invitation_status ON Invitations(status);
CREATE INDEX idx_invitation_expires ON Invitations(expires_at);

-- Views Section

CREATE VIEW user_projects AS
SELECT 
    u.userId,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    u.phone_number,
    u.website,
    u.written_language,
    u.affiliation,
    u.department,
    u.country,
    p.projectID,
    p.project_name,
    p.description as project_description,
    p.status as project_status,
    utp.project_permission,
    utp.assigned_at
FROM User u
JOIN user_to_project utp ON u.userId = utp.userId
JOIN Project p ON utp.projectID = p.projectID
WHERE u.is_active = TRUE;

CREATE VIEW project_files AS
SELECT 
    p.projectID,
    p.project_name,
    p.status as project_status,
    ef.elanId,
    ef.filename,
    ef.file_path,
    ef.file_size
FROM Project p
JOIN ELAN_Files ef ON p.projectID = ef.projectID;

-- Stored Procedures Section

DELIMITER //
CREATE PROCEDURE AddUserToProject(
    IN p_userId INT,
    IN p_projectID INT,
    IN p_permission ENUM('read', 'write', 'admin')
)
BEGIN
    INSERT INTO user_to_project (userId, projectID, project_permission)
    VALUES (p_userId, p_projectID, p_permission)
    ON DUPLICATE KEY UPDATE 
        project_permission = p_permission,
        assigned_at = CURRENT_TIMESTAMP;
END //

CREATE PROCEDURE RemoveUserFromProject(
    IN p_userId INT,
    IN p_projectID INT
)
BEGIN
    DELETE FROM user_to_project 
    WHERE userId = p_userId AND projectID = p_projectID;
END //

CREATE PROCEDURE AcceptInvitation(
    IN p_invitationID INT
)
BEGIN
    DECLARE v_userId INT;
    DECLARE v_projectID INT;
    DECLARE v_permission ENUM('read', 'write', 'admin');
    
    SELECT userId, projectID, projet_permission 
    INTO v_userId, v_projectID, v_permission
    FROM Invitations 
    WHERE invitationID = p_invitationID AND status = 'pending';
    
    IF v_userId IS NOT NULL THEN
        UPDATE Invitations 
        SET status = 'accepted', 
            responded_at = CURRENT_TIMESTAMP
        WHERE invitationID = p_invitationID;
        
        INSERT INTO user_to_project (userId, projectID, project_permission)
        VALUES (v_userId, v_projectID, v_permission)
        ON DUPLICATE KEY UPDATE 
            project_permission = v_permission,
            assigned_at = CURRENT_TIMESTAMP;
    END IF;
END //

DELIMITER ;

-- Triggers Section

DELIMITER //
CREATE TRIGGER update_user_timestamp
    BEFORE UPDATE ON User
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //

CREATE TRIGGER update_project_timestamp
    BEFORE UPDATE ON Project
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //

CREATE TRIGGER check_invitation_expiry
    BEFORE UPDATE ON Invitations
    FOR EACH ROW
BEGIN
    IF NEW.expires_at < CURRENT_TIMESTAMP AND OLD.status = 'pending' THEN
        SET NEW.status = 'expired';
    END IF;
END //

DELIMITER ;

