#Ce fichier contient toutes les fonctions d'intéraction avec le sondage Doodle

from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import requests as rq
import json
import datetime
import time
from . import with_calendar


url="https://doodle.com/api/v2.0/polls/"

#On introduit service
service=with_calendar.connection_cal()
#Fonction qui permet de convertir les dates de début et de fin d'un créneau doodle sous la forme d'un json. Ce json est sous la forme qu'il faut envoyer à google
#calendar pour ajouter un evenemet. Prend en argument le titre le lieu et la description du doodle ainsi que la liste des dates des créneaux.
def conversion(eventdate,titre,lieu,description,allday):
    res=[]
    for ki in range( len(eventdate)//2):
        if (allday==False):
            event2 = {
                          'summary': titre,
                          'location': lieu,
                          'description': description,
                          'start': {
                            'dateTime': eventdate[2*ki],
                            'timeZone': 'Europe/London',
                          },
                          'end': {
                            'dateTime': eventdate[2*ki+1],
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
        else:

            event2 = {
                          'summary': titre,
                          'location': lieu,
                          'description': description,
                          'start': {
                            'dateTime': eventdate[2*ki].split('T')[0]+'T00:00:01+01:00',
                            'timeZone': 'Europe/London',
                          },
                          'end': {
                            'dateTime': eventdate[2*ki+1].split('T')[0]+'T23:59:59+01:00',
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
        print(eventdate[2*ki+1].split('T')[0])
        res.append(event2)
    return res


def remplissage_doodle(preferences,optionsHash,key, nom_utilisateur, participantKey):

    #Json à envoyer pour remplir le doodle
    envoi = {"name" : nom_utilisateur, "preferences" :
    preferences, "participantKey" : participantKey,
    "optionsHash" : optionsHash}

    #url nécessaire pour modifier le doodle
    url2=url+ key + "/participants"


    #requête post pour écrire pour la première fois dans le doodle
    ri = rq.post(url2, json = envoi)




def recup_creneau(key,nom_utilisateur, participant_key, maj):

    #1er janvier 1970 en date python
    a = datetime.datetime(1970, 1, 1)

    #on stocke le json dans le dictionnaire l
    r = rq.get(url+key)
    l = json.loads(r.content)
    optionsHash=l["optionsHash"]

    #booleen qui dit si les horaires sont allday ou non
    allday=False
    #la liste des options (créneaux) de notre doodle (vide pour l'instant)
    liste_options = []

    #la liste préférences est la liste de 0 et/ou 1 qu'il faut envoyer au Doodle pour le remplir
    preferences=[]

    #représente les places des créneaux finaux dans la liste des préférences
    place=[]

    #compteur représentant le nombre de créneaux
    re=0


    #D'abord, on récupère la liste des dates des débuts et des fins (alternées 2 à 2) des évènements du Doodles.
    #On distingue le cas ou le Doodle est fermé ou non

    try:
        #On regarde si le sondage est fermé ou pas
        t=l['closed']

        #Si le sondage est fermé on récupère tous les crénaux qui sont finaux
        for temps in l["options"]:

            try:
                #on vérifie si l'évenement est final
                bool=temps['final']


                #Date et heure de commencement de l'évènement
                secondesEnPlusDebut = int(str(temps["start"])[0:len(str(temps["start"]))])

                #Date et heure de fin de l'évènement
                secondesEnPlusFin = int(str(temps["end"])[0:len(str(temps["end"]))])

                #On ajoute les deux à la liste des options
                optionDebut = a + datetime.timedelta(milliseconds = int(secondesEnPlusDebut)+3600000)
                liste_options.append(optionDebut)
                optionFin = a + datetime.timedelta(milliseconds = int(secondesEnPlusFin)+3600000)
                liste_options.append(optionFin)

                #Au début, on met par défaut que la personne est libre à tous les crénaux finaux
                preferences.append(1)
                #Vu qu'on récupère seulement les crénaux finaux on conserve leur place dans la liste des preferences
                place.append(re)

            except:
                #Si la date n'est pas finale on ajoute 0 aux préférences, et nous n'avons donc pas à nous soucier des dates non-finales
                preferences.append(0)

            re+=1


    except:
        #Si le sondage est toujours ouvert on récupère tous les créneaux du doodle
        for temps in l["options"]:
            try:
                #Date et heure de commencement de l'évènement
                secondesEnPlusDebut = int(str(temps["start"])[0:len(str(temps["start"]))])

                #Date et heure de fin de l'évènement
                secondesEnPlusFin = int(str(temps["end"])[0:len(str(temps["end"]))])

                #On ajoute les deux à la liste des options
                optionDebut = a + datetime.timedelta(milliseconds = int(secondesEnPlusDebut)+3600000)
                liste_options.append(optionDebut)
                optionFin = a + datetime.timedelta(milliseconds = int(secondesEnPlusFin)+3600000)
                liste_options.append(optionFin)
            except:
                allday=True
                #Date et heure de commencement de l'évènement
                secondesEnPlusDebut = int(str(temps["date"])[0:len(str(temps["date"]))])

                #Date et heure de fin de l'évènement
                secondesEnPlusFin = int(str(temps["date"])[0:len(str(temps["date"]))])

                #On ajoute les deux à la liste des options
                optionDebut = a + datetime.timedelta(milliseconds = int(secondesEnPlusDebut)+3600000)
                liste_options.append(optionDebut)
                optionFin = a + datetime.timedelta(milliseconds = int(secondesEnPlusFin)+3600000)
                liste_options.append(optionFin)


            #Par défault on met dans la liste des préférences qu'on est libre à aucun créneaux
            preferences.append(0)

            #On ajoute la place de chaque créneau dans la liste des préference
            place.append(re)
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

    #On récupère la date actuelle en format adapté aux dates du Doodle
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indique le temps UTC

    #Nous récupérons les évènements du calendrier sur les créneaux récupérés dans listes_options

    i = 1
    eventdate=[]
    for option in liste_options :

        #si i est pair, c'est une date de début
        if i%2==1 :
            debut=str(option)[0:10]+'T'+str(option)[11:20]+'+01:00'
            i+=1

        #si i est impair c'est une date de fin
        else :
            fin=str(option)[0:10]+'T'+str(option)[11:20]+'+01:00'
            if(allday==True):
                #on récupère les évènement du calendrier se situant entre début et fin (même s'ils commencent ou terminent après)
                events_result = service.events().list(calendarId='primary', timeMin=debut.split('T')[0]+'T00:00:01+01:00', timeMax=fin.split('T')[0]+'T23:59:59+01:00').execute()
                events = events_result.get('items', [])
            else:
                #on récupère les évènement du calendrier se situant entre début et fin (même s'ils commencent ou terminent après)
                events_result = service.events().list(calendarId='primary', timeMin=debut, timeMax=fin).execute()
                events = events_result.get('items', [])

            #Si il n'y a pas d'évènement dans le calendrier à ce créneau, on remplit le calendrier en réservant le créneau et on modifie la liste
            #preference en mettant 1 à la bonne place dans la liste
            if not events:
                eventdate.append(debut)
                eventdate.append(fin)
                preferences[place[i//2-1]]=1


            i+=1

    #on convertit la liste des horaires des créneaux en liste des événements qu'on va envoyer au calendrier
    eventdate2=conversion(eventdate,titre,lieu,description,allday)
    if (maj==False):
        remplissage_doodle(preferences,optionsHash,key, nom_utilisateur, participant_key)

    #Cette fonction renvoie la liste des évenement à reserver dans le calendrier, la liste des préférences à envoyer au doodle et l'optionhash qui est utile
    #pour ecrire dans un doodle.
    return eventdate2,preferences,optionsHash,titre,lieu,description,allday


def reserve_creneaux(eventdate, key):

    eventfinal=[]

    #On parcours les evenement qu'on a convertit après avoir récupéré les dates des créneaux dans le doodle
    for k in eventdate:

        #On reserve le créneaux prévu dans le calendrier
        service.events().insert(calendarId='primary', body=k).execute()

        #On récupère les événement qu'on vient juste de résérver car lorsqu'on insère un evenenement il y a un id qui est créé par le calendrier et
        #on en a besoin pour effacer les evenement quand nécessaire
        event=service.events().list(calendarId='primary', timeMin=k['start']['dateTime'], timeMax=k['end']['dateTime']).execute()['items']
        j=0

        #La commande précedente renvoie un liste des évenement qui ont un moment de commun avec l'intervalle donné, on parcours donc la liste jusqu'a trouve
        #l'événement qu'on vient d'insérer en comparant les date de début et de fin
        while event[j]['end']['dateTime']!=k['end']['dateTime'] and event[j]['start']['dateTime']!=k['start']['dateTime']:
            j=j+1

        #On l'ajoute à la liste des evénement, cette liste est comme eventdate sauf qu'on a les id en plus
        eventfinal.append(event[0])

    return eventfinal



#Cette fonction permet d'effacer du calendrier tous les créneaux reservés précedement à partir du doodle afin de tout recommencer lors d'une mis à jour
def efface(eventdate):
    #On recupère les evenement à effacer et on les supprime
    for evenement in eventdate :
        try:
            service.events().delete(calendarId='primary', eventId=line['id']).execute()
        except:
            #Au cas ou le propriétaire du calendrier a supprimé l'evenement à la main
            print('Déja sup')


#Fonction qui permet de mettre à jour les réponses apportées au doodle et les evnt réservés, par exemple si le doodle est modifié
def mise_a_jour(key,nom_utilisateur,eventdate, participant_key):

    #On commence par tout effacer dans le calendrier
    efface(eventdate)

    #on récupère les créneaux ou on est libre
    eventts=recup_creneau(key, nom_utilisateur, participant_key,True)
    #Et enfin on reserve dans le calendrier les créneaux libres
    creneau_reserve=reserve_creneaux(eventts[0],key)
    #On récupère de la fonction recupcreneaux les préferneces pour les envoyer au doodle
    preferences = eventts[1]

    #Paramètres important pour écrire dans le doodle
    participantKey = "et5qinsv"
    optionsHash = eventts[2]

    #On récupère tout le json du doodle pour retouver l'id de la personne considérée par la mise à jour
    l=rq.get(url+key)
    ri=json.loads(l.content)
    li=0

    #on attend de tomber sur le participant ayant le même nom que le propriétaire du calendrier
    while(ri['participants'][li]['name']!=nom_utilisateur):
        li+=1
    print(ri['participants'][li]['id'])
    #On créé le json à envoyer au doodle pour modifier les choix de l'utilisateur
    envoi = {"id":ri['participants'][li]['id'],"name" : nom_utilisateur,
             "optionsHash" : optionsHash, "participantKey": participantKey,
             "preferences" : preferences}

    #Url nécesssaire pour l'envoi des infos
    url2=url+"/participants/"+str(ri['participants'][li]['id'])
    #requête put qui modifie un post précedent
    ra = rq.put(url2, json = envoi)
    return creneau_reserve
