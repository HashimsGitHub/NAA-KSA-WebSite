# NUST Alumni on Firebase Spark

Project: `nust-alumni-association`. Work is isolated on `feature/nust-firebase-migration`.

## Architecture

- Firebase Hosting serves `frontend/` at `https://nust-alumni-association.web.app` after deployment.
- Firebase Authentication handles email and password only. The email address is the login username. Passwords are not stored in Firestore.
- Firestore stores `users`, `events`, `knowledge`, `alumni`, and `alumniPrivate` documents. Rules enforce approval and roles.
- Azure Blob Storage serves existing public assets. Administrators upload new public images to Azure and paste their HTTPS Blob URLs into the content editor. Browser uploads require a secure backend and are unavailable in this Spark design.
- Existing Azure Table records are disposable dummy data. No migration is required.
- The existing Azure SWA deployment on `main` remains available during testing.

## Firebase Console setup

1. Enable **Authentication → Sign-in method → Email/Password**. Leave Google and other providers disabled. Under **Users → Add user**, create test accounts and record their UIDs.
2. Create one **Firestore Standard** database in production mode. Choose its region before creating it; Doha (`me-central1`) is an option for a KSA audience.
3. Register a **Web app** in **Project settings → Your apps**. Copy its public config fields into `frontend/firebase-config.js` (replace the placeholders). Never paste service-account keys into this file.
4. Deploy the committed Firestore rules before adding personal records. For each Auth test user, create a document at `users/{UID}` with string fields `full_name`, `role` (`admin` or `alumni`) and `status` (`approved`). Its ID must be exactly the Authentication UID. Bootstrap the first administrator in the Firebase Console; browser clients cannot grant themselves admin privileges.
5. Enable **Hosting**. From the repository root on the migration branch, with Node.js installed:

   ```sh
   npm install -g firebase-tools
   firebase login
   firebase use nust-alumni-association
   firebase deploy --only firestore:rules
   firebase hosting:channel:deploy nust-test
   ```

   Hosting runs `npm ci` and `npm run build` before each deploy. The build outputs `dist/` and bundles the browser SDK with Firestore Lite. Do not run `firebase init` or deploy `frontend/` directly.

6. Test the preview URL, then deploy live with `firebase deploy --only hosting`. Keep the Azure SWA available for rollback.

## Acceptance checks

- A visitor sees published events; a wrong password fails; an Auth user without an approved `users/{UID}` record cannot use protected pages.
- An approved alumni user sees active/visible alumni and published knowledge but cannot write records or read private contacts.
- The admin creates and edits an alumni profile, event and knowledge record; private email and mobile remain in `alumniPrivate`.
- A public image uploaded to Azure Blob Storage loads from its HTTPS URL on the Firebase preview.

The old `api/` is retained for rollback. Auth accounts are created in Firebase Console, not by creating a Firestore record. Contributor publishing and secure browser-to-Azure uploads need a separate workflow. All reads count toward Spark quotas.
