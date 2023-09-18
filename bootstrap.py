import os, json, requests
from bs4 import BeautifulSoup
from app import db, DB_FILE, DB_FILE_STORAGE, app
from models import *


# Scrape all the clubs from the website using BeautifulSoup
def scrape_clubs():
    url = "https://ocwp.pennlabs.org/"
    response = requests.get(url)

    if response.status_code == 200:
        with db.session() as session:
            soup = BeautifulSoup(response.content, 'html.parser')
            box_divs = soup.find_all('div', class_='box')

            # Loop through all the boxes
            for box_div in box_divs:
                name = box_div.find('strong').text
                tags = box_div.find('span').text
                description = box_div.find('em').text

                # Since all the scraping data only have 1 tag, I'm just going to split the tags by commas
                tags = get_all_tags(tags.split(','))

                # Create new club objects
                club = Club(
                    name=name,
                    description=description,
                    tags=tags
                )
                session.add(club)

            session.commit()
    else:
        print("Failed to retrieve the page. Status code:", response.status_code)


# Retrieves a list of tag objects from db based on a provided list of tag names.
def get_all_tags(names):
    tags = Tag.query.filter(Tag.name.in_(names)).all()
    newTagNames = set(names) - set([tag.name for tag in tags])
    tags.extend([Tag(name=name) for name in newTagNames])
    return tags


# Create a dummy user
def create_user():
    with db.session() as session:
        user = User(
            username='josh',
            first_name='josh',
            last_name='kuo',
            graduation_year=2026,
            password='1234'
        )
        session.add(user)
        session.commit()


# Load the data from the json file
def load_data():
    # Read the whole clubs.json file
    with open('clubs.json', 'r') as file:
        clubs = json.load(file)

    with db.session() as session:
        for club_info in clubs:
            # Put in information about Clubs
            club = Club(
                code=club_info['code'],
                name=club_info['name'],
                description=club_info['description']
            )

            session.add(club)

            # Put in information about Tags
            for tag_name in club_info['tags']:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)

                club.tags.append(tag)


        session.commit()


# def create_client():
#     default_client = OAuth2Client(
#         client_id='12345',
#         client_secret='pennlabs',
#         client_name='pennlabsclient',
#         is_confidential=True
#     )

#     # Add the client to the database
#     db.session.add(default_client)
#     db.session.commit()


# No need to modify the below code.
if __name__ == '__main__':
    # Delete any existing database before bootstrapping a new one.
    if os.path.exists(DB_FILE_STORAGE):
        print("Deleting existing database file.")
        os.remove(DB_FILE_STORAGE)

    with app.app_context():
        db.create_all()
        print("Created new database.")

        create_user()
        scrape_clubs()
        load_data()
        # create_client()  # For OAuth2