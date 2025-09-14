from flask import render_template, jsonify, request
from sqlalchemy import select
from app import db
from models import User, UserType
from . import map_bp

@map_bp.route('/')
def show_map():
    return render_template('map/map.html')

@map_bp.route('/merchants')
def get_merchants():
    location_filter = request.args.get('location', '')

    query = select(User).where(User.user_type == UserType.MERCHANT)

    if location_filter:
        query = query.where(User.address.ilike(f'%{location_filter}%'))

    merchants = db.session.scalars(query).all()
    
    merchant_data = []
    for merchant in merchants:
        merchant_data.append({
            'business_name': merchant.business_name,
            'address': merchant.address
        })
    
    return jsonify(merchant_data)
