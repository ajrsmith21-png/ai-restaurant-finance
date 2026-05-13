ALTER TABLE restaurant ADD COLUMN IF NOT EXISTS clover_access_token TEXT;
ALTER TABLE restaurant ADD COLUMN IF NOT EXISTS clover_merchant_id VARCHAR(255);
ALTER TABLE restaurant ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMP;