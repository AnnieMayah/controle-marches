"""
Routes API REST pour le suivi des recommandations émises après un contrôle.
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models import Recommandation

recommandations_bp = Blueprint("recommandations", __name__)


@recommandations_bp.route("", methods=["GET"])
def lister_recommandations():
    id_entite = request.args.get("id_entite", type=int)
    query = Recommandation.query
    if id_entite:
        query = query.filter_by(id_entite=id_entite)
    recommandations = query.order_by(Recommandation.date_emission.desc()).all()
    return jsonify([_reco_en_dict(r) for r in recommandations])


@recommandations_bp.route("", methods=["POST"])
def creer_recommandation():
    data = request.get_json()
    reco = Recommandation(
        id_entite=data["id_entite"],
        id_controle=data.get("id_controle"),
        texte=data["texte"],
    )
    db.session.add(reco)
    db.session.commit()
    return jsonify(_reco_en_dict(reco)), 201


@recommandations_bp.route("/<int:id_reco>/statut", methods=["PUT"])
def changer_statut(id_reco):
    data = request.get_json()
    reco = Recommandation.query.get_or_404(id_reco)
    reco.statut = data["statut"]  # EMISE / EN_COURS / APPLIQUEE / NON_APPLIQUEE
    db.session.commit()
    return jsonify(_reco_en_dict(reco))


@recommandations_bp.route("/<int:id_reco>", methods=["DELETE"])
def supprimer_recommandation(id_reco):
    reco = Recommandation.query.get_or_404(id_reco)
    db.session.delete(reco)
    db.session.commit()
    return "", 204


def _reco_en_dict(r):
    return {
        "id": r.id, "id_entite": r.id_entite, "id_controle": r.id_controle,
        "texte": r.texte, "statut": r.statut,
        "date_emission": r.date_emission.isoformat(),
        "date_relance": r.date_relance.isoformat() if r.date_relance else None,
    }
