DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS ledger_entries CASCADE;
DROP TABLE IF EXISTS wallets CASCADE;

CREATE TABLE wallets (
    wallet_id SERIAL PRIMARY KEY,
    owner_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    currency CHAR(3) NOT NULL DEFAULT 'TRY',
    balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00 CHECK (balance >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE ledger_entries (
    entry_id BIGSERIAL PRIMARY KEY,
    transaction_uuid UUID NOT NULL,
    wallet_id INT NOT NULL REFERENCES wallets(wallet_id) ON DELETE RESTRICT,
    entry_type VARCHAR(10) NOT NULL CHECK (entry_type IN ('DEBIT', 'CREDIT')),
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    description VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ledger_wallet_id ON ledger_entries(wallet_id);
CREATE INDEX idx_ledger_tx_uuid ON ledger_entries(transaction_uuid);

CREATE TABLE audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    wallet_id INT NOT NULL,
    action_type VARCHAR(20) NOT NULL,
    change_details JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION log_wallet_balance_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.balance IS DISTINCT FROM NEW.balance THEN
        INSERT INTO audit_logs (wallet_id, action_type, change_details)
        VALUES (
            NEW.wallet_id,
            'BALANCE_UPDATE',
            jsonb_build_object(
                'old_balance', OLD.balance,
                'new_balance', NEW.balance,
                'difference', NEW.balance - OLD.balance,
                'currency', NEW.currency
            )
        );
    END IF;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_wallet_audit
AFTER UPDATE OF balance ON wallets
FOR EACH ROW
EXECUTE FUNCTION log_wallet_balance_change();