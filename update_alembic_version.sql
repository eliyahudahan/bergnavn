-- ============================================
-- עדכון גרסת alembic בלבד - ללא שינוי בסקימה
-- ============================================
UPDATE alembic_version SET version_num = 'rtz_final_fix' WHERE version_num = '6ee84f482a42';

-- בדוק את העדכון
SELECT version_num, now() as updated_at 
FROM alembic_version;
