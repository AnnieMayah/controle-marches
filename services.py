"""
Logique métier : calcul de conformité et détection d'irrégularités par règles.
Équivalent Python/Flask de ControleService.java et DetectionIrregulariteService.java
"""
from datetime import datetime
from extensions import db
from models import Controle, ControleEtape, Irregularite, Document

SEUIL_CONFORMITE = 2
# Seuils indicatifs — À ADAPTER selon les vrais seuils du Code des marchés publics
SEUIL_APPEL_OFFRES_OUVERT = 50_000_000
SEUIL_RISQUE_MONTANT = 30_000_000


def recalculer_conclusion(id_controle):
    """
    Recalcule la note globale et la conclusion d'un contrôle.
    - note_globale = moyenne des notes des étapes déjà saisies
    - conclusion = CONFORME si moyenne >= 2
    - MAIS non-conforme automatique si : hors PPM, marché de régularisation,
      ou une irrégularité liée impacte l'attribution du marché
    """
    controle = Controle.query.get_or_404(id_controle)
    etapes = ControleEtape.query.filter_by(id_controle=id_controle).all()

    notes = [e.note for e in etapes if e.note is not None]
    note_globale = round(sum(notes) / len(notes), 2) if notes else None
    controle.note_globale = note_globale

    if _est_disqualifie_automatiquement(controle, etapes):
        controle.conclusion = "NON_CONFORME"
    elif note_globale is not None and note_globale >= SEUIL_CONFORMITE:
        controle.conclusion = "CONFORME"
    else:
        controle.conclusion = "NON_CONFORME"

    db.session.commit()
    return controle


def _est_disqualifie_automatiquement(controle, etapes):
    marche = controle.marche

    if marche.hors_ppm:
        return True
    if marche.marche_regularisation:
        return True

    for etape in etapes:
        irregularites = Irregularite.query.filter_by(id_controle_etape=etape.id).all()
        if any(irr.impacte_attribution for irr in irregularites):
            return True
    return False


def valider_controle(id_controle, id_utilisateur_validateur):
    """Verrouille le contrôle une fois validé par un utilisateur de rôle PCNM."""
    controle = recalculer_conclusion(id_controle)
    controle.id_utilisateur_validateur = id_utilisateur_validateur
    controle.date_validation = datetime.utcnow()
    db.session.commit()
    return controle


def detecter_anomalies(marche):
    """
    Analyse un marché et retourne une liste de suggestions d'irrégularités.
    Système de règles métier — reste à valider par le contrôleur (Membre/CC).
    """
    suggestions = []

    mode = marche.mode_passation.libelle
    mode_non_concurrentiel = mode.lower() in ("gré à gré", "achat direct")

    if mode_non_concurrentiel and float(marche.montant) > SEUIL_APPEL_OFFRES_OUVERT:
        suggestions.append(
            f"Montant ({marche.montant} Ar) élevé pour un mode de passation non concurrentiel "
            f"({mode}) — vérifier la justification du choix du mode de passation."
        )

    if marche.hors_ppm:
        suggestions.append("Marché hors Plan de Passation des Marchés (PPM) — non-conformité automatique.")

    if marche.marche_regularisation:
        suggestions.append("Marché de régularisation — non-conformité automatique.")

    documents = Document.query.filter_by(id_marche=marche.id).all()
    libelles = [d.type_document.libelle.lower() for d in documents]

    if not any("contrat" in lib for lib in libelles):
        suggestions.append("Contrat manquant au dossier — pièce essentielle non fournie.")
    if not any("ouverture des plis" in lib for lib in libelles):
        suggestions.append("PV d'ouverture des plis manquant — pièce essentielle non fournie.")

    return suggestions


def calculer_score_risque(marche, taux_non_conformite_entite):
    """
    Score de risque (0 à 7) pour prioriser quels marchés contrôler en priorité.
    """
    score = 0
    mode = marche.mode_passation.libelle
    mode_non_concurrentiel = mode.lower() in ("gré à gré", "achat direct")

    if mode_non_concurrentiel and float(marche.montant) > SEUIL_RISQUE_MONTANT:
        score += 3
    if marche.hors_ppm:
        score += 2
    if taux_non_conformite_entite > 0.5:
        score += 2
    return score
