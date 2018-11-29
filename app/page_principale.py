from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from applicationCode.auth import login_required
from applicationCode.db import get_db
from . import with_doodle
from datetime import datetime

bp = Blueprint('page_principale', __name__)

@bp.route('/')
def liste_sondages():
    db = get_db()
    sondages = db.execute(
        'SELECT * FROM sondage'
    ).fetchall()
    return render_template('liste_sondages.html', sondages=sondages)

@bp.route('/ajouter', methods=('GET', 'POST'))
@login_required
def ajouter():
    error=None
    if request.method == 'POST':
        key = request.form['key']
        print(key)

        if not key:
            error = 'Veuillez entrer la clé du sondage.'

        if error is not None:
            flash(error)
        else:
            sond = with_doodle.recup_creneau(key)

            titre=sond[3]
            lieu=sond[4]
            description=sond[5]
            liste_options=sond[5]
            date=datetime.now().date()
            db = get_db()
            db.execute(
                'INSERT INTO sondage (key, titre, lieu, description,liste_options,date_maj)'
                ' VALUES (?, ?, ?, ?, ?)',
                (key, titre, lieu, description,liste_options,date)

            )
            db.commit()
            crenau_reserve=with_doodle.reserve_creneaux(sond[0],key)

            #Ajouter les creneau reserve à la base de donnée!

            return redirect(url_for('page_principale.liste_sondages'))

    return render_template('ajouter.html')


#L'utilisateur peut mettre à jour ses sondages afin d'actualiser les changements qu'il y aurait pu avoir, ou de voir si il est final
@bp.route('/<string:key>/mise_a_jour', methods=('POST',))
@login_required
def mise_a_jour(key):
    db = get_db()
    #fonction de mise à jour du sondage
    desc = 'Le sondage a été mis à jour'
    date_maj=datetime.now().date()
    db.execute(
                'UPDATE sondage SET description = ?, date_maj = ?'
                ' WHERE key = ?',
                (desc, date_maj,key)
            )
    db.commit()

    creneau_reserve=with_doodle.mise_a_jour(key, "bob")
    #Remettre dans la base de donnée les nouveaux créneaux résérvésc

    return redirect(url_for('page_principale'))

#L'utilisateur peut supprimer ses sondages si il le souhaite
@bp.route('/<string:key>/supprimer', methods=('POST',))
@login_required
def supprimer(key):
    db = get_db()
    db.execute(
                'DELETE FROM sondage WHERE key = ?',(key,)
            )
    db.commit()
    return redirect(url_for('page_principale'))
