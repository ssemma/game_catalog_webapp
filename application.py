from database_setup import User, Theme, Game, Base
from flask import Flask, jsonify, request, url_for, abort
from flask import g, render_template, redirect, flash
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, asc, desc, func
from flask_httpauth import HTTPBasicAuth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response
import requests
import json
import random
import string
from flask import session as login_session
import datetime


# Connect to Database and create database session
engine = create_engine('sqlite:///gamedatabasewithusers.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

CLIENT_ID = json.loads(
                       open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "GAME APPLICATION"


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(
                                 json.dumps('Invalid state parameter.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
                                 json.dumps('Failed to upgrade the authorization code.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['sub'] != gplus_id:
        response = make_response(
                                 json.dumps("Token's user ID doesn't match given user ID."),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is valid for this app.
    if result['aud'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
                                 json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = credentials.id_token['sub']

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: " '
    output += ' "150px;-webkit-border-radius:  '
    output += ' 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s"
          % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(username=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        return "You have been logged out."
    else:
        response = make_response(
                                 json.dumps('Failed to revoke token for given user.'),
                                 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON one specific theme information
@app.route('/theme/<int:theme_id>/games/JSON')
def themeGameJSON(theme_id):
    theme = session.query(Theme).filter_by(id=theme_id).one()
    games = session.query(Game).filter_by(theme_id=theme_id).all()
    return jsonify(Games=[i.serialize for i in games])


# JSON all games in one theme information
@app.route('/theme/<int:theme_id>/game/<int:game_id>/JSON')
def gameJSON(theme_id, game_id):
    game = session.query(Game).filter_by(id=game_id).one()
    return jsonify(Game=game.serialize)


# JSON all themes information
@app.route('/theme/JSON')
def themesJSON():
    themes = session.query(Theme).all()
    return jsonify(themes=[r.serialize for r in themes])


# Show all themes with recent games
@app.route('/')
@app.route('/theme/')
def showThemes():
    lists = []
    themes = session.query(Theme).order_by(asc(Theme.name))
    latestgames = session.query(Game).order_by(desc(Game.release_date_number)).limit(10)
    # Get theme id, name and game id, name in dictionary at a list
    for latestgame in latestgames:
        gametheme = session.query(Theme).filter_by(id=latestgame.theme_id).one()
        lists.append({"name": latestgame.name + " (" + gametheme.name + ")",
                      "theme_id": latestgame.theme_id,
                      "game_id": latestgame.id})
    # render diff template for login user and non-login one
    if 'username' not in login_session:
        return render_template('publicthemes.html', themes=themes, lists=lists)
    else:
        return render_template('themes.html', themes=themes, lists=lists)


# Create a new theme
@app.route('/theme/new/', methods=['GET', 'POST'])
def newTheme():
    # Make sure user is logged in
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newTheme = Theme(name=request.form['name'],
                         user_id=login_session['user_id'])
        session.add(newTheme)
        flash('New Theme %s Successfully Created' % newTheme.name)
        session.commit()
        return redirect(url_for('showThemes'))
    else:
        return render_template('newTheme.html')


# Edit a theme
@app.route('/theme/<int:theme_id>/edit/', methods=['GET', 'POST'])
def editTheme(theme_id):
    editedTheme = session.query(Theme).filter_by(id=theme_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    # Make sure the user is the one who created this theme
    if editedTheme.user_id != login_session['user_id']:
        output = ""
        output += "<script>function myFunction() "
        output += "{alert('You are not authorized to edit "
        output += " this theme. Please create your  "
        output += "own theme in order to edit.');} "
        output += " </script><body onload='myFunction()'> "
        return output
    if request.method == 'POST':
        if request.form['name']:
            editedTheme.name = request.form['name']
            flash('Theme Successfully Edited %s' % editedTheme.name)
            return redirect(url_for('showThemes'))
    else:
        return render_template('editTheme.html', theme=editedTheme)


# Delete a theme
@app.route('/theme/<int:theme_id>/delete/', methods=['GET', 'POST'])
def deleteTheme(theme_id):
    themeToDelete = session.query(Theme).filter_by(id=theme_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    # Make sure the user is the one who created this theme
    if themeToDelete.user_id != login_session['user_id']:
        output = ""
        output += " <script>function myFunction() "
        output += " {alert('You are not authorized to delete "
        output += " this theme. Please create your "
        output += " own theme in order to delete.');} "
        output += " </script><body onload='myFunction()'> "
        return output
    if request.method == 'POST':
        session.delete(themeToDelete)
        flash('%s Successfully Deleted' % themeToDelete.name)
        session.commit()
        return redirect(url_for('showThemes', theme_id=theme_id))
    return render_template('deleteTheme.html', theme=themeToDelete)


# Show games of a theme
@app.route('/theme/<int:theme_id>/')
@app.route('/theme/<int:theme_id>/games/')
def showGames(theme_id):
    all_themes = session.query(Theme).order_by(asc(Theme.name))
    theme = session.query(Theme).filter_by(id=theme_id).one()
    games = session.query(Game).filter_by(theme_id=theme_id).all()
    # Count the number of games in that theme
    number = 0
    for game in games:
        number += 1
    # If user is not the creator of the theme,
    # Render templates without the modify power
    if 'username' not in login_session or theme.user_id != login_session['user_id']:
        return render_template('publicgames.html',
                               games=games, theme=theme,
                               number=number, allthemes=all_themes)
    else:
        return render_template('onethemegames.html',
                               games=games, theme=theme,
                               number=number, allthemes=all_themes)


# Show a game
@app.route('/theme/<int:theme_id>/game/<int:game_id>/')
def showOneGame(theme_id, game_id):
    game = session.query(Game).filter_by(id=game_id).one()
    theme = session.query(Theme).filter_by(id=theme_id).one()
    if 'username' not in login_session or theme.user_id != login_session['user_id']:
        return render_template('publiconegame.html', game=game)
    else:
        return render_template('game.html', game=game)


# Create a new game
@app.route('/theme/<int:theme_id>/game/new/', methods=['GET', 'POST'])
def newGame(theme_id):
    if 'username' not in login_session:
        return redirect('/login')
    theme = session.query(Theme).filter_by(id=theme_id).one()
    # Make sure the user is the owner of the theme
    if login_session['user_id'] != theme.user_id:
        output = ""
        output += " <script>function myFunction() "
        output += " {alert('You are not authorized to add "
        output += " game to this theme. Please create your  "
        output += " own theme in order to add game.');} "
        output += " </script><body onload='myFunction()'> "
        return output
    if request.method == 'POST':
        # Get the latest release date number and increment it by 1
        latestgame = session.query(Game).order_by(desc(Game.release_date_number)).limit(1)
        number = int(latestgame[0].release_date_number) + 1
        # Get the current date
        release_date = datetime.datetime.now().date()
        # Make sure the fields are not empty
        if request.form['name'] == '' or request.form['description'] == '':
            return render_template('warning.html')
        if request.form['img_src'] == '' or request.form['url'] == '':
            return render_template('warning.html')
        newGame = Game(name=request.form['name'],
                       summary=request.form['description'],
                       cover=request.form['img_src'],
                       theme_id=theme.id, release_date_number=number,
                       url=request.form['url'],
                       user_id=login_session['user_id'],
                       release_date=release_date)
        session.add(newGame)
        session.commit()
        flash('New Game %s Successfully Created' % (newGame.name))
        return redirect(url_for('showGames',  theme_id=theme.id))
    else:
        return render_template('newgame.html', theme=theme)


# Edit a game
@app.route('/theme/<int:theme_id>/game/<int:game_id>/edit',
           methods=['GET', 'POST'])
def editGame(theme_id, game_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedGame = session.query(Game).filter_by(id=game_id).one()
    otheme = session.query(Theme).filter_by(id=theme_id).one()
    # Make sure the user is the owner of the theme
    if login_session['user_id'] != otheme.user_id:
        output = ""
        output += "<script>function myFunction() "
        output += " {alert('You are not authorized to edit "
        output += " this game to this theme. Please create your "
        output += " own theme in order to edit game.');} "
        output += " </script><body onload='myFunction()'> "
        return output
    if request.method == 'POST':
        if request.form['name']:
            editedGame.name = request.form['name']
        if request.form['description']:
            editedGame.summary = request.form['description']
        if request.form['img_src']:
            editedGame.cover = request.form['img_src']
        if request.form['url']:
            editedGame.url = request.form['url']
        session.add(editedGame)
        session.commit()
        flash('The Game Successfully Edited')
        return redirect(url_for('showGames', theme_id=theme_id))
    else:
        return render_template('editgame.html', game=editedGame)


# Delete a game
@app.route('/theme/<int:theme_id>/game/<int:game_id>/delete',
           methods=['GET', 'POST'])
def deleteGame(theme_id, game_id):
    if 'username' not in login_session:
        return redirect('/login')
    theme = session.query(Theme).filter_by(id=theme_id).one()
    gameToDelete = session.query(Game).filter_by(id=game_id).one()
    if login_session['user_id'] != theme.user_id:
        output = ""
        output += "<script>function myFunction() "
        output += " {alert('You are not authorized to delete "
        output += " this game to this theme. Please create your "
        output += " own theme in order to delete game.');} "
        output += " </script><body onload='myFunction()'> "
        return output
    if request.method == 'POST':
        session.delete(gameToDelete)
        session.commit()
        flash('The Game Successfully Deleted')
        return redirect(url_for('showGames', theme_id=theme_id))

    else:
        return render_template('deletegame.html', game=gameToDelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showThemes'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showThemes'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
