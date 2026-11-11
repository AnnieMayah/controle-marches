"""
Pièces justificatives liées à une irrégularité (table documents_irregularites).
Les requêtes sont écrites en SQL direct : aucune classe supplémentaire n'est nécessaire dans models.py.
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import text

from extensions import db

preuves_bp = Blueprint("preuves", __name__)

_CONTEXTE = text("""SELECT c.id_marche, c.date_validation
                    FROM irregularites i
                    JOIN controle_etapes ce ON ce.id = i.id_controle_etape
                    JOIN controles c ON c.id = ce.id_controle
                    WHERE i.id = :i""")


def noms_pieces(id_irregularite):
    """Noms des fichiers liés à une irrégularité (pour le rapport)."""
    lignes = db.session.execute(text("""SELECT d.nom_fichier FROM documents d
                                        JOIN documents_irregularites di ON di.id_document = d.id
                                        WHERE di.id_irregularite = :i ORDER BY d.id"""), {"i": id_irregularite})
    return [r[0] for r in lignes]


@preuves_bp.route("/preuves/irregularite/<int:id_irregularite>", methods=["GET"])
def lire(id_irregularite):
    lignes = db.session.execute(text("SELECT id_document FROM documents_irregularites WHERE id_irregularite = :i"),
                                {"i": id_irregularite})
    return jsonify({"ids_documents": [r[0] for r in lignes]})


@preuves_bp.route("/preuves/irregularite/<int:id_irregularite>", methods=["PUT"])
def remplacer(id_irregularite):
    ctx = db.session.execute(_CONTEXTE, {"i": id_irregularite}).first()
    if ctx is None:
        return jsonify({"erreur": "Constat introuvable."}), 404
    id_marche, date_validation = ctx
    if date_validation is not None:
        return jsonify({"erreur": "Ce contrôle est validé : il n'est plus modifiable."}), 409
    try:
        ids = sorted({int(x) for x in (request.get_json() or {}).get("ids_documents", [])})
    except (TypeError, ValueError):
        return jsonify({"erreur": "Liste de documents invalide."}), 400
    for id_doc in ids:
        ok = db.session.execute(text("SELECT 1 FROM documents WHERE id = :d AND id_marche = :m"),
                                {"d": id_doc, "m": id_marche}).first()
        if not ok:
            return jsonify({"erreur": "Un document ne correspond pas à ce marché."}), 400
    db.session.execute(text("DELETE FROM documents_irregularites WHERE id_irregularite = :i"), {"i": id_irregularite})
    for id_doc in ids:
        db.session.execute(text("INSERT INTO documents_irregularites (id_document, id_irregularite) VALUES (:d, :i)"),
                           {"d": id_doc, "i": id_irregularite})
    db.session.commit()
    return jsonify({"ids_documents": ids})
