from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from applicationCode.auth import login_required
from applicationCode.db import get_db
from . import with_doodle
from datetime import datetime

bp = Blueprint('page_principale', __name__)

#Sur la page principale on affiche les sondages en cours de l'utilisateur
@bp.route('/')
@login_required
def liste_sondages():
    db = get_db()
    sondages = db.execute(
        'SELECT * FROM sondage JOIN (SELECT sondage_key FROM sondage_user WHERE user_id = ?) sond ON sondage.key=sond.sondage_key',(g.user['id'],)
    ).fetchall()
    return render_template('liste_sondages.html', sondages=sondages)

#L'utilisateur peut choisir d'ajouter un nouveau sondage
@bp.route('/ajouter', methods=('GET', 'POST'))
@login_required
def ajouter():
    error=None
    db = get_db()
    if request.method == 'POST':
        key = request.form['key']

        if not key:
            error = 'Veuillez entrer la clé du sondage.'
        elif db.execute(
            'SELECT key FROM sondage WHERE key = ?', (key,)
        ).fetchone() is not None:
            error = 'Le sondage {} existe déjà.'.format(key)

        if error is not None:
            flash(error)
        else:
            #try :
            nom_utilisateur= (db.execute(
                                    'SELECT nom_doodle FROM user WHERE id = ?', (g.user['id'],)
                                    ).fetchone())['nom_doodle']

            #On met une clé au hasard
            participant_key = "et5qinsv"

            sond = with_doodle.recup_creneau(key,nom_utilisateur, participant_key)
            titre=sond[3]
            lieu=sond[4]
            description=sond[5]
            final=sond[7]
            date=datetime.now().date()
            creneau_reserve=str(with_doodle.reserve_creneaux(sond[0],sond[6],key))
            db.execute(
                'INSERT INTO sondage (key, titre, lieu, description,liste_options,date_maj,date_entree, est_final)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (key, titre, lieu, description,creneau_reserve,date,date, final)
            )
            db.execute(
                'INSERT INTO sondage_user (sondage_key, user_id)'
                ' VALUES (?, ?)',
                (key, g.user['id'])
            )
            db.commit()
            return redirect(url_for('page_principale.liste_sondages'))
            #except :
            #    flash('Clé de sondage invalide')

    return render_template('ajouter.html')




#L'utilisateur peut mettre à jour ses sondages afin d'actualiser les changements qu'il y aurait pu avoir, ou de voir si il est final
@bp.route('/<string:key>/<int:id>/<string:nom_utilisateur>/mise_a_jour', methods=('POST',))
@login_required
def mise_a_jour(key,id,nom_utilisateur):

    #on met la même clé (au hasard)
    participant_key = "et5qinsv"

    db = get_db()
    eventdate = eval((db.execute(
                            'SELECT liste_options FROM sondage WHERE key = ?', (key,)
                            ).fetchone())['liste_options'])

    maj = with_doodle.mise_a_jour(key,nom_utilisateur,eventdate, participant_key)
    event_maj = str(maj[0])
    date_maj=datetime.now().date()
    db.execute(
                'UPDATE sondage SET liste_options = ?, date_maj = ?, est_final = ?'
                ' WHERE key = ?',
                (event_maj, date_maj, maj[1],key)
            )
    db.commit()
    return redirect(url_for('page_principale'))

#L'utilisateur peut supprimer ses sondages si il le souhaite
@bp.route('/<string:key>/<string:nom_utilisateur>/supprimer', methods=('POST',))
@login_required
def supprimer(key, nom_utilisateur):
    db = get_db()
    eventdate = eval((db.execute(
                            'SELECT liste_options FROM sondage WHERE key = ?', (key,)
                            ).fetchone())['liste_options'])

    with_doodle.efface(eventdate, key, nom_utilisateur)
    db.execute(
                'DELETE FROM sondage WHERE key = ?',(key,)
            )
    db.execute(
        'DELETE FROM sondage_user WHERE sondage_key = ?', (key,)
    )
    db.commit()
    return redirect(url_for('page_principale'))
