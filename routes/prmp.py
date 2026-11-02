"""
Gestion des PRMP (Personne Responsable des Marchés Publics) : liste, ajout, modification,
suppression, rattachées à une entité.
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import func

from extensions import db
from models import Prmp, Entite, Marche

prmp_bp = Blueprint("prmp", __name__)


def nom_prmp_marche(marche):
    """Nom de la PRMP d'un marché : celle choisie sur le marché, sinon l'unique PRMP de l'entité."""
    if getattr(marche, "id_prmp", None):
        p = db.session.get(Prmp, marche.id_prmp)
        return p.nom if p else None
    candidates = Prmp.query.filter_by(id_entite=marche.id_entite).all()
    return candidates[0].nom if len(candidates) == 1 else None


def infos_prmp(marche):
    """À insérer dans les dictionnaires JSON d'un marché : {"id_prmp": ..., "prmp": nom}."""
    return {"id_prmp": getattr(marche, "id_prmp", None), "prmp": nom_prmp_marche(marche)}


def _en_dict(p):
    entite = db.session.get(Entite, p.id_entite)
    return {
        "id": p.id,
        "nom": p.nom,
        "id_entite": p.id_entite,
        "entite": entite.nom if entite else None,
        "nb_marches": Marche.query.filter_by(id_prmp=p.id).count(),
    }


@prmp_bp.route("/prmp", methods=["GET"])
def lister_prmp():
    """?id_entite=3 pour ne garder que les PRMP d'une entité (liste déroulante du formulaire marché)."""
    requete = Prmp.query.order_by(Prmp.nom)
    id_entite = request.args.get("id_entite", type=int)
    if id_entite:
        requete = requete.filter_by(id_entite=id_entite)
    return jsonify([_en_dict(p) for p in requete.all()])


@prmp_bp.route("/prmp/entites", methods=["GET"])
def entites_pour_prmp():
    """Liste des entités (id, nom) pour les listes déroulantes de l'écran PRMP."""
    return jsonify([{"id": e.id, "nom": e.nom} for e in Entite.query.order_by(Entite.nom).all()])


@prmp_bp.route("/prmp", methods=["POST"])
def creer_prmp():
    d = request.get_json() or {}
    nom = (d.get("nom") or "").strip()
    id_entite = d.get("id_entite")
    if not nom:
        return jsonify({"erreur": "Le nom de la PRMP est obligatoire."}), 400
    if not id_entite or not db.session.get(Entite, id_entite):
        return jsonify({"erreur": "Choisis une entité valide."}), 400
    if Prmp.query.filter(func.lower(Prmp.nom) == nom.lower(), Prmp.id_entite == id_entite).first():
        return jsonify({"erreur": "Cette PRMP existe déjà pour cette entité."}), 409
    p = Prmp(nom=nom, id_entite=id_entite)
    db.session.add(p)
    db.session.commit()
    return jsonify(_en_dict(p)), 201


@prmp_bp.route("/prmp/<int:id_prmp>", methods=["PUT"])
def modifier_prmp(id_prmp):
    p = db.get_or_404(Prmp, id_prmp)
    d = request.get_json() or {}
    nom = (d.get("nom") or "").strip()
    id_entite = d.get("id_entite", p.id_entite)
    if not nom:
        return jsonify({"erreur": "Le nom de la PRMP est obligatoire."}), 400
    if not db.session.get(Entite, id_entite):
        return jsonify({"erreur": "Choisis une entité valide."}), 400
    if id_entite != p.id_entite and Marche.query.filter_by(id_prmp=p.id).count():
        return jsonify({"erreur": "Cette PRMP est rattachée à des marchés : on ne peut pas la changer d'entité."}), 409
    doublon = Prmp.query.filter(func.lower(Prmp.nom) == nom.lower(), Prmp.id_entite == id_entite,
                                Prmp.id != p.id).first()
    if doublon:
        return jsonify({"erreur": "Cette PRMP existe déjà pour cette entité."}), 409
    p.nom, p.id_entite = nom, id_entite
    db.session.commit()
    return jsonify(_en_dict(p))


@prmp_bp.route("/prmp/<int:id_prmp>", methods=["DELETE"])
def supprimer_prmp(id_prmp):
    p = db.get_or_404(Prmp, id_prmp)
    nb = Marche.query.filter_by(id_prmp=p.id).count()
    if nb:
        return jsonify({"erreur": f"Suppression impossible : cette PRMP est rattachée à {nb} marché(s)."}), 409
    db.session.delete(p)
    db.session.commit()
    return jsonify({"ok": True})