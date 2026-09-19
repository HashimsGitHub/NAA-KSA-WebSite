# VCNITY PWA checks

This PWA is an installable version of the existing static site. It needs an internet
connection for member information, events, the Knowledge Hub, and admin actions.
Only fixed public assets are cached. Every page navigation is requested from the
network; while offline it shows the offline page instead of stored member data.

## Test the PR

1. Open the Azure Static Web Apps preview URL from the PR check. The workflow
   runs for PRs targeting `develop-vcnity`. Avoid merging into `main` during UAT.
2. In Chrome DevTools, open **Application → Manifest**. Check the name, start
   URL `/`, standalone display, theme colour, and both 192 and 512 icons.
3. Open **Application → Service workers** and confirm `/service-worker.js` is
   activated. Under **Cache storage**, check that there are no API responses,
   HTML pages, profiles, or member directory entries.
4. Reload while online. Switch DevTools to offline and visit `/pages/members.html`:
   the generic offline page should appear, with no member details. Go online and
   confirm login, directory, events and admin actions still use live API data.
5. On Android Chrome, use **Install app** / **Add to Home screen**. On iOS Safari,
   use **Share → Add to Home Screen**. Launch from the home screen and check the
   icon and navigation on a phone.

Lighthouse Performance is a separate metric. Run its PWA/installability checks
against the HTTPS preview URL after deployment; localhost can be used for basic
development, but a plain static server will not serve the Azure Functions API.
