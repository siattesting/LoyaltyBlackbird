from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from extensions import Model
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

class User(UserMixin, Model):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType), nullable=False)
    business_name: Mapped[Optional[str]] = mapped_column(String(120))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    # latitude: Mapped[Optional[float]] = mapped_column(Float)
    # longitude: Mapped[Optional[float]] = mapped_column(Float)
    points_balance: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    
    # Relationships
    sent_transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", foreign_keys="Transaction.sender_id", back_populates="sender"
    )
    received_transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", foreign_keys="Transaction.receiver_id", back_populates="receiver"
    )
    vouchers: Mapped[List["Voucher"]] = relationship(
        "Voucher", foreign_keys="Voucher.merchant_id", back_populates="merchant"
    )

class Transaction(Model):
    __tablename__ = 'transactions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    sender_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'))
    receiver_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'))
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    voucher_code: Mapped[Optional[str]] = mapped_column(String(50))
    qr_code: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    
    # Relationships
    sender: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[sender_id], back_populates="sent_transactions"
    )
    receiver: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[receiver_id], back_populates="received_transactions"
    )

class Voucher(Model):
    __tablename__ = 'vouchers'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    merchant_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    points_value: Mapped[int] = mapped_column(Integer, nullable=False)
    is_redeemed: Mapped[bool] = mapped_column(Boolean, default=False)
    redeemed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    redeemed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    merchant: Mapped["User"] = relationship("User", foreign_keys=[merchant_id], back_populates="vouchers")
