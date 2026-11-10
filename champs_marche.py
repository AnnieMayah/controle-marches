"""
Informations générales complémentaires d'un marché (reprises de la grille de contrôle) :
numéro de saisie, direction/service, forme du contrat, montants min/max/TEF, forme du prix,
délai d'exécution, financement et dates de signature, d'approbation et de notification.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

TEXTES = ["numero_saisie", "direction_service", "delai_execution", "financement"]
MONTANTS = ["montant_min", "montant_max", "montant_tef"]
DATES = ["date_signature", "date_approbation", "date_notification"]
CHOIX = {"forme_contrat": ("QUANTITE_FIXE", "COMMANDES"), "forme_prix": ("UNITAIRE", "FORFAITAIRE")}
CHAMPS = TEXTES + MONTANTS + DATES + list(CHOIX)


def valider(data):
    """Message d'erreur si une information complémentaire est invalide, sinon None."""
    for champ, valeurs in CHOIX.items():
        v = data.get(champ)
        if v not in (None, "") and v not in valeurs:
            return f"Valeur invalide pour « {champ} »."
    nombres = {}
    for champ in MONTANTS:
        v = data.get(champ)
        if v in (None, ""):
            continue
        try:
            nombres[champ] = Decimal(str(v))
        except InvalidOperation:
            return f"Le champ « {champ} » doit être un nombre."
        if nombres[champ] < 0:
            return f"Le champ « {champ} » ne peut pas être négatif."
    if "montant_min" in nombres and "montant_max" in nombres and nombres["montant_min"] > nombres["montant_max"]:
        return "Le montant minimum ne peut pas dépasser le montant maximum."
    for champ in DATES:
        v = data.get(champ)
        if v in (None, ""):
            continue
        try:
            date.fromisoformat(str(v)[:10])
        except ValueError:
            return f"La date « {champ} » est invalide."
    return None


def _convertir(champ, v):
    if v in (None, ""):
        return None
    if champ in MONTANTS:
        return Decimal(str(v))
    if champ in DATES:
        return date.fromisoformat(str(v)[:10])
    return str(v).strip() or None


def appliquer(marche, data):
    """Copie sur le marché les informations complémentaires présentes dans data."""
    for champ in CHAMPS:
        if champ in data:
            setattr(marche, champ, _convertir(champ, data[champ]))


def infos_generales(m):
    """À insérer dans le JSON d'un marché."""
    def d(v): return v.isoformat() if v else None
    def n(v): return float(v) if v is not None else None
    return {c: (n(getattr(m, c, None)) if c in MONTANTS else d(getattr(m, c, None)) if c in DATES else getattr(m, c, None))
            for c in CHAMPS}
