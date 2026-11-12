import os
import uuid
from decimal import Decimal
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "ledgerflow"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "2025"),  # Buraya kendi PostgreSQL şifreni yaz
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route("/wallets/<int:wallet_id>", methods=["GET"])
def get_wallet(wallet_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM wallets WHERE wallet_id = %s;", (wallet_id,))
            wallet = cur.fetchone()
            if not wallet:
                return jsonify({"error": "Cüzdan bulunamadı"}), 404

            cur.execute(
                "SELECT * FROM ledger_entries WHERE wallet_id = %s ORDER BY created_at DESC LIMIT 10;",
                (wallet_id,)
            )
            transactions = cur.fetchall()
            return jsonify({"wallet": wallet, "recent_entries": transactions}), 200
    finally:
        conn.close()

@app.route("/transfer", methods=["POST"])
def transfer_funds():
    data = request.get_json()
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    description = data.get("description", "Para Transferi")

    try:
        amount = Decimal(str(data.get("amount")))
    except Exception:
        return jsonify({"error": "Geçersiz tutar formatı"}), 400

    if not sender_id or not receiver_id or sender_id == receiver_id:
        return jsonify({"error": "Gönderici ve alıcı cüzdanlar farklı olmalıdır"}), 400
    if amount <= Decimal("0.00"):
        return jsonify({"error": "Transfer tutarı sıfırdan büyük olmalıdır"}), 400

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                first_id, second_id = sorted([sender_id, receiver_id])
                cur.execute(
                    "SELECT wallet_id, balance, currency FROM wallets WHERE wallet_id IN (%s, %s) ORDER BY wallet_id FOR UPDATE;",
                    (first_id, second_id)
                )
                locked_wallets = {row["wallet_id"]: row for row in cur.fetchall()}

                if sender_id not in locked_wallets or receiver_id not in locked_wallets:
                    return jsonify({"error": "Cüzdanlardan biri mevcut değil"}), 404

                sender = locked_wallets[sender_id]
                if sender["balance"] < amount:
                    return jsonify({"error": "Yetersiz bakiye"}), 400

                tx_uuid = str(uuid.uuid4())

                cur.execute(
                    "UPDATE wallets SET balance = balance - %s WHERE wallet_id = %s;",
                    (amount, sender_id)
                )
                cur.execute(
                    "UPDATE wallets SET balance = balance + %s WHERE wallet_id = %s;",
                    (amount, receiver_id)
                )
                cur.execute(
                    """
                    INSERT INTO ledger_entries (transaction_uuid, wallet_id, entry_type, amount, description)
                    VALUES (%s, %s, 'DEBIT', %s, %s), (%s, %s, 'CREDIT', %s, %s);
                    """,
                    (tx_uuid, sender_id, amount, description, tx_uuid, receiver_id, amount, description)
                )

        return jsonify({
            "status": "success",
            "transaction_uuid": tx_uuid,
            "transferred_amount": str(amount)
        }), 201

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({"error": "Veri tabanı işlem hatası", "details": str(e)}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=True, port=5000)