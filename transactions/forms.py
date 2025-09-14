from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, RadioField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class IssuePointsForm(FlaskForm):
    issue_type = RadioField('Issue Type', choices=[('voucher', 'Voucher'), ('qr_code', 'QR Code'), ('airdrop', 'Airdrop')], validators=[DataRequired()])
    points = FloatField('Points', validators=[DataRequired(), NumberRange(min=0.1)])
    description = StringField('Description')
    customer_email = StringField('Customer Email')
    submit = SubmitField('Issue Points')

class TransferPointsForm(FlaskForm):
    recipient_email = StringField('Recipient Email', validators=[DataRequired()])
    points = FloatField('Points', validators=[DataRequired(), NumberRange(min=0.1)])
    description = StringField('Description')
    submit = SubmitField('Transfer Points')

class RedeemVoucherForm(FlaskForm):
    voucher_code = StringField('Voucher Code', validators=[DataRequired()])
    submit = SubmitField('Redeem Voucher')
