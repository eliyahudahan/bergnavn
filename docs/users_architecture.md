# User Tables Architecture in BergNavn Project

## Overview

The BergNavn project maintains two separate user tables in the database, each serving distinct purposes:

### 1. Regular Users Table (`users`)

- **Purpose:**  
  Stores real, registered users such as operators, administrators, or future authenticated users.

- **Key Fields:**  
  - `username`  
  - `email`  
  - `password_hash` (encrypted password)  
  - `date_created`  
  - `is_verified`  
  - `is_admin`

- **Current Status:**  
  This table is preserved as-is and not modified during development phases focused on mock users.

- **Future Use:**  
  When real users or operators join the platform, their data will be managed through this table.

---

### 2. Dummy Users Table (`dummy_users`)

- **Purpose:**  
  Contains mock or dummy users used strictly for development, testing, demos, and UI presentations.

- **Key Fields:**  
  - `username`  
  - `email`  
  - `scenario` (e.g., demo scenarios)  
  - `active` status  
  - `created_at` timestamp  
  - `flags` (JSON field to control user-specific features and behavior)  
  - Additional user profile info such as `gender`, `nationality`, `language`, and `preferred_sailing_areas`

- **Rationale for Separation:**  
  Keeping dummy users in a dedicated table ensures clear separation from real user data, avoiding accidental changes or security risks.

- **Development Usage:**  
  This table is actively used to create, update, and manage mock users without affecting production data.

---

## Recommendations for Development

- **Do not alter or delete the `users` table** during mock user development phases to protect real user data integrity.

- **Perform all mock user operations exclusively on the `dummy_users` table**, such as adding, editing, or deactivating dummy users.

- **Extend the `dummy_users` schema as needed** to support additional testing requirements, without impacting real users.

- **Prepare for future integration** where real users and mock users will coexist, each managed through their respective tables.

---

## Summary Explanation

> The project uses two separate user tables: one for real registered users (operators, admins, etc.), and one for mock users used solely for development and testing purposes. The real users table remains untouched to maintain data integrity, while all mock user manipulations occur in a dedicated table to ensure safety and clear separation.

---

© 2025 BergNavn – Internal Documentation
