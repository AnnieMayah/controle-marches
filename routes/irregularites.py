"""
Routes API REST pour les irrégularités constatées lors d'une étape de contrôle.
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models import Irregularite, ControleEtape
from services import recalculer_conclusion

irregularites_bp = Blueprint("irregularites", __name__)


@irregularites_bp.route("/etape/<int:id_controle_etape>", methods=["GET"])
def lister_irregularites_etape(id_controle_etape):
    irregularites = Irregularite.query.filter_by(id_controle_etape=id_controle_etape).all()
    return jsonify([_irregularite_en_dict(i) for i in irregularites])


@irregularites_bp.route("/controle/<int:id_controle>", methods=["GET"])
def lister_irregularites_controle(id_controle):
    """Toutes les irrégularités d'un contrôle, avec le libellé de l'étape concernée."""
    etapes = ControleEtape.query.filter_by(id_controle=id_controle).all()
    resultat = []
    for e in etapes:
        for i in Irregularite.query.filter_by(id_controle_etape=e.id).all():
            resultat.append({**_irregularite_en_dict(i), "libelle_etape": e.etape.libelle})
    return jsonify(resultat)


@irregularites_bp.route("", methods=["POST"])
def ajouter_irregularite():
    data = request.get_json()
    etape_cible = ControleEtape.query.get_or_404(data["id_controle_etape"])
    if etape_cible.controle.date_validation:
        return jsonify({"erreur": "Ce contrôle est validé : il n'est plus modifiable."}), 409
    if not data.get("description", "").strip():
        return jsonify({"erreur": "La description de l'irrégularité est obligatoire."}), 400
    irregularite = Irregularite(
        id_controle_etape=data["id_controle_etape"],
        description=data["description"],
        texte_applicable=data.get("texte_applicable"),
        risque=data.get("risque"),
        recommandation=data.get("recommandation"),
        impacte_attribution=data.get("impacte_attribution", False),
    )
    db.session.add(irregularite)
    db.session.commit()

    etape = ControleEtape.query.get(data["id_controle_etape"])
    recalculer_conclusion(etape.id_controle)

    return jsonify(_irregularite_en_dict(irregularite)), 201


@irregularites_bp.route("/<int:id_irregularite>", methods=["DELETE"])
def supprimer_irregularite(id_irregularite):
    irregularite = Irregularite.query.get_or_404(id_irregularite)
    etape = ControleEtape.query.get(irregularite.id_controle_etape)
    if etape.controle.date_validation:
        return jsonify({"erreur": "Ce contrôle est validé : il n'est plus modifiable."}), 409

    db.session.delete(irregularite)
    db.session.commit()
    recalculer_conclusion(etape.id_controle)
    return "", 204


def _irregularite_en_dict(i):
    return {
        "id": i.id, "id_controle_etape": i.id_controle_etape, "description": i.description,
        "texte_applicable": i.texte_applicable, "risque": i.risque,
        "recommandation": i.recommandation, "impacte_attribution": i.impacte_attribution,
    }
