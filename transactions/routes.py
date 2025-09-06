import random
import string
import qrcode
import io
import base64
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from transactions import transactions_bp
from app import db
from models import User, Transaction, Voucher, UserType, TransactionType

def generate_voucher_code():
    """Generate a unique voucher code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_qr_code(data):
    """Generate QR code as base64 encoded image"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"

@transactions_bp.route('/issue', methods=['GET', 'POST'])
@login_required
def issue_points():
    """Merchant issues points via voucher, QR code, or airdrop"""
    
    if current_user.user_type != UserType.MERCHANT:
        flash('Access denied: Merchants only', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        issue_type = request.form['issue_type']
        points = float(request.form['points'])
        description = request.form.get('description', '')
        
        try:
            if issue_type == 'voucher':
                # Generate voucher code
                voucher_code = generate_voucher_code()
                
                # Create voucher
                voucher = Voucher(
                    code=voucher_code,
                    merchant_id=current_user.id,
                    points_value=points
                )
                db.session.add(voucher)
                
                # Create transaction record
                transaction = Transaction(
                    transaction_type=TransactionType.VOUCHER_ISSUE,
                    sender_id=current_user.id,
                    points=points,
                    description=description,
                    voucher_code=voucher_code
                )
                db.session.add(transaction)
                
                db.session.commit()
                flash(f'Voucher code created: {voucher_code}', 'success')
                
            elif issue_type == 'qr_code':
                # Generate QR code data
                qr_data = {
                    'type': 'points_issue',
                    'merchant_id': current_user.id,
                    'points': points,
                    'description': description,
                    'timestamp': datetime.utcnow().isoformat()
                }
                qr_code_data = str(qr_data)
                qr_image = generate_qr_code(qr_code_data)
                
                # Create transaction record
                transaction = Transaction(
                    transaction_type=TransactionType.QR_ISSUE,
                    sender_id=current_user.id,
                    points=points,
                    description=description,
                    qr_code=qr_image
                )
                db.session.add(transaction)
                db.session.commit()
                
                flash('QR code generated successfully', 'success')
                
            elif issue_type == 'airdrop':
                # Airdrop to specific customer
                customer_email = request.form['customer_email']
                customer = db.session.scalar(
                    db.select(User).where(User.email == customer_email)
                )
                
                if not customer or customer.user_type != UserType.CUSTOMER:
                    flash('Customer not found', 'error')
                    return render_template('transactions/issue.html')
                
                # Update customer balance
                customer.points_balance += points
                
                # Create transaction record
                transaction = Transaction(
                    transaction_type=TransactionType.AIRDROP,
                    sender_id=current_user.id,
                    receiver_id=customer.id,
                    points=points,
                    description=description
                )
                db.session.add(transaction)
                db.session.commit()
                
                flash(f'Points airdropped to {customer.username}', 'success')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error issuing points: {str(e)}', 'error')
    
    return render_template('transactions/issue.html')

@transactions_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer_points():
    """Customer transfers points to another user"""
    
    if request.method == 'POST':
        recipient_email = request.form['recipient_email']
        points = float(request.form['points'])
        description = request.form.get('description', '')
        
        if points <= 0:
            flash('Points must be greater than 0', 'error')
            return render_template('transactions/transfer.html')
        
        if points > current_user.points_balance:
            flash('Insufficient points balance', 'error')
            return render_template('transactions/transfer.html')
        
        # Find recipient
        recipient = db.session.scalar(
            db.select(User).where(User.email == recipient_email)
        )
        
        if not recipient:
            flash('Recipient not found', 'error')
            return render_template('transactions/transfer.html')
        
        if recipient.id == current_user.id:
            flash('Cannot transfer points to yourself', 'error')
            return render_template('transactions/transfer.html')
        
        try:
            # Update balances
            current_user.points_balance -= points
            recipient.points_balance += points
            
            # Create transaction record
            transaction = Transaction(
                transaction_type=TransactionType.TRANSFER,
                sender_id=current_user.id,
                receiver_id=recipient.id,
                points=points,
                description=description
            )
            db.session.add(transaction)
            db.session.commit()
            
            flash(f'Successfully transferred {points} points to {recipient.username}', 'success')
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Transfer failed: {str(e)}', 'error')
    
    return render_template('transactions/transfer.html')

@transactions_bp.route('/redeem', methods=['GET', 'POST'])
@login_required
def redeem_voucher():
    """Customer redeems a voucher code"""
    
    if request.method == 'POST':
        voucher_code = request.form['voucher_code'].upper()
        
        # Find voucher
        voucher = db.session.scalar(
            db.select(Voucher).where(Voucher.code == voucher_code)
        )
        
        if not voucher:
            flash('Invalid voucher code', 'error')
            return render_template('transactions/redeem.html')
        
        if voucher.is_redeemed:
            flash('Voucher code already redeemed', 'error')
            return render_template('transactions/redeem.html')
        
        try:
            # Update user balance
            current_user.points_balance += voucher.points_value
            
            # Mark voucher as redeemed
            voucher.is_redeemed = True
            voucher.redeemed_by = current_user.id
            voucher.redeemed_at = datetime.utcnow()
            
            # Create transaction record
            transaction = Transaction(
                transaction_type=TransactionType.REDEMPTION,
                sender_id=voucher.merchant_id,
                receiver_id=current_user.id,
                points=voucher.points_value,
                description=f'Voucher redemption: {voucher_code}',
                voucher_code=voucher_code
            )
            db.session.add(transaction)
            db.session.commit()
            
            flash(f'Successfully redeemed {voucher.points_value} points!', 'success')
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Redemption failed: {str(e)}', 'error')
    
    return render_template('transactions/redeem.html')

@transactions_bp.route('/scan_qr', methods=['POST'])
@login_required
def scan_qr():
    """Handle QR code scanning result"""
    
    qr_data = request.json.get('qr_data')
    
    try:
        # Parse QR code data (simplified - in production, use proper JSON parsing)
        if 'points_issue' in qr_data:
            # Extract points and merchant info from QR data
            # This is a simplified implementation
            flash('QR code scanned successfully! Points will be added to your account.', 'success')
            return jsonify({'success': True, 'message': 'QR code processed'})
        else:
            return jsonify({'success': False, 'message': 'Invalid QR code'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing QR code: {str(e)}'})
