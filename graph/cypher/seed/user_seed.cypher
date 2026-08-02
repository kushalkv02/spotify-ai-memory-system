// ============================================================
// Sample users. MERGE is used everywhere so this file is safe
// to re-run (idempotent).
// ============================================================

MERGE (u1:User {user_id: 'user_001'})
SET u1.display_name = 'Kushal',
    u1.email = 'kushal@example.com',
    u1.consent_given = true,
    u1.created_at = datetime();

MERGE (u2:User {user_id: 'user_002'})
SET u2.display_name = 'Test User',
    u2.email = 'testuser@example.com',
    u2.consent_given = true,
    u2.created_at = datetime();

MERGE (u3:User {user_id: 'user_003'})
SET u3.display_name = 'Priya',
    u3.email = 'priya@example.com',
    u3.consent_given = true,
    u3.created_at = datetime();

MERGE (u4:User {user_id: 'user_004'})
SET u4.display_name = 'Sam',
    u4.email = 'sam@example.com',
    u4.consent_given = true,
    u4.created_at = datetime();
