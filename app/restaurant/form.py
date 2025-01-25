from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired
from app.models import OrderStatus

class EditOrderForm(FlaskForm):
    # id - hidden int id
    id = StringField('ID', render_kw={'readonly': True})
    status = SelectField('Status', 
                        choices=[(status.value, status.name) for status in OrderStatus],
                        validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')