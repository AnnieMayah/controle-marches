"""
Catalogue des observations prédéfinies par étape (listes déroulantes).
Ajout : tout utilisateur. Suppression : administrateur uniquement.
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models import ObservationType, Utilisateur

observations_bp = Blueprint("observations", __name__)


def _out(o):
    return {"id": o.id, "id_etape": o.id_etape, "libelle": o.libelle}


@observations_bp.route("", methods=["GET"])
def lister():
    return jsonify([_out(o) for o in ObservationType.query.order_by(ObservationType.id).all()])


@observations_bp.route("", methods=["POST"])
def ajouter():
    data = request.get_json()
    libelle = (data.get("libelle") or "").strip()
    if not libelle:
        return jsonify({"erreur": "Le libellé est obligatoire."}), 400
    if ObservationType.query.filter_by(id_etape=data["id_etape"], libelle=libelle).first():
        return jsonify({"erreur": "Cette observation existe déjà pour cette étape."}), 409
    o = ObservationType(id_etape=data["id_etape"], libelle=libelle)
    db.session.add(o)
    db.session.commit()
    return jsonify(_out(o)), 201


@observations_bp.route("/<int:id_obs>", methods=["DELETE"])
def supprimer(id_obs):
    user = Utilisateur.query.get(request.args.get("id_utilisateur", type=int))
    if not user or user.role != "ADMIN":  # adapte au nom/valeur réels du rôle
        return jsonify({"erreur": "Seul l'administrateur peut supprimer une observation de la liste."}), 403
    db.session.delete(ObservationType.query.get_or_404(id_obs))
    db.session.commit()
    return "", 204


@observations_bp.route("/<int:id_obs>", methods=["PUT"])
def modifier(id_obs):
    o = ObservationType.query.get_or_404(id_obs)
    libelle = (request.get_json().get("libelle") or "").strip()
    if not libelle:
        return jsonify({"erreur": "Le libellé est obligatoire."}), 400
    doublon = ObservationType.query.filter(
        ObservationType.id_etape == o.id_etape, ObservationType.libelle == libelle, ObservationType.id != id_obs
    ).first()
    if doublon:
        return jsonify({"erreur": "Cette observation existe déjà pour cette étape."}), 409
    o.libelle = libelle
    db.session.commit()
    return jsonify(_out(o))