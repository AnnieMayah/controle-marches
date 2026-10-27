"""
Authentification : connexion, création de compte avec code e-mail, mot de passe oublié,
gestion des comptes (administrateur).

Les codes à 6 chiffres sont stockés hachés, valables 10 minutes, limités à 5 essais,
à usage unique. Un compte créé via l'inscription reçoit le rôle INVITE (lecture seule) :
un administrateur peut ensuite lui attribuer un autre rôle.
"""
import json
import random
import re
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

import mailer
from extensions import db
from models import Utilisateur, CodeVerification

auth_bp = Blueprint("auth", __name__)

DUREE_CODE_MIN = 10
MAX_TENTATIVES = 5
DELAI_RENVOI_S = 60
ROLES = ["ADMIN", "COLLECTE", "VERIFICATION", "ANALYSE", "VALIDATION", "PCNM", "ENTITE", "INVITE"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ----------------------------------------------------------------- outils
def _valider_mot_de_passe(mdp):
    if len(mdp or "") < 8:
        return "Le mot de passe doit contenir au moins 8 caractères."
    if not re.search(r"[A-Za-z]", mdp) or not re.search(r"\d", mdp):
        return "Le mot de passe doit contenir au moins une lettre et un chiffre."
    return None


def _par_email(email):
    return Utilisateur.query.filter(func.lower(Utilisateur.email) == email).first()


def _attente_restante(email, objet):
    """Secondes à patienter avant un nouvel envoi (0 si autorisé)."""
    dernier = (CodeVerification.query.filter_by(email=email, objet=objet)
               .order_by(CodeVerification.id.desc()).first())
    if dernier:
        ecoule = (datetime.utcnow() - dernier.date_creation).total_seconds()
        if ecoule < DELAI_RENVOI_S:
            return int(DELAI_RENVOI_S - ecoule) + 1
    return 0


def _emettre_code(email, objet, donnees=None):
    """Génère, enregistre (haché) et envoie un code. Lève mailer.ErreurEnvoi si l'envoi échoue."""
    CodeVerification.query.filter(CodeVerification.expire_le < datetime.utcnow() - timedelta(days=1)).delete()
    CodeVerification.query.filter_by(email=email, objet=objet).delete()
    code = f"{random.SystemRandom().randint(0, 999999):06d}"
    enreg = CodeVerification(
        email=email, objet=objet, code_hash=generate_password_hash(code),
        donnees=json.dumps(donnees) if donnees else None,
        expire_le=datetime.utcnow() + timedelta(minutes=DUREE_CODE_MIN),
    )
    db.session.add(enreg)
    db.session.commit()
    try:
        mailer.envoyer_code(email, code, objet, DUREE_CODE_MIN)
    except mailer.ErreurEnvoi:
        db.session.delete(enreg)
        db.session.commit()
        raise


def _verifier_code(email, objet, code):
    """Retourne (enregistrement, None) si le code est bon, sinon (None, message d'erreur)."""
    enreg = (CodeVerification.query.filter_by(email=email, objet=objet, utilise=False)
             .order_by(CodeVerification.id.desc()).first())
    if not enreg:
        return None, "Aucun code en attente pour cette adresse. Demande un nouveau code."
    if enreg.expire_le < datetime.utcnow():
        return None, "Ce code a expiré. Demande un nouveau code."
    if not check_password_hash(enreg.code_hash, (code or "").strip()):
        enreg.tentatives += 1
        if enreg.tentatives >= MAX_TENTATIVES:
            enreg.utilise = True
        db.session.commit()
        restant = MAX_TENTATIVES - enreg.tentatives
        if restant <= 0:
            return None, "Code incorrect. Trop de tentatives : demande un nouveau code."
        return None, f"Code incorrect. Il te reste {restant} tentative{'s' if restant > 1 else ''}."
    return enreg, None


def _erreur_envoi(e):
    return jsonify({"erreur": "Impossible d'envoyer l'e-mail. Vérifie la configuration SMTP (config_mail.py). "
                              f"Détail : {e}"}), 502


def _utilisateur_en_dict(u):
    return {"id": u.id, "nom": u.nom, "prenom": u.prenom, "email": u.email, "login": u.login,
            "role": u.role, "actif": u.actif}


# ----------------------------------------------------------------- connexion
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    utilisateur = Utilisateur.query.filter_by(login=(data.get("login") or "").strip()).first()
    if not utilisateur or not check_password_hash(utilisateur.mot_de_passe_hash, data.get("mot_de_passe") or ""):
        return jsonify({"erreur": "Identifiants incorrects."}), 401
    if not utilisateur.actif:
        return jsonify({"erreur": "Ce compte est désactivé."}), 403
    return jsonify(_utilisateur_en_dict(utilisateur))


# ----------------------------------------------------------------- inscription (code par e-mail)
@auth_bp.route("/inscription", methods=["POST"])
def inscription():
    d = request.get_json() or {}
    nom, prenom = (d.get("nom") or "").strip(), (d.get("prenom") or "").strip()
    email, login_ = (d.get("email") or "").strip().lower(), (d.get("login") or "").strip()
    mdp = d.get("mot_de_passe") or ""

    if not nom or not login_:
        return jsonify({"erreur": "Le nom et l'identifiant sont obligatoires."}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"erreur": "Adresse e-mail invalide."}), 400
    if len(login_) < 3:
        return jsonify({"erreur": "L'identifiant doit contenir au moins 3 caractères."}), 400
    erreur = _valider_mot_de_passe(mdp)
    if erreur:
        return jsonify({"erreur": erreur}), 400
    if _par_email(email):
        return jsonify({"erreur": "Un compte existe déjà avec cette adresse e-mail."}), 409
    if Utilisateur.query.filter_by(login=login_).first():
        return jsonify({"erreur": "Cet identifiant est déjà utilisé."}), 409

    attente = _attente_restante(email, "INSCRIPTION")
    if attente:
        return jsonify({"erreur": f"Patiente {attente} s avant de demander un nouveau code."}), 429
    try:
        _emettre_code(email, "INSCRIPTION", {"nom": nom, "prenom": prenom, "login": login_,
                                              "mot_de_passe_hash": generate_password_hash(mdp)})
    except mailer.ErreurEnvoi as e:
        return _erreur_envoi(e)
    return jsonify({"ok": True, "email": email, "mode_dev": not mailer.smtp_configure()})


@auth_bp.route("/inscription/verifier", methods=["POST"])
def verifier_inscription():
    d = request.get_json() or {}
    email = (d.get("email") or "").strip().lower()
    enreg, erreur = _verifier_code(email, "INSCRIPTION", d.get("code"))
    if erreur:
        return jsonify({"erreur": erreur}), 400

    infos = json.loads(enreg.donnees)
    if _par_email(email) or Utilisateur.query.filter_by(login=infos["login"]).first():
        return jsonify({"erreur": "Ce compte (adresse ou identifiant) vient d'être créé par quelqu'un d'autre."}), 409

    utilisateur = Utilisateur(nom=infos["nom"], prenom=infos["prenom"], email=email, login=infos["login"],
                              mot_de_passe_hash=infos["mot_de_passe_hash"], role="INVITE")
    enreg.utilise = True
    db.session.add(utilisateur)
    db.session.commit()
    return jsonify(_utilisateur_en_dict(utilisateur)), 201


# ----------------------------------------------------------------- renvoi d'un code
@auth_bp.route("/code/renvoyer", methods=["POST"])
def renvoyer_code():
    d = request.get_json() or {}
    email, objet = (d.get("email") or "").strip().lower(), d.get("objet")
    if objet not in ("INSCRIPTION", "REINITIALISATION"):
        return jsonify({"erreur": "Type de code inconnu."}), 400
    reponse = {"ok": True, "email": email, "mode_dev": not mailer.smtp_configure()}

    attente = _attente_restante(email, objet)
    if objet == "INSCRIPTION":
        dernier = (CodeVerification.query.filter_by(email=email, objet=objet)
                   .order_by(CodeVerification.id.desc()).first())
        if not dernier or not dernier.donnees:
            return jsonify({"erreur": "Aucune inscription en cours pour cette adresse."}), 404
        if attente:
            return jsonify({"erreur": f"Patiente {attente} s avant de demander un nouveau code."}), 429
        try:
            _emettre_code(email, objet, json.loads(dernier.donnees))
        except mailer.ErreurEnvoi as e:
            return _erreur_envoi(e)
        return jsonify(reponse)

    # réinitialisation : réponse identique que le compte existe ou non
    utilisateur = _par_email(email)
    if utilisateur and utilisateur.actif:
        if attente:
            return jsonify({"erreur": f"Patiente {attente} s avant de demander un nouveau code."}), 429
        try:
            _emettre_code(email, objet)
        except mailer.ErreurEnvoi as e:
            return _erreur_envoi(e)
    return jsonify(reponse)


# ----------------------------------------------------------------- mot de passe oublié
@auth_bp.route("/mot-de-passe-oublie", methods=["POST"])
def mot_de_passe_oublie():
    email = ((request.get_json() or {}).get("email") or "").strip().lower()
    if not EMAIL_RE.match(email):
        return jsonify({"erreur": "Adresse e-mail invalide."}), 400

    utilisateur = _par_email(email)
    if utilisateur and utilisateur.actif and not _attente_restante(email, "REINITIALISATION"):
        try:
            _emettre_code(email, "REINITIALISATION")
        except mailer.ErreurEnvoi as e:
            return _erreur_envoi(e)
    # réponse volontairement identique si l'adresse n'existe pas (pas de fuite d'information)
    return jsonify({"ok": True, "email": email, "mode_dev": not mailer.smtp_configure()})


@auth_bp.route("/reinitialiser", methods=["POST"])
def reinitialiser():
    d = request.get_json() or {}
    email = (d.get("email") or "").strip().lower()
    erreur = _valider_mot_de_passe(d.get("nouveau"))
    if erreur:
        return jsonify({"erreur": erreur}), 400
    enreg, erreur = _verifier_code(email, "REINITIALISATION", d.get("code"))
    if erreur:
        return jsonify({"erreur": erreur}), 400
    utilisateur = _par_email(email)
    if not utilisateur or not utilisateur.actif:
        return jsonify({"erreur": "Compte introuvable ou désactivé."}), 400
    utilisateur.mot_de_passe_hash = generate_password_hash(d["nouveau"])
    enreg.utilise = True
    db.session.commit()
    return jsonify({"ok": True})


# ----------------------------------------------------------------- gestion des comptes
@auth_bp.route("/utilisateurs", methods=["GET"])
def lister_utilisateurs():
    return jsonify([_utilisateur_en_dict(u) for u in Utilisateur.query.order_by(Utilisateur.id).all()])


@auth_bp.route("/utilisateurs", methods=["POST"])
def creer_utilisateur():
    """Création d'un compte par un administrateur (sans vérification par e-mail)."""
    d = request.get_json() or {}
    nom, login_ = (d.get("nom") or "").strip(), (d.get("login") or "").strip()
    email = (d.get("email") or "").strip().lower() or None
    if not nom or not login_:
        return jsonify({"erreur": "Le nom et l'identifiant sont obligatoires."}), 400
    if email and not EMAIL_RE.match(email):
        return jsonify({"erreur": "Adresse e-mail invalide."}), 400
    if d.get("role") not in ROLES:
        return jsonify({"erreur": "Rôle invalide."}), 400
    erreur = _valider_mot_de_passe(d.get("mot_de_passe"))
    if erreur:
        return jsonify({"erreur": erreur}), 400
    if Utilisateur.query.filter_by(login=login_).first():
        return jsonify({"erreur": "Ce login est déjà utilisé."}), 409
    if email and _par_email(email):
        return jsonify({"erreur": "Cette adresse e-mail est déjà utilisée."}), 409

    utilisateur = Utilisateur(nom=nom, prenom=d.get("prenom"), email=email, login=login_, role=d["role"],
                              mot_de_passe_hash=generate_password_hash(d["mot_de_passe"]), id_entite=d.get("id_entite"))
    db.session.add(utilisateur)
    db.session.commit()
    return jsonify(_utilisateur_en_dict(utilisateur)), 201


@auth_bp.route("/mot-de-passe", methods=["PUT"])
def changer_mot_de_passe():
    d = request.get_json() or {}
    utilisateur = Utilisateur.query.get_or_404(d.get("id_utilisateur"))
    if not check_password_hash(utilisateur.mot_de_passe_hash, d.get("ancien") or ""):
        return jsonify({"erreur": "L'ancien mot de passe est incorrect."}), 400
    erreur = _valider_mot_de_passe(d.get("nouveau"))
    if erreur:
        return jsonify({"erreur": erreur}), 400
    utilisateur.mot_de_passe_hash = generate_password_hash(d["nouveau"])
    db.session.commit()
    return jsonify({"ok": True})


@auth_bp.route("/utilisateurs/<int:id_utilisateur>/actif", methods=["PUT"])
def basculer_actif(id_utilisateur):
    utilisateur = Utilisateur.query.get_or_404(id_utilisateur)
    utilisateur.actif = not utilisateur.actif
    db.session.commit()
    return jsonify(_utilisateur_en_dict(utilisateur))


@auth_bp.route("/utilisateurs/<int:id_utilisateur>/role", methods=["PUT"])
def changer_role(id_utilisateur):
    d = request.get_json() or {}
    if d.get("role") not in ROLES:
        return jsonify({"erreur": "Rôle invalide."}), 400
    if d.get("id_demandeur") == id_utilisateur:
        return jsonify({"erreur": "Tu ne peux pas modifier ton propre rôle."}), 400
    utilisateur = Utilisateur.query.get_or_404(id_utilisateur)
    utilisateur.role = d["role"]
    db.session.commit()
    return jsonify(_utilisateur_en_dict(utilisateur))
