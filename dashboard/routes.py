from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from dashboard import dashboard_bp
from app import db
from models import User, Transaction, UserType, TransactionType

@dashboard_bp.route('/')
@login_required
def index():
    if current_user.user_type == UserType.MERCHANT:
        return render_template('dashboard/merchant.html', user=current_user)
    else:
        return render_template('dashboard/customer.html', user=current_user)

@dashboard_bp.route('/transactions')
@login_required
def get_transactions():
    """Get filtered and sorted transactions for the dashboard"""
    
    # Get filter parameters
    transaction_type = request.args.get('type', '')
    sender_receiver = request.args.get('sender_receiver', '')
    date_range = request.args.get('date_range', '')
    sort_by = request.args.get('sort', 'date_desc')
    
    # Base query - get transactions where user is sender or receiver
    query = select(Transaction).where(
        (Transaction.sender_id == current_user.id) |
        (Transaction.receiver_id == current_user.id)
    )
    
    # Apply filters
    if transaction_type:
        query = query.where(Transaction.transaction_type == TransactionType(transaction_type))
    
    # Date range filter
    if date_range:
        today = datetime.utcnow().date()
        if date_range == '7days':
            start_date = today - timedelta(days=7)
        elif date_range == '30days':
            start_date = today - timedelta(days=30)
        elif date_range == '90days':
            start_date = today - timedelta(days=90)
        else:
            start_date = None
            
        if start_date:
            query = query.where(Transaction.created_at >= start_date)
    
    # Apply sorting
    if sort_by == 'date_desc':
        query = query.order_by(Transaction.created_at.desc())
    elif sort_by == 'date_asc':
        query = query.order_by(Transaction.created_at.asc())
    elif sort_by == 'points_desc':
        query = query.order_by(Transaction.points.desc())
    elif sort_by == 'points_asc':
        query = query.order_by(Transaction.points.asc())
    
    transactions = db.session.scalars(query).all()
    
    # If this is an HTMX request, return just the transaction rows
    if request.headers.get('HX-Request'):
        return render_template('partials/transaction_row.html', 
                             transactions=transactions, 
                             current_user=current_user)
    
    # Otherwise return JSON
    transaction_data = []
    for t in transactions:
        sender_name = t.sender.username if t.sender else "System"
        receiver_name = t.receiver.username if t.receiver else "System"
        
        transaction_data.append({
            'id': t.id,
            'type': t.transaction_type.value,
            'sender': sender_name,
            'receiver': receiver_name,
            'points': t.points,
            'description': t.description or '',
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify(transaction_data)

@dashboard_bp.route('/stats')
@login_required
def get_stats():
    """Get user statistics for dashboard"""
    
    # Calculate user stats
    total_earned = db.session.scalar(
        select(func.sum(Transaction.points)).where(
            Transaction.receiver_id == current_user.id
        )
    ) or 0
    
    total_spent = db.session.scalar(
        select(func.sum(Transaction.points)).where(
            Transaction.sender_id == current_user.id
        )
    ) or 0
    
    # Recent transactions count (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_transactions = db.session.scalar(
        select(func.count(Transaction.id)).where(
            ((Transaction.sender_id == current_user.id) |
             (Transaction.receiver_id == current_user.id)) &
            (Transaction.created_at >= thirty_days_ago)
        )
    ) or 0
    
    return jsonify({
        'points_balance': current_user.points_balance,
        'total_earned': total_earned,
        'total_spent': total_spent,
        'recent_transactions': recent_transactions
    })
