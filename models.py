from app import db


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


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(120), unique=True, nullable=False)
    content = db.Column(db.LargeBinary, nullable=False)
    content_type = db.Column(db.String(80), nullable=False, default="application/octet-stream") # sets the default as an arbitrary binary data

    def __repr__(self):
        return '<File %r>' % self.path


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



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    first_name = db.Column(db.String(80), unique=False, nullable=False)
    last_name = db.Column(db.String(80), unique=False, nullable=False)

    # Store graduation year as an integer instead of string for memory efficiency reasons
    graduation_year = db.Column(db.Integer, unique=False, nullable=False)

    # Need clubs so that after someone joins some clubs, they can not only see what clubs they have joined
    # But the website can also recommend them other clubs based on similarity
    clubs = db.relationship('Club', secondary=user_club_association, backref=db.backref('club', lazy=True))


    def __repr__(self):
        return '<Users %r>' % self.username

    def to_json(self):
        return {'username': self.username,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'clubs': [club.name for club in self.clubs]}
