"""
Fil d'activité récent (affiché dans la cloche de notifications).
Calculé à partir des données existantes — pas de table dédiée.
"""
from flask import Blueprint, jsonify
from models import Controle, Document, Recommandation, Marche

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("", methods=["GET"])
def lister_notifications():
    evenements = []

    for c in Controle.query.filter(Controle.date_validation.isnot(None)).all():
        niveau = "succes" if c.conclusion == "CONFORME" else "alerte"
        evenements.append({
            "date": c.date_validation.isoformat(),
            "niveau": niveau,
            "texte": f"Contrôle CTRL-{c.id:04d} validé : {c.conclusion.replace('_', ' ').lower()}",
        })

    for d in Document.query.all():
        evenements.append({
            "date": d.date_upload.isoformat(), "niveau": "info",
            "texte": f"Document « {d.nom_fichier} » ajouté ({d.type_document.libelle})",
        })

    for m in Marche.query.filter_by(hors_ppm=True).all():
        evenements.append({
            "date": m.date_creation.isoformat(), "niveau": "alerte",
            "texte": f"Marché {m.reference} hors PPM : non-conformité automatique",
        })

    for r in Recommandation.query.all():
        evenements.append({
            "date": f"{r.date_emission.isoformat()}T00:00:00", "niveau": "info",
            "texte": f"Recommandation émise ({r.statut.lower().replace('_', ' ')})",
        })

    evenements.sort(key=lambda e: e["date"], reverse=True)
    return jsonify(evenements[:12])
