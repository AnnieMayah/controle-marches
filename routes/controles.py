"""
Routes API REST pour les contrôles — liste, détail, notation par étape, validation.
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models import Controle, ControleEtape, Etape, Marche
from services import recalculer_conclusion, valider_controle

controles_bp = Blueprint("controles", __name__)


@controles_bp.route("", methods=["GET"])
def lister_controles():
    """Liste des contrôles (plus récents d'abord). Filtres : ?id_marche=3&limit=5"""
    id_marche = request.args.get("id_marche", type=int)
    limit = request.args.get("limit", type=int)
    query = Controle.query
    if id_marche:
        query = query.filter_by(id_marche=id_marche)
    query = query.order_by(Controle.id.desc())
    if limit:
        query = query.limit(limit)
    return jsonify([_controle_resume(c) for c in query.all()])


@controles_bp.route("/<int:id_controle>", methods=["GET"])
def obtenir_controle(id_controle):
    controle = Controle.query.get_or_404(id_controle)
    etapes = ControleEtape.query.filter_by(id_controle=id_controle).all()
    return jsonify({
        **_controle_resume(controle),
        "marche": _marche_resume(controle.marche),
        "etapes_notees": [
            {"id": e.id, "id_etape": e.id_etape, "libelle_etape": e.etape.libelle,
             "note": e.note, "observations": e.observations}
            for e in etapes
        ],
    })


@controles_bp.route("", methods=["POST"])
def creer_controle():
    """Crée un contrôle pour un marché (ou renvoie celui déjà en cours s'il existe)."""
    data = request.get_json()
    id_marche = data["id_marche"]
    Marche.query.get_or_404(id_marche)

    existant = Controle.query.filter_by(id_marche=id_marche, date_validation=None).first()
    if existant:
        return jsonify(_controle_resume(existant)), 200

    controle = Controle(id_marche=id_marche)
    db.session.add(controle)
    db.session.commit()
    return jsonify(_controle_resume(controle)), 201


@controles_bp.route("/<int:id_controle>/etapes", methods=["POST"])
def saisir_note_etape(id_controle):
    """Saisie ou mise à jour de la note (0-4) et des observations pour une étape."""
    controle = Controle.query.get_or_404(id_controle)
    if controle.date_validation:
        return jsonify({"erreur": "Ce contrôle est validé : il n'est plus modifiable."}), 409

    data = request.get_json()
    note = data.get("note")
    if note is None or not (0 <= int(note) <= 4):
        return jsonify({"erreur": "La note doit être comprise entre 0 et 4."}), 400

    id_etape = data["id_etape"]
    etape = ControleEtape.query.filter_by(id_controle=id_controle, id_etape=id_etape).first()
    if etape is None:
        etape = ControleEtape(id_controle=id_controle, id_etape=id_etape)
        db.session.add(etape)

    etape.note = int(note)
    etape.observations = data.get("observations")
    etape.id_utilisateur = data.get("id_utilisateur")
    db.session.commit()

    controle = recalculer_conclusion(id_controle)
    return jsonify(_controle_resume(controle)), 201


@controles_bp.route("/<int:id_controle>/valider", methods=["POST"])
def valider(id_controle):
    """Validation finale (PCNM) — exige que toutes les étapes soient notées."""
    controle = Controle.query.get_or_404(id_controle)
    if controle.date_validation:
        return jsonify({"erreur": "Ce contrôle est déjà validé."}), 409

    total_etapes = Etape.query.count()
    notees = ControleEtape.query.filter(
        ControleEtape.id_controle == id_controle, ControleEtape.note.isnot(None)
    ).count()
    if notees < total_etapes:
        return jsonify({"erreur": f"Toutes les étapes doivent être notées avant validation ({notees}/{total_etapes})."}), 400

    data = request.get_json()
    controle = valider_controle(id_controle, data["id_utilisateur_validateur"])
    return jsonify(_controle_resume(controle))


def _controle_resume(c):
    notees = ControleEtape.query.filter(
        ControleEtape.id_controle == c.id, ControleEtape.note.isnot(None)
    ).count()
    return {
        "id": c.id,
        "reference": f"CTRL-{c.id:04d}",
        "id_marche": c.id_marche,
        "reference_marche": c.marche.reference,
        "entite": c.marche.entite.nom,
        "nature": c.marche.nature.libelle,
        "date_controle": c.date_controle.isoformat() if c.date_controle else None,
        "note_globale": float(c.note_globale) if c.note_globale is not None else None,
        "conclusion": c.conclusion,
        "nb_etapes_notees": notees,
        "valide": c.date_validation is not None,
        "date_validation": c.date_validation.isoformat() if c.date_validation else None,
    }


def _marche_resume(m):
    return {
        "id": m.id, "reference": m.reference, "objet": m.objet, "entite": m.entite.nom,
        "nature": m.nature.libelle, "mode_passation": m.mode_passation.libelle,
        "montant": float(m.montant), "titulaire": m.titulaire,
        "annee_exercice": m.annee_exercice, "hors_ppm": m.hors_ppm,
        "marche_regularisation": m.marche_regularisation,
    }
