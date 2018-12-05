#Ce fichier contient toutes les fonctions d'intéraction avec le calendrier
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
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'


def connection_cal():
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('credentials.json',scopes=['https://www.googleapis.com/auth/calendar'])
        flow.redirect_uri = flask.url_for('page_principale.ajouter', _external=True)


        authorization_url, state = flow.authorization_url(access_type='offline',include_granted_scopes='true')
        print(authorization_url)
        return flask.redirect(authorization_url)

        authorization_response = flask.request.url
        print('ici')
        print(authorization_response)
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials



    service = build('calendar', 'v3', http=creds.authorize(Http()))
    return service
