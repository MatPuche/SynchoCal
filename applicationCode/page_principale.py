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
@login_required
def liste_sondages():
    db = get_db()
    sondages = db.execute(
        #'SELECT * FROM sondage JOIN sondage_user ON sondage.key=sondage_user.sondage_key'
        'SELECT * FROM sondage JOIN (SELECT sondage_key FROM sondage_user WHERE user_id = ?) sond ON sondage.key=sond.sondage_key',(g.user['id'],)
    ).fetchall()
    return render_template('liste_sondages.html', sondages=sondages)

@bp.route('/ajouter', methods=('GET', 'POST'))
@login_required
def ajouter():
    error=None
    if request.method == 'POST':
        key = request.form['key']

        if not key:
            error = 'Veuillez entrer la clé du sondage.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            nom_utilisateur= (db.execute(
                                    'SELECT nom_doodle FROM user WHERE id = ?', (g.user['id'],)
                                    ).fetchone())['nom_doodle']

            #On met une clé au hasard
            participant_key = "et5qinsv"

            sond = with_doodle.recup_creneau(key,nom_utilisateur, participant_key,False)
            titre=sond[3]
            lieu=sond[4]
            description=sond[5]
            liste_options=str(sond[0])
            date=datetime.now().date()
            db.execute(
                'INSERT INTO sondage (key, titre, lieu, description,liste_options,date_maj,date_entree)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                (key, titre, lieu, description,liste_options,date,date)
            )
            db.execute(
                'INSERT INTO sondage_user (sondage_key, user_id)'
                ' VALUES (?, ?)',
                (key, g.user['id'])
            )
            db.commit()
            crenau_reserve=with_doodle.reserve_creneaux(sond[0],key)

            return redirect(url_for('page_principale.liste_sondages'))

    return render_template('ajouter.html')




#L'utilisateur peut mettre à jour ses sondages afin d'actualiser les changements qu'il y aurait pu avoir, ou de voir si il est final
@bp.route('/<string:key>/<int:id>/mise_a_jour', methods=('POST',))
@login_required
def mise_a_jour(key,id):

    #on met la même clé (au hasard)
    participant_key = "et5qinsv"

    db = get_db()
    nom_utilisateur= (db.execute(
                            'SELECT nom_doodle FROM user WHERE id = ?', (id,)
                            ).fetchone())['nom_doodle']
    eventdate = eval((db.execute(
                            'SELECT liste_options FROM sondage WHERE key = ?', (key,)
                            ).fetchone())['liste_options'])
    event_maj = str(with_doodle.mise_a_jour(key,nom_utilisateur,eventdate, participant_key))
    date_maj=datetime.now().date()
    db.execute(
                'UPDATE sondage SET liste_options = ?, date_maj = ?'
                ' WHERE key = ?',
                (event_maj, date_maj,key)
            )
    db.commit()
    return redirect(url_for('page_principale'))

#L'utilisateur peut supprimer ses sondages si il le souhaite
@bp.route('/<string:key>/supprimer', methods=('POST',))
@login_required
def supprimer(key):
    db = get_db()
    eventdate = eval((db.execute(
                            'SELECT liste_options FROM sondage WHERE key = ?', (key,)
                            ).fetchone())['liste_options'])
    with_doodle.efface(eventdate)
    db.execute(
                'DELETE FROM sondage WHERE key = ?',(key,)
            )
    db.execute(
        'DELETE FROM sondage_user WHERE sondage_key = ?', (key,)
    )
    db.commit()
    return redirect(url_for('page_principale'))
