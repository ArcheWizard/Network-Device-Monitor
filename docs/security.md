# Security

- Store secrets in environment variables or a secret manager
- Avoid binding API to public interfaces without auth
- SNMP v2c is plaintext; prefer v3 where possible (future work)
- Validate CIDR inputs to avoid scanning unintended networks
