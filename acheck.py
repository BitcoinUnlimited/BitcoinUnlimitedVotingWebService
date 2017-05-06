# acheck: Checks on actions
from jvalidate import ValidationError

def checkAuthor(action, authorname):
    if action.author.name != authorname:
        raise ValidationError(
            "Action's signed author %s does not match author %s in action text."
            % (action.author.name, authorname))

def checkUpload(upload, upload_data):
    if upload is None or upload_data is None:
        raise ValidationError(
            "Action proposal-upload needs upload data.")


def checkNoUpload(upload, upload_data):
    if upload_data is not None and len(upload_data)>0:
        print("Upload:", upload)
        print("Upload data:", upload_data)
        raise ValidationError(
            "Upload data not allowed.")
    
