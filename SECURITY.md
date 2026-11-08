# Security policy

Curb is a local, single-user application. It binds to loopback and rejects foreign-origin writes. It is not an authenticated network service. Do not expose its port through a proxy or firewall forwarding rule.

Camera credentials are stored in the local SQLite database, protected by the Windows account and filesystem permissions, not application-level encryption. API responses, diagnostics and backups omit connection credentials. Do not share the database, log files or evidence publicly without reviewing them.

For a vulnerability, use the repository's **Security → Report a vulnerability** if available. Do not put credentials or a weaponized exploit in a public issue. Security support covers the latest published Curb release; dependencies and the original research pipeline have their own upstream support policies.

The initial Windows installer is unsigned. Release checksums detect file changes but are not a substitute for publisher code signing. No automatic executable update runs inside Curb; the update link opens the official GitHub release page in the user's browser.

Backup restore rejects traversal/symlink entries, requires a new directory and checks SQLite integrity. Only restore backups from a trusted source. Existing data is retained on failed restore, update and uninstall.
