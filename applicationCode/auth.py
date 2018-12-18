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
#from . import with_doodle
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['DEBUG'] = '1'



#creation d'un blueprint nommé "auth", associé à l'URL /auth
bp = Blueprint('auth', __name__, url_prefix='/auth')


#Cette variable donne le nom du fichier qui contient les informations qui permet
#de se connecter avec OAuth 2.0
CLIENT_SECRETS_FILE = "client_secret.json"


#Le scope est un accès de OAuth 2.0 pour pouvoir écrire et lire dans le calendrier
#de l'utilisateur identifié
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

app = flask.Flask(__name__)
#Clé privé choisi par nous pour protéger notre application
app.secret_key = 'ljgjhkgl'






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

            if 'credentials' not in flask.session:
                return flask.redirect(url_for('auth.authorize'))

             # On prend les credentials liée à la sesson
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
  #Créé un flow pour gérer l'autorisation de l'authentification
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = flask.url_for('auth.oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
      #Permet de réactualiser les token pour avoir accès au calendrier sans
      #avoir à redemander l'autorisation à chaque fois
      access_type='offline',
      include_granted_scopes='true')

  # Stock l'état de la réponse d l'autorisation dans la session courante
    flask.session['state'] = state
    print(authorization_url)
    return flask.redirect(authorization_url)


@bp.route('/oauth2callback')
def oauth2callback():

  #Récupère l'état de l'autorisation lorsque l'on demande l'accès au calenrier de Google
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
  session.clear()
  return redirect(url_for('auth.login'))


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

    return redirect(url_for('auth.revoke'))

#certaines fonctionnalités requierent d'être connecté à un compte pour être utilisées
#on redirige donc vers la page d'identification login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
