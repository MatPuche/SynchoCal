#Ce fichier contient toutes les fonctions d'intéraction entre le calendrier et le sondage Doodle

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
#calendar pour ajouter un evenement. Prend en argument le titre le lieu et la description du doodle ainsi que la liste des dates des créneaux.
def conversion(eventdate,titre,lieu,description, jour_entier):
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

    else :
        for ki in range( len(eventdate)//2):

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
            res.append(event2)

    return res


#Fonction qui remplit le Doodle selon les préférences de 'utilisateur receuillies à partir de son calendrier'
def remplissage_doodle(preferences,optionsHash,key, nom_utilisateur, participantKey):

    #Json à envoyer pour remplir le doodle
    envoi = {"name" : nom_utilisateur, "preferences" :
    preferences, "participantKey" : participantKey,
    "optionsHash" : optionsHash}

    #url nécessaire pour modifier le doodle
    url2=url+ key + "/participants"


    #requête post pour écrire pour la première fois dans le doodle
    ri = rq.post(url2, json = envoi)


#Fonction qui renvoie True si le sondage effectué est sur une journée entière, False sinon
def jourEntier (evenement):
    try :
        evenement["end"]
        return False
    except :
        return True


def recup_creneau(key,nom_utilisateur, participant_key):

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

            jour_entier = journtier(temps)

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

            jour_entier = jourEntier(temps)

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


    #Nous récupérons les évènements du calendrier sur les créneaux récupérés dans listes_options


    eventdate=[]
    i = 1

    if jour_entier :

        for option in liste_options :

            #pour un sondage sur un jour entier, on a la listes de jours du sondage dans liste_options
            jour = str(option)[0:10]
            debut=str(option)[0:10]+'T00:00:00+01:00'
            fin=str(option)[0:10]+'T23:59:59+01:00'
            events_result = service.events().list(calendarId='primary', timeMin=debut, timeMax=fin, singleEvents=True).execute()
            events = events_result.get('items', [])

            #Si il n'y a pas d'évènement dans le calendrier cette journée là, on remplit le calendrier en réservant la journée et on modifie la liste
            #preference en mettant 1 à la bonne place dans la liste
            if not events:
                eventdate.append(jour)
                preferences[place[i-1]]=1
            i+=1

    else :

        for option in liste_options :

            #pour un sondage sur des créneaux et non sur des jours entiers, on a successivement les horaires de début et de fin dans liste_options

            #si i est pair, c'est une date de début
            if i%2==1 :
                debut=str(option)[0:10]+'T'+str(option)[11:20]+'+01:00'
                i+=1

            #si i est impair c'est une date de fin
            else :
                fin=str(option)[0:10]+'T'+str(option)[11:20]+'+01:00'
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
    eventdate2 = conversion(eventdate,titre,lieu,description, jour_entier)
    remplissage_doodle(preferences,optionsHash,key, nom_utilisateur, participant_key)

    #Cette fonction renvoie la liste des évenement à reserver dans le calendrier, la liste des préférences à envoyer au doodle et l'optionhash qui est utile
    #pour ecrire dans un doodle.
    return eventdate2,preferences,optionsHash,titre,lieu,description, jour_entier


#On remplit le calendrier avec les créneaux réservés pour le sondage tant qu'il n'est pas terminé
def reserve_creneaux(eventdate, jour_entier, key):

    eventfinal=[]
    #On parcourt les evenements qu'on a converti après avoir récupéré les dates des créneaux dans le doodle
    for k in eventdate:

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

    return eventfinal



#Cette fonction permet d'effacer du calendrier tous les créneaux reservés précedement à partir du doodle afin de tout recommencer lors d'une mise à jour
def efface(eventdate, key,nom_utilisateur):
    #On recupère les evenement à effacer et on les supprime
    for evenement in eventdate :
        print(evenement)
        try:
            service.events().delete(calendarId='primary', eventId=evenement['id']).execute()
        except:
            #Au cas où le propriétaire du calendrier a supprimé l'evenement à la main
            print('Déja sup')

    #On récupère tout le json du doodle pour retouver l'id de la personne considérée par la mise à jour
    l=rq.get(url+key)
    ri=json.loads(l.content)
    li=0

    #on attend de tomber sur le participant ayant le même nom que le propriétaire du calendrier
    while(ri['participants'][li]['name']!=nom_utilisateur):
        li+=1

    #Url nécesssaire pour l'envoi des infos
    url2=url+key+"/participants/"+str(ri['participants'][li]['id'])
    print(url2)
    #requête put qui modifie un post précedent
    ra = rq.delete(url2)


#Fonction qui permet de mettre à jour les réponses apportées au doodle et les evnt réservés, par exemple si le doodle est modifié
def mise_a_jour(key,nom_utilisateur,eventdate, participant_key):

    #On commence par tout effacer dans le calendrier
    efface(eventdate, key, nom_utilisateur)

    #on récupère les créneaux ou on est libre
    eventts=recup_creneau(key, nom_utilisateur, participant_key)
    #Et enfin on reserve dans le calendrier les créneaux libres
    creneau_reserve=reserve_creneaux(eventts[0],eventts[6],key)

    return creneau_reserve
