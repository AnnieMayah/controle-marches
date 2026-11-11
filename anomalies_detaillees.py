"""
Anomalies détectées automatiquement, avec l'étape concernée et le texte applicable.
Le tableau REGLES est le seul endroit à adapter : mot-clé cherché dans le message de detecter_anomalies,
étape de la procédure concernée, texte réglementaire à imprimer (à compléter avec les articles du Code des
marchés publics et des manuels de la CNM).
"""
from services import detecter_anomalies

REGLES = [
    ("hors ppm", "Planification", ""),
    ("non concurrentiel", "Planification", ""),
    ("pv d'ouverture", "Ouverture des plis", ""),
    ("ouverture des plis", "Ouverture des plis", ""),
    ("contrat", "Attribution", ""),
    ("régularisation", "Attribution", ""),
]


def detailler(message):
    t = message.lower().replace("’", "'")
    for mot, etape, texte in REGLES:
        if mot in t:
            return {"description": message, "etape": etape, "texte_applicable": texte}
    return {"description": message, "etape": None, "texte_applicable": ""}


def detecter_detaille(marche):
    return [detailler(m) for m in detecter_anomalies(marche)]
