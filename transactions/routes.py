import random
import string
import qrcode
import io
import base64
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone
from sqlalchemy import select
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from transactions import transactions_bp
from app import db
from models import User, Transaction, Voucher, UserType, TransactionType
from .forms import IssuePointsForm, TransferPointsForm, RedeemVoucherForm

def _create_transaction(transaction_type, points, sender_id=None, receiver_id=None, description=None, voucher_code=None, qr_code=None):
    """Helper function to create a transaction"""
    transaction = Transaction(
        transaction_type=transaction_type,
        sender_id=sender_id,
        receiver_id=receiver_id,
        points=points,
        description=description,
        voucher_code=voucher_code,
        qr_code=qr_code
    )
    db.session.add(transaction)
    return transaction

def generate_voucher_code():
    """Generate a unique voucher code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_qr_code(data):
    """Generate QR code as base64 encoded image"""
    s = URLSafeTimedSerializer(current_app.secret_key)
    signed_data = s.dumps(data)

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(signed_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"

def verify_qr_code_data(signed_data, max_age=300):
    """Verify the signature of the QR code data"""
    s = URLSafeTimedSerializer(current_app.secret_key)
    try:
        data = s.loads(signed_data, max_age=max_age)
        return data
    except Exception:
        return None

@transactions_bp.route('/issue', methods=['GET', 'POST'])
@login_required
def issue_points():
    """Merchant issues points via voucher, QR code, or airdrop"""
    form = IssuePointsForm()
    if current_user.user_type != UserType.MERCHANT:
        flash('Access denied: Merchants only', 'error')
        return redirect(url_for('dashboard.index'))

    if form.validate_on_submit():
        issue_type = form.issue_type.data
        points = form.points.data
        description = form.description.data
        
        try:
            if issue_type == 'voucher':
                voucher_code = generate_voucher_code()
                
                voucher = Voucher(
                    code=voucher_code,
                    merchant_id=current_user.id,
                    points_value=points
                )
                db.session.add(voucher)
                
                _create_transaction(
                    transaction_type=TransactionType.VOUCHER_ISSUE,
                    sender_id=current_user.id,
                    points=points,
                    description=description,
                    voucher_code=voucher_code
                )
                
                db.session.commit()
                flash(f'Voucher code created: {voucher_code}', 'success')
                
            elif issue_type == 'qr_code':
                qr_data = {
                    'type': 'points_issue',
                    'merchant_id': current_user.id,
                    'points': points,
                    'description': description,
                }
                qr_image = generate_qr_code(qr_data)
                
                _create_transaction(
                    transaction_type=TransactionType.QR_ISSUE,
                    sender_id=current_user.id,
                    points=points,
                    description=description,
                    qr_code=qr_image
                )
                db.session.commit()
                
                flash('QR code generated successfully', 'success')
                
            elif issue_type == 'airdrop':
                customer_email = form.customer_email.data
                
                with db.session.begin_nested():
                    customer = db.session.scalar(
                        select(User).where(User.email == customer_email).with_for_update()
                    )
                    
                    if not customer or customer.user_type != UserType.CUSTOMER:
                        flash('Customer not found', 'error')
                        return render_template('transactions/issue.html', form=form)
                    
                    customer.points_balance += points
                    
                    _create_transaction(
                        transaction_type=TransactionType.AIRDROP,
                        sender_id=current_user.id,
                        receiver_id=customer.id,
                        points=points,
                        description=description
                    )
                
                db.session.commit()
                
                flash(f'Points airdropped to {customer.username}', 'success')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error issuing points: {str(e)}', 'error')
    
    return render_template('transactions/issue.html', form=form)

@transactions_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer_points():
    """Customer transfers points to another user"""
    form = TransferPointsForm()
    if form.validate_on_submit():
        recipient_email = form.recipient_email.data
        points = form.points.data
        description = form.description.data
        
        if points > current_user.points_balance:
            flash('Insufficient points balance', 'error')
            return render_template('transactions/transfer.html', form=form)

        with db.session.begin_nested():
            sender = db.session.get(User, current_user.id, with_for_update=True)

            if points > sender.points_balance:
                flash('Insufficient points balance', 'error')
                return render_template('transactions/transfer.html', form=form)
            
            recipient = db.session.scalar(
                select(User).where(User.email == recipient_email).with_for_update()
            )
            
            if not recipient:
                flash('Recipient not found', 'error')
                return render_template('transactions/transfer.html', form=form)
            
            if recipient.id == sender.id:
                flash('Cannot transfer points to yourself', 'error')
                return render_template('transactions/transfer.html', form=form)
            
            sender.points_balance -= points
            recipient.points_balance += points
            
            _create_transaction(
                transaction_type=TransactionType.TRANSFER,
                sender_id=sender.id,
                receiver_id=recipient.id,
                points=points,
                description=description
            )
        
        db.session.commit()
        
        flash(f'Successfully transferred {points} points to {recipient.username}', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('transactions/transfer.html', form=form)

@transactions_bp.route('/redeem', methods=['GET', 'POST'])
@login_required
def redeem_voucher():
    """Customer redeems a voucher code"""
    form = RedeemVoucherForm()
    if form.validate_on_submit():
        voucher_code = form.voucher_code.data.upper()
        
        with db.session.begin_nested():
            voucher = db.session.scalar(
                select(Voucher).where(Voucher.code == voucher_code).with_for_update()
            )
            
            if not voucher:
                flash('Invalid voucher code', 'error')
                return render_template('transactions/redeem.html', form=form)
            
            if voucher.is_redeemed:
                flash('Voucher code already redeemed', 'error')
                return render_template('transactions/redeem.html', form=form)
            
            user = db.session.get(User, current_user.id, with_for_update=True)
            
            user.points_balance += voucher.points_value
            
            voucher.is_redeemed = True
            voucher.redeemed_by = user.id
            voucher.redeemed_at = datetime.now(timezone.utc)
            
            _create_transaction(
                transaction_type=TransactionType.REDEMPTION,
                sender_id=voucher.merchant_id,
                receiver_id=user.id,
                points=voucher.points_value,
                description=f'Voucher redemption: {voucher_code}',
                voucher_code=voucher_code
            )
        
        db.session.commit()
        
        flash(f'Successfully redeemed {voucher.points_value} points!', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('transactions/redeem.html', form=form)

@transactions_bp.route('/scan_qr', methods=['POST'])
@login_required
def scan_qr():
    """Handle QR code scanning result"""
    
    signed_qr_data = request.json.get('qr_data')
    
    if not signed_qr_data:
        return jsonify({'success': False, 'message': 'QR data missing'})

    try:
        qr_data = verify_qr_code_data(signed_qr_data)
    except SignatureExpired:
        return jsonify({'success': False, 'message': 'QR code has expired'})
    except BadTimeSignature:
        return jsonify({'success': False, 'message': 'Invalid QR code signature'})
    except Exception as e:
        current_app.logger.error(f"Error verifying QR code: {e}")
        return jsonify({'success': False, 'message': 'Error processing QR code'})
    
    if not qr_data or qr_data.get('type') != 'points_issue':
        return jsonify({'success': False, 'message': 'Invalid QR code content'})

    points = qr_data.get('points')
    merchant_id = qr_data.get('merchant_id')
    description = qr_data.get('description')

    if not all([points, merchant_id]):
        return jsonify({'success': False, 'message': 'Incomplete QR code data'})

    try:
        with db.session.begin_nested():
            receiver = db.session.get(User, current_user.id, with_for_update=True)
            sender = db.session.get(User, merchant_id, with_for_update=True)

            if not sender or sender.user_type != UserType.MERCHANT:
                return jsonify({'success': False, 'message': 'Invalid merchant in QR code'})

            receiver.points_balance += points

            _create_transaction(
                transaction_type=TransactionType.QR_ISSUE,
                sender_id=sender.id,
                receiver_id=receiver.id,
                points=points,
                description=description
            )
        
        db.session.commit()
        
        flash(f'Successfully received {points} points from {sender.business_name}', 'success')
        return jsonify({'success': True, 'message': 'Points awarded successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing QR code transaction: {e}")
        return jsonify({'success': False, 'message': f'Transaction failed: {str(e)}'})
