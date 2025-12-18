from .database import db
# from functions import schedule

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    insite_username = db.Column(db.String(100), nullable=False)
    insite_password = db.Column(db.String(255), nullable=False)  # Encrypted
    major = db.Column(db.String(100))
    discipline = db.Column(db.String(100))
    expected_grad_date = db.Column(db.String(50))
    counselor = db.Column(db.String(100))
    registration_date = db.Column(db.String(100))
    schedule = db.Column(db.String(100))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'insite_username': self.insite_username,
            # Password intentionally excluded
            'major': self.major,
            'discipline': self.discipline,
            'expected_grad_date': self.expected_grad_date,
            'counselor': self.counselor,
            'registration_date': self.registration_date,
            'schedule': self.schedule
        }

