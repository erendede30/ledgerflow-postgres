# LedgerFlow — ACID-Compliant Double-Entry Wallet Engine

PostgreSQL'in eşzamanlılık kontrolü (concurrency control), işlem bütünlüğü (ACID) ve tetikleyici (trigger) mimarisini sergileyen çift taraflı muhasebe tabanlı cüzdan ve para transfer motoru.

## Mimari ve Veri Tabanı Özellikleri

- **Çift Taraflı Muhasebe (Double-Entry Bookkeeping):** Her transfer işlemi `ledger_entries` tablosunda benzersiz bir `transaction_uuid` altında eşleşen bir `DEBIT` ve bir `CREDIT` kaydı üretir.
- **Yarış Durumu (Race Condition) Koruması:** Eşzamanlı para çekme/gönderme isteklerinde bakiyenin tutarsızlaşmasını önlemek için `SELECT ... FOR UPDATE` satır kilitleme mekanizması kullanılmıştır.
- **Deadlock Önleme Stratejisi:** Karşılıklı eşzamanlı transferlerde kilitlenme yaşanmaması için cüzdan satırları her zaman artan `wallet_id` sırasıyla kilitlenir.
- **Veri Tabanı Seviyesinde Kısıtlamalar:** `CHECK (balance >= 0)` ve `ON DELETE RESTRICT` kuralları ile finansal kayıtların silinmesi veya eksi bakiyeye düşmesi çekirdek katmanda engellenmiştir.
- **Otomatik JSONB Denetim Logları:** `trg_wallet_audit` tetikleyicisi, cüzdan bakiyesindeki her değişikliği eski/yeni değerleriyle birlikte değiştirilemez `JSONB` formatında `audit_logs` tablosuna işler.

## Kurulum ve Çalıştırma

### 1. Veri Tabanını Oluşturun
```bash
psql -U postgres -c "CREATE DATABASE ledgerflow;"
psql -U postgres -d ledgerflow -f sql/schema.sql
psql -U postgres -d ledgerflow -f sql/seed.sql