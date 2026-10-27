"""
Recherche globale (barre du haut) : marchés, entités et contrôles en une seule requête.
"""
from flask import Blueprint, request, jsonify
from models import Marche, Entite, Controle

recherche_bp = Blueprint("recherche", __name__)


@recherche_bp.route("", methods=["GET"])
def rechercher():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify({"marches": [], "entites": [], "controles": []})

    motif = f"%{q}%"
    marches = Marche.query.filter(
        (Marche.reference.ilike(motif)) | (Marche.objet.ilike(motif)) | (Marche.titulaire.ilike(motif))
    ).limit(8).all()
    entites = Entite.query.filter(Entite.nom.ilike(motif)).limit(8).all()

    # contrôles : par numéro (« CTRL-0003 » ou « 3 ») ou via la référence / l'entité du marché
    chiffres = "".join(ch for ch in q if ch.isdigit())
    controles = Controle.query.join(Marche, Controle.id_marche == Marche.id).join(Entite, Marche.id_entite == Entite.id).filter(
        (Marche.reference.ilike(motif)) | (Entite.nom.ilike(motif)) |
        ((Controle.id == int(chiffres)) if chiffres and q.upper().startswith(("CTRL", "#")) or q.isdigit() else False)
    ).limit(8).all()

    return jsonify({
        "marches": [{"id": m.id, "reference": m.reference, "objet": m.objet} for m in marches],
        "entites": [{"id": e.id, "nom": e.nom, "type": e.type} for e in entites],
        "controles": [{"id": c.id, "reference": f"CTRL-{c.id:04d}", "reference_marche": c.marche.reference,
                       "entite": c.marche.entite.nom} for c in controles],
    })
