from __future__ import print_function
import datetime
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

import requests as rq
import json
import time



# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'


store = file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('calendar', 'v3', http=creds.authorize(Http()))

#key ="v4ickxzkuqvnguwp"
key="zmu5hb6ymg9mtkq6"
url="https://doodle.com/api/v2.0/polls/"


#1er janvier 1970 en date python
a = datetime.datetime(1970, 1, 1)

#on stocke le json dans le dictionnaire l
r = rq.get(url+key)
l = json.loads(r.content)
optionsHash=l["optionsHash"]

#le sondage peut être sur des creneaux horraires ou sur des jours entiers.
#On initialise à False le booléen qui indique si le sondage est sur des jours entiers ou non.
jour_entier = False

#la liste des options (créneaux) de notre doodle (vide pour l'instant)
liste_options = []

#la liste préférences est la liste de 0 et/ou 1 qu'il faut envoyer au Doodle pour le remplir
preferences=[]

#représente les places des créneaux finaux dans la liste des préférences
place=[]

#compteur représentant le nombre de créneaux
re=0

#D'abord, on récupère la liste des dates des débuts et des fins (alternées 2 à 2) des évènements du Doodle.

#On distingue le cas ou le Doodle est fermé ou non

try:
    #On regarde si le sondage est fermé ou pas
    t=l['closed']

    #Si le sondage est fermé on récupère tous les crénaux qui sont finaux
    for temps in l["options"]:

        try :
            temps["end"]
            jour_entier = False
        except :
            jour_entier = True

        try:
            #on vérifie si l'évenement est final
            bool=temps['final']

            #Date et heure de commencement de l'évènement
            secondesEnPlusDebut = int(str(temps["start"])[0:len(str(temps["start"]))])

            #On ajoute l'heure de début à la liste des options
            optionDebut = a + datetime.timedelta(milliseconds = int(secondesEnPlusDebut)+3600000)
            liste_options.append(optionDebut)

            #Au début, on met par défaut que la personne est libre à tous les crénaux finaux
            preferences.append(1)

            #Vu qu'on récupère seulement les crénaux finaux on conserve leur place dans la liste des preferences
            place.append(re)

            #si le sondage n'est pas sur le jour entier, on récupère l'horraire de fin
            if not jour_entier :

                #Date et heure de fin de l'évènement
                secondesEnPlusFin = int(str(temps["end"])[0:len(str(temps["end"]))])

                #On l'ajoute à la liste des options
                optionFin = a + datetime.timedelta(milliseconds = int(secondesEnPlusFin)+3600000)
                liste_options.append(optionFin)

        except:
            #Si la date n'est pas finale on ajoute 0 aux préférences, et nous n'avons donc pas à nous soucier des dates non-finales
            preferences.append(0)

        re+=1


except:
    #Si le sondage est toujours ouvert on récupère tous les créneaux du doodle
    for temps in l["options"]:

        try :
            temps["end"]
            jour_entier = False
        except :
            jour_entier = True

        #Date et heure de commencement de l'évènement
        secondesEnPlusDebut = int(str(temps["start"])[0:len(str(temps["start"]))])

        #On ajoute l'heure de début à la liste des options
        optionDebut = a + datetime.timedelta(milliseconds = int(secondesEnPlusDebut)+3600000)
        liste_options.append(optionDebut)

        #Par défault on met dans la liste des préférences qu'on est libre à aucun créneaux
        preferences.append(0)

        #On ajoute la place de chaque créneau dans la liste des préference
        place.append(re)

        #si le sondage n'est pas sur le jour entier, on récupère l'horraire de fin
        if not jour_entier :

            #Date et heure de fin de l'évènement
            secondesEnPlusFin = int(str(temps["end"])[0:len(str(temps["end"]))])

            #On ajoute les deux à la liste des options
            optionFin = a + datetime.timedelta(milliseconds = int(secondesEnPlusFin)+3600000)
            liste_options.append(optionFin)

        re+=1


#On stocke les infos importantes du doodle
titre = l["title"]
try :
    lieu = l["location"]["name"]
except:
    lieu = "Pas de lieu spécifié"
try:
    description = l["description"]
except:
    description = "Pas de description spécifiée"

print(liste_options)

eventdate=[]

i=1

for option in liste_options :
     #pour un sondage sur un jour entier, on a la listes de jours du sondage dans liste_options
     jour = str(option)[0:10]
     debut=str(option)[0:10]+'T00:00:00+01:00'
     fin=str(option)[0:10]+'T23:59:59+01:00'
     events_result = service.events().list(calendarId='primary', timeMin=debut, timeMax=fin, singleEvents=True).execute()
     events = events_result.get('items', [])
     print(events)
     #Si il n'y a pas d'évènement dans le calendrier cette journée là, on remplit le calendrier en réservant la journée et on modifie la liste
     #preference en mettant 1 à la bonne place dans la liste
     if not events:
         eventdate.append(jour)
         preferences[place[i-1]]=1
     i+=1

print("eventdate= ")
print(eventdate)

res=[]
if jour_entier :

    for k in range(len(eventdate)):

        event2 = {
                      'summary': titre,
                      'location': lieu,
                      'description': description,
                      'start': {
                        'date': eventdate[k],
                        'timeZone': 'Europe/London',
                      },
                      'end': {
                        'date': eventdate[k],
                        'timeZone': 'Europe/London',
                      },
                      'recurrence': [
                        'RRULE:FREQ=DAILY;COUNT=1'
                      ],
                      'reminders': {
                        'useDefault': False,
                        'overrides': [
                          {'method': 'email', 'minutes': 24 * 60},
                          {'method': 'popup', 'minutes': 10},
                        ],
                      },
                    }

        res.append(event2)

eventfinal=[]

#On parcourt les evenements qu'on a converti après avoir récupéré les dates des créneaux dans le doodle
for k in res:

    #On reserve le créneaux prévu dans le calendrier
    service.events().insert(calendarId='primary', body=k).execute()
    j=0
    #On récupère les événement qu'on vient juste de résérver car lorsqu'on insère un evenenement il y a un id qui est créé par le calendrier et
    #on en a besoin pour effacer les evenement quand nécessaire
    if jour_entier :
        event=service.events().list(calendarId='primary', timeMin=k['start']['date']+'T00:00:00+01:00', timeMax=k['end']['date']+'T23:59:59+01:00', singleEvents=True).execute()['items']
    else :
        event=service.events().list(calendarId='primary', timeMin=k['start']['dateTime'], timeMax=k['end']['dateTime']).execute()['items']

        #La commande précedente renvoie un liste des évenement qui ont un moment de commun avec l'intervalle donné, on parcours donc la liste jusqu'a trouve
        #l'événement qu'on vient d'insérer en comparant les date de début et de fin
        while event[j]['end']['dateTime']!=k['end']['dateTime'] and event[j]['start']['dateTime']!=k['start']['dateTime']:
            j=j+1

        #On l'ajoute à la liste des evénement, cette liste est comme eventdate sauf qu'on a les id en plus
    eventfinal.append(event[j])
for event in eventfinal :
    print(event)
