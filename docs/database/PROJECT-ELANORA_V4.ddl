-- *********************************************
-- * Standard SQL generation                   
-- *--------------------------------------------
-- * DB-MAIN version: 11.0.2              
-- * Generator date: Sep 14 2021              
-- * Generation date: Mon Jul  7 11:22:11 2025 
-- * LUN file: C:\Users\Laffineur\Documents\school\m1\corpus-mdl\PROJECT-ELANORA.lun 
-- * Schema: anto-schema-relationnal/SQL2 
-- ********************************************* 


-- Database Section
-- ________________ 

create database anto-schema-relationnal;


-- DBSpace Section
-- _______________


-- Tables Section
-- _____________ 

create table ANNOTATION (
     annotationId char(1) not null,
     annotation_value char(1) not null,
     start_time char(1) not null,
     end_time char(1) not null,
     tierId char(1) not null,
     constraint ID_ANNOTATION_ID primary key (annotationId));

create table ANNOTATION_STANTARD (
     standardId char(1) not null,
     standard_name char(1) not null,
     description char(1) not null,
     regex char(1) not null,
     constraint ID_ANNOTATION_STANTARD_ID primary key (standardId));

create table COMMENT (
     commentId char(1) not null,
     content char(1) not null,
     target_type char(1) not null,
     created_at date not null,
     userId numeric(1) not null,
     parent_commentId char(1) not null,
     constraint ID_COMMENT_ID primary key (commentId));

create table COMMENT_CONFLICT (
     commentId char(1) not null,
     conflictId char(1) not null,
     constraint ID_COMME_COMME_2_ID primary key (commentId));

create table COMMENT_ELAN_FILE (
     commentId char(1) not null,
     elanId numeric(1) not null,
     constraint ID_COMME_COMME_1_ID primary key (commentId));

create table COMMENT_PROJECT (
     commentId char(1) not null,
     projectId numeric(1) not null,
     constraint ID_COMME_COMME_ID primary key (commentId));

create table CONFLICT (
     conflictId char(1) not null,
     conflict_type char(1) not null,
     conflict_description char(1) not null,
     severity char(1) not null,
     status char(1) not null,
     detected_at char(1) not null,
     resolved_at char(1) not null,
     resolved_by numeric(1) not null,
     projectId numeric(1) not null,
     constraint ID_CONFLICT_ID primary key (conflictId));

create table ELAN_FILE (
     elanId numeric(1) not null,
     filename varchar(255) not null,
     file_path varchar(500) not null,
     file_size numeric(1) not null,
     userId numeric(1) not null,
     constraint ID_ELAN_FILE_ID primary key (elanId));

create table CONFLICT_OF_ELAN_FILE (
     conflictId char(1) not null,
     elanId numeric(1) not null,
     constraint ID_CONFLICT_OF_ELAN_FILE_ID primary key (elanId, conflictId));

create table INSTANCE (
     instanceId numeric(1) not null,
     instance_name char(1) not null,
     institution_name char(1) not null,
     contact_email char(1) not null,
     domain char(1) not null,
     timezone char(1) not null,
     default_language char(1) not null,
     max_file_size_mb float(1) not null,
     max_users float(1) not null,
     is_active char not null,
     created_at date not null,
     updated_at date not null,
     constraint ID_INSTANCE_ID primary key (instanceId));

create table INVITATION (
     invitationID char(1) not null,
     project_permission char(1) not null,
     status char(1) not null,
     created_at date not null,
     expires_at date not null,
     responded_at date not null,
     sender numeric(1) not null,
     receiver numeric(1) not null,
     projectId numeric(1) not null,
     constraint ID_INVITATION_ID primary key (invitationID));

create table PROJECT (
     projectId numeric(1) not null,
     project_name char(1) not null,
     description char(1) not null,
     instanceId numeric(1) not null,
     constraint ID_PROJECT_ID primary key (projectId));

create table ELAN_FILE_TO_PROJECT (
     elanId numeric(1) not null,
     projectId numeric(1) not null,
     constraint ID_ELAN_FILE_TO_PROJECT_ID primary key (elanId, projectId));

create table ELAN_FILE_TO_TIER (
     elanId numeric(1) not null,
     tierId char(1) not null,
     constraint ID_ELAN_FILE_TO_TIER_ID primary key (tierId, elanId));

create table PROJECT_ANNOT_STANDARD (
     standardId char(1) not null,
     projectId numeric(1) not null,
     constraint ID_PROJECT_ANNOT_STANDARD_ID primary key (projectId, standardId));

create table TIER (
     tierId char(1) not null,
     tier_name char(1) not null,
     parent_tierId char(1) not null,
     constraint ID_TIER_ID primary key (tierId));

create table USER (
     userId numeric(1) not null,
     username char(1) not null,
     email char(1) not null,
     password char(1) not null,
     first_name char(1) not null,
     last_name char(1) not null,
     phone_number char(1) not null,
     created_at char(1) not null,
     updated_at char(1) not null,
     is_active char(1) not null,
     last_login char(1) not null,
     constraint ID_USER_ID primary key (userId));

create table USER_TO_PROJECT (
     projectId numeric(1) not null,
     userId numeric(1) not null,
     permission char(1) not null,
     constraint ID_USER_TO_PROJECT_ID primary key (userId, projectId));

create table USER_WORK_ON_CONFLICT (
     conflictId char(1) not null,
     userId numeric(1) not null,
     constraint ID_USER_WORK_ON_CONFLICT_ID primary key (userId, conflictId));


-- Constraints Section
-- ___________________ 

alter table ANNOTATION add constraint REF_ANNOT_TIER_FK
     foreign key (tierId)
     references TIER;

alter table COMMENT add constraint REF_COMME_USER_FK
     foreign key (userId)
     references USER;

alter table COMMENT add constraint REF_COMME_COMME_FK
     foreign key (parent_commentId)
     references COMMENT;

alter table COMMENT_CONFLICT add constraint ID_COMME_COMME_2_FK
     foreign key (commentId)
     references COMMENT;

alter table COMMENT_CONFLICT add constraint REF_COMME_CONFL_FK
     foreign key (conflictId)
     references CONFLICT;

alter table COMMENT_ELAN_FILE add constraint ID_COMME_COMME_1_FK
     foreign key (commentId)
     references COMMENT;

alter table COMMENT_ELAN_FILE add constraint REF_COMME_ELAN__FK
     foreign key (elanId)
     references ELAN_FILE;

alter table COMMENT_PROJECT add constraint ID_COMME_COMME_FK
     foreign key (commentId)
     references COMMENT;

alter table COMMENT_PROJECT add constraint REF_COMME_PROJE_FK
     foreign key (projectId)
     references PROJECT;

alter table CONFLICT add constraint REF_CONFL_USER_FK
     foreign key (resolved_by)
     references USER;

alter table CONFLICT add constraint REF_CONFL_PROJE_FK
     foreign key (projectId)
     references PROJECT;

alter table ELAN_FILE add constraint REF_ELAN__USER_FK
     foreign key (userId)
     references USER;

alter table CONFLICT_OF_ELAN_FILE add constraint REF_CONFL_ELAN_
     foreign key (elanId)
     references ELAN_FILE;

alter table CONFLICT_OF_ELAN_FILE add constraint REF_CONFL_CONFL_FK
     foreign key (conflictId)
     references CONFLICT;

alter table INVITATION add constraint REF_INVIT_USER_1_FK
     foreign key (sender)
     references USER;

alter table INVITATION add constraint REF_INVIT_USER_FK
     foreign key (receiver)
     references USER;

alter table INVITATION add constraint REF_INVIT_PROJE_FK
     foreign key (projectId)
     references PROJECT;

alter table PROJECT add constraint REF_PROJE_INSTA_FK
     foreign key (instanceId)
     references INSTANCE;

alter table ELAN_FILE_TO_PROJECT add constraint REF_ELAN__PROJE_FK
     foreign key (projectId)
     references PROJECT;

alter table ELAN_FILE_TO_PROJECT add constraint REF_ELAN__ELAN__1
     foreign key (elanId)
     references ELAN_FILE;

alter table ELAN_FILE_TO_TIER add constraint REF_ELAN__TIER
     foreign key (tierId)
     references TIER;

alter table ELAN_FILE_TO_TIER add constraint REF_ELAN__ELAN__FK
     foreign key (elanId)
     references ELAN_FILE;

alter table PROJECT_ANNOT_STANDARD add constraint REF_PROJE_PROJE
     foreign key (projectId)
     references PROJECT;

alter table PROJECT_ANNOT_STANDARD add constraint REF_PROJE_ANNOT_FK
     foreign key (standardId)
     references ANNOTATION_STANTARD;

alter table TIER add constraint REF_TIER_TIER_FK
     foreign key (parent_tierId)
     references TIER;

alter table USER_TO_PROJECT add constraint REF_USER__USER_1
     foreign key (userId)
     references USER;

alter table USER_TO_PROJECT add constraint REF_USER__PROJE_FK
     foreign key (projectId)
     references PROJECT;

alter table USER_WORK_ON_CONFLICT add constraint REF_USER__USER
     foreign key (userId)
     references USER;

alter table USER_WORK_ON_CONFLICT add constraint REF_USER__CONFL_FK
     foreign key (conflictId)
     references CONFLICT;


-- Index Section
-- _____________ 

create unique index ID_ANNOTATION_IND
     on ANNOTATION (annotationId);

create index REF_ANNOT_TIER_IND
     on ANNOTATION (tierId);

create unique index ID_ANNOTATION_STANTARD_IND
     on ANNOTATION_STANTARD (standardId);

create unique index ID_COMMENT_IND
     on COMMENT (commentId);

create index REF_COMME_USER_IND
     on COMMENT (userId);

create index REF_COMME_COMME_IND
     on COMMENT (parent_commentId);

create unique index ID_COMME_COMME_2_IND
     on COMMENT_CONFLICT (commentId);

create index REF_COMME_CONFL_IND
     on COMMENT_CONFLICT (conflictId);

create unique index ID_COMME_COMME_1_IND
     on COMMENT_ELAN_FILE (commentId);

create index REF_COMME_ELAN__IND
     on COMMENT_ELAN_FILE (elanId);

create unique index ID_COMME_COMME_IND
     on COMMENT_PROJECT (commentId);

create index REF_COMME_PROJE_IND
     on COMMENT_PROJECT (projectId);

create unique index ID_CONFLICT_IND
     on CONFLICT (conflictId);

create index REF_CONFL_USER_IND
     on CONFLICT (resolved_by);

create index REF_CONFL_PROJE_IND
     on CONFLICT (projectId);

create unique index ID_ELAN_FILE_IND
     on ELAN_FILE (elanId);

create index REF_ELAN__USER_IND
     on ELAN_FILE (userId);

create unique index ID_CONFLICT_OF_ELAN_FILE_IND
     on CONFLICT_OF_ELAN_FILE (elanId, conflictId);

create index REF_CONFL_CONFL_IND
     on CONFLICT_OF_ELAN_FILE (conflictId);

create unique index ID_INSTANCE_IND
     on INSTANCE (instanceId);

create unique index ID_INVITATION_IND
     on INVITATION (invitationID);

create index REF_INVIT_USER_1_IND
     on INVITATION (sender);

create index REF_INVIT_USER_IND
     on INVITATION (receiver);

create index REF_INVIT_PROJE_IND
     on INVITATION (projectId);

create unique index ID_PROJECT_IND
     on PROJECT (projectId);

create index REF_PROJE_INSTA_IND
     on PROJECT (instanceId);

create unique index ID_ELAN_FILE_TO_PROJECT_IND
     on ELAN_FILE_TO_PROJECT (elanId, projectId);

create index REF_ELAN__PROJE_IND
     on ELAN_FILE_TO_PROJECT (projectId);

create unique index ID_ELAN_FILE_TO_TIER_IND
     on ELAN_FILE_TO_TIER (tierId, elanId);

create index REF_ELAN__ELAN__IND
     on ELAN_FILE_TO_TIER (elanId);

create unique index ID_PROJECT_ANNOT_STANDARD_IND
     on PROJECT_ANNOT_STANDARD (projectId, standardId);

create index REF_PROJE_ANNOT_IND
     on PROJECT_ANNOT_STANDARD (standardId);

create unique index ID_TIER_IND
     on TIER (tierId);

create index REF_TIER_TIER_IND
     on TIER (parent_tierId);

create unique index ID_USER_IND
     on USER (userId);

create unique index ID_USER_TO_PROJECT_IND
     on USER_TO_PROJECT (userId, projectId);

create index REF_USER__PROJE_IND
     on USER_TO_PROJECT (projectId);

create unique index ID_USER_WORK_ON_CONFLICT_IND
     on USER_WORK_ON_CONFLICT (userId, conflictId);

create index REF_USER__CONFL_IND
     on USER_WORK_ON_CONFLICT (conflictId);

