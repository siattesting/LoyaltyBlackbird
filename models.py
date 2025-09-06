from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from app import db
import enum

class UserType(enum.Enum):
    MERCHANT = "merchant"
    CUSTOMER = "customer"

class TransactionType(enum.Enum):
    VOUCHER_ISSUE = "voucher_issue"
    QR_ISSUE = "qr_issue"
    AIRDROP = "airdrop"
    TRANSFER = "transfer"
    REDEMPTION = "redemption"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType), nullable=False)
    business_name: Mapped[Optional[str]] = mapped_column(String(120))
    points_balance: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sent_transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", foreign_keys="Transaction.sender_id", back_populates="sender"
    )
    received_transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", foreign_keys="Transaction.receiver_id", back_populates="receiver"
    )
    vouchers: Mapped[List["Voucher"]] = relationship("Voucher", back_populates="merchant")

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    sender_id: Mapped[Optional[int]] = mapped_column(Integer, db.ForeignKey('users.id'))
    receiver_id: Mapped[Optional[int]] = mapped_column(Integer, db.ForeignKey('users.id'))
    points: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    voucher_code: Mapped[Optional[str]] = mapped_column(String(50))
    qr_code: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sender: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[sender_id], back_populates="sent_transactions"
    )
    receiver: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[receiver_id], back_populates="received_transactions"
    )

class Voucher(db.Model):
    __tablename__ = 'vouchers'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    merchant_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'), nullable=False)
    points_value: Mapped[float] = mapped_column(Float, nullable=False)
    is_redeemed: Mapped[bool] = mapped_column(Boolean, default=False)
    redeemed_by: Mapped[Optional[int]] = mapped_column(Integer, db.ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    redeemed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    merchant: Mapped["User"] = relationship("User", foreign_keys=[merchant_id], back_populates="vouchers")
