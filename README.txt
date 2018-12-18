Pour faire fonctionner l'application WEB en local :

1) Telecharger Python 3.7

2) Installer Flask : pip install Flask

3) A chaque nouvelle utilisation, dans l'invite de commande executer les lignes suivantes :
    set FLASK_APP=applicationCode
    set FLASK_ENV=development

4) Pour la première utilisation seulement, il faut initialiser la base de donnée :
    py -m flask init-db

5)Pour permettre à l'application de fonctionner, il faut télécharger certains modules :
       pip install --upgrade google-api-python-client oauth2client
       pip install requests

6) Pour pouvoir utiliser l'application, placer le fichier credentials.json dans le même dossier que l'application (dans le dossier applicationCode)
cf. le tutoriel fourni par Google API pour se procurer les credentials (clé identifiant client)

7) Pour lancer l'application, se placer dans le répertoire de l'application et executer dans l'invite de commande (sous Windows) :
    py -m flask run

8) Se rendre sur l'URL locale suivante : http://127.0.0.1:5000
