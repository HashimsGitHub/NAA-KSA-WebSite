# 1. `UserAccounts`

Stores login, roles, approval status.

```
PartitionKey: NUST-KSARowKey: user_email_lowercase
```

Fields:

```
user_idemailfull_namemobilerole: admin | alumni | contributorstatus: pending | approved | rejected | suspendedauth_method: password | google | microsoft | facebook | qrpassword_hashpassword_reset_requiredlinked_alumni_idcreated_atapproved_byapproved_atlast_login_at
```

---

# 2. `AlumniProfiles`

Main alumni directory.

```
PartitionKey: NUST-KSARowKey: alumni_id
```

Fields:

```
alumni_idfull_namepreferred_nameemailmobilecitycountrydegreedepartmentgraduation_yearcurrent_companycurrent_positionindustrylinkedin_urlfacebook_urlinstagram_urlwebsite_urlbioskillsinterestsavailable_to_mentor: true/falselooking_for_jobs: true/falseavailable_to_recruit: true/falseprofile_image_urlvisibility: visible | hiddenshow_mobile: true/falseshow_email: true/falsestatus: active | inactive | suspendedcreated_atupdated_at
```

Do not store:

```
date_of_birthhome_addresspassport / IDsensitive documents
```

---

# 3. `RegistrationRequests`

For new users waiting for admin approval.

```
PartitionKey: NUST-KSARowKey: request_id
```

Fields:

```
request_idfull_nameemailmobiledegreedepartmentgraduation_yearcitycountrylinkedin_urlstatus: pending | approved | rejectedadmin_notessubmitted_atreviewed_byreviewed_at
```

---

# 4. `Sessions`

For login/session tracking.

```
PartitionKey: NUST-KSARowKey: session_id
```

Fields:

```
session_idemailuser_idrolestatuscreated_atexpires_atrevoked: true/falseip_addressuser_agent
```

---

# 5. `LoginTokens`

For QR/passwordless login.

```
PartitionKey: NUST-KSARowKey: token_id
```

Fields:

```
token_idemailtoken_hashpurpose: login | password_resetexpires_atused: true/falsecreated_atused_atip_address
```

---

# 6. `Events`

Events page.

```
PartitionKey: NUST-KSARowKey: event_id
```

Fields:

```
event_idtitleslugdescriptionevent_datestart_timeend_timevenuecitygoogle_maps_urlregistration_required: true/falseregistration_open_atregistration_close_atcapacitycover_image_urlstatus: draft | published | cancelled | completedcreated_bycreated_atupdated_at
```

---

# 7. `EventRegistrations`

Who registered for which event.

```
PartitionKey: event_idRowKey: user_email_lowercase
```

Fields:

```
event_idemailfull_namemobileregistration_status: registered | cancelled | attended | no_showregistered_atchecked_in_at
```

---

# 8. `BlogPosts`

Blog metadata only.

```
PartitionKey: NUST-KSARowKey: post_id
```

Fields:

```
post_idtitleslugsummaryauthor_emailauthor_namemarkdown_blob_pathcover_image_urltagsstatus: draft | submitted | approved | published | rejectedviewslikescreated_atsubmitted_atapproved_byapproved_atpublished_atupdated_at
```

Blog body should be stored as Markdown in Blob Storage.

---

# 9. `MediaAssets`

All uploaded files/images.

```
PartitionKey: NUST-KSARowKey: media_id
```

Fields:

```
media_idasset_type: profile | blog | event | documentlinked_entity_idowner_emailblob_containerblob_pathfile_namecontent_typefile_sizestatus: uploaded | approved | rejected | deletedcreated_atapproved_byapproved_at
```

---

# 10. `AuditLogs`

Security and admin tracking.

```
PartitionKey: NUST-KSARowKey: timestamp_eventid
```

Fields:

```
event_idactor_emailactor_roleactiontarget_tabletarget_iddetailsip_addresscreated_at
```

Examples:

```
USER_APPROVEDALUMNI_UPDATEDBLOG_PUBLISHEDEVENT_CREATEDLOGIN_SUCCESSLOGIN_FAILEDPASSWORD_RESET
```

---

# 11. `ImportJobs`

CSV/Excel imports.

```
PartitionKey: NUST-KSARowKey: import_id
```

Fields:

```
import_idfile_namesource_type: csv | excel | google_forms | linkedin | whatsappuploaded_bystatus: uploaded | processing | completed | failedrecords_totalrecords_createdrecords_updatedrecords_failederror_summarycreated_atcompleted_at
```

---

# 12. `SystemSettings`

Portal-wide settings.

```
PartitionKey: NUST-KSARowKey: setting_name
```

Fields:

```
setting_namesetting_valuedescriptionupdated_byupdated_at
```

Examples:

```
registration_enabledblog_submission_enabledevent_registration_enableddirectory_visible_to_approved_users_only
```

---

# Blob containers

```
profile-imagesblog-imagesevent-imagesblog-contentevent-assetsdocumentsimports
```

All containers should be:

```
Private / No anonymous access
```

---

# Recommended access rules

```
Public visitor:- View home page- View public events- View published blogs- Submit registration requestPending user:- Login/register only- Cannot search directoryApproved alumni:- Search alumni directory- View events- Register for events- View published blogsContributor:- Alumni rights- Submit blog drafts- Upload blog imagesAdmin:- Full CRUD- Approve users- Approve blogs- Manage events- Import CSV/Excel- View audit logs
```

---

# Search model

For 2,000 records, use application-side filtering.

```
Fetch approved + visible alumniFilter in API:- name- degree- department- graduation_year- city- country- company- industry- skillsSort in API:- full_name- graduation_year- city- company
```

This is suitable for Azure Tables at your scale.

---

# Storage design summary

```
Azure Tables:structured data, users, profiles, events, blogs metadata, sessionsAzure Blob Storage:images, markdown blog files, event assets, import filesAzure Static Web App:frontendAzure Functions:secure API and business logic
```