import flask
import requests

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

import os
import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from applicationCode.db import get_db
from . import with_doodle
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['DEBUG'] = '1'



#creation d'un blueprint nommé "auth", associé à l'URL /auth
bp = Blueprint('auth', __name__, url_prefix='/auth')

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

app = flask.Flask(__name__)
# Note: A secret key is included in the sample so that it works.
# If you use this code in your application, replace this with a truly secret
# key. See http://flask.pocoo.org/docs/0.12/quickstart/#sessions.
app.secret_key = 'ljgjhkgl'

global service

#formulaire d'inscription à remplir pour créer son compte sur l'application
@bp.route('/inscription', methods=('GET', 'POST'))
def inscription():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nom_doodle = request.form['nom_doodle']
        db = get_db()
        error=None

        if not username:
            error = 'Veuillez entrer un nom d\'utilisateur.'
        elif not password:
            error = 'Veuillez entrer un mot de passe pour votre compte.'
        elif not nom_doodle:
            error = 'Veuillez entrer un nom pour le remplissage des Doodle.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'L\'utilisateur {} existe déjà.'.format(username)

        if error is None:
            db.execute(
                'INSERT INTO user (username, password, nom_doodle) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), nom_doodle)
            )
            db.commit()


            return redirect(url_for('auth.login'))

        flash(error)
    return render_template('inscription.html')

#page pour se connecter à l'application
@bp.route('/login', methods=('GET', 'POST'))
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Nom d\'utilisateur incorrect.'
        elif not check_password_hash(user['password'], password):
            error = 'Mot de passe incorrect.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            #return redirect(url_for('page_principale.liste_sondages'))

            if 'credentials' not in flask.session:
                return flask.redirect(url_for('auth.authorize'))

             # Load credentials from the session.
            credentials = google.oauth2.credentials.Credentials(
                 **flask.session['credentials'])

            service = googleapiclient.discovery.build(
                 API_SERVICE_NAME, API_VERSION, credentials=credentials)

            flask.session['credentials'] = credentials_to_dict(credentials)

            return redirect(url_for('page_principale.liste_sondages'))

        flash(error)

    return render_template('login.html')



@bp.route('/authorize')
def authorize():
  # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = flask.url_for('auth.oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

  # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state
    print(authorization_url)
    return flask.redirect(authorization_url)


@bp.route('/oauth2callback')
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = flask.session['state']

  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
  flow.redirect_uri = flask.url_for('auth.oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = flask.request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  credentials = flow.credentials
  flask.session['credentials'] = credentials_to_dict(credentials)

  return flask.redirect(flask.url_for('page_principale.liste_sondages'))


@bp.route('/revoke')
def revoke():
  if 'credentials' not in flask.session:
    return ('You need to <a href="/authorize">authorize</a> before ' +
            'testing the code to revoke credentials.')

  credentials = google.oauth2.credentials.Credentials(
    **flask.session['credentials'])

  revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})

  status_code = getattr(revoke, 'status_code')
  if status_code == 200:
    return('Credentials successfully revoked.' + print_index_table())
  else:
    return('An error occurred.' + print_index_table())


@bp.route('/clear')
def clear_credentials():
  if 'credentials' in flask.session:
    del flask.session['credentials']
  return ('Credentials have been cleared.<br><br>' +
          print_index_table())


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}



#identifie si un utilisateur est connecté dans la session.
#permet d'ouvrir les pages accessibles seulement par des utilisateurs
#et d'acceder aux données de leur compte
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

#page pour se deconnecter
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

#certaines fonctionnalités requierent d'être connecté à un compte pour être utilisées
#on redirige donc vers la page d'identification login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
