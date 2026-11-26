"""
Configuration de l'envoi des e-mails (codes de vérification).

"""
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_SECURITE = "starttls"      # "starttls" (port 587), "ssl" (port 465) ou "aucune"
SMTP_UTILISATEUR = "secretariatcrmhm@gmail.com"
SMTP_MOT_DE_PASSE = "wlmp mhgo bfdi kbrv"
SMTP_EXPEDITEUR = "secretariatcrmhm@gmail.com"            # adresse affichée ; par défaut = SMTP_UTILISATEUR
