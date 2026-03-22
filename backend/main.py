import hashlib
import json
import secrets
import ecdsa
import math

from time import time
from fastapi import FastAPI, Depends, HTTPException  # помилки в http запитах
from sqlalchemy.orm import Session  # взаємодія з бдб session - db.context
from fastapi.middleware.cors import CORSMiddleware #тестування роботи бек і фронтенду

from database import SessionLocal, DBUser, DBBlock, DBTransaction, DBUserContacts, Base, engine  # імпорт моделей та сесії з бази даних

Base.metadata.create_all(bind=engine)  

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Дозволяємо всі джерела для тестування, сервіс доступний для будь-яких клієнтів
    allow_methods=["*"],  # Дозволяємо всі HTTP методи (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Дозволяємо всі заголовки
)

DIFFICULTY = 6
REWARD = 10.0

def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_hash(block_data: dict) -> str:
    encoded = json.dumps(block_data, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()

def verify_signature(public_key_hex, signature_hex, message) -> bool:
    try:
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key_hex), 
                                            curve=ecdsa.SECP256k1)  # Алгоритм шифрування цифрових підписів, який використовується в блокчейні
        return vk.verify(bytes.fromhex(signature_hex), message.encode())
    except:
        return False

@app.post("/register")
def register(username: str, db: Session = Depends(get_db)):
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    private_key = sk.to_string().hex()
    address = sk.get_verifying_key().to_string().hex()

    user = DBUser(username=username, address=address, private_key=private_key)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


    # return {
    #     'address': address,
    #     'private_key': private_key
    # }
# автоматично буде повертати саме json
# Користувач буде його розпаковувати і зберігати у себе, 
#   щоб потім використовувати для транзакцій та отримання балансу


@app.post("/login")
def login(private_key: str, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.private_key == private_key).first()
    if not user:
        raise HTTPException(status_code=400, detail="ключ невірний!")
    return user

@app.post('/transactions/send-secure')
def send_secure(sender_address: str, recipient_address: str, amount: float,
                signature: str, db: Session = Depends(get_db)):
    #0. Перевірка кількості грошей (від'ємні значення переводимо в додатні)
    amount = math.fabs(amount)
    print(amount)

    #1. Перевірка підпису:
    msg = f'{recipient_address}{float(amount)}'
    if not verify_signature(sender_address, signature, msg):
        raise HTTPException(status_code=400, detail="Invalid signature")

    #2. Перевірка балансу:
    sender = db.query(DBUser).filter(DBUser.address == sender_address).first()
    recipient = db.query(DBUser).filter(DBUser.address == recipient_address).first()
    if not sender or sender.balance < amount:
        raise HTTPException(status_code=401, detail="Wrong amount! Insufficient funds")

    #3. Transver of funds
    if recipient:
        recipient.balance += amount
        sender.balance -= amount
    else:
        raise HTTPException(status_code=402, detail="Recipient address not found")


    #4. Add transaction to db
    new_tx = DBTransaction(sender = sender_address, recipient = recipient_address,
                           amount = amount, signature = signature)

    db.add(new_tx)
    db.commit()
    return {
        'message': 'Transaction was sent successfully!',
        'current_balance_sender': f'{sender.balance}',
    }

app.post('/mine')
def mine(miner_address: str, db: Session = Depends(get_db)):
    last_block=db.query(DBBlock).order_by(DBBlock.index.desc()).first()
    prev_hash = last_block.hash if last_block else "0"
    prev_proof = last_block.proof if last_block else 100
    proof = 0
    while True:
        guess = f'{prev_proof}{proof}{prev_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        if guess_hash[:DIFFICULTY] == '0' * DIFFICULTY:
            break
        proof += 1
    
    new_block = DBBlock(
        index=(last_block.index + 1) if last_block else 1,
        timestamp=time(),
        proof=proof,
        previous_hash=prev_hash,
        hash=guess_hash
    )
    db.add(new_block)
    db.flush()
    #->
    pending_txs = db.query(DBTransaction).filter(DBTransaction.block_id == None).all()
    for tx in pending_txs:
        tx.block_id = new_block.id
    #->
    miner = db.query(DBUser).filter(DBUser.address == miner_address).first()
    if miner:
        miner.balance += REWARD
    #->
    db.commit()
    return new_block

@app.get('/chain')
def get_chain(db: Session = Depends(get_db)):
    return db.query(DBBlock).all()


@app.post('/add_contact')
def add_contact(owner_address: str, future_contact_address: str, nickname: str, db: Session = Depends(get_db)):
    
    # 1. Перевірка існування самого юзера
    owner = db.query(DBUser).filter(DBUser.address == owner_address).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Неіснуючий юзер")

    # 2. Перевірка існування майбутнього контакта
    future_contact_user = db.query(DBUser).filter(DBUser.address == future_contact_address).first()
    if not future_contact_user:
        raise HTTPException(status_code=403, detail="Такого користувача не існує")

    # 3. Не можна додати самого себе
    if owner_address == future_contact_address:
        raise HTTPException(status_code=402, detail="Ви не можете додати самого себе в контакти")

    # 4. Перевірка, чи не додали ми його вже раніше
    existing_contact = db.query(DBUserContacts).filter(
        DBUserContacts.owner_id == owner.id,
        DBUserContacts.address == future_contact_address
    ).first()
    
    if existing_contact:
        raise HTTPException(status_code=401, detail="Цей контакт вже є у вашому списку")


    # 5. Yовий запис
    new_contact = DBUserContacts(
        owner_id=owner.id,
        nickname=nickname,  
        address=future_contact_address
    )

    db.add(new_contact)
    db.commit()

    all_contacts = db.query(DBUserContacts).filter(DBUserContacts.owner_id == owner.id).all()
    
    return {
        "message": f"Контакт {nickname} успішно доданий!",
        "all contacts": all_contacts,   
        }



@app.get('/contacts')
def get_user_contacts(private_key: str,db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.private_key == private_key).first()
    if not user:
        raise HTTPException(status_code=400, detail="Ключ невірний!")
    try:
        response = db.query(DBUserContacts).filter(DBUserContacts.owner_id == user.id).all()
        if response != 0:
            return response
        else:
            return {
                'message': 'There are no any contacts'
            }
    except Exception as ex:
        return {
            'Exception': f'{ex}'
        }



@app.get('/')
def init_test():
    return {
        'status': 'API server -> OK!!'
    }
