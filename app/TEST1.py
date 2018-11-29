from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import requests
import json
import datetime
import time
import requests as rq


#RECUPERATION DES DISPONIBILITES DE L'UTILISATEUR SUR CES CRENEAUX

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'

store = file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentialsthib.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('calendar', 'v3', http=creds.authorize(Http()))


#Fonction qui permet de convertir les dates de début et de fin d'un créneau doodle sous la forme d'un json. Ce json est sous la forme qu'il faut envoyer à google
#calendar pour ajouter un evenemet. Prend en argument le titre le lieu et la description du doodle ainsi que la liste des dates des créneaux.
def conversion(eventdate,titre,lieu,description):
    res=[]
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

#Cette fonction renvoie la liste des évenement à reserver dans le calendrier, la liste des préférences à envoyer au doodle et l'optionhash qui est utile
#pour ecrire dans un doodle.
def recupcreneaux( url, key):
    #1er janvier 1970 en date python
    a = datetime.datetime(1970, 1, 1)



    #on stocke le json dans le dictionnaire l
    r = requests.get(url)
    l = json.loads(r.content)
    optionsHash=l["optionsHash"]


    #la liste des options (créneaux) de notre doodle (vide pour l'instant)
    liste_options = []

    #la liste préférence est la liste qu'il faut envoyer au doodle pour remplir le doodle
    preferences=[]
    place=[]
    re=0

    #les options du doodle sont stockées sous forme de listes (qu'on appelle temps ici) pour la clé "options" du dictionnaire l
    try:
        #On regarde si le sondage est fermé ou pas
        t=l['closed']

        #Si le sondage est fermé on récupére tous les crénaux qui sont finaux
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

                #On met par défaut au début que la paersonne est libre à tous les crénaux finaux
                preferences.append(1)
                #Vu qu'on récupère seulement les crénaux finaux on conserve leur place dans la liste des preference
                place.append(re)

            except:
                #Si la date n'est pas final on ajoute 0 au préférence comme ça on ne se souci pas de ses dates
                preferences.append(0)


            #Incrément qui représente le nombre de créneaux
            re+=1


    except:
        #Si le sondage est toujours ouvert on récupère tous les créneaux du doodle
        for temps in l["options"]:

            #Date et heure de commencement de l'évènement
            secondesEnPlusDebut = int(str(temps["start"])[0:len(str(temps["start"]))])

            #Date et heure de fin de l'évènement
            secondesEnPlusFin = int(str(temps["end"])[0:len(str(temps["end"]))])

            #On ajoute les deux à la liste des options
            optionDebut = a + datetime.timedelta(milliseconds = int(secondesEnPlusDebut)+3600000)
            liste_options.append(optionDebut)
            optionFin = a + datetime.timedelta(milliseconds = int(secondesEnPlusFin)+3600000)
            liste_options.append(optionFin)

            #Par défault on met dans la liste des préférences par défaut qu'on est libre à aucun créneaux
            preferences.append(0)

            #On ajoute la place de chaque créneau dans la liste des préference
            place.append(re)
            re+=1



    #On stock les infos importantes du doodle
    titre = l["title"]
    lieu = l["location"]["name"]
    description = l["description"]




    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indique le temps UTC

    #Nous récupérons les évènements du calendrier sur les créneaux donnés par le Doodle
    i = 1
    eventdate=[]
    for option in liste_options :

        if i%2==1 :
            debut=str(option)[0:10]+'T'+str(option)[11:20]+'+01:00'
            i+=1

        else :
            fin=str(option)[0:10]+'T'+str(option)[11:20]+'+01:00'
            events_result = service.events().list(calendarId='primary', timeMin=debut, timeMax=fin).execute()
            events = events_result.get('items', [])


            #Si il n'y a pas d'évènement dans le calendrier à ce créneau, on remplit le calendrier en réservant le créneau et on modifie la liste
            #preference en mettant 1 à la bonne place dans la liste
            if not events:
                eventdate.append(debut)
                eventdate.append(fin)
                preferences[place[i//2-1]]=1


            i+=1
            #on converti la liste des horaires des créneaux en liste des événements qu'on va envoyé au calendrier
            eventdate2=conversion(eventdate,titre,lieu,description)


    return eventdate2,preferences,optionsHash




def reservecreneaux(eventdate, key):

    #On écrit dans un fichier qui prend le nom de la clé du sondage tous les événement qqu'on a réservé dans le calendrier
    fichier=open(key+".txt","w")


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
        eventfinal.append(event[j])

        #On écrit dans le fichier les événement réservé
        fichier.write(str(event[j])+'\n')

    fichier.close()



#Cette fonction permet d'effacer du calendrier tous les créneaux reservés précedement à partir du doodle afin de tout recommencer lors d'une mis à jour
def efface(key):
    #On ouvre le fichier qui stock tous les evn réservés
    f=open(key + ".txt" , "r")

    #Et pour chaque ligne on efface l'événement à partir de son id
    for line in f:
        try:
            service.events().delete(calendarId='primary', eventId=eval(line)['id']).execute()
        except:
            #Au cas ou le propriétaire du calendrier à supprimer l'evn à la main
            print('Déja sup')
    f.close()



#Fonction qui permet de mettre à jour les réponses apportés au doodle et les evn réservés, par exemple si le doodle est modifié
def misajour(url,key,nom_utilisateur):

    #On commence par tout effacer dans le calendrier
    efface(key)

    #on récupère les créneaux ou on est libre
    eventts=recupcreneaux(url, key)
    #Et enfin on reserve dans le calendrier les créneaux libres
    reservecreneaux(eventts[0],key)
    #On récupère de la fonction recupcreneaux les préferneces pour les envoyer au doodle
    preferences = eventts[1]

    #Paramètres important pour écrire dans le doodle
    participantKey = "et5qinsv"
    optionsHash = eventts[2]

    #On récupère tout le json du doodle pour retouver l'id de la personne considéré par la mise à jour
    l=rq.get('https://doodle.com/api/v2.0/polls/dzvsdpkhe534rivt')
    ri=json.loads(l.content)
    li=0

    #on attend de tomber sur le participant qui a le même nom que celui qui a le calendrier
    while(ri['participants'][li]['name']!=nom_utilisateur):
        li+=1

    #On créé le json à envoyer au doodle pour modifier les choix de l'utilisateur
    envoi = {"id":ri['participants'][li]['id'],"name" : nom_utilisateur,
             "optionsHash" : optionsHash, "participantKey": participantKey,
             "preferences" : preferences}

    #Url nécesssaire pour l'envoi des infos
    url2=url+"/participants/"+str(ri['participants'][li]['id'])
    #requête put qui modifie un post précedent
    ra = rq.put(url2, json = envoi)
    print("Sondage"+key+"mis à jour")






def main():
    #url du sondage et identifiant de l'utilisateur
    url = "https://doodle.com/api/v2.0/polls/"
    nom_utilisateur =str(input("Entrer votre nom d'utilisateur \n"))
    mdp=str(input("entrer votre mdp \n"))

    #On essaye d'ouvrir le fichier à partir des identifiants
    try:
        fi=open(nom_utilisateur+mdp+".txt","r")
        print("compte déja existant")
        #Le compte existe déja donc le fichier contient tous les clé des sondages déjà ajouté par la personne, on les met donc tous à jour
        for ligne in fi:
            url+=ligne
            misajour(url,str(ligne),nom_utilisateur)
        fi.close()

    except:
        #Si c'est une nouvelle personne on créé le fichier qui contiendra les clés des sondages
        print("on créé le compte")
        fv=open(nom_utilisateur+mdp+'.txt',"w")
        fv.close()


    #Dans tous les cas on demande si la personne veut ajouter un nouveau sondage
    print("voulez vous ajouter un sondage? o/n")
    rep=str(input())
    if(rep=="o"):
        fi=open(nom_utilisateur+mdp+'.txt',"a")
        key=str(input("Entrez la key du sondage \n"))

        #on écrit la clé du sondage dans le fichier
        fi.write(key+'\n')
        fi.close()


        #url du sondage
        url = "https://doodle.com/api/v2.0/polls/" + key

        #on récupère les créneaux ou on est libre
        eventts=recupcreneaux(url,key)

        #On réserve les créneaux ou on est disponible
        reservecreneaux(eventts[0],key)

        #informations nécessaire pour remplir le doodle
        preferences = eventts[1]
        participantKey = "et5qinsv"
        optionsHash =eventts[2]


        #Json à envoyer pour remplir le doodle
        envoi = {"name" : nom_utilisateur, "preferences" :
        preferences, "participantKey" : participantKey,
        "optionsHash" : optionsHash}

        #url nécessaire pour modifier le doodle
        url2=url+"/participants"

        #requête post pour écrire pour la première fois dans le doodle
        ri = rq.post(url2, json = envoi)
        print(ri.text)




"""    try:

        f=open(key+".txt","r")
        print("b")
        f.close()

        misajour(url,key,nom_utilisateur)


    except:
        eventts=recupcreneaux(url,key)
        reservecreneaux(eventts[0],key)

        preferences = eventts[1]
        participantKey = "et5qinsv"
        optionsHash =eventts[2]

        envoi = {"name" : nom_utilisateur, "preferences" :
        preferences, "participantKey" : participantKey,
        "optionsHash" : optionsHash}


        url2=url+"/participants"
        ri = rq.post(url2, json = envoi)
        print(ri.text)"""
