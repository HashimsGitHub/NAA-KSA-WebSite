# NUST Alumni migration: Firebase Hosting and Firestore, Azure API and blobs

Project: `nust-alumni-association`. This branch is not ready for a live deployment.

## No-billing target

- Firebase Hosting Spark plan serves `frontend/` at `https://nust-alumni-association.web.app` (subject to project/site creation). The public HTML, CSS and JavaScript are hosted there.
- Azure Blob Storage continues to hold site images, uploaded content and documents. Confirm public read settings on assets meant to be public; private alumni media requires controlled delivery.
- A **separate Azure Function App** hosts the NUST Python `/api` endpoints and connects to Firestore using a server credential stored in Azure settings. Firebase Spark cannot host the existing Python API with Cloud Run/Functions without a billing account.
- Firestore stores the former Azure Table records. `firestore.rules` denies browser SDK access; server SDK access is governed by IAM.
- The JavaScript currently calls relative `/api`. It must be updated to the standalone Azure Function App HTTPS URL *before* publishing the Firebase site. Allow the exact `https://nust-alumni-association.web.app` origin in the Azure Function App CORS configuration; test JSON requests and the `X-Session-Id` preflight. Do not put Function keys in browser JavaScript.
- An Azure Static Web App managed API is coupled to its SWA deployment. Do not use its `nice-meadow` endpoint as the long-term NUST API when that SWA will serve VCNITY.

## Browser setup

1. In Firebase Console enable Hosting; the Spark plan supports static hosting and a `web.app` domain. Do not enable billing, Cloud Run, Cloud Functions or Firebase Storage.
2. Create exactly one Firestore Standard database in production mode; choose its location before creation. Doha `me-central1` is an option if it meets your data-location requirements.
3. Keep Azure Blob containers for assets. Stand up a dedicated Azure Function App for NUST and configure its CORS with only the Firebase Hosting origin and any staging origin needed.
4. Migrate a backed-up copy of Azure Tables to Firestore and verify record counts and account behavior, then test the API and frontend on a Firebase preview channel. Keep an Azure Tables rollback copy.
5. When testing passes, deploy Hosting to its live channel and change any desired links to the `web.app` URL. Move VCNITY to its own repository after stakeholder approval; keep NUST `main` and existing SWA running until cutover.

`firebase.json` intentionally has no `/api` rewrite. Firebase Hosting cannot magically run the Azure Functions backend. Publishing static files now would show pages but break login, directory and admin features because `/api` currently resolves against the page origin.

**Status:** Firebase Hosting config is staged. API portability, Firestore migration, Azure Function deployment, frontend API URL and user acceptance tests remain.
