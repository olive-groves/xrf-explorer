from os.path import join

from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired


class UploadFileForm(FlaskForm):

    file: FileField = FileField("File", validators=[InputRequired()])
    submit: SubmitField = SubmitField("Upload File")

    def serialize(self) -> dict:
        return {
            # "hidden_tag": self.hidden_tag(),
            "file": self.file,
            "submit": self.submit
        }



def upload_file(file, upload_folder: str) -> str:
    file.save(join(upload_folder, secure_filename(file.filename)))
    return "Uploaded file"