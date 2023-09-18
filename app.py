import os
from flask import Flask, request, jsonify, abort, make_response, redirect, url_for, session, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import logout_user, login_required, login_user, LoginManager, current_user


### For OAUTH2 which I didn't end up using because I need a domain name
# from authlib.oauth2 import OAuth2Error
# from authlib.integrations.flask_oauth2 import AuthorizationServer
# from authlib.integrations.flask_oauth2 import ResourceProtector
# from authlib.integrations.sqla_oauth2 import (
#     create_query_client_func,
#     create_save_token_func,
#     create_revocation_endpoint
# )


DB_FILE_STORAGE = "./instance/clubreview.db"
DB_FILE = "clubreview.db"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_FILE}"
db = SQLAlchemy(app)

secret_key = os.urandom(24)
app.secret_key = secret_key

# A folder to store all the files when uploading
UPLOAD_FOLDER = 'folders'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)

from models import *

# Necessary for logging users in
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# Retrieves a list of tag objects from db based on a provided list of tag names.
# This method is primarily so that I don't accidentally create another Tag object when the same object already exists in the database.
def get_all_tags(names):
    tags = Tag.query.filter(Tag.name.in_(names)).all()
    newTagNames = set(names) - set([tag.name for tag in tags])
    tags.extend([Tag(name=name) for name in newTagNames])
    return tags


# Retrieve a file object from db based on a provided file path
# This method is primarily so that I don't accidentally create another File object when the same object already exists in the database.
def get_files(path, binary_data, content_type):
    file = File.query.filter_by(path=path).first()
    if file:
        return file, 200
    else:
        return File(path=path, content=binary_data, content_type=content_type), 201


# Method to create a success response
def create_success_response(data):
    return jsonify({'success': True, 'data': data})


# Method to create an error response
def create_error_response(message, status_code):
    return jsonify({'success': False, 'message': message}), status_code


# Default endpoint
@app.route('/')
def main():
    return "Welcome to Penn Club Review2!"


# Default endpoint
@app.route('/api')
def api():
    return jsonify({"message": "Welcome to the Penn Club Review API!."})


# Get all the existing clubs' information
@app.route('/api/clubs', methods=['GET'])
# @oauth.require_oauth()
def get_clubs():
    try:
        clubs = Club.query.all()
        club_data = [club.to_json() for club in clubs]
        return create_success_response(club_data)
    except Exception as e:
        return create_error_response(str(e), 500)


@app.route('/api/users/<string:username>', methods=['GET'])
def get_username(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return create_success_response(user.to_json())
    else:
        return create_error_response(f"User '{username}' not found", 404)


# Get a specific club's information based on if the name is a substring
@app.route('/api/clubs/<string:search_name>', methods=['GET'])
def get_clubs_by_name(search_name):
    try:
        # The club's name for this method is CASE INSENSITIVE
        clubs = Club.query.filter(func.lower(Club.name).contains(search_name.lower())).all()
        if clubs: # If the club exists
            return create_success_response([club.to_json() for club in clubs])
        else:
            return create_error_response(f"No clubs found matching '{search_name}'", 404)
    except Exception as e:
        return create_error_response(str(e), 500)


# Add a new club if it doesn't exist
@app.route('/api/clubs/new', methods=['POST'])
@login_required
def add_club():
    try:
        club_info = request.get_json()

        # Check if 'name' is present in the JSON data
        if 'name' not in club_info:
            return create_error_response("Not all required fields were sent", 400)

        # Check if a club with the same name already exists
        existing_club = Club.query.filter_by(name=club_info["name"]).first()
        if existing_club:
            return create_error_response("Club name already exists", 400)

        code = club_info.get('code', "")
        description = club_info.get('description', "")
        tags = club_info.get('tags', [])

        # Create and add the club to the database
        club = Club(
            code=code,
            name=club_info['name'],
            description=description,
            tags=get_all_tags(tags)
        )

        db.session.add(club)
        db.session.commit()

        return create_success_response({"message": f"Added {club_info['name']} to the database."})

    except Exception as e:
        return create_error_response(str(e), 500)


# Favorite a specific club
@app.route('/api/clubs/fav/<string:club_name>', methods=['POST'])
@login_required
def fav_club(club_name):
    try:
        club = Club.query.filter_by(name=club_name).first()

        if club:
            # Increment the favorite count
            club.favorite_count += 1
            db.session.commit()
            return create_success_response(f"{club_name} favorited")
        else:
            return create_error_response(f"{club_name} not in database", 400)

    except Exception as e:
        return create_error_response(str(e), 500)


# Modify a club's information if it exists
@app.route('/api/clubs/mod/<string:club_name>', methods=['PUT'])
@login_required
def modify_club(club_name):
    try:
        club = Club.query.filter_by(name=club_name).first()

        if club:
            club_info = request.get_json()

            # Can only modify the code, description, and tags
            club.code = club_info.get('code', club.code)
            club.description = club_info.get('description', club.description)
            if 'tags' in club_info:
                club.tags = get_all_tags(club_info['tags'])

            db.session.commit()
            return create_success_response(f"{club_name} modified")
        else:
            return create_error_response(f"{club_name} not in database", 400)

    except Exception as e:
        return create_error_response(str(e), 500)


# Show a list of tags and the number of clubs associated with each tag.
@app.route('/api/tags/count', methods=['GET'])
def get_tags():
    try:
        # Get the number of clubs associated with each tag
        tag_counts = db.session.query(Tag.name, func.count(Club.id)) \
            .outerjoin(Club.tags) \
            .group_by(Tag.name) \
            .all()

        result = [{"tag": name, "club_count": count} for name, count in tag_counts]
        return create_success_response(result)
    except Exception as e:
        return create_error_response(str(e), 500)


# Get all the names of the clubs given a tag
@app.route('/api/tags/<string:tag_name>/names', methods=['GET'])
def get_clubs_by_tag(tag_name):
    try:
        # Find the club objects that have that tag
        clubs_with_tag = Club.query.filter(Club.tags.any(name=tag_name)).all()
        club_names = [club.name for club in clubs_with_tag]
        return create_success_response({"clubs": club_names})
    except Exception as e:
        return create_error_response(str(e), 500)


# Delete a club
@app.route('/api/clubs/<string:club_name>', methods=['DELETE'])
@login_required
def delete_club(club_name):
    try:
        club = Club.query.filter_by(name=club_name).first()

        if club:
            db.session.delete(club)
            db.session.commit()
            return create_success_response(f"{club_name} deleted.")
        else:
            return create_error_response(f"{club_name} not in database", 400)

    except Exception as e:
        return create_error_response(str(e), 500)



# ## User login ##
# def query_client(client_id):
#     return OAuth2Client.query.filter_by(client_id=client_id).first()

# def save_token(token_data, request):
#     client = request.client
#     user = request.user if request.user else None
#     expires_in = token_data.get('expires_in')
#     if user and expires_in:
#         token = OAuth2Token(
#             client_id=client.client_id,
#             user_id=user.id,
#             token_type=token_data['token_type'],
#             access_token=token_data['access_token'],
#             refresh_token=token_data['refresh_token'],
#             expires_in=expires_in
#         )
#         db.session.add(token)
#         db.session.commit()

# authorization = AuthorizationServer(app, query_client=query_client, save_token=save_token)
# revocation = create_revocation_endpoint(authorization, token_model=OAuth2Token)


# Sign up
@app.route('/signup', methods=['POST'])
def signup():
    try:
        user_info = request.get_json()

        if not user_info.get('username') or not user_info.get('password'):
            return create_error_response("Not all required fields were sent", 400)

        # Check if the username already exists in your database
        user = User.query.filter_by(username=user_info['username']).first()
        if user:
            return create_error_response("Username already exists", 409)

        # Hash the password with the sha256 algorithm and save it to the database
        hashed_password = generate_password_hash(user_info['password'], method='sha256')
        new_user = User(username=user_info['username'], password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return create_success_response({'message': 'User registered successfully'})

    except Exception as e:
        return create_error_response(str(e), 500)



# Login
# @app.route('/login', methods=['POST'])
# def login():
#     user_info = request.get_json()

#     if not user_info['username'] or not user_info['password']:
#         abort(400, description="Not all required fields were sent")

#     user = User.query.filter_by(username=user_info['username']).first()

#     if not user:
#         abort(400, description=f"{user_info['username']} not in database")

#     # Check if the password is correct
#     if not check_password_hash(user.password, user_info['password']):
#         abort(400, description="Incorrect password")
#     else:
#         # Go to an authorization server to retrieve a token
#         session['user_id'] = user.id
#         return gen_token()

# def gen_token():
#     # Disable the previous token
#     for token in OAuth2Token.query.filter_by(user_id=session['user_id']):
#         token.revoked = True

#     # Get new token from the authorization server
#     token = authorization.create_token_response()
#     return jsonify(token)

# @app.route('/token', methods=['GET', 'POST'])
# def token():
#     # Make sure the user is already authenticated (they didn't just access the /gettoken endpoint directly)
#     if 'user_id' not in session:
#         return redirect(url_for('login'))

#     # Get a new token
#     return gen_token()

# # Logout
# @app.route('/logout', methods=['POST'])
# def logout():
#     session.pop('user_id', None)
#     return jsonify({"message": "Logged out."})



## Normal flask login
@app.route('/login', methods=['POST'])
def login():
    try:
        if current_user.is_authenticated:
            return create_error_response("Already logged in to an account.", 400)

        user_info = request.get_json()
        if not user_info.get('username') or not user_info.get('password'):
            return create_error_response("Not all required fields were sent", 400)

        user = User.query.filter_by(username=user_info['username']).first()

        # Check if the user account is locked
        if user and user.is_account_locked():
            return create_error_response("Account is locked. Try again later.", 400)

        # Combine this together so the person won't know if it's the username or password that's wrong (for security reasons)
        if not user or not check_password_hash(user.password, user_info['password']):
            # Increase login attempts if the user exists
            if user:
                user.increase_login_attempts()
                db.session.commit()
            return create_error_response("Wrong username or password.", 400)

        login_user(user)
        return create_success_response({"message": "Logged in."})

    except Exception as e:
        return create_error_response(str(e), 500)


# Logs the user out
@app.route('/logout', methods=['POST'])
def logout():
    try:
        # If the user is currently logged in
        if current_user.is_authenticated:
            logout_user()
            return create_success_response({"message": "Logged out."})
        else:
            return create_error_response("Not logged in.", 400)

    except Exception as e:
        return create_error_response(str(e), 500)



## File management ##
## NOTE: Normally, I would upload the files to a file server like S3, but in this case, I am just going to save it under "folders"

# Upload a file to a specific club
@app.route('/api/clubs/<string:club_name>/files/<path:resource_path>', methods=['PUT'])
def upload_file(club_name, resource_path):
    try:
        club = Club.query.filter_by(name=club_name).first()

        file_path = club_name + "/" + resource_path

        if club:
            # Get the binary data and the content type header
            binary_data = request.data
            content_type = request.headers.get('Content-Type')

            # Check if the file is empty
            if not binary_data:
                return create_error_response(f"{club_name} file is empty.", 400)

            # Get everything after "upload" as the file name
            file_path = os.path.join(UPLOAD_FOLDER, file_path)

            # Write the binary data to a file
            with open(file_path, 'wb') as f:
                f.write(binary_data)

            # Append the file_path to the club's files
            file_obj, response_code = get_files(file_path, binary_data, content_type)
            club.files.append(file_obj)
            db.session.commit()

            return "", response_code
        else:
            return create_error_response(f"{club_name} not in database.", 400)

    except Exception as e:
        return create_error_response(str(e), 500)


# Retrieve all the file contents for a specific club
@app.route('/api/clubs/<string:club_name>/files/<path:resource_path>', methods=['GET'])
def retrieve_file(club_name, resource_path):
    try:
        club = Club.query.filter_by(name=club_name).first()

        file_path = club_name + "/" + resource_path

        if club:
            file_path = os.path.join(UPLOAD_FOLDER, file_path)

            # Check if the file path exists
            if not os.path.exists(file_path):
                return create_error_response(f"{file_path} file does not exist.", 400)

            file_obj = File.query.filter_by(path=file_path).first()

            if not file_obj:
                return create_error_response(f"{file_path} file does not exist.", 400)

            content_type = file_obj.content_type

            with open(file_path, 'rb') as f:
                binary_data = f.read()

            # Get the content type for specifying how the binary data should be stored
            response = make_response(binary_data)
            response.headers.set('Content-Type', content_type)
            response.headers.set(
                'Content-Disposition', 'attachment', filename=file_path)
            return response
        else:
            return create_error_response(f"{club_name} not in database.", 400)

    except Exception as e:
        return create_error_response(str(e), 500)




## Comments ##
# Create a comment
@app.route('/api/clubs/<string:club_name>/comments', methods=['POST'])
@login_required
def create_comment(club_name):
    try:
        club = Club.query.filter_by(name=club_name).first()

        if club:
            # Get the information about the comment
            comment_info = request.get_json()

            # Check if all the required fields were sent
            if 'comment' not in comment_info:
                return create_error_response("Not all required fields were sent", 400)

            # Create a new comment object and add it to database
            comment = Comment(
                content=comment_info['comment'],
                user_id=current_user.id,
                club_id=club.id
            )
            db.session.add(comment)
            db.session.commit()

            return create_success_response(f"Added comment to {club_name}.")

        else:
            return create_error_response(f"{club_name} not in database.", 400)

    except Exception as e:
        return create_error_response(str(e), 500)


# Retrieve all comments for a club
@app.route('/api/clubs/<string:club_name>/comments', methods=['GET'])
def retrieve_comments(club_name):
    try:
        club = Club.query.filter_by(name=club_name).first()

        if club:
            # Find the comments
            comments = Comment.query.filter_by(club_id=club.id).all()
            return create_success_response([comment.to_json() for comment in comments])
        else:
            return create_error_response(f"{club_name} not in database.", 400)

    except Exception as e:
        return create_error_response(str(e), 500)


# Retrieve a specific comment
@app.route('/api/clubs/comments/<int:comment_id>', methods=['GET'])
@login_required
def retrieve_specific_comment(comment_id):
    try:
        # Find the specific comment
        comment = Comment.query.filter_by(id=comment_id).first()

        if comment:
            return create_success_response(comment.to_json())
        else:
            return create_error_response(f"{comment_id} not in database.", 400)

    except Exception as e:
        return create_error_response(str(e), 500)


# Update a comment
@app.route('/api/clubs/comments/<int:comment_id>', methods=['PUT'])
@login_required
def update_comment(comment_id):
    try:
        comment = Comment.query.filter_by(id=comment_id).first()

        if comment:
            comment_info = request.get_json()

            # Check if all the required fields were sent
            if 'content' not in comment_info:
                return create_error_response("Not all required fields were sent", 400)

            comment.content = comment_info['content']
            db.session.commit()

            return create_success_response(f"Updated comment {comment_id}.")

        else:
            return create_error_response(f"{comment_id} not in database.", 400)

    except Exception as e:
        return create_error_response(str(e), 500)


# Delete a specific comment
@app.route('/api/clubs/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    try:
        comment = Comment.query.filter_by(id=comment_id).first()

        if comment:
            db.session.delete(comment)
            db.session.commit()
            return create_success_response(f"Deleted comment {comment_id}.")

        else:
            return create_error_response(f"{comment_id} not in database.", 400)

    except Exception as e:
        return create_error_response(str(e), 500)


# Reply to a specific comment thread
@app.route('/api/clubs/comments/<int:comment_id>/reply', methods=['POST'])
@login_required
def reply_comment(comment_id):
    try:
        comment = Comment.query.filter_by(id=comment_id).first()

        if comment:
            comment_info = request.get_json()

            # Check if all the required fields were sent
            if 'comment' not in comment_info:
                return create_error_response("Not all required fields were sent", 400)

            # Create a new Comment object and relate it to the parent thread with parent_id
            reply = Comment(
                content=comment_info['comment'],
                user_id=current_user.id,
                club_id=comment.club_id,
                parent_id=comment.id
            )
            db.session.add(reply)
            db.session.commit()

            return create_success_response(f"Added reply to comment {comment_id}.")

        else:
            return create_error_response(f"{comment_id} not in database.", 400)

    except Exception as e:
        return create_error_response(str(e), 500)


if __name__ == '__main__':
    app.run()
