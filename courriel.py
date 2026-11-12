"""
Envoi d'e-mails par SMTP (avec pièces jointes).

Lit la configuration dans config_mail.py (à la racine du projet) :
    SMTP_HOST, SMTP_PORT, SMTP_SECURITE ("starttls", "ssl" ou "aucune"),
    SMTP_UTILISATEUR, SMTP_MOT_DE_PASSE, SMTP_EXPEDITEUR (facultatif).

Si config_mail.py est absent ou incomplet : mode développement.
Rien n'est envoyé, le message est affiché dans la console et envoyer() renvoie False.
"""
import smtplib
import ssl
from email.message import EmailMessage


class ErreurEnvoi(Exception):
    """Levée quand le serveur de messagerie refuse ou n'est pas joignable."""


def _config():
    try:
        import config_mail as c
    except ImportError:
        return None
    hote = getattr(c, "SMTP_HOST", None)
    utilisateur = getattr(c, "SMTP_UTILISATEUR", None)
    mot_de_passe = getattr(c, "SMTP_MOT_DE_PASSE", None)
    if not (hote and utilisateur and mot_de_passe):
        return None
    return {
        "hote": hote,
        "port": int(getattr(c, "SMTP_PORT", 587)),
        "securite": (getattr(c, "SMTP_SECURITE", "starttls") or "starttls").lower(),
        "utilisateur": utilisateur,
        "mot_de_passe": mot_de_passe,
        "expediteur": getattr(c, "SMTP_EXPEDITEUR", "") or utilisateur,
    }


def envoyer(destinataire, sujet, corps, pieces_jointes=None):
    """
    Envoie un e-mail. pieces_jointes : liste de (nom_fichier, octets, type_mime).
    Retourne True si envoyé, False en mode développement (rien n'est envoyé).
    Lève ErreurEnvoi en cas d'échec.
    """
    cfg = _config()
    if cfg is None:
        print(f"[MODE DEV] E-mail non envoyé -> {destinataire} | {sujet}\n{corps}")
        return False

    msg = EmailMessage()
    msg["From"] = cfg["expediteur"]
    msg["To"] = destinataire
    msg["Subject"] = sujet
    msg.set_content(corps)
    for nom, octets, mime in (pieces_jointes or []):
        type_principal, _, sous_type = mime.partition("/")
        msg.add_attachment(octets, maintype=type_principal, subtype=sous_type or "octet-stream", filename=nom)

    try:
        if cfg["securite"] == "ssl":
            serveur = smtplib.SMTP_SSL(cfg["hote"], cfg["port"], timeout=20, context=ssl.create_default_context())
        else:
            serveur = smtplib.SMTP(cfg["hote"], cfg["port"], timeout=20)
        with serveur:
            if cfg["securite"] == "starttls":
                serveur.starttls(context=ssl.create_default_context())
            serveur.login(cfg["utilisateur"], cfg["mot_de_passe"])
            serveur.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        raise ErreurEnvoi(str(e)) from e
    return True