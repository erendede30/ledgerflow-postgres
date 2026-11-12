import concurrent.futures
import requests

URL = "http://127.0.0.1:5000/transfer"

def send_transfer(i):
    payload = {
        "sender_id": 1,
        "receiver_id": 2,
        "amount": 500.00,
        "description": f"Es zamanli test #{i}"
    }
    res = requests.post(URL, json=payload)
    return res.status_code, res.json()

if __name__ == "__main__":
    # Kalan 4250 TRY bakiye varken aynı anda 12 adet 500 TRY (toplam 6000 TRY) istek gönderilir.
    # Sadece 8 tanesi başarılı olmalı, 4 tanesi 'Yetersiz bakiye' ile reddedilmelidir.
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(send_transfer, i) for i in range(1, 13)]
        results = [f.result() for f in futures]

    success_count = sum(1 for status, _ in results if status == 201)
    rejected_count = sum(1 for status, _ in results if status == 400)

    print(f"Başarılı Transfer Sayısı: {success_count}")
    print(f"Yetersiz Bakiye Nedeniyle Reddedilen: {rejected_count}")