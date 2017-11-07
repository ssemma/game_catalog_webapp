from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import User, Theme, Game, Base
from igdb_api_python.igdb import igdb
engine = create_engine('sqlite:///gamedatabasewithusers.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

igdb = igdb("5383da4777e121af7911808a1d437772")
# Add User1 into the database
user1 = User(username="SS XIA", email="shanshan122593@gmail.com",
             picture='static/img/black_user.GIF')
session.add(user1)
session.commit()
# Get 10 themes from the igdb api
result = igdb.themes({
    'ids': [18, 19, 20, 21, 22, 23, 27, 28, 31, 32]
})

counter = 1
# Iterate from one theme, get game_id from theme
for theme in result.body:
    for i in range(40):
        # Get properties from each game on that theme
        r = igdb.games(theme['games'][i])
        # Make sure the game we gather has all the properties we want
        if 'summary' not in r.body[0]:
            print "summary"
            continue
        if 'date' not in r.body[0]['release_dates'][0]:
            print "dates"
            continue
        else:
            # Add each game into database
            for game in r.body:
                game1 = Game(name=game['name'], cover=game['cover']['url'],
                             release_date=game['release_dates'][0]['human'],
                             release_date_number=game['release_dates'][0]['date'],
                             url=game['url'], user_id=1,
                             summary=game['summary'], theme_id=counter)
                session.add(game1)
                session.commit()
    # Add each theme into database
    theme1 = Theme(name=theme['name'], user_id=1)
    session.add(theme1)
    session.commit()
    counter += 1
# Print final statement
print "added games!"
