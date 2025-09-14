import random
from app import create_app, db
from models import User, UserType, Transaction, TransactionType, Voucher, Model
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Create all tables
    Model.metadata.create_all(db.engine)

    # Clean up old data
    db.session.query(Transaction).delete()
    db.session.query(Voucher).delete()
    db.session.query(User).delete()
    db.session.commit()

    # Create users
    users = []
    for i in range(10):
        user_type = random.choice([UserType.CUSTOMER, UserType.MERCHANT])
        user = User(
            username=f'{user_type.value}{i}',
            email=f'{user_type.value}{i}@example.com',
            phone=f'123456789{i}',
            password_hash=generate_password_hash('password'),
            user_type=user_type,
            business_name=f'Business {i}' if user_type == UserType.MERCHANT else None,
            address=f'{i} Main St, Anytown, USA' if user_type == UserType.MERCHANT else None,
            points_balance=random.randint(0, 1000)
        )
        users.append(user)
        db.session.add(user)
    
    db.session.commit()

    # Create transactions
    for _ in range(20):
        sender = random.choice(users)
        receiver = random.choice(users)
        while sender == receiver:
            receiver = random.choice(users)
        
        transaction = Transaction(
            transaction_type=random.choice(list(TransactionType)),
            sender_id=sender.id,
            receiver_id=receiver.id,
            points=random.randint(10, 100),
            description=f'Test transaction'
        )
        db.session.add(transaction)
    
    db.session.commit()

    # Create vouchers
    merchants = [user for user in users if user.user_type == UserType.MERCHANT]
    for merchant in merchants:
        for _ in range(5):
            voucher = Voucher(
                code=''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8)),
                merchant_id=merchant.id,
                points_value=random.randint(10, 100)
            )
            db.session.add(voucher)
    
    db.session.commit()

    print('Database seeded successfully!')
