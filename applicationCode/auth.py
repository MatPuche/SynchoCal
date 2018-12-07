from __future__ import print_function
from flask import (Blueprint, flash, g, redirect, render_template, request, url_for)
import json
import datetime
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import flask
import argparse
import google.oauth2.credentials
import google_auth_oauthlib.flow

import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from applicationCode.db import get_db
from . import with_calendar
from . import with_doodle
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'



#creation d'un blueprint nommé "auth", associé à l'URL /auth
bp = Blueprint('auth', __name__, url_prefix='/auth')

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
            return redirect(url_for('auth.connection_cal'))

        flash(error)

    return render_template('login.html')

@bp.route('/cal')
def connection_cal():
    global state
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('credentials.json',scopes=['https://www.googleapis.com/auth/calendar'])
        flow.redirect_uri = flask.url_for('auth.token', _external=True)


        authorization_url, state = flow.authorization_url(access_type='offline',include_granted_scopes='true')
        print('la')
        print(state)
        return flask.redirect(authorization_url)

@bp.route('/token')
def token():
    print(state)
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('credentials.json',scopes=['https://www.googleapis.com/auth/calendar'],state=state)
    flow.redirect_uri = flask.url_for('page_principale.liste_sondages', _external=True)
    authorization_response = flask.request.url
    print('ici')
    print(authorization_response)
    codes= authorization_response.split("&")[1]
    codet=codes.split("=")[1]
    print(codet)
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials



    service = build('calendar', 'v3', http=credentials.authorize(Http()))
    return service
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
