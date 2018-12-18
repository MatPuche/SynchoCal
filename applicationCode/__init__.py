#Ce fichier contient le constructeur de l’application (fonction create_app) et indique à Python que le répertoire applicationCode doit être traité comme un package.
#C’est à partir de ce fichier que tout est initialisé et que le lancement de l’application est rendu possible.

from flask import Flask
from . import db
from . import auth
from . import page_principale
import os


def create_app(test_config=None):

    #Créé et configure l'application
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # assure que le dossier de l'application existe
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # récupère les données dans la base de données
    db.init_app(app)

    # ajoute les Blueprint à l'application
    app.register_blueprint(auth.bp)
    app.register_blueprint(page_principale.bp)

    #La vue de la page principale est reliée à l'index principal "/"
    app.add_url_rule('/', endpoint='page_principale')

    return app

app=create_app()
