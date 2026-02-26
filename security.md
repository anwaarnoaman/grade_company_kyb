# Security Practices for KYB & Financial Risk Assessment

This project handles synthetic company KYB and financial data for regulatory compliance demonstration purposes. All sensitive operations follow security best practices appropriate for a cloud-based POC/prototype.

---

## Secrets Management

- All secrets, credentials, and configuration variables are stored in **Azure Key Vault**.
- No credentials or sensitive data are hard-coded in source code or configuration files.
- Backend containers retrieve secrets securely at runtime using managed identities.

---

## Data Storage & Encryption

- **Azure Blob Storage**:
  - Stores uploaded documents.
  - Server-side encryption (SSE) is enabled by default.
- **PostgreSQL**:
  - Stores structured company profile and document metadata.
  - Connections secured via SSL/TLS.
- **MongoDB**:
  - Stores unified JSON KYB data.
  - TLS/SSL enforced for all connections.
- Sensitive fields in logs or UI are masked (e.g., company identifiers).

---

## Access Control

- Backend services have **least-privilege access** to Blob Storage, PostgreSQL, and MongoDB.
- Frontend communicates only with the backend via **HTTPS API using OAuth JWT tokens** for authentication and authorization.
- Direct DB or storage access from frontend is prohibited.
- Users authenticate through the frontend and can only access documents or data they are authorized to view.

---

## Audit & Logging

- All critical actions are logged with structured audit information:
  - Document uploads and processing
  - Data extraction and field changes
  - Risk scoring computation
  - Manual edits from Review & Confirm UI
- Logs mask sensitive values (e.g., company names, IDs) for privacy.
- Logs are stored securely and can be exported for regulatory review.

---

## Data Privacy

- Only synthetic or publicly available data is used for this demo project.
- No real PII, financial, or confidential information is stored or processed.

---

## Network & Communication Security

- All communication between frontend and backend, and between backend and databases/storage, uses **HTTPS/TLS**.
- Backend containers are isolated within the Azure Container Apps environment.
- No public database endpoints are exposed.

---

## Risks & Limitations

- This system is a **POC/prototype**, not production-grade.
- Security measures are designed for demonstration purposes.
- Additional production security considerations would include:
  - Role-based access control (RBAC)
  - Multi-factor authentication
  - Data retention policies
  - Advanced monitoring and alerting

