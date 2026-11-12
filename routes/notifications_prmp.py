"""
Envoi du résultat d'un contrôle validé à la PRMP du marché, par e-mail,
avec le rapport PDF en pièce jointe.

- envoyer_resultat_controle(controle) : fonction réutilisable (appelée automatiquement
  à la validation depuis routes/controles.py, et par la route manuelle ci-dessous).
- POST /resultats/controle/<id>/envoyer : envoi (ou renvoi) manuel.
"""
from flask import Blueprint, jsonify

from extensions import db
from models import Controle, Marche, Prmp
from securite import role_requis
import courriel
from routes.rapports import _donnees_rapport, construire_pdf

notif_prmp_bp = Blueprint("notif_prmp", __name__)


def _prmp_du_marche(marche):
    """PRMP choisie sur le marché, sinon l'unique PRMP de l'entité."""
    if marche.id_prmp:
        return db.session.get(Prmp, marche.id_prmp)
    candidates = Prmp.query.filter_by(id_entite=marche.id_entite).all()
    return candidates[0] if len(candidates) == 1 else None


def _libelle_conclusion(controle):
    valeur = str(getattr(controle.conclusion, "value", controle.conclusion)).split(".")[-1].upper()
    return {"CONFORME": "conforme", "NON_CONFORME": "non conforme"}.get(valeur, "en cours")


def envoyer_resultat_controle(controle):
    """
    Envoie le résultat du contrôle à la PRMP du marché.
    Retourne (dictionnaire, code HTTP). Ne lève pas d'exception d'envoi.
    """
    marche = db.session.get(Marche, controle.id_marche)
    prmp = _prmp_du_marche(marche)
    if prmp is None:
        return {"ok": False, "erreur": "Ce marché n'a pas de PRMP : choisis-en une dans le formulaire du marché."}, 400
    if not prmp.email:
        return {"ok": False, "erreur": f"La PRMP « {prmp.nom} » n'a pas d'adresse e-mail (page PRMP)."}, 400

    corps = (f"Madame, Monsieur {prmp.nom},\n\n"
             f"Le contrôle a posteriori du marché {marche.reference} ({marche.objet}) est terminé.\n\n"
             f"Conclusion : procédure {_libelle_conclusion(controle)}\n\n"
             "La liste des irrégularités et anomalies constatées, avec les procédures applicables, "
             "est jointe à ce message.\n\nCordialement,\nCommission Régionale des Marchés")

    try:
        m, groupes, concl = _donnees_rapport(marche.id)
        pdf = construire_pdf(m, groupes, concl).read()
        envoye = courriel.envoyer(
            prmp.email,
            f"COMMISSION REGIONALE DU MARCHE - Résultat du contrôle a posteriori — marché {marche.reference}",
            corps,
            [(f"rapport_{marche.reference}.pdf", pdf, "application/pdf")],
        )
    except courriel.ErreurEnvoi as e:
        return {"ok": False, "erreur": f"Impossible d'envoyer l'e-mail. Vérifie config_mail.py. Détail : {e}"}, 502
    except Exception as e:  # erreur de génération du rapport, par exemple
        return {"ok": False, "erreur": f"Impossible de préparer l'e-mail : {e}"}, 500

    return {"ok": True, "destinataire": prmp.email, "mode_dev": not envoye}, 200


@notif_prmp_bp.route("/resultats/controle/<int:id_controle>/envoyer", methods=["POST"])
@role_requis("ADMIN", "VALIDATION", "PCNM")
def envoyer_resultat(id_controle):
    controle = db.get_or_404(Controle, id_controle)
    if controle.date_validation is None:
        return jsonify({"erreur": "Le contrôle doit être validé avant d'envoyer le résultat."}), 409
    resultat, code = envoyer_resultat_controle(controle)
    if not resultat.get("ok"):
        return jsonify({"erreur": resultat["erreur"]}), code
    return jsonify(resultat), code