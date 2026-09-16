from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class NotepadForm(FlaskForm):
    title = StringField('Title',filters=[lambda value: value.strip() if value else value], validators=[DataRequired(), Length(max=256)])
    body = TextAreaField('Body', validators=[DataRequired()])
    submit = SubmitField('Save notepad')
