create table ANNOTATION_STANDARD
(
    standard_id   varchar(50)  not null
        primary key,
    standard_name varchar(100) not null,
    description   text         not null,
    regex         varchar(500) not null
);

create table ANNOTATION_VALUE
(
    value_id         int auto_increment
        primary key,
    annotation_value varchar(255) collate utf8mb4_bin not null,
    constraint annotation_value
        unique (annotation_value)
)
    collate = utf8mb4_unicode_ci;

create table COUNTRY
(
    country_id   int auto_increment
        primary key,
    country_code varchar(2)                          not null,
    country_name varchar(100)                        not null,
    created_at   timestamp default CURRENT_TIMESTAMP null,
    updated_at   timestamp default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    constraint country_code
        unique (country_code),
    constraint country_name
        unique (country_name)
);

create table CITY
(
    city_id      int auto_increment
        primary key,
    city_name    varchar(100)                        not null,
    country_id   int                                 not null,
    region_state varchar(100)                        null,
    created_at   timestamp default CURRENT_TIMESTAMP null,
    updated_at   timestamp default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    constraint CITY_ibfk_1
        foreign key (country_id) references COUNTRY (country_id)
);

create table ADDRESS
(
    address_id     int auto_increment
        primary key,
    street_number  varchar(100)                        null,
    street_name    varchar(100)                        not null,
    city_id        int                                 not null,
    postal_code    varchar(20)                         not null,
    address_line_2 varchar(100)                        null,
    created_at     timestamp default CURRENT_TIMESTAMP null,
    updated_at     timestamp default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    constraint ADDRESS_ibfk_1
        foreign key (city_id) references CITY (city_id)
);

create index idx_address_city
    on ADDRESS (city_id);

create index idx_address_postal
    on ADDRESS (postal_code);

create index idx_city_name
    on CITY (city_name);

create index idx_country_city
    on CITY (country_id, city_name);

create index idx_country_code
    on COUNTRY (country_code);

create index idx_country_name
    on COUNTRY (country_name);

create table INSTANCE
(
    instance_id      int auto_increment
        primary key,
    instance_name    varchar(100)                             not null,
    institution_name varchar(100)                             not null,
    contact_email    varchar(100)                             not null,
    domain           varchar(100)                             not null,
    timezone         varchar(50)                              not null,
    default_language varchar(10)    default 'en'              not null,
    max_file_size_mb decimal(10, 2) default 100.00            not null,
    max_users        int            default 1000              not null,
    is_active        tinyint(1)     default 1                 not null,
    created_at       timestamp      default CURRENT_TIMESTAMP null,
    updated_at       timestamp      default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP
);

create index idx_instance_active
    on INSTANCE (is_active);

create index idx_instance_name
    on INSTANCE (instance_name);

create definer = root@`%` trigger update_instance_timestamp
    before update
    on INSTANCE
    for each row
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END;

create table PROJECT
(
    project_id   int auto_increment
        primary key,
    project_name varchar(100) not null,
    project_path varchar(512) not null,
    description  text         not null,
    instance_id  int          not null,
    constraint project_path
        unique (project_path),
    constraint PROJECT_ibfk_1
        foreign key (instance_id) references INSTANCE (instance_id)
            on delete cascade
);

create index idx_project_instance
    on PROJECT (instance_id);

create index idx_project_name
    on PROJECT (project_name);

create table PROJECT_ANNOT_STANDARD
(
    standard_id varchar(50) not null,
    project_id  int         not null,
    primary key (project_id, standard_id),
    constraint PROJECT_ANNOT_STANDARD_ibfk_1
        foreign key (project_id) references PROJECT (project_id)
            on delete cascade,
    constraint PROJECT_ANNOT_STANDARD_ibfk_2
        foreign key (standard_id) references ANNOTATION_STANDARD (standard_id)
            on delete cascade
);

create index standard_id
    on PROJECT_ANNOT_STANDARD (standard_id);

create table USER
(
    user_id             int auto_increment
        primary key,
    username            varchar(50)                                        not null,
    email               varchar(100)                                       not null,
    hashed_password     char(60)                                           not null,
    first_name          varchar(50)                                        not null,
    last_name           varchar(50)                                        not null,
    phone_number        varchar(20)                                        null,
    is_active           tinyint(1)               default 1                 not null,
    last_login          timestamp                                          null,
    created_at          timestamp                default CURRENT_TIMESTAMP null,
    updated_at          timestamp                default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP,
    affiliation         varchar(100)                                       not null,
    department          varchar(100)                                       not null,
    address_id          int                                                null,
    activation_code     varchar(100)                                       not null,
    is_verified_account tinyint(1)               default 0                 not null,
    role                enum ('ADMIN', 'PUBLIC') default 'PUBLIC'          not null,
    constraint email
        unique (email),
    constraint username
        unique (username),
    constraint USER_ibfk_1
        foreign key (address_id) references ADDRESS (address_id)
            on delete set null
);

create table COMMENT
(
    comment_id        varchar(50)                                                     not null
        primary key,
    content           text                                                            not null,
    target_type       enum ('PROJECT', 'ELAN_FILE', 'CONFLICT', 'TIER', 'ANNOTATION') not null,
    created_at        timestamp default CURRENT_TIMESTAMP                             null,
    user_id           int                                                             not null,
    parent_comment_id varchar(50)                                                     null,
    constraint COMMENT_ibfk_1
        foreign key (user_id) references USER (user_id)
            on delete cascade,
    constraint COMMENT_ibfk_2
        foreign key (parent_comment_id) references COMMENT (comment_id)
            on delete cascade
);

create index idx_comment_created
    on COMMENT (created_at);

create index idx_comment_parent
    on COMMENT (parent_comment_id);

create index idx_comment_target_type
    on COMMENT (target_type);

create index idx_comment_user
    on COMMENT (user_id);

create table COMMENT_PROJECT
(
    comment_id varchar(50) not null
        primary key,
    project_id int         not null,
    constraint COMMENT_PROJECT_ibfk_1
        foreign key (comment_id) references COMMENT (comment_id)
            on delete cascade,
    constraint COMMENT_PROJECT_ibfk_2
        foreign key (project_id) references PROJECT (project_id)
            on delete cascade
);

create index project_id
    on COMMENT_PROJECT (project_id);

create table CONFLICT
(
    conflict_id          varchar(50)                                                                             not null
        primary key,
    conflict_type        enum ('ANNOTATION_OVERLAP', 'TIER_MISMATCH', 'VALUE_DIFFERENCE', 'STRUCTURAL', 'OTHER') not null,
    conflict_description text                                                                                    not null,
    severity             enum ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')                                              not null,
    status               enum ('DETECTED', 'IN_PROGRESS', 'RESOLVED', 'DISMISSED') default 'DETECTED'            not null,
    detected_at          timestamp                                                 default CURRENT_TIMESTAMP     null,
    resolved_at          timestamp                                                                               null,
    resolved_by          int                                                                                     null,
    project_id           int                                                                                     not null,
    constraint CONFLICT_ibfk_1
        foreign key (resolved_by) references USER (user_id)
            on delete set null,
    constraint CONFLICT_ibfk_2
        foreign key (project_id) references PROJECT (project_id)
            on delete cascade
);

create table COMMENT_CONFLICT
(
    comment_id  varchar(50) not null
        primary key,
    conflict_id varchar(50) not null,
    constraint COMMENT_CONFLICT_ibfk_1
        foreign key (comment_id) references COMMENT (comment_id)
            on delete cascade,
    constraint COMMENT_CONFLICT_ibfk_2
        foreign key (conflict_id) references CONFLICT (conflict_id)
            on delete cascade
);

create index conflict_id
    on COMMENT_CONFLICT (conflict_id);

create index idx_conflict_project
    on CONFLICT (project_id);

create index idx_conflict_resolved_by
    on CONFLICT (resolved_by);

create index idx_conflict_severity
    on CONFLICT (severity);

create index idx_conflict_status
    on CONFLICT (status);

create index idx_conflict_type
    on CONFLICT (conflict_type);

create definer = root@`%` trigger update_conflict_resolved_time
    before update
    on CONFLICT
    for each row
BEGIN
    IF NEW.status = 'RESOLVED' AND OLD.status != 'RESOLVED' THEN
        SET NEW.resolved_at = CURRENT_TIMESTAMP;
    END IF;
END;

create table ELAN_FILE
(
    elan_id   int auto_increment
        primary key,
    filename  varchar(255) not null,
    file_path varchar(500) not null,
    file_size int          not null,
    user_id   int          not null,
    constraint ELAN_FILE_ibfk_1
        foreign key (user_id) references USER (user_id)
            on delete cascade
);

create table COMMENT_ELAN_FILE
(
    comment_id varchar(50) not null
        primary key,
    elan_id    int         not null,
    constraint COMMENT_ELAN_FILE_ibfk_1
        foreign key (comment_id) references COMMENT (comment_id)
            on delete cascade,
    constraint COMMENT_ELAN_FILE_ibfk_2
        foreign key (elan_id) references ELAN_FILE (elan_id)
            on delete cascade
);

create index elan_id
    on COMMENT_ELAN_FILE (elan_id);

create table CONFLICT_OF_ELAN_FILE
(
    conflict_id varchar(50) not null,
    elan_id     int         not null,
    primary key (elan_id, conflict_id),
    constraint CONFLICT_OF_ELAN_FILE_ibfk_1
        foreign key (elan_id) references ELAN_FILE (elan_id)
            on delete cascade,
    constraint CONFLICT_OF_ELAN_FILE_ibfk_2
        foreign key (conflict_id) references CONFLICT (conflict_id)
            on delete cascade
);

create index conflict_id
    on CONFLICT_OF_ELAN_FILE (conflict_id);

create index idx_elan_filename
    on ELAN_FILE (filename);

create index idx_elan_user
    on ELAN_FILE (user_id);

create table ELAN_FILE_TO_PROJECT
(
    elan_id    int not null,
    project_id int not null,
    primary key (elan_id, project_id),
    constraint ELAN_FILE_TO_PROJECT_ibfk_1
        foreign key (elan_id) references ELAN_FILE (elan_id)
            on delete cascade,
    constraint ELAN_FILE_TO_PROJECT_ibfk_2
        foreign key (project_id) references PROJECT (project_id)
            on delete cascade
);

create index idx_elan_project_project
    on ELAN_FILE_TO_PROJECT (project_id);

create table INVITATION
(
    invitation_id      varchar(50)                                                                   not null
        primary key,
    project_permission enum ('READ', 'WRITE', 'ADMIN', 'OWNER')            default 'READ'            not null,
    hashed_code        char(60)                                                                      not null,
    status             enum ('PENDING', 'ACCEPTED', 'REJECTED', 'EXPIRED') default 'PENDING'         not null,
    created_at         timestamp                                           default CURRENT_TIMESTAMP null,
    expires_at         timestamp                                                                     not null,
    responded_at       timestamp                                                                     null,
    sender             int                                                                           not null,
    receiver           int                                                                           null,
    receiver_email     varchar(100)                                                                  null,
    project_id         int                                                                           not null,
    constraint INVITATION_ibfk_1
        foreign key (sender) references USER (user_id)
            on delete cascade,
    constraint INVITATION_ibfk_2
        foreign key (receiver) references USER (user_id)
            on delete cascade,
    constraint INVITATION_ibfk_3
        foreign key (project_id) references PROJECT (project_id)
            on delete cascade
);

create index idx_invitation_expires
    on INVITATION (expires_at);

create index idx_invitation_project
    on INVITATION (project_id);

create index idx_invitation_receiver
    on INVITATION (receiver);

create index idx_invitation_sender
    on INVITATION (sender);

create index idx_invitation_status
    on INVITATION (status);

create definer = root@`%` trigger check_invitation_expiry
    before update
    on INVITATION
    for each row
BEGIN
    IF NEW.expires_at < CURRENT_TIMESTAMP AND OLD.status = 'pending' THEN
        SET NEW.status = 'expired';
    END IF;
END;

create table TIER
(
    tier_id        varchar(50)  not null
        primary key,
    tier_name      varchar(100) not null,
    parent_tier_id varchar(50)  null,
    elan_id        int          not null,
    constraint TIER_ibfk_1
        foreign key (parent_tier_id) references TIER (tier_id)
            on delete cascade,
    constraint fk_tier_elan_file
        foreign key (elan_id) references ELAN_FILE (elan_id)
            on delete cascade
);

create table ANNOTATION
(
    annotation_id varchar(50)    not null,
    start_time    decimal(10, 3) not null,
    end_time      decimal(10, 3) not null,
    tier_id       varchar(50)    not null,
    value_id      int            null,
    elan_id       int            not null,
    primary key (annotation_id, elan_id),
    constraint ANNOTATION_ibfk_1
        foreign key (tier_id) references TIER (tier_id)
            on delete cascade,
    constraint fk_annotation_elanfile
        foreign key (elan_id) references ELAN_FILE (elan_id)
            on delete cascade,
    constraint fk_annotation_value
        foreign key (value_id) references ANNOTATION_VALUE (value_id)
            on delete cascade
);

create index idx_annotation_tier
    on ANNOTATION (tier_id);

create index idx_annotation_time
    on ANNOTATION (start_time, end_time);

create table ELAN_FILE_TO_TIER
(
    elan_id int         not null,
    tier_id varchar(50) not null,
    primary key (tier_id, elan_id),
    constraint ELAN_FILE_TO_TIER_ibfk_1
        foreign key (tier_id) references TIER (tier_id)
            on delete cascade,
    constraint ELAN_FILE_TO_TIER_ibfk_2
        foreign key (elan_id) references ELAN_FILE (elan_id)
            on delete cascade
);

create index idx_elan_tier_elan
    on ELAN_FILE_TO_TIER (elan_id);

create index idx_tier_name
    on TIER (tier_name);

create index idx_tier_parent
    on TIER (parent_tier_id);

create index idx_user_active
    on USER (is_active);

create index idx_user_address
    on USER (address_id);

create index idx_user_affiliation
    on USER (affiliation);

create index idx_user_department
    on USER (department);

create index idx_user_email
    on USER (email);

create index idx_user_last_login
    on USER (last_login);

create index idx_user_role
    on USER (role);

create index idx_user_username
    on USER (username);

create index idx_user_verified
    on USER (is_verified_account);

create definer = root@`%` trigger update_user_timestamp
    before update
    on USER
    for each row
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END;

create table USER_TO_PROJECT
(
    project_id int                                                     not null,
    user_id    int                                                     not null,
    permission enum ('READ', 'WRITE', 'ADMIN', 'OWNER') default 'READ' not null,
    primary key (user_id, project_id),
    constraint USER_TO_PROJECT_ibfk_1
        foreign key (user_id) references USER (user_id)
            on delete cascade,
    constraint USER_TO_PROJECT_ibfk_2
        foreign key (project_id) references PROJECT (project_id)
            on delete cascade
);

create index idx_user_project_permission
    on USER_TO_PROJECT (permission);

create index project_id
    on USER_TO_PROJECT (project_id);

create table USER_WORK_ON_CONFLICT
(
    conflict_id varchar(50) not null,
    user_id     int         not null,
    primary key (user_id, conflict_id),
    constraint USER_WORK_ON_CONFLICT_ibfk_1
        foreign key (user_id) references USER (user_id)
            on delete cascade,
    constraint USER_WORK_ON_CONFLICT_ibfk_2
        foreign key (conflict_id) references CONFLICT (conflict_id)
            on delete cascade
);

create index conflict_id
    on USER_WORK_ON_CONFLICT (conflict_id);

create definer = root@`%` view UserAddressView as
select `u`.`user_id`                                          AS `user_id`,
       `u`.`username`                                         AS `username`,
       `u`.`email`                                            AS `email`,
       `u`.`first_name`                                       AS `first_name`,
       `u`.`last_name`                                        AS `last_name`,
       `u`.`affiliation`                                      AS `affiliation`,
       `u`.`department`                                       AS `department`,
       concat_ws(' ', `a`.`street_number`, `a`.`street_name`) AS `full_street`,
       `a`.`address_line_2`                                   AS `address_line_2`,
       `c`.`city_name`                                        AS `city_name`,
       `c`.`region_state`                                     AS `region_state`,
       `co`.`country_name`                                    AS `country_name`,
       `co`.`country_code`                                    AS `country_code`,
       `a`.`postal_code`                                      AS `postal_code`
from (((`elanora`.`USER` `u` left join `elanora`.`ADDRESS` `a`
        on ((`u`.`address_id` = `a`.`address_id`))) left join `elanora`.`CITY` `c`
       on ((`a`.`city_id` = `c`.`city_id`))) left join `elanora`.`COUNTRY` `co`
      on ((`c`.`country_id` = `co`.`country_id`)));

create definer = root@`%` view active_conflicts as
select `c`.`conflict_id`          AS `conflict_id`,
       `c`.`conflict_type`        AS `conflict_type`,
       `c`.`conflict_description` AS `conflict_description`,
       `c`.`severity`             AS `severity`,
       `c`.`status`               AS `status`,
       `c`.`detected_at`          AS `detected_at`,
       `p`.`project_name`         AS `project_name`,
       `u`.`username`             AS `resolved_by_user`
from ((`elanora`.`CONFLICT` `c` join `elanora`.`PROJECT` `p`
       on ((`c`.`project_id` = `p`.`project_id`))) left join `elanora`.`USER` `u`
      on ((`c`.`resolved_by` = `u`.`user_id`)))
where (`c`.`status` in ('detected', 'in_progress'));

create definer = root@`%` view project_files as
select `p`.`project_id`   AS `project_id`,
       `p`.`project_name` AS `project_name`,
       `ef`.`elan_id`     AS `elan_id`,
       `ef`.`filename`    AS `filename`,
       `ef`.`file_path`   AS `file_path`,
       `ef`.`file_size`   AS `file_size`,
       `u`.`username`     AS `uploaded_by`
from (((`elanora`.`PROJECT` `p` join `elanora`.`ELAN_FILE_TO_PROJECT` `efp`
        on ((`p`.`project_id` = `efp`.`project_id`))) join `elanora`.`ELAN_FILE` `ef`
       on ((`efp`.`elan_id` = `ef`.`elan_id`))) join `elanora`.`USER` `u` on ((`ef`.`user_id` = `u`.`user_id`)));

create definer = root@`%` view user_projects as
select `u`.`user_id`      AS `user_id`,
       `u`.`username`     AS `username`,
       `u`.`email`        AS `email`,
       `u`.`first_name`   AS `first_name`,
       `u`.`last_name`    AS `last_name`,
       `u`.`is_active`    AS `is_active`,
       `p`.`project_id`   AS `project_id`,
       `p`.`project_name` AS `project_name`,
       `p`.`description`  AS `project_description`,
       `utp`.`permission` AS `project_permission`
from ((`elanora`.`USER` `u` join `elanora`.`USER_TO_PROJECT` `utp`
       on ((`u`.`user_id` = `utp`.`user_id`))) join `elanora`.`PROJECT` `p`
      on ((`utp`.`project_id` = `p`.`project_id`)))
where (`u`.`is_active` = true);