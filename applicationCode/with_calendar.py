from __future__ import print_function
import json
import datetime
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import flask
import argparse

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'

#   Afin de créer le fichier token.json, il faut exécuter
def connection_cal():
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)

        parser = argparse.ArgumentParser(parents=[tools.argparser])
        flags = parser.parse_args(args=[])

        creds = tools.run_flow(flow, store, flags)
    service = build('calendar', 'v3', http=creds.authorize(Http()))


    return service
