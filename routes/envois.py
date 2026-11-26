"""
Circuit d'envoi : CC / directeur (ADMIN) -> membre (chef de service) -> CV.

  Marché : A_CONTROLER --(directeur, « À contrôler »)--> A_ENVOYER --(directeur, choix du service)--> ENVOYE
  Le contrôle est créé dès le clic sur « À contrôler » (visible du directeur dans la liste des contrôles) ;
  l'envoi lui attribue le service. Le membre envoie ensuite les marchés à un CV de son service,
  qui remplit leurs informations.
"""
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from extensions import db
from models import Marche, Controle, Service, Utilisateur
from securite import connexion_requise

envois_bp = Blueprint("envois", __name__)


def _role(u):
    return getattr(u.role, "value", u.role)


def _nom(u):
    return " ".join(x for x in [u.prenom, u.nom] if x)


def _ids(data):
    ids = (data or {}).get("ids")
    if not isinstance(ids, list):
        return []
    try:
        return sorted({int(i) for i in ids})
    except (TypeError, ValueError):
        return []


def _refus():
    return jsonify({"erreur": "Accès refusé : action réservée au directeur."}), 403


@envois_bp.route("/services", methods=["GET"])
@connexion_requise
def lister_services():
    """Services avec le nom de leur chef (None si aucun chef actif)."""
    resultat = []
    for s in Service.query.order_by(Service.nom).all():
        chef = Utilisateur.query.filter_by(id_service=s.id, role="CHEF_SERVICE", actif=True).first()
        resultat.append({"id": s.id, "nom": s.nom, "chef": _nom(chef) if chef else None})
    return jsonify(resultat)


@envois_bp.route("/marches/a-controler", methods=["POST"])
@connexion_requise
def marquer_a_controler():
    if _role(g.utilisateur) != "ADMIN":
        return _refus()
    ids = _ids(request.get_json())
    marches = Marche.query.filter(Marche.id.in_(ids), Marche.statut_controle == "A_CONTROLER").all()
    if not marches:
        return jsonify({"erreur": "Aucun marché à marquer (déjà traités ou introuvables)."}), 400
    for m in marches:
        m.statut_controle = "A_ENVOYER"
        if Controle.query.filter_by(id_marche=m.id, date_validation=None).first() is None:
            db.session.add(Controle(id_marche=m.id))
    db.session.commit()
    return jsonify({"nb": len(marches)})


@envois_bp.route("/marches/envoyer", methods=["POST"])
@connexion_requise
def envoyer_marches():
    if _role(g.utilisateur) != "ADMIN":
        return _refus()
    data = request.get_json() or {}
    ids = _ids(data)
    service = db.session.get(Service, data.get("id_service") or 0)
    if service is None:
        return jsonify({"erreur": "Choisis le service destinataire."}), 400
    chef = Utilisateur.query.filter_by(id_service=service.id, role="CHEF_SERVICE", actif=True).first()
    if chef is None:
        return jsonify({"erreur": f"{service.nom} n'a pas de chef de service actif."}), 400

    marches = Marche.query.filter(Marche.id.in_(ids), Marche.statut_controle == "A_ENVOYER").all()
    if not marches:
        return jsonify({"erreur": "Aucun marché à envoyer (ils doivent d'abord être « À envoyer »)."}), 400
    for m in marches:
        controle = Controle.query.filter_by(id_marche=m.id, date_validation=None).first()
        if controle is None:
            controle = Controle(id_marche=m.id)
            db.session.add(controle)
        controle.id_service = service.id
        controle.id_utilisateur_assigne = None
        controle.date_envoi = datetime.utcnow()
        m.statut_controle = "ENVOYE"
    db.session.commit()
    return jsonify({"nb": len(marches), "service": service.nom, "chef": _nom(chef)})


@envois_bp.route("/equipe", methods=["GET"])
@connexion_requise
def equipe():
    """CV du service du membre (chef de service) connecté."""
    u = g.utilisateur
    if _role(u) != "CHEF_SERVICE":
        return jsonify({"erreur": "Accès refusé : réservé au chef de service."}), 403
    membres = (Utilisateur.query
               .filter(Utilisateur.id_service == u.id_service, Utilisateur.role == "CV",
                       Utilisateur.actif.is_(True))
               .order_by(Utilisateur.nom).all())
    return jsonify([{"id": m.id, "nom": _nom(m), "titre": _role(m)} for m in membres])


@envois_bp.route("/marches/assigner", methods=["POST"])
@connexion_requise
def assigner_marches():
    """Le membre (chef de service) envoie un ou plusieurs marchés de son service à un CV."""
    u = g.utilisateur
    if _role(u) != "CHEF_SERVICE":
        return jsonify({"erreur": "Accès refusé : réservé au membre (chef de service)."}), 403
    data = request.get_json() or {}
    ids = _ids(data)
    cible = db.session.get(Utilisateur, data.get("id_utilisateur") or 0)
    if cible is None or not cible.actif or cible.id_service != u.id_service or _role(cible) != "CV":
        return jsonify({"erreur": "Choisis un CV de ton service."}), 400

    controles = Controle.query.filter(Controle.id_marche.in_(ids), Controle.id_service == u.id_service,
                                      Controle.date_validation.is_(None)).all()
    if not ids or {c.id_marche for c in controles} != set(ids):
        return jsonify({"erreur": "Certains marchés ne sont pas de ton service ou sont déjà contrôlés."}), 400
    for c in controles:
        c.id_utilisateur_assigne = cible.id
    db.session.commit()
    return jsonify({"nb": len(controles), "destinataire": _nom(cible)})