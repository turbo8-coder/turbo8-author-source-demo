# Turbo8 cartridge source

Use a dedicated public GitHub repository. Export each game as a Player cartridge ZIP
with its cover included, then commit the ZIPs under `cartridges/` on the default branch.
Keep the filename when updating a game. Each filename has its own cartridge ID and version.

In GitHub Actions, run **Publish Turbo8 cartridges** on the default branch.
The workflow validates the ZIPs and uploads a draft Release before making it public.
Share your repository URL with players. In Turbo8 they can open **Online → Source → Add and open**.
No GitHub login is needed to browse or install.

Run the workflow again after changing the ZIPs. Changed games advance by one patch
version. Removing a ZIP unlists the game on the next release. Keep previous Releases
since unchanged games can still use their assets. Reserve the repository’s latest
Release for the catalog. An interrupted upload can leave an unpublished draft.
