# Distribution Release Checklist

## Positioning and disclosure

- [ ] Product name is `PageWatch — SwiftUI＋FastAPI学習用ソース`.
- [ ] Price is free.
- [ ] Any voluntary support option states that payment does not add support, features, priority, or a different license.
- [ ] Listing says this is learning and modification source, not a finished App Store app.
- [ ] Listing says device and TestFlight verification is incomplete.
- [ ] Listing lists the work still required before publication.
- [ ] Listing states that individual setup, debugging, modification, and App Store review support are not included.
- [ ] Listing states that URL terms, robots.txt, rights, access load, and legal compliance are the user's responsibility.
- [ ] `[有料商品のURL]` has been replaced with a real URL or the entire funnel paragraph has been removed.

## Backend validation

- [ ] A clean Python 3.12 virtual environment has been used.
- [ ] Dependencies install from `requirements.txt`.
- [ ] Alembic migrates a new SQLite database successfully.
- [ ] FastAPI starts and `/health` responds successfully.
- [ ] Anonymous device creation, URL registration, list, detail, pause, resume, delete, and account deletion have been checked.
- [ ] Worker and scheduled enqueue commands have been checked.
- [ ] Repository tests have been run and their results recorded.
- [ ] No `.env`, token pepper, production database URL, signing asset, customer data, or private URL is tracked.

## iOS validation and honest status

- [ ] `xcodegen generate` succeeds with the documented toolchain.
- [ ] Debug build succeeds in a clean environment, or the exact failure is disclosed.
- [ ] Release API URL placeholder remains clearly disclosed until replaced.
- [ ] Apple Developer Team and signing are not falsely described as configured.
- [ ] Device and TestFlight status in the listing matches the latest actual test result.
- [ ] App icon, Bundle ID, privacy text, terms URL, and support URL status are accurately disclosed.

## Licensing and distribution

- [ ] `sales/COMMERCIAL_LICENSE_JA.md` has been reviewed by the rights holder.
- [ ] Dependency licenses have been inventoried and required notices are included.
- [ ] The distributor has confirmed that all included code and assets may be distributed.
- [ ] The distribution page has current operator/contact and transaction information where required.
- [ ] Free distribution and voluntary support terms are consistent across the listing and license.

## Package

- [ ] Run the `Build distribution ZIP` GitHub Actions workflow from the release commit or a `product-v*` tag.
- [ ] Download and unpack the generated ZIP in a clean temporary directory.
- [ ] Confirm the ZIP includes source, README, docs, requirements, iOS project source, and all `sales/` documents.
- [ ] Confirm the ZIP does not include `.git`, real secrets, database files, build output, signing files, logs, or customer data.
- [ ] Record version, release date, commit SHA, ZIP filename, and SHA-256.
- [ ] Upload that exact ZIP to the distribution platform.

## Listing assets and final test

- [ ] Add one cover image and three to five screenshots using only test data.
- [ ] Clearly show `無料 / 学習用 / TestFlight未確認 / 個別サポートなし`.
- [ ] Preview the listing on mobile.
- [ ] Download through the same delivery path a user will use.
- [ ] Compare the delivered ZIP's SHA-256 with the release record.
- [ ] Preserve a copy of the published listing text, license version, ZIP, and release record.

