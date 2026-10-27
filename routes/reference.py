"""
Routes API REST pour les référentiels (listes utilisées dans les menus
déroulants côté React) : natures de marché et modes de passation.
"""
from flask import Blueprint, jsonify
from models import NatureMarche, ModePassation

reference_bp = Blueprint("reference", __name__)


@reference_bp.route("/natures", methods=["GET"])
def lister_natures():
    natures = NatureMarche.query.all()
    return jsonify([{"id": n.id, "libelle": n.libelle} for n in natures])


@reference_bp.route("/modes-passation", methods=["GET"])
def lister_modes_passation():
    modes = ModePassation.query.all()
    return jsonify([{"id": m.id, "libelle": m.libelle} for m in modes])


@reference_bp.route("/etapes", methods=["GET"])
def lister_etapes():
    from models import Etape
    etapes = Etape.query.order_by(Etape.ordre).all()
    return jsonify([{"id": e.id, "libelle": e.libelle, "ordre": e.ordre} for e in etapes])


@reference_bp.route("/types-document", methods=["GET"])
def lister_types_document():
    from models import TypeDocument
    types = TypeDocument.query.all()
    return jsonify([{"id": t.id, "libelle": t.libelle} for t in types])
