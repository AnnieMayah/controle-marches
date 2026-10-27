"""
Routes API REST pour les entités contractantes.
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models import Entite

entites_bp = Blueprint("entites", __name__)


@entites_bp.route("", methods=["GET"])
def lister_entites():
    entites = Entite.query.all()
    return jsonify([_entite_en_dict(e) for e in entites])


@entites_bp.route("/<int:id_entite>", methods=["GET"])
def obtenir_entite(id_entite):
    entite = Entite.query.get_or_404(id_entite)
    return jsonify(_entite_en_dict(entite))


@entites_bp.route("", methods=["POST"])
def creer_entite():
    data = request.get_json()
    if not data.get("nom", "").strip():
        return jsonify({"erreur": "Le nom de l'entité est obligatoire."}), 400
    if data.get("type") not in ("STD", "CTD", "EPN"):
        return jsonify({"erreur": "Le type doit être STD, CTD ou EPN."}), 400
    entite = Entite(nom=data["nom"].strip(), type=data["type"], region=data.get("region"))
    db.session.add(entite)
    db.session.commit()
    return jsonify(_entite_en_dict(entite)), 201


@entites_bp.route("/<int:id_entite>", methods=["PUT"])
def modifier_entite(id_entite):
    entite = Entite.query.get_or_404(id_entite)
    data = request.get_json()
    entite.nom = data.get("nom", entite.nom)
    entite.type = data.get("type", entite.type)
    entite.region = data.get("region", entite.region)
    db.session.commit()
    return jsonify(_entite_en_dict(entite))


@entites_bp.route("/<int:id_entite>", methods=["DELETE"])
def supprimer_entite(id_entite):
    entite = Entite.query.get_or_404(id_entite)
    if entite.marches:
        return jsonify({"erreur": "Impossible de supprimer : des marchés sont rattachés à cette entité."}), 409
    db.session.delete(entite)
    db.session.commit()
    return "", 204


def _entite_en_dict(e):
    return {"id": e.id, "nom": e.nom, "type": e.type, "region": e.region}
