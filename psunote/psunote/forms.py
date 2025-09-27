# File: psunote/psunote/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from wtforms_sqlalchemy.orm import model_form

import models


class TagListField(StringField):
    """Simple Tag list field, separated by comma"""

    def _value(self):
        if self.raw_data:
            return ", ".join(self.raw_data)
        return ""

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [tag.strip() for tag in valuelist[0].split(",") if tag.strip()]
        else:
            self.data = []


BaseNoteForm = model_form(
    models.Note,
    base_class=FlaskForm,
    exclude=["created_date", "updated_date"],
    db_session=models.db.session,
)


class NoteForm(BaseNoteForm):
    tags = TagListField("Tags")

    class Meta:
        locales = ["en_US"]
