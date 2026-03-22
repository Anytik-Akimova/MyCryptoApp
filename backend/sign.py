import ecdsa
import math

# ДАНІ ДЛЯ ТЕСТУ (Зміни на свої)
# priv_key_hex = "ТУТ_ТВІЙ_ПРИВАТНИЙ_КЛЮЧ"
priv_key_hex = "9e79f99f830ef805b9ac35f7319124257c80bd16503572d04f1eae48e239aa78"
# recipient = "АДРЕСА_ОТРИМУВАЧА"
recipient = "fb7e7ba29d109c38fbb8a89399ca0da09e4231184a5760e488675f71a4e7f3479ecbb56b48527ca950d0d2032c1e85fa59ce8be6f5132af4aea107fbbd3a3de6"
amount = -4.0  # Обов'язково з .0



# Формуємо повідомлення точно так, як це зробить сервер
amount_fl = float(amount)
message = f"{recipient}{math.fabs(amount_fl)}"



# Генеруємо підпис
sk = ecdsa.SigningKey.from_string(bytes.fromhex(priv_key_hex), curve=ecdsa.SECP256k1)
signature = sk.sign(message.encode()).hex()



print(f"--- ДАНІ ДЛЯ SWAGGER ---")
print(f"Recipient: {recipient}")
print(f"Amount: {math.fabs(amount_fl)}")
print(f"Signature: {signature}")