"""
Routes API REST pour les contrôles — liste, détail, notation par étape, validation.

Visibilité : le directeur (ADMIN) et les rôles historiques voient tout ; un chef de service ne voit que les
contrôles envoyés à son service ; un CV ne voit que ceux que son chef de service lui a assignés.
Un contrôle ne peut pas être ouvert tant que le CV n'a pas renseigné les informations du marché.
Seul le CC / administrateur valide un contrôle, quand toutes les étapes sont notées.
"""
from flask import Blueprint, request, jsonify, g
from extensions import db
from models import Controle, ControleEtape, Etape, Marche, Service, Utilisateur
from services import recalculer_conclusion, valider_controle
import champs_marche
from securite import connexion_requise
from routes.transferts import _niveau_actuel as niveau_actuel
from routes.notifications_prmp import envoyer_resultat_controle
from routes.transferts import _niveau_actuel as niveau_actuel
controles_bp = Blueprint("controles", __name__)

MESSAGE_NON_RENSEIGNE = ("Ce contrôle ne peut pas être ouvert : les informations du marché "
                         "doivent d'abord être renseignées par le CV.")


def _role(u):
    return getattr(u.role, "value", u.role)


def _visible(controle, u):
    """Le contrôle a-t-il été envoyé à cet utilisateur ?"""
    role = _role(u)
    if role == "CHEF_SERVICE":
        return controle.id_service == u.id_service
    if role == "CV":
        return controle.id_utilisateur_assigne == u.id
    return True


def _renseigne(m):
    """Les informations obligatoires du marché ont-elles été remplies par le CV ?"""
    return all(v not in (None, "") for v in
               (m.reference, m.id_nature, m.id_mode_passation, m.montant, m.annee_exercice))


@controles_bp.route("", methods=["GET"])
@connexion_requise
def lister_controles():
    """Liste des contrôles (plus récents d'abord). Filtres : ?id_marche=3&limit=5"""
    id_marche = request.args.get("id_marche", type=int)
    limit = request.args.get("limit", type=int)
    query = Controle.query
    if id_marche:
        query = query.filter_by(id_marche=id_marche)

    u = g.utilisateur
    role = _role(u)
    if role == "CHEF_SERVICE":
        query = query.filter(Controle.id_service == u.id_service)
    elif role == "CV":
        query = query.filter(Controle.id_utilisateur_assigne == u.id)

    query = query.order_by(Controle.id.desc())
    if limit:
        query = query.limit(limit)
    return jsonify([_controle_resume(c) for c in query.all()])


@controles_bp.route("/<int:id_controle>", methods=["GET"])
@connexion_requise
def obtenir_controle(id_controle):
    controle = Controle.query.get_or_404(id_controle)
    if not _visible(controle, g.utilisateur):
        return jsonify({"erreur": "Accès refusé : ce contrôle ne t'a pas été envoyé."}), 403
    if not _renseigne(controle.marche):
        return jsonify({"erreur": MESSAGE_NON_RENSEIGNE}), 409
    etapes = ControleEtape.query.filter_by(id_controle=id_controle).all()
    return jsonify({
        **_controle_resume(controle),
        "marche": _marche_resume(controle.marche),
        "etapes_notees": [
            {"id": e.id, "id_etape": e.id_etape, "libelle_etape": e.etape.libelle,
             "note": e.note, "observations": e.observations}
            for e in etapes
        ],
    })


@controles_bp.route("", methods=["POST"])
@connexion_requise
def creer_controle():
    """Ouvre le contrôle d'un marché déjà envoyé (renvoie celui en cours s'il existe)."""
    data = request.get_json()
    id_marche = data["id_marche"]
    marche = Marche.query.get_or_404(id_marche)

    existant = Controle.query.filter_by(id_marche=id_marche, date_validation=None).first()
    if existant:
        if not _visible(existant, g.utilisateur):
            return jsonify({"erreur": "Accès refusé : ce contrôle ne t'a pas été envoyé."}), 403
        if not _renseigne(marche):
            return jsonify({"erreur": MESSAGE_NON_RENSEIGNE}), 409
        return jsonify(_controle_resume(existant)), 200

    if marche.statut_controle != "ENVOYE":
        return jsonify({"erreur": "Ce marché n'a pas encore été envoyé à un chef de service."}), 409
    if not _renseigne(marche):
        return jsonify({"erreur": MESSAGE_NON_RENSEIGNE}), 409

    controle = Controle(id_marche=id_marche)
    db.session.add(controle)
    db.session.commit()
    return jsonify(_controle_resume(controle)), 201


@controles_bp.route("/<int:id_controle>/etapes", methods=["POST"])
@connexion_requise
def saisir_note_etape(id_controle):
    """Saisie ou mise à jour de la note (0-4) et des observations pour une étape."""
    controle = Controle.query.get_or_404(id_controle)
    if not _visible(controle, g.utilisateur):
        return jsonify({"erreur": "Accès refusé : ce contrôle ne t'a pas été envoyé."}), 403
    if not _renseigne(controle.marche):
        return jsonify({"erreur": MESSAGE_NON_RENSEIGNE}), 409
    if controle.date_validation:
        return jsonify({"erreur": "Ce contrôle est validé : il n'est plus modifiable."}), 409

    data = request.get_json()
    note = data.get("note")
    if niveau_actuel(id_controle) == "VALIDATION":
        return jsonify({"erreur": "Le contrôle est au niveau VALIDATION : les notes ne sont plus modifiables. Renvoie-le à un niveau précédent."}), 409
    if note is None or not (0 <= int(note) <= 4):
        return jsonify({"erreur": "La note doit être comprise entre 0 et 4."}), 400

    id_etape = data["id_etape"]
    etape = ControleEtape.query.filter_by(id_controle=id_controle, id_etape=id_etape).first()
    if etape is None:
        etape = ControleEtape(id_controle=id_controle, id_etape=id_etape)
        db.session.add(etape)

    etape.note = int(note)
    etape.observations = data.get("observations")
    etape.id_utilisateur = data.get("id_utilisateur") or g.utilisateur.id
    db.session.commit()

    controle = recalculer_conclusion(id_controle)
    return jsonify(_controle_resume(controle)), 201


@controles_bp.route("/<int:id_controle>/valider", methods=["POST"])
@connexion_requise
def valider(id_controle):
    """Validation finale : réservée au CC / administrateur, et possible seulement quand toutes les étapes sont notées."""
    if _role(g.utilisateur) != "ADMIN":
        return jsonify({"erreur": "Accès refusé : seul le CC / administrateur peut valider un contrôle."}), 403
    controle = Controle.query.get_or_404(id_controle)
    if controle.date_validation:
        return jsonify({"erreur": "Ce contrôle est déjà validé."}), 409
    if _niveau_actuel(controle.id) != NIVEAUX[-1]:
        return jsonify(...), 409
    total_etapes = Etape.query.count()
    notees = ControleEtape.query.filter(
        ControleEtape.id_controle == id_controle, ControleEtape.note.isnot(None)
    ).count()
    if notees < total_etapes:
        return jsonify({"erreur": f"Toutes les étapes doivent être notées avant validation ({notees}/{total_etapes})."}), 400

    data = request.get_json(silent=True) or {}
    controle = valider_controle(id_controle, data.get("id_utilisateur_validateur") or g.utilisateur.id)

    try:
        notification, _ = envoyer_resultat_controle(controle)
    except Exception as e:
        notification = {"ok": False, "erreur": str(e)}

    resume = _controle_resume(controle)
    resume["notification"] = notification
    return jsonify(resume)


def _nom(u):
    return " ".join(x for x in [u.prenom, u.nom] if x) if u else None


def _controle_resume(c):
    notees = ControleEtape.query.filter(
        ControleEtape.id_controle == c.id, ControleEtape.note.isnot(None)
    ).count()
    service = db.session.get(Service, c.id_service) if c.id_service else None
    assigne = db.session.get(Utilisateur, c.id_utilisateur_assigne) if c.id_utilisateur_assigne else None
    m = c.marche
    return {
        "id": c.id,
        "reference": f"CTRL-{c.id:04d}",
        "id_marche": c.id_marche,
        "reference_marche": m.reference or "—",
        "marche_renseigne": _renseigne(m),
        "entite": m.entite.nom,
        "nature": m.nature.libelle if m.nature else "—",
        "date_controle": c.date_controle.isoformat() if c.date_controle else None,
        "note_globale": float(c.note_globale) if c.note_globale is not None else None,
        "conclusion": c.conclusion,
        "nb_etapes_notees": notees,
        "niveau": niveau_actuel(c.id),
        "valide": c.date_validation is not None,
        "date_validation": c.date_validation.isoformat() if c.date_validation else None,
        # circuit d'envoi
        "id_service": c.id_service,
        "service": service.nom if service else None,
        "id_assigne": c.id_utilisateur_assigne,
        "assigne_a": _nom(assigne),
        # « À démarrer » : envoyé à un service mais aucune étape notée pour l'instant
        "etat": "A_DEMARRER" if (c.id_service and notees == 0 and c.date_validation is None) else None,
    }


def _marche_resume(m):
    return {
        "id": m.id, "reference": m.reference, "objet": m.objet, "entite": m.entite.nom,
        "nature": m.nature.libelle if m.nature else None,
        "mode_passation": m.mode_passation.libelle if m.mode_passation else None,
        "montant": float(m.montant) if m.montant is not None else None, "titulaire": m.titulaire,
        "annee_exercice": m.annee_exercice, "hors_ppm": m.hors_ppm,
        "marche_regularisation": m.marche_regularisation,
        **champs_marche.infos_generales(m),
    }