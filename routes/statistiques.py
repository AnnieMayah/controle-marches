"""
Routes API REST pour le tableau de bord.
Les indicateurs de conformité ne comptent que les contrôles VALIDÉS (réalisés).
"""
from datetime import date, datetime
from collections import defaultdict
from flask import Blueprint, jsonify
from sqlalchemy import func
from extensions import db
from models import (Marche, NatureMarche, ModePassation, Controle, Entite, Irregularite)

statistiques_bp = Blueprint("statistiques", __name__)

MOIS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]


def _controles_valides():
    return Controle.query.filter(Controle.date_validation.isnot(None))


def _delta_pct(courant, precedent):
    """Variation en % ; None si pas de base de comparaison."""
    if precedent == 0:
        return None
    return round((courant - precedent) / precedent * 100)


def _mois_precedent(d):
    return (d.year - 1, 12) if d.month == 1 else (d.year, d.month - 1)


@statistiques_bp.route("/resume", methods=["GET"])
def resume():
    """Chiffres clés du tableau de bord."""
    aujourd_hui = date.today()
    mois_courant = (aujourd_hui.year, aujourd_hui.month)
    mois_prec = _mois_precedent(aujourd_hui)

    controles = Controle.query.all()
    valides = [c for c in controles if c.date_validation]

    planifies_courant = sum(1 for c in controles if c.date_controle and (c.date_controle.year, c.date_controle.month) == mois_courant)
    planifies_prec = sum(1 for c in controles if c.date_controle and (c.date_controle.year, c.date_controle.month) == mois_prec)
    realises_courant = sum(1 for c in valides if (c.date_validation.year, c.date_validation.month) == mois_courant)
    realises_prec = sum(1 for c in valides if (c.date_validation.year, c.date_validation.month) == mois_prec)

    total_irregularites = Irregularite.query.count()
    critiques = Irregularite.query.filter_by(impacte_attribution=True).count()
    entites_controlees = len({c.marche.id_entite for c in controles})

    return jsonify({
        "controles_planifies": len(controles),
        "controles_planifies_delta": _delta_pct(planifies_courant, planifies_prec),
        "controles_realises": len(valides),
        "controles_realises_delta": _delta_pct(realises_courant, realises_prec),
        "anomalies": total_irregularites,
        "anomalies_critiques": critiques,
        "entites_controlees": entites_controlees,
        "entites_total": Entite.query.count(),
    })


@statistiques_bp.route("/evolution", methods=["GET"])
def evolution():
    """Contrôles planifiés (créés) vs réalisés (validés) sur les 6 derniers mois."""
    aujourd_hui = date.today()
    mois = []
    y, m = aujourd_hui.year, aujourd_hui.month
    for _ in range(6):
        mois.append((y, m))
        y, m = _mois_precedent(date(y, m, 1))
    mois.reverse()

    planifies = defaultdict(int)
    realises = defaultdict(int)
    for c in Controle.query.all():
        if c.date_controle:
            planifies[(c.date_controle.year, c.date_controle.month)] += 1
        if c.date_validation:
            realises[(c.date_validation.year, c.date_validation.month)] += 1

    return jsonify([
        {"mois": MOIS[m - 1], "planifies": planifies[(y, m)], "realises": realises[(y, m)]}
        for (y, m) in mois
    ])


@statistiques_bp.route("/par-nature", methods=["GET"])
def stats_par_nature():
    resultats = (
        db.session.query(NatureMarche.libelle, func.count(Marche.id), func.coalesce(func.sum(Marche.montant), 0))
        .join(Marche, Marche.id_nature == NatureMarche.id)
        .group_by(NatureMarche.libelle).all()
    )
    return jsonify([{"nature": r[0], "nombre": r[1], "montant": float(r[2])} for r in resultats])


@statistiques_bp.route("/par-mode-passation", methods=["GET"])
def stats_par_mode_passation():
    resultats = (
        db.session.query(ModePassation.libelle, func.count(Marche.id), func.coalesce(func.sum(Marche.montant), 0))
        .join(Marche, Marche.id_mode_passation == ModePassation.id)
        .group_by(ModePassation.libelle).all()
    )
    return jsonify([{"mode_passation": r[0], "nombre": r[1], "montant": float(r[2])} for r in resultats])


@statistiques_bp.route("/taux-conformite", methods=["GET"])
def taux_conformite_global():
    valides = _controles_valides().all()
    total = len(valides)
    conformes = sum(1 for c in valides if c.conclusion == "CONFORME")
    return jsonify({
        "total_controles": total, "conformes": conformes, "non_conformes": total - conformes,
        "taux_conformite_pct": round(conformes / total * 100, 1) if total else 0,
    })


@statistiques_bp.route("/taux-conformite-par-entite", methods=["GET"])
def taux_conformite_par_entite():
    resultat = []
    for entite in Entite.query.all():
        valides = [c for c in _controles_valides().all() if c.marche.id_entite == entite.id]
        total = len(valides)
        if total == 0:
            continue  # on n'affiche que les entités déjà contrôlées
        conformes = sum(1 for c in valides if c.conclusion == "CONFORME")
        resultat.append({
            "entite": entite.nom, "total_controles": total, "conformes": conformes,
            "taux_conformite_pct": round(conformes / total * 100, 1),
        })
    return jsonify(resultat)
