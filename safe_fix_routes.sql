-- ============================================
-- תיקון בטוח לטבלת routes - מוסיף רק מה שחסר
-- ============================================
-- לא מוחק שום עמודה קיימת!
-- לא משנה שום נתון קיים!

DO $$ 
BEGIN
    -- 1. בדוק קודם מה יש
    RAISE NOTICE 'בדיקת עמודות קיימות...';
    
    -- 2. הוסף רק מה שחסר
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'routes' AND column_name = 'source') THEN
        ALTER TABLE routes ADD COLUMN source VARCHAR(50) DEFAULT 'NCA';
        RAISE NOTICE 'נוספה עמודה: source';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'routes' AND column_name = 'rtz_filename') THEN
        ALTER TABLE routes ADD COLUMN rtz_filename VARCHAR(255);
        RAISE NOTICE 'נוספה עמודה: rtz_filename';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'routes' AND column_name = 'waypoint_count') THEN
        ALTER TABLE routes ADD COLUMN waypoint_count INTEGER DEFAULT 0;
        RAISE NOTICE 'נוספה עמודה: waypoint_count';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'routes' AND column_name = 'rtz_file_hash') THEN
        ALTER TABLE routes ADD COLUMN rtz_file_hash VARCHAR(64);
        RAISE NOTICE 'נוספה עמודה: rtz_file_hash';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'routes' AND column_name = 'vessel_draft_min') THEN
        ALTER TABLE routes ADD COLUMN vessel_draft_min DOUBLE PRECISION;
        RAISE NOTICE 'נוספה עמודה: vessel_draft_min';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'routes' AND column_name = 'vessel_draft_max') THEN
        ALTER TABLE routes ADD COLUMN vessel_draft_max DOUBLE PRECISION;
        RAISE NOTICE 'נוספה עמודה: vessel_draft_max';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'routes' AND column_name = 'created_at') THEN
        ALTER TABLE routes ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'נוספה עמודה: created_at';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'routes' AND column_name = 'updated_at') THEN
        ALTER TABLE routes ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'נוספה עמודה: updated_at';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'routes' AND column_name = 'parsed_at') THEN
        ALTER TABLE routes ADD COLUMN parsed_at TIMESTAMP;
        RAISE NOTICE 'נוספה עמודה: parsed_at';
    END IF;
    
    RAISE NOTICE '✅ תיקון הושלם בהצלחה!';
END $$;
