import smtplib, ssl
import config_mail as c

mdp = c.SMTP_MOT_DE_PASSE.replace(" ", "")
print("Hôte :", c.SMTP_HOST, "| port :", c.SMTP_PORT, "| sécurité :", c.SMTP_SECURITE)
try:
    if c.SMTP_SECURITE == "ssl":
        s = smtplib.SMTP_SSL(c.SMTP_HOST, c.SMTP_PORT, timeout=20)
    else:
        s = smtplib.SMTP(c.SMTP_HOST, c.SMTP_PORT, timeout=20)
    s.set_debuglevel(1)
    if c.SMTP_SECURITE == "starttls":
        s.starttls(context=ssl.create_default_context())
    s.login(c.SMTP_UTILISATEUR, mdp)
    print("Identification OK")
    s.quit()
except Exception as e:
    print("ÉCHEC :", type(e).__name__, e)