"""
Objets de marché : liste fixe (lecture seule), chaque objet est lié à un compte budgétaire (ex. 6115).
Le compte d'un marché est celui de son objet ; il s'imprime dans les rapports PDF et Word.
"""
from flask import Blueprint, jsonify

from extensions import db
from models import ObjetMarche

objets_bp = Blueprint("objets", __name__)


def compte_marche(marche):
    """Compte du marché (celui de son objet), ou None pour un ancien marché sans objet choisi."""
    if getattr(marche, "id_objet", None):
        o = db.session.get(ObjetMarche, marche.id_objet)
        return o.compte if o else None
    return None


def infos_objet(marche):
    """À insérer dans le JSON d'un marché : {"id_objet": ..., "compte": ...}."""
    return {"id_objet": getattr(marche, "id_objet", None), "compte": compte_marche(marche)}


@objets_bp.route("/objets", methods=["GET"])
def lister_objets():
    return jsonify([{"id": o.id, "compte": o.compte, "libelle": o.libelle}
                    for o in ObjetMarche.query.order_by(ObjetMarche.compte, ObjetMarche.libelle).all()])