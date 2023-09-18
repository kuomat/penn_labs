from app import db
from flask_login import UserMixin
from datetime import datetime, timedelta


# Establish many-to-many relationships between different tables based on their primary keys
club_tag_association = db.Table(
    'club_tag_association',
    db.Column('club_id', db.Integer, db.ForeignKey('club.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)
user_club_association = db.Table(
    'user_club_association',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'))
)
club_file_association = db.Table(
    'club_file_association',
    db.Column('club_id', db.Integer, db.ForeignKey('club.id')),
    db.Column('file_id', db.Integer, db.ForeignKey('file.id'))
)


# A different database for the tags because of data normalization where if for example, I need to update a tag's name,
# I don't have to go to the Clubs database and update every instance of the tag there
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '<Tag %r>' % self.name

    def to_json(self):
        return {'name': self.name}


# For uploading files
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(120), unique=True, nullable=False)
    content = db.Column(db.LargeBinary, nullable=False)
    content_type = db.Column(db.String(80), nullable=False, default="application/octet-stream") # sets the default as an arbitrary binary data

    def __repr__(self):
        return '<File %r>' % self.path


# Main class that stores all the information about clubs
class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(80), primary_key=False, unique=False)
    name = db.Column(db.String(80), unique=True, nullable=False) # A club needs to have a unique name
    description = db.Column(db.String(120), unique=False)
    favorite_count = db.Column(db.Integer, unique=False, nullable=False, default=0)

    # Many to many relationship
    tags = db.relationship('Tag', secondary=club_tag_association, backref=db.backref('club', lazy=True))
    files = db.relationship('File', secondary=club_file_association, backref=db.backref('club', lazy=True))


    def __repr__(self):
        return '<Club %r>' % self.name

    def to_json(self):
        return {'code': self.code,
                'name': self.name,
                'description': self.description,
                'likes': self.favorite_count,
                'tags': [tag.name for tag in self.tags],
                'files': [file.path for file in self.files]}


# Different users for when signing in
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    first_name = db.Column(db.String(80), unique=False, nullable=True)
    last_name = db.Column(db.String(80), unique=False, nullable=True)

    # Store graduation year as an integer instead of string for memory efficiency reasons
    graduation_year = db.Column(db.Integer, unique=False, nullable=True)

    # To prevent brute force attacks
    login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)

    # Need clubs so that after someone joins some clubs, they can not only see what clubs they have joined
    # But the website can also recommend them other clubs based on similarity
    clubs = db.relationship('Club', secondary=user_club_association, backref=db.backref('club', lazy=True))

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<Users %r>' % self.username

    def to_json(self):
        return {'username': self.username,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'clubs': [club.name for club in self.clubs]}

    def is_account_locked(self):
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def increase_login_attempts(self):
        self.login_attempts += 1
        print("login attempts:", self.login_attempts)
        if self.login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=10)
            self.login_attempts = 0


# For each comment
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)
    content = db.Column(db.String(120), unique=False, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))

    def __repr__(self):
        return '<Comment %r>' % self.content

    def to_json(self):
        return {'user_id': self.user_id,
                'club_id': self.club_id,
                'content': self.content,
                'comment id': self.id,
                'parent id': self.parent_id}


## For OAUTH2 that I wasn't able to implement because of the domain names
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(100), unique=True, nullable=False)
#     password = db.Column(db.String(100), nullable=False)
#     tokens = db.relationship('OAuth2Token', backref=db.backref('user', lazy=True))

# class OAuth2Client(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     client_id = db.Column(db.String(40), unique=True)
#     client_secret = db.Column(db.String(55), nullable=False)
#     client_name = db.Column(db.String(100))
#     is_confidential = db.Column(db.Boolean)

# class OAuth2Token(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
#     client_id = db.Column(db.String(40), db.ForeignKey('o_auth2_client.client_id'), nullable=False)
#     token_type = db.Column(db.String(40))
#     access_token = db.Column(db.String(100), unique=True)
#     refresh_token = db.Column(db.String(100), unique=True)
#     expires_in = db.Column(db.Integer)
#     revoked = db.Column(db.Boolean, nullable=False, default=False)
