from __future__ import print_function
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from oauth2client import file, client, tools
import flask
from httplib2 import Http



API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

#   Afin de créer le fichier token.json, il faut exécuter
def connection_cal():
    #récupère les credentials de la session
    credentials = google.oauth2.credentials.Credentials(
         **flask.session['credentials'])
    #Construit le service qui permet d'envoyer des requêtes à l'ApI de google
    service = googleapiclient.discovery.build(
         API_SERVICE_NAME, API_VERSION, credentials=credentials)

    return service
