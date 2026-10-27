"""
Routes API REST pour les documents justificatifs liés à un marché.
Gère le vrai upload de fichier (multipart/form-data), stocké sur disque.
"""
import os
import uuid
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from extensions import db
from models import Document, TypeDocument

documents_bp = Blueprint("documents", __name__)


@documents_bp.route("/marche/<int:id_marche>", methods=["GET"])
def lister_documents_marche(id_marche):
    documents = Document.query.filter_by(id_marche=id_marche).all()
    return jsonify([_document_en_dict(d) for d in documents])


@documents_bp.route("/upload", methods=["POST"])
def uploader_document():
    """
    Reçoit un fichier réel (multipart/form-data) + ses métadonnées,
    l'enregistre sur disque dans UPLOAD_FOLDER, et crée la ligne en base.
    Champs attendus (form-data) : fichier, id_marche, id_type_document
    """
    if "fichier" not in request.files:
        return jsonify({"erreur": "Aucun fichier reçu (champ 'fichier' manquant)."}), 400

    fichier = request.files["fichier"]
    id_marche = request.form.get("id_marche", type=int)
    id_type_document = request.form.get("id_type_document", type=int)

    if not id_marche or not id_type_document:
        return jsonify({"erreur": "id_marche et id_type_document sont requis."}), 400

    nom_original = secure_filename(fichier.filename)
    nom_stocke = f"{uuid.uuid4().hex}_{nom_original}"  # évite les collisions de noms
    chemin_complet = os.path.join(current_app.config["UPLOAD_FOLDER"], nom_stocke)
    fichier.save(chemin_complet)
    taille_ko = os.path.getsize(chemin_complet) // 1024

    document = Document(
        id_marche=id_marche,
        id_type_document=id_type_document,
        nom_fichier=nom_original,
        chemin_fichier=nom_stocke,
        taille_ko=taille_ko,
    )
    db.session.add(document)
    db.session.commit()
    return jsonify(_document_en_dict(document)), 201


@documents_bp.route("/fichier/<path:nom_stocke>", methods=["GET"])
def telecharger_fichier(nom_stocke):
    """Sert le fichier stocké (pour le visualiser/télécharger depuis React)."""
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], nom_stocke)


@documents_bp.route("/<int:id_document>", methods=["DELETE"])
def supprimer_document(id_document):
    document = Document.query.get_or_404(id_document)
    chemin_complet = os.path.join(current_app.config["UPLOAD_FOLDER"], document.chemin_fichier)
    if os.path.exists(chemin_complet):
        os.remove(chemin_complet)
    db.session.delete(document)
    db.session.commit()
    return "", 204


@documents_bp.route("/marche/<int:id_marche>/completude", methods=["GET"])
def verifier_completude(id_marche):
    """Compare les documents fournis à la liste des types attendus."""
    tous_les_types = TypeDocument.query.all()
    fournis = {d.id_type_document for d in Document.query.filter_by(id_marche=id_marche).all()}
    manquants = [t.libelle for t in tous_les_types if t.id not in fournis and t.libelle != "PV de carence"]
    return jsonify({"id_marche": id_marche, "complet": len(manquants) == 0, "pieces_manquantes": manquants})



@documents_bp.route("/<int:id_document>", methods=["PUT"])
def modifier_document(id_document):
    """Modifie uniquement le type de document associé (pas le fichier lui-même)."""
    document = Document.query.get_or_404(id_document)
    data = request.get_json()
    document.id_type_document = data["id_type_document"]
    db.session.commit()
    return jsonify(_document_en_dict(document))


def _document_en_dict(d):
    return {
        "id": d.id,
        "id_marche": d.id_marche,
        "type_document": d.type_document.libelle,
        "nom_fichier": d.nom_fichier,
        "chemin_fichier": d.chemin_fichier,
        "taille_ko": d.taille_ko,
        "date_upload": d.date_upload.isoformat(),
    }
