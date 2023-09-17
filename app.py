import os
from flask import Flask, request, jsonify, abort, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

DB_FILE_STORAGE = "./instance/clubreview.db"
DB_FILE = "clubreview.db"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_FILE}"
db = SQLAlchemy(app)
UPLOAD_FOLDER = 'folders'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from models import *

def get_all_tags(names):
    tags = Tag.query.filter(Tag.name.in_(names)).all()
    newTagNames = set(names) - set([tag.name for tag in tags])
    tags.extend([Tag(name=name) for name in newTagNames])
    return tags

def get_files(path, binary_data, content_type):
    file = File.query.filter_by(path=path).first()
    if file:
        return file, 200
    else:
        return File(path=path, content=binary_data, content_type=content_type), 201


@app.route('/')
def main():
    return "Welcome to Penn Club Review2!"


@app.route('/api')
def api():
    return jsonify({"message": "Welcome to the Penn Club Review API!."})


# Get all the existing clubs
@app.route('/api/clubs', methods=['GET'])
def get_clubs():
    clubs = Club.query.all()
    return jsonify([club.to_json() for club in clubs])


# Get a specific user
@app.route('/api/users/<string:username>', methods=['GET'])
def get_username(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify(user.to_json())
    else:
        abort(400, description=f"{username} not in database")


# Get a specific club
@app.route('/api/clubs/<string:search_name>', methods=['GET'])
def get_club(search_name):
    clubs = Club.query.filter(func.lower(Club.name).contains(search_name.lower())).all()
    if clubs:
        return jsonify([club.to_json() for club in clubs])
    else:
        abort(400, description=f"{search_name} not in database")


# Add a new club
@app.route('/api/clubs/new/', methods=['POST'])
def add_club():
    club_info = request.get_json()

    # Note: this is CASE SENSITIVE
    clubs = Club.query.filter_by(name=club_info["name"]).first()

    # Check if the club name already exists
    if clubs:
        abort(400, description="Club name already exists")

    # Check if all the required fields were sent
    if not 'name' in club_info:
        abort(400, description="Not all required fields were sent")


    tags = club_info['tags'] if 'tags' in club_info else []
    club = Club(
        code=club_info['code'],
        name=club_info['name'],
        description=club_info['description'],
        tags=get_all_tags(tags)
    )
    db.session.add(club)
    db.session.commit()

    return jsonify({"message": f"Added {club_info['name']} to database."})


# Favorite a club
@app.route('/api/clubs/fav/<string:club_name>', methods=['POST'])
def fav_club(club_name):
    club = Club.query.filter_by(name=club_name).first()

    if club:
        club.favorite_count += 1
        db.session.commit()
        return jsonify({"message": f"{club_name} favorited"})
    else:
        abort(400, description=f"{club_name} not in database")


# Modify a club
@app.route('/api/clubs/mod/<string:club_name>', methods=['POST'])
def modify_club(club_name):
    club = Club.query.filter_by(name=club_name).first()

    if club:
        club_info = request.get_json()

        # Can only modify the code, description, and tags
        club.code = club_info['code'] if 'code' in club_info else club.code
        club.description = club_info['description'] if 'description' in club_info else club.description
        if club_info['tags']:
            club.tags = get_all_tags(club_info['tags'])

        db.session.commit()
        return jsonify({"message": f"{club_name} modified"})
    else:
        abort(400, description=f"{club_name} not in database")



@app.route('/api/tags/count', methods=['GET'])
def get_tags():
    tag_counts = db.session.query(Tag.name, func.count(Club.id)) \
        .outerjoin(Club.tags) \
        .group_by(Tag.name) \
        .all()

    return jsonify([{"tag": name, "club_count": count} for name, count in tag_counts])


# Get all the names of the clubs given a tag
@app.route('/api/tags/name/<string:tag_name>', methods=['GET'])
def get_clubs_by_tag(tag_name):
    clubs_with_tag = Club.query.filter(Club.tags.any(name=tag_name)).all()
    club_names = [club.name for club in clubs_with_tag]

    return jsonify({"clubs": club_names})


# Delete a club
@app.route('/api/clubs/delete/<string:club_name>', methods=['DELETE'])
def delete_club(club_name):
    club = Club.query.filter_by(name=club_name).first()

    if club:
        db.session.delete(club)
        db.session.commit()
        return jsonify({"message": f"{club_name} deleted."})
    else:
        abort(400, description=f"{club_name} not in database")



# Sign up
@app.route('/signup', methods=['POST'])
def signup():


# Login
# @app.route('/login', methods=['POST'])
# def login():


# Logout
# @app.route('/logout', methods=['POST'])
# def logout




# File management
## NOTE: Normally, I would upload the files to a file server like S3, but in this case, I am just going to save it under "folders"
@app.route('/api/clubs/<string:club_name>/files/<path:resource_path>', methods=['PUT'])
def upload_file(club_name,resource_path):
    club = Club.query.filter_by(name=club_name).first()

    if club:
        binary_data = request.data
        content_type = request.headers.get('Content-Type')

        # Check if the file is empty
        if not binary_data:
            abort(400, description=f"{club_name} file is empty.")

        # Get everything after "upload" as the file name
        file_path = os.path.join(UPLOAD_FOLDER, resource_path)

        with open(file_path, 'wb') as f:
            # Write the binary data to the file
            f.write(binary_data)

        # Append the file_path to the club's files
        file_obj, response_code = get_files(file_path, binary_data, content_type) # response_code = 201 if modify, 201 if created
        club.files.append(file_obj)
        db.session.commit()

        return "", response_code
    else:
        abort(400, description=f"{club_name} not in database.")


# Retrieve all the file contents for a specific club
@app.route('/api/clubs/<string:club_name>/files/<path:resource_path>', methods=['GET'])
def retrieve_file(club_name, resource_path):
    club = Club.query.filter_by(name=club_name).first()

    if club:
        file_path = os.path.join(UPLOAD_FOLDER, resource_path)

        if not os.path.exists(file_path):
            abort(400, description=f"{resource_path} file does not exist.")

        # file_obj = File.query.filter_by(path=file_path).first()
        # file_obj = File.query.filter(File.path == file_path, File.club_id == club.id).first()
        file_obj = club.files.filter_by(path=file_path).first()

        if not file_obj:
            abort(400, description=f"{resource_path} file does not exist.")

        content_type = file_obj.content_type

        with open(file_path, 'rb') as f:
            binary_data = f.read()

        # Get the content type for specifying how the binary data should be stored
        response = make_response(binary_data)
        response.headers.set('Content-Type', content_type)
        response.headers.set(
            'Content-Disposition', 'attachment', filename=resource_path)
        return response
    else:
        abort(400, description=f"{club_name} not in database.")


if __name__ == '__main__':
    app.run()
