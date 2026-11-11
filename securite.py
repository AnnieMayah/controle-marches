"""
Sécurité de l'API : jeton signé à la connexion, vérifié sur chaque route protégée.
Le jeton contient seulement l'identifiant de l'utilisateur ; le rôle est relu en base à chaque requête.
"""
from functools import wraps

from flask import request, jsonify, current_app, g
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from extensions import db
from models import Utilisateur

DUREE_JETON_S = 8 * 3600  # 8 heures

# routes accessibles sans être connecté (connexion, inscription, mot de passe oublié)
ROUTES_PUBLIQUES = {
    "/api/auth/login", "/api/auth/inscription", "/api/auth/inscription/verifier",
    "/api/auth/code/renvoyer", "/api/auth/mot-de-passe-oublie", "/api/auth/reinitialiser",
}


# Droits par rôle, identiques à ceux de utils/permissions.js (côté interface).
ROLES_DONNEES = ["ADMIN", "COLLECTE"]                      # entités, marchés, PRMP
ROLES_DOCUMENTS = ["ADMIN", "COLLECTE", "VERIFICATION"]    # pièces justificatives
ROLES_NOTER = ["ADMIN", "ANALYSE"]                         # contrôles, notes, constats, recommandations
ROLES_VALIDER = ["ADMIN", "PCNM", "VALIDATION"]            # validation finale d'un contrôle
METHODES_ECRITURE = {"POST", "PUT", "PATCH", "DELETE"}


def _roles_exiges(chemin, methode):
    """Rôles autorisés à MODIFIER la ressource, ou None si l'écriture est libre à tout utilisateur connecté.
    La lecture (GET) est ouverte à tout utilisateur connecté."""
    if methode not in METHODES_ECRITURE:
        return None
    if chemin.startswith("/api/controles"):
        return ROLES_VALIDER if "valid" in chemin else ROLES_NOTER
    regles = {
        "/api/marches": ROLES_DONNEES, "/api/entites": ROLES_DONNEES, "/api/prmp": ROLES_DONNEES,
        "/api/documents": ROLES_DOCUMENTS,
        "/api/irregularites": ROLES_NOTER, "/api/recommandations": ROLES_NOTER, "/api/preuves": ROLES_NOTER,
    }
    for prefixe, roles in regles.items():
        if chemin == prefixe or chemin.startswith(prefixe + "/"):
            return roles
    return None


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="jeton-acces")


def creer_jeton(utilisateur):
    return _serializer().dumps({"id": utilisateur.id})


def _lire_jeton():
    entete = request.headers.get("Authorization", "")
    if entete.startswith("Bearer "):
        return entete[7:].strip()
    return request.args.get("token")  # pour les liens de téléchargement (PDF, Word, fichiers)


def _authentifier():
    """Retourne (utilisateur, None) si le jeton est bon, sinon (None, réponse d'erreur)."""
    jeton = _lire_jeton()
    if not jeton:
        return None, (jsonify({"erreur": "Authentification requise."}), 401)
    try:
        donnees = _serializer().loads(jeton, max_age=DUREE_JETON_S)
    except SignatureExpired:
        return None, (jsonify({"erreur": "Session expirée, reconnecte-toi."}), 401)
    except BadSignature:
        return None, (jsonify({"erreur": "Jeton invalide."}), 401)
    utilisateur = db.session.get(Utilisateur, donnees.get("id"))
    if not utilisateur or not utilisateur.actif:
        return None, (jsonify({"erreur": "Compte introuvable ou désactivé."}), 401)
    return utilisateur, None


def connexion_requise(f):
    @wraps(f)
    def enveloppe(*args, **kwargs):
        utilisateur, erreur = _authentifier()
        if erreur:
            return erreur
        g.utilisateur = utilisateur
        return f(*args, **kwargs)
    return enveloppe


def role_requis(*roles):
    """@role_requis("ADMIN", "COLLECTE") : accès réservé à ces rôles."""
    def decorateur(f):
        @connexion_requise
        @wraps(f)
        def enveloppe(*args, **kwargs):
            role = getattr(g.utilisateur.role, "value", g.utilisateur.role)
            if role not in roles:
                return jsonify({"erreur": "Accès refusé : droits insuffisants."}), 403
            return f(*args, **kwargs)
        return enveloppe
    return decorateur


def proteger_api(app, prefixe="/api"):
    """Exige un jeton valide sur TOUTES les routes de l'API (sauf connexion/inscription)
    et applique les droits par rôle sur les routes qui modifient des données."""
    @app.before_request
    def exiger_jeton():
        if request.method == "OPTIONS" or not request.path.startswith(prefixe):
            return None
        if request.path in ROUTES_PUBLIQUES:
            return None
        utilisateur, erreur = _authentifier()
        if erreur:
            return erreur
        g.utilisateur = utilisateur
        roles = _roles_exiges(request.path, request.method)
        role = getattr(utilisateur.role, "value", utilisateur.role)
        if roles is not None and role not in roles:
            return jsonify({"erreur": "Accès refusé : droits insuffisants."}), 403
        return None


def peut_voir_entite(id_entite):
    """Un utilisateur de rôle ENTITE ne voit que les données de sa propre entité ; les autres rôles voient tout."""
    u = getattr(g, "utilisateur", None)
    if u is None:
        return True
    if getattr(u.role, "value", u.role) != "ENTITE":
        return True
    return getattr(u, "id_entite", None) == id_entite
