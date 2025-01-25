from flask_wtf import FlaskForm
from wtforms import DateField, StringField, SubmitField, TextAreaField, SelectField, DateTimeField, HiddenField
from wtforms.validators import DataRequired
from app.models import OrderStatus

edit_order_choices = [
    ('Registered', 'Registered'),
    ('InPreparation', 'In preparation'),
    ('WaitingForDelivery', 'Waiting for delivery'),
    ('Ready', 'Ready'),
]
class EditOrderForm(FlaskForm):
    # id - hidden int id
    order_id = HiddenField('ID', render_kw={'readonly': True})
    status = SelectField('Status', 
                        choices=edit_order_choices,
                        validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')

class CreateDeliveryForm(FlaskForm):
    date = DateField('Date',
                     format='%Y-%m-%d',
                     validators=[DataRequired()])
    time = DateTimeField('Time',
                         format='%H:%M',
                         validators=[DataRequired()])
    deliverer_id = SelectField('Deliverer',
                               coerce=int,
                               validators=[DataRequired()])
    order_id = HiddenField('Order ID')
    status = HiddenField('Status')
    notes = HiddenField('Notes')
    submit = SubmitField('Submit')