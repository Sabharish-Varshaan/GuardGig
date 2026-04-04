-- Enforce one claim per user per IST day and expose IST-day count helper.

CREATE OR REPLACE FUNCTION guardgig_claims_today_count_ist(p_user_id uuid)
RETURNS integer
LANGUAGE sql
STABLE
AS $$
    SELECT COUNT(*)::integer
    FROM claims
    WHERE user_id = p_user_id
    AND DATE(created_at AT TIME ZONE 'Asia/Kolkata') = DATE(NOW() AT TIME ZONE 'Asia/Kolkata');
$$;

CREATE OR REPLACE FUNCTION guardgig_enforce_daily_claim_limit()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    claim_day_ist date;
BEGIN
    claim_day_ist := DATE(COALESCE(NEW.created_at, NOW()) AT TIME ZONE 'Asia/Kolkata');

    IF EXISTS (
        SELECT 1
        FROM claims
        WHERE user_id = NEW.user_id
          AND DATE(created_at AT TIME ZONE 'Asia/Kolkata') = claim_day_ist
    ) THEN
        RAISE EXCEPTION 'Daily claim limit reached'
            USING ERRCODE = '23505';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_guardgig_daily_claim_limit ON claims;

CREATE TRIGGER trg_guardgig_daily_claim_limit
BEFORE INSERT ON claims
FOR EACH ROW
EXECUTE FUNCTION guardgig_enforce_daily_claim_limit();

CREATE INDEX IF NOT EXISTS claims_user_ist_day_idx
ON claims (user_id, ((created_at AT TIME ZONE 'Asia/Kolkata')::date));
