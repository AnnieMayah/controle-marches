"""Envoi des e-mails de vérification (SMTP). Sans configuration : mode développement (code affiché en console)."""
import os
import smtplib
import ssl
from email.message import EmailMessage

try:
    import config_mail as _cfg
except ImportError:  # fichier absent : on se rabat sur les variables d'environnement
    _cfg = None


class ErreurEnvoi(Exception):
    """Échec d'envoi de l'e-mail (serveur SMTP injoignable, identifiants refusés…)."""


def _param(nom, defaut=""):
    valeur = os.environ.get(nom)
    if valeur not in (None, ""):
        return valeur
    return getattr(_cfg, nom, defaut) if _cfg else defaut


def smtp_configure():
    return bool(_param("SMTP_HOST"))


def envoyer_code(destinataire, code, objet, duree_min):
    """Envoie le code. Retourne True si un e-mail est parti, False en mode développement."""
    if objet == "INSCRIPTION":
        sujet = "Votre code de vérification — création de compte"
        phrase = "Pour finaliser la création de votre compte, saisissez ce code de vérification :"
    else:
        sujet = "Votre code de réinitialisation de mot de passe"
        phrase = "Pour réinitialiser votre mot de passe, saisissez ce code de vérification :"
    texte = (f"Bonjour,\n\n{phrase}\n\n    {code}\n\n"
             f"Ce code est valable {duree_min} minutes et ne peut être utilisé qu'une seule fois.\n"
             "Si vous n'êtes pas à l'origine de cette demande, ignorez simplement ce message.\n\n"
             "— Contrôle a posteriori des marchés publics")

    if not smtp_configure():
        print("\n" + "=" * 62)
        print("[MODE DÉVELOPPEMENT — aucun serveur e-mail configuré]")
        print(f"Code de vérification pour {destinataire} : {code}   (valable {duree_min} min)")
        print("=" * 62 + "\n", flush=True)
        return False

    utilisateur = _param("SMTP_UTILISATEUR")
    message = EmailMessage()
    message["Subject"] = sujet
    message["From"] = _param("SMTP_EXPEDITEUR") or utilisateur or "no-reply@localhost"
    message["To"] = destinataire
    message.set_content(texte)

    try:
        hote, port = _param("SMTP_HOST"), int(_param("SMTP_PORT", 587))
        securite = str(_param("SMTP_SECURITE", "starttls")).lower()
        if securite == "ssl":
            serveur = smtplib.SMTP_SSL(hote, port, timeout=20, context=ssl.create_default_context())
        else:
            serveur = smtplib.SMTP(hote, port, timeout=20)
        with serveur:
            if securite == "starttls":
                serveur.starttls(context=ssl.create_default_context())
            if utilisateur:
                serveur.login(utilisateur, _param("SMTP_MOT_DE_PASSE"))
            serveur.send_message(message)
    except (smtplib.SMTPException, OSError) as e:
        raise ErreurEnvoi(str(e)) from e
    return True
