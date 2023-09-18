# Penn Labs Backend Challenge

## Documentation
This is a mini-project I created with flask and SQLAlchemy. In this project, I imported data from clubs.json file, stored them into a database named "clubreview.db", and created several routes to perform tasks such as listing out all the clubs in json format and the standard GET, POST, PUT, and DELETE methods for the clubs database. In addition, I also did the first, third, and fifth bonus challenges.

## File Structure

- `app.py`: Main file. Has configuration and setup at the top along with URL routes at the bottom.
- `models.py`: Model definitions for SQLAlchemy database models.
- `bootstrap.py`: Code for creating and populating your local database.
- folders: A folder for storing all the uploaded files for the third bonus challenge.

## Installation
1. Install `pipenv`
   - `pip install --user --upgrade pipenv`
2. Install packages using `pipenv install`.
   - `pipenv install requests`
   - `pipenv install flask_login`
   - `pipenv install bs4`


## Development Process
Step 1: I started by creating a database model Club in which it contains fields such as id (primary key), name of the club, the code, the descriptions, and the tags. All of the fields are optional excpet the name of the club (which has to be unique because I don't want to have two clubs with the exact same name). I made these fields because they are the necessary components from the clubs.json file. Next, because I want to standardize my database in the sense that if I change the name of a tag, I want all the clubs' tags to also change. Thus, I decided to break the Club model into two parts: one is still the Club model with the same components, but I created a model for Tags and establish a many to many relationship between them. I did a many to many relationship because each club can have multiple tags and each tag can be a part of multiple models.

Step 2: Next, I created a User model with fields such as username (required), password (required), first name (optional), last name (optional). This is so that later on when I create login/signup endpoints, I can do them easily.

### Routes:
Get all clubs: (/api/clubs, GET) For this route, since I already have a Club model, I can just loop through all the elements inside that database and return it. One thing to note is that when I return the elements as a json object, I don't include all the fields. Although most of the fields are pretty important when it comes to letting the users know about all the clubs, I chose to not include the "ID" of the club because I feel like it won't be as helpful for people looking to find clubs to join.

Get user profile: (/api/users/<string:username>, GET) For this route, I chose to include the username (has to be unique) as part of the parameter and have it set as a GET request because it makes it easier for users to find other people if they can just put their target's name as part of the url and get their information. However, one thing to note is that just like the clubs, I chose to not include every field. Some of the fields I didn't include are the user's password and their graduation year.

Search clubs: (/api/clubs/<string:search_name>, GET) The decision choices for this route is pretty much the same as the user profile but this time, instead of putting in the username, I want them to input the club's name (which also has to be unique).

Add a new club: (/api/clubs/new, POST) For this route, I didn't want to include the information all in the uri because sometimes when a person creates a new club, there are other information that they might want to put in. Thus, this is a POST request in which people can enter information about a new club that they want to create, provided that the name of the club is unique. However, note that for someone to access this endpoint, they need to first login. This is because I don't want people to spam new clubs without logging in.

Favorite a club: (/api/clubs/fav/<string:club_name>, POST) For this, I added a new field in the Club model in which it keeps track of the number of favorites a club has (this field is also shown in the /api/clubs endpoint). Once again, note that you have to login before being able to access this endpoint.

Modify a club: (/api/clubs/mod/<string:club_name>, POST) The user first has to select the name of the club that they want to modify. The three things the users can modify are the description, tags, and code of the club. This is because I don't want them to modify fields like the name of the club or the number of favorites they have.

Show number of clubs for each tag: (/api/tags/count, GET) This is an endpoint that run a SQL query and returns the number of clubs for each tag. I chose to do a SQL query because it is faster than just looping through all the clubs and create a hashmap to that increments a specific tag.

A route of your choice 1: (/api/tags/<string:tag_name>/names, GET) Because of the last endpoint, I thought that it will be interesting if I have an endpoint that gets all the NAMES of the clubs for each tag instead of just returning the number of clubs for a specific tag.

A route of your choice 2: (/api/clubs/<string:club_name>, DELETE) For this route, I chose to do a DELETE method where the user can delete a club from the database. I chose this because I feel like DELETE is a very useful method and in the real world, people sometimes just want to abandon clubs.


### Authentication:
Originally, I wanted to use OAuth2 because it generates tokens so that even if the token somehow gets leaked, by the time it gets leaked, the token would have probably expired already. However, OAuth2 requires a domain name, but since I'm not actually deploying this backend, this is impossible. Thus, I decided to use the normal FLask login. To strengthen the security, I made sure that if someone tries a password too many times (5) but is wrong, it will automatically lock the account for 10 minutes. Thus, this will make brute force attacks impossible. Next, to not reveal if a username actually exists, if the user inputs either their username or password wrongly, it will tell them something is wrong instead of specifying if it is the username that doesn't exist or that the password is incorrect.


### Bonus Challenges
I did 3 challenges in total and they are Scraping, File Management, and Club Comments

Scraping: I used BeautifulSoup to scrape data from the given website and put all the entries into the database.

File Management: (/api/clubs/<string:club_name>/files/<path:resource_path>, PUT) For this endpoint, I created a new database model called File in which it has fields such as the path and the content. In addition, I connected this database model to Clubs in which each club will have its own unique files. This method gets the binary data from the request and writes it in a binary file and creates a File object to store in the database.

File Management 2: (/api/clubs/<string:club_name>/files/<path:resource_path>, GET) The above endpoint stores the file data in the database. This endpoint on the other hand, retrieves the specific data from the database and downloads the file when the user runs the endpoint.

Club Comments: There is a series of other endpoints I implemented for this feature. But the main idea is that I created a new database model called Comments that keeps track of the commenter's id, the context of the comment, the club's id, and the parent comment id. Storing the parent's comment ID is so that there can be a comment chain for people to respond to others. Note that the user needs to be authenticated before using this feature.