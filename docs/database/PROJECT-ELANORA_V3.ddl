-- *********************************************
-- * Standard SQL generation                   
-- *--------------------------------------------
-- * DB-MAIN version: 11.0.2              
-- * Generator date: Sep 14 2021              
-- * Generation date: Mon Jul  7 11:06:54 2025 
-- * LUN file: C:\Users\Laffineur\Documents\school\m1\corpus-mdl\PROJECT-ELANORA.lun 
-- * Schema: anto-schema/SQL 
-- ********************************************* 


-- Database Section
-- ________________ 

create database anto-schema;


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
     Par_commentId char(1) not null,
     constraint ID_COMMENT_ID primary key (commentId));

create table COMMENT_CONFLICT (
     commentId char(1) not null,
     conflictId char(1) not null,
     constraint FKCOM_COM_2_ID primary key (commentId));

create table COMMENT_ELAN_FILE (
     commentId char(1) not null,
     elanId numeric(1) not null,
     constraint FKCOM_COM_ID primary key (commentId));

create table COMMENT_PROJECT (
     commentId char(1) not null,
     projectId numeric(1) not null,
     constraint FKCOM_COM_1_ID primary key (commentId));

create table CONFLICT (
     conflictId char(1) not null,
     conflict_type char(1) not null,
     conflict_description char(1) not null,
     severity char(1) not null,
     status char(1) not null,
     detected_at char(1) not null,
     resolved_at char(1) not null,
     projectId numeric(1) not null,
     constraint ID_CONFLICT_ID primary key (conflictId));

create table ELAN_FILE (
     elanId numeric(1) not null,
     filename varchar(255) not null,
     file_path varchar(500) not null,
     file_size numeric(1) not null,
     userId numeric(1) not null,
     constraint ID_ELAN_FILE_ID primary key (elanId));

create table generate (
     conflictId char(1) not null,
     elanId numeric(1) not null,
     constraint ID_generate_ID primary key (elanId, conflictId));

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
     projet_permission char(1) not null,
     status char(1) not null,
     created_at date not null,
     expires_at date not null,
     responded_at date not null,
     userId numeric(1) not null,
     Rec_userId numeric(1) not null,
     projectId numeric(1) not null,
     constraint ID_INVITATION_ID primary key (invitationID));

create table linked (
     elanId numeric(1) not null,
     projectId numeric(1) not null,
     constraint ID_linked_ID primary key (elanId, projectId));

create table made_of (
     elanId numeric(1) not null,
     tierId char(1) not null,
     constraint ID_made_of_ID primary key (tierId, elanId));

create table operate_on (
     standardId char(1) not null,
     projectId numeric(1) not null,
     constraint ID_operate_on_ID primary key (projectId, standardId));

create table PROJECT (
     projectId numeric(1) not null,
     project_name char(1) not null,
     description char(1) not null,
     instanceId numeric(1) not null,
     constraint ID_PROJECT_ID primary key (projectId));

create table TIER (
     tierId char(1) not null,
     tier_name char(1) not null,
     Par_tierId char(1) not null,
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

create table user_to_project (
     projectId numeric(1) not null,
     userId numeric(1) not null,
     permission char(1) not null,
     constraint ID_user_to_project_ID primary key (userId, projectId));

create table work_on (
     conflictId char(1) not null,
     userId numeric(1) not null,
     constraint ID_work_on_ID primary key (userId, conflictId));


-- Constraints Section
-- ___________________ 

alter table ANNOTATION add constraint FKhas_FK
     foreign key (tierId)
     references TIER;

alter table COMMENT add constraint FKwrite_FK
     foreign key (userId)
     references USER;

alter table COMMENT add constraint FKparent_of_FK
     foreign key (Par_commentId)
     references COMMENT;

alter table COMMENT_CONFLICT add constraint FKCOM_COM_2_FK
     foreign key (commentId)
     references COMMENT;

alter table COMMENT_CONFLICT add constraint FKabout_conflict_FK
     foreign key (conflictId)
     references CONFLICT;

alter table COMMENT_ELAN_FILE add constraint FKCOM_COM_FK
     foreign key (commentId)
     references COMMENT;

alter table COMMENT_ELAN_FILE add constraint FKabout_elan_file_FK
     foreign key (elanId)
     references ELAN_FILE;

alter table COMMENT_PROJECT add constraint FKCOM_COM_1_FK
     foreign key (commentId)
     references COMMENT;

alter table COMMENT_PROJECT add constraint FKabout_project_FK
     foreign key (projectId)
     references PROJECT;

alter table CONFLICT add constraint FKhas_conflict_FK
     foreign key (projectId)
     references PROJECT;

alter table ELAN_FILE add constraint FKupload_FK
     foreign key (userId)
     references USER;

alter table generate add constraint FKgen_ELA
     foreign key (elanId)
     references ELAN_FILE;

alter table generate add constraint FKgen_CON_FK
     foreign key (conflictId)
     references CONFLICT;

alter table INVITATION add constraint FKsend_FK
     foreign key (userId)
     references USER;

alter table INVITATION add constraint FKreceive_FK
     foreign key (Rec_userId)
     references USER;

alter table INVITATION add constraint FKabout_FK
     foreign key (projectId)
     references PROJECT;

alter table linked add constraint FKlin_PRO_FK
     foreign key (projectId)
     references PROJECT;

alter table linked add constraint FKlin_ELA
     foreign key (elanId)
     references ELAN_FILE;

alter table made_of add constraint FKmad_TIE
     foreign key (tierId)
     references TIER;

alter table made_of add constraint FKmad_ELA_FK
     foreign key (elanId)
     references ELAN_FILE;

alter table operate_on add constraint FKope_PRO
     foreign key (projectId)
     references PROJECT;

alter table operate_on add constraint FKope_ANN_FK
     foreign key (standardId)
     references ANNOTATION_STANTARD;

alter table PROJECT add constraint FKhost_FK
     foreign key (instanceId)
     references INSTANCE;

alter table TIER add constraint FKparent_of_tier_FK
     foreign key (Par_tierId)
     references TIER;

alter table user_to_project add constraint FKuse_USE
     foreign key (userId)
     references USER;

alter table user_to_project add constraint FKuse_PRO_FK
     foreign key (projectId)
     references PROJECT;

alter table work_on add constraint FKwor_USE
     foreign key (userId)
     references USER;

alter table work_on add constraint FKwor_CON_FK
     foreign key (conflictId)
     references CONFLICT;


-- Index Section
-- _____________ 

create unique index ID_ANNOTATION_IND
     on ANNOTATION (annotationId);

create index FKhas_IND
     on ANNOTATION (tierId);

create unique index ID_ANNOTATION_STANTARD_IND
     on ANNOTATION_STANTARD (standardId);

create unique index ID_COMMENT_IND
     on COMMENT (commentId);

create index FKwrite_IND
     on COMMENT (userId);

create index FKparent_of_IND
     on COMMENT (Par_commentId);

create unique index FKCOM_COM_2_IND
     on COMMENT_CONFLICT (commentId);

create index FKabout_conflict_IND
     on COMMENT_CONFLICT (conflictId);

create unique index FKCOM_COM_IND
     on COMMENT_ELAN_FILE (commentId);

create index FKabout_elan_file_IND
     on COMMENT_ELAN_FILE (elanId);

create unique index FKCOM_COM_1_IND
     on COMMENT_PROJECT (commentId);

create index FKabout_project_IND
     on COMMENT_PROJECT (projectId);

create unique index ID_CONFLICT_IND
     on CONFLICT (conflictId);

create index FKhas_conflict_IND
     on CONFLICT (projectId);

create unique index ID_ELAN_FILE_IND
     on ELAN_FILE (elanId);

create index FKupload_IND
     on ELAN_FILE (userId);

create unique index ID_generate_IND
     on generate (elanId, conflictId);

create index FKgen_CON_IND
     on generate (conflictId);

create unique index ID_INSTANCE_IND
     on INSTANCE (instanceId);

create unique index ID_INVITATION_IND
     on INVITATION (invitationID);

create index FKsend_IND
     on INVITATION (userId);

create index FKreceive_IND
     on INVITATION (Rec_userId);

create index FKabout_IND
     on INVITATION (projectId);

create unique index ID_linked_IND
     on linked (elanId, projectId);

create index FKlin_PRO_IND
     on linked (projectId);

create unique index ID_made_of_IND
     on made_of (tierId, elanId);

create index FKmad_ELA_IND
     on made_of (elanId);

create unique index ID_operate_on_IND
     on operate_on (projectId, standardId);

create index FKope_ANN_IND
     on operate_on (standardId);

create unique index ID_PROJECT_IND
     on PROJECT (projectId);

create index FKhost_IND
     on PROJECT (instanceId);

create unique index ID_TIER_IND
     on TIER (tierId);

create index FKparent_of_tier_IND
     on TIER (Par_tierId);

create unique index ID_USER_IND
     on USER (userId);

create unique index ID_user_to_project_IND
     on user_to_project (userId, projectId);

create index FKuse_PRO_IND
     on user_to_project (projectId);

create unique index ID_work_on_IND
     on work_on (userId, conflictId);

create index FKwor_CON_IND
     on work_on (conflictId);

