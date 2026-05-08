-- ============================================================
-- STEP 1: Truncate all sensor data (resets IDs too)
-- Usage: mysql -u root -proot1234 sleep_optimizer < truncate_data.sql
-- ============================================================

TRUNCATE TABLE sensor_data;

SELECT 'sensor_data table cleared successfully.' AS status;
