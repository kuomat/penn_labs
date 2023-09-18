# Penn Labs Backend Challenge

## Documentation
This is a mini-project I created with flask and SQLAlchemy. In this project, I imported data from clubs.json file, stored them into a database named "clubreview.db", and created several routes to perform tasks such as listing out all the clubs in json format and the standard GET, POST, PUT, and DELETE methods for the clubs database. In addition, I also did the first, third, and fifth bonus challenges.

## File Structure
- `app.py`: Main application file with configuration and URL routes.
- `models.py`: Definitions for SQLAlchemy database models.
- `bootstrap.py`: Code for creating and populating the local database.
- `folders`: A directory for storing uploaded files (bonus challenge).

## Installation
1. Install `pipenv`:
   - `pip install --user --upgrade pipenv`

2. Install required packages:
   - `pipenv install`
   - `pipenv install requests`
   - `pipenv install flask_login`
   - `pipenv install bs4`


## Development Process

### Routes

#### Get All Clubs
For this route, since I already have a Club model, I can just loop through all the elements inside that database and return it. One thing to note is that when I return the elements as a json object, I don't include all the fields. Although most of the fields are pretty important when it comes to letting the users know about all the clubs, I chose to not include the "ID" of the club because I feel like it won't be as helpful for people looking to find clubs to join.
- **URL**: `/api/clubs` (GET)
- **Description**: Retrieve a list of all clubs in JSON format.
- **Example**: `/api/clubs`

#### Get User Profile
For this route, I chose to include the username (has to be unique) as part of the parameter and have it set as a GET request because it makes it easier for users to find other people if they can just put their target's name as part of the url and get their information. However, one thing to note is that just like the clubs, I chose to not include every field. Some of the fields I didn't include are the user's password and their graduation year.
- **URL**: `/api/users/<string:username>` (GET)
- **Description**: Retrieve user information by username.
- **Example**: `/api/users/josh`

#### Search Clubs
The decision choices for this route is pretty much the same as the user profile but this time, instead of putting in the username, I want them to input the club's name (which also has to be unique).
- **URL**: `/api/clubs/<string:search_name>` (GET)
- **Description**: Search for clubs by name.
- **Example**: `/api/clubs/Penn Lorem Ipsum Club`

#### Add a New Club
For this route, I didn't want to include the information all in the uri because sometimes when a person creates a new club, there are other information that they might want to put in. Thus, this is a POST request in which people can enter information about a new club that they want to create, provided that the name of the club is unique. However, note that for someone to access this endpoint, they need to first login. This is because I don't want people to spam new clubs without logging in.
- **URL**: `/api/clubs/new` (POST)
- **Description**: Add a new club (requires authentication).
- **Example**: `/api/clubs/new`
- **Request Body**: `{"name": "Penn Labs", "code": "PL", "description": "Penn Labs is a club."}`

#### Favorite a Club
For this, I added a new field in the Club model in which it keeps track of the number of favorites a club has (this field is also shown in the /api/clubs endpoint). Once again, note that you have to login before being able to access this endpoint.
- **URL**: `/api/clubs/fav/<string:club_name>` (POST)
- **Description**: Increase the favorite count for a club (requires authentication).
- **Example**: `/api/clubs/fav/Penn Lorem Ipsum Club`

#### Modify a Club
The user first has to select the name of the club that they want to modify. The three things the users can modify are the description, tags, and code of the club. This is because I don't want them to modify fields like the name of the club or the number of favorites they have.
- **URL**: `/api/clubs/mod/<string:club_name>` (POST)
- **Description**: Modify club details (code, description, tags) (requires authentication).
- **Example**: `/api/clubs/mod/Penn Lorem Ipsum Club`
- **Request Body**: `{"code": "new_code", "description": "new description."}`

#### Show Number of Clubs for Each Tag
This is an endpoint that run a SQL query and returns the number of clubs for each tag. I chose to do a SQL query because it is faster than just looping through all the clubs and create a hashmap to that increments a specific tag.
- **URL**: `/api/tags/count` (GET)
- **Description**: Retrieve the number of clubs for each tag.
- **Example**: `/api/tags/count`

#### Get Club Names by Tag
Because of the last endpoint, I thought that it will be interesting if I have an endpoint that gets all the NAMES of the clubs for each tag instead of just returning the number of clubs for a specific tag.
- **URL**: `/api/tags/<string:tag_name>/names` (GET)
- **Description**: Retrieve club names for a specific tag.
- **Example**: `/api/tags/academic/names`

#### Delete a Club
For this route, I chose to do a DELETE method where the user can delete a club from the database. I chose this because I feel like DELETE is a very useful method and in the real world, people sometimes just want to abandon clubs.
- **URL**: `/api/clubs/<string:club_name>` (DELETE)
- **Description**: Delete a club from the database (requires authentication).
- **Example**: `/api/clubs/Penn Lorem Ipsum Club`

### Authentication
Originally, I wanted to use OAuth2 because it generates tokens so that even if the token somehow gets leaked, by the time it gets leaked, the token would have probably expired already. However, OAuth2 requires a domain name, but since I'm not actually deploying this backend, this is impossible. Thus, I decided to use the normal FLask login. To strengthen the security, I made sure that if someone tries a password too many times (5) but is wrong, it will automatically lock the account for 10 minutes. Thus, this will make brute force attacks impossible. Next, to not reveal if a username actually exists, if the user inputs either their username or password wrongly, it will tell them something is wrong instead of specifying if it is the username that doesn't exist or that the password is incorrect.
- **Signup**: `/signup` (POST)
  - **Description**: Register a new user.
  - **Example**: `/signup`
  - **Request Body**: `{"username": "josh", "password": "1234"}`

- **Login**: `/login` (POST)
  - **Description**: Log in to an account.
  - **Example**: `/login`
  - **Request Body**: `{"username": "josh", "password": "1234"}`

- **Logout**: `/logout` (POST)
  - **Description**: Log out of the current session.
  - **Example**: `/logout`

### Bonus Challenges

#### Scraping
- **Description**: Scraped data from a specified website and stored it in the database.

#### File Management
For this endpoint, I created a new database model called File in which it has fields such as the path and the content. In addition, I connected this database model to Clubs in which each club will have its own unique files. This method gets the binary data from the request and writes it in a binary file and creates a File object to store in the database. The user can put any type of file they want. Images and pdfs seem to work.
- **Upload File**: `/api/clubs/<string:club_name>/files/<path:resource_path>` (PUT)
  - **Description**: Upload files to a club.
  - **Example**: `/api/clubs/Penn%20Lorem%20Ipsum%20Club/files/hello3.png`

The above endpoint stores the file data in the database. This endpoint on the other hand, retrieves the specific data from the database and downloads the file when the user runs the endpoint.
- **Download File**: `/api/clubs/<string:club_name>/files/<path:resource_path>` (GET)
  - **Description**: Retrieve files from a club.
  - **Example**: `/api/clubs/Penn%20Lorem%20Ipsum%20Club/files/hello3.png`

#### Club Comments
There is a series of other endpoints I implemented for this feature. But the main idea is that I created a new database model called Comments that keeps track of the commenter's id, the context of the comment, the club's id, and the parent comment id. Storing the parent's comment ID is so that there can be a comment chain for people to respond to others. Note that the user needs to be authenticated before using this feature.
- **Create Comment**: `/api/clubs/<string:club_name>/comments` (POST)
  - **Description**: Create a new comment for a club (requires authentication).
  - **Example**: `/api/clubs/Penn%20Lorem%20Ipsum%20Club/comments`
  - **Request Body**: `{"comment": "I love this club."}`

- **Retrieve Comments**: `/api/clubs/<string:club_name>/comments` (GET)
  - **Description**: Retrieve all comments for a club.
  - **Example**: `/api/clubs/Penn%20Lorem%20Ipsum%20Club/comments`

- **Retrieve Specific Comment**: `/api/clubs/comments/<int:comment_id>` (GET)
  - **Description**: Retrieve a specific comment by ID.
  - **Example**: `/api/clubs/comments/1`

- **Update Comment**: `/api/clubs/comments/<int:comment_id>` (POST)
  - **Description**: Update a comment (requires authentication).
  - **Example**: `/api/clubs/comments/1`
  - **Request Body**: `{"comment": "updated comment."}`

- **Delete Comment**: `/api/clubs/comments/<int:comment_id>` (DELETE)
  - **Description**: Delete a specific comment (requires authentication).
  - **Example**: `/api/clubs/comments/1`

- **Reply to Comment**: `/api/clubs/comments/<int:comment_id>/reply` (POST)
  - **Description**: Reply to a comment thread (requires authentication).
  - **Example**: `/api/clubs/comments/1/reply`
  - **Request Body**: `{"comment": "I like your post."}`
