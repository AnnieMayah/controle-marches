"""
Routes API REST pour les marchés — appelées par React.
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models import Marche
from collections import defaultdict
from models import Controle
from services import detecter_anomalies, calculer_score_risque

marches_bp = Blueprint("marches", __name__)


@marches_bp.route("", methods=["GET"])
def lister_marches():
    marches = Marche.query.all()
    return jsonify([_marche_en_dict(m) for m in marches])


@marches_bp.route("/risques", methods=["GET"])
def marches_a_risque():
    """
    Module de détection automatique : pour chaque marché, anomalies détectées par les règles métier
    et score de risque (0 à 7). Sert à prioriser les marchés à contrôler.
    """
    bilan = defaultdict(lambda: [0, 0])  # entité -> [contrôles validés, non conformes]
    dernier_controle = {}
    for c in Controle.query.order_by(Controle.id).all():
        dernier_controle[c.id_marche] = c
        if c.date_validation:
            bilan[c.marche.id_entite][0] += 1
            bilan[c.marche.id_entite][1] += 1 if c.conclusion != "CONFORME" else 0

    resultats = []
    for m in Marche.query.all():
        total, non_conformes = bilan[m.id_entite]
        anomalies = detecter_anomalies(m)
        score = calculer_score_risque(m, (non_conformes / total) if total else 0)
        points = score + len(anomalies)
        niveau = "Élevé" if points >= 5 else "Moyen" if points >= 3 else "Faible" if points >= 1 else "Aucun"
        c = dernier_controle.get(m.id)
        resultats.append({
            "id": m.id, "reference": m.reference, "objet": m.objet, "entite": m.entite.nom, "montant": float(m.montant),
            "score": score, "anomalies": anomalies, "niveau": niveau, "points": points,
            "id_controle": c.id if c else None, "controle_valide": bool(c and c.date_validation),
        })
    resultats.sort(key=lambda r: (-r["points"], -r["montant"]))
    return jsonify(resultats)


@marches_bp.route("/<int:id_marche>", methods=["GET"])
def obtenir_marche(id_marche):
    marche = Marche.query.get_or_404(id_marche)
    return jsonify(_marche_en_dict(marche))


@marches_bp.route("", methods=["POST"])
def creer_marche():
    data = request.get_json()
    erreur = _valider(data)
    if erreur:
        return jsonify({"erreur": erreur}), 400
    if Marche.query.filter_by(reference=data["reference"]).first():
        return jsonify({"erreur": "Un marché avec cette référence existe déjà."}), 409
    marche = Marche(
        reference=data["reference"], objet=data["objet"], id_entite=data["id_entite"],
        id_prmp=data.get("id_prmp"), id_nature=data["id_nature"],
        id_mode_passation=data["id_mode_passation"], montant=data["montant"],
        titulaire=data.get("titulaire"), annee_exercice=data["annee_exercice"],
        hors_ppm=data.get("hors_ppm", False), marche_regularisation=data.get("marche_regularisation", False),
    )
    db.session.add(marche)
    db.session.commit()
    return jsonify(_marche_en_dict(marche)), 201


@marches_bp.route("/<int:id_marche>", methods=["PUT"])
def modifier_marche(id_marche):
    marche = Marche.query.get_or_404(id_marche)
    data = request.get_json()
    erreur = _valider(data, partiel=True)
    if erreur:
        return jsonify({"erreur": erreur}), 400
    autre = Marche.query.filter_by(reference=data.get("reference", marche.reference)).first()
    if autre and autre.id != marche.id:
        return jsonify({"erreur": "Un marché avec cette référence existe déjà."}), 409
    for champ in ["reference", "objet", "id_entite", "id_prmp", "id_nature", "id_mode_passation",
                  "montant", "titulaire", "annee_exercice", "hors_ppm", "marche_regularisation"]:
        if champ in data:
            setattr(marche, champ, data[champ])
    db.session.commit()
    return jsonify(_marche_en_dict(marche))


@marches_bp.route("/<int:id_marche>", methods=["DELETE"])
def supprimer_marche(id_marche):
    marche = Marche.query.get_or_404(id_marche)
    db.session.delete(marche)
    db.session.commit()
    return "", 204


@marches_bp.route("/<int:id_marche>/anomalies", methods=["GET"])
def detecter_anomalies_marche(id_marche):
    marche = Marche.query.get_or_404(id_marche)
    suggestions = detecter_anomalies(marche)
    return jsonify({"id_marche": id_marche, "suggestions": suggestions})


def _valider(data, partiel=False):
    """Retourne un message d'erreur si les données sont invalides, sinon None."""
    if not partiel:
        for champ in ("reference", "objet", "id_entite", "id_nature", "id_mode_passation", "montant", "annee_exercice"):
            if data.get(champ) in (None, ""):
                return f"Le champ « {champ} » est obligatoire."
    if "montant" in data and float(data["montant"]) <= 0:
        return "Le montant doit être strictement positif."
    if "annee_exercice" in data and not (2000 <= int(data["annee_exercice"]) <= 2100):
        return "L'année d'exercice n'est pas valide."
    return None


def _marche_en_dict(m):
    return {
        "id": m.id, "reference": m.reference, "objet": m.objet, "montant": float(m.montant),
        "titulaire": m.titulaire, "annee_exercice": m.annee_exercice, "hors_ppm": m.hors_ppm,
        "marche_regularisation": m.marche_regularisation, "nature": m.nature.libelle,
        "mode_passation": m.mode_passation.libelle, "entite": m.entite.nom,
        "id_entite": m.id_entite, "id_nature": m.id_nature, "id_mode_passation": m.id_mode_passation,
    }
