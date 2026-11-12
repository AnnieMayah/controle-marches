"""
Point d'entrée Flask — configuration et enregistrement des routes.
"""
import os
from flask import Flask
from flask_cors import CORS
from extensions import db
from securite import proteger_api


def create_app(config=None):
    app = Flask(__name__)
    CORS(app)  # autorise les appels depuis React (ex: http://localhost:5173)
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY manquante : définis la variable d'environnement.")
    app.config["SECRET_KEY"] = secret
    try:
        from config_db import DATABASE_URI
    except ImportError:
        raise RuntimeError("config_db.py manquant : crée-le avec DATABASE_URI.")
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Dossier où sont stockés les fichiers uploadés (DAO, PV, contrats...)
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    if config:
        app.config.update(config)  # surcharge possible (tests)

    db.init_app(app)

    # crée la table des codes de vérification si elle n'existe pas encore (aucune migration manuelle nécessaire)
    with app.app_context():
        try:
            from models import CodeVerification
            CodeVerification.__table__.create(bind=db.engine, checkfirst=True)
        except Exception as e:  # base injoignable au démarrage : l'erreur apparaîtra à la première requête
            print("Avertissement : table codes_verification non vérifiée :", e)

    from routes.marches import marches_bp
    from routes.controles import controles_bp
    from routes.documents import documents_bp
    from routes.irregularites import irregularites_bp
    from routes.statistiques import statistiques_bp
    from routes.entites import entites_bp
    from routes.reference import reference_bp
    from routes.auth import auth_bp
    from routes.recommandations import recommandations_bp
    from routes.rapports import rapports_bp
    from routes.recherche import recherche_bp
    from routes.notifications import notifications_bp
    from routes.prmp import prmp_bp
    from routes.objets import objets_bp
    from routes.transferts import transferts_bp
    from routes.preuves import preuves_bp
    from routes.notifications_prmp import notif_prmp_bp
    app.register_blueprint(marches_bp, url_prefix="/api/marches")
    app.register_blueprint(controles_bp, url_prefix="/api/controles")
    app.register_blueprint(documents_bp, url_prefix="/api/documents")
    app.register_blueprint(irregularites_bp, url_prefix="/api/irregularites")
    app.register_blueprint(statistiques_bp, url_prefix="/api/statistiques")
    app.register_blueprint(entites_bp, url_prefix="/api/entites")
    app.register_blueprint(reference_bp, url_prefix="/api/reference")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(recommandations_bp, url_prefix="/api/recommandations")
    app.register_blueprint(rapports_bp, url_prefix="/api/rapports")
    app.register_blueprint(recherche_bp, url_prefix="/api/recherche")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(prmp_bp, url_prefix="/api")
    app.register_blueprint(objets_bp, url_prefix="/api")
    app.register_blueprint(transferts_bp, url_prefix="/api")
    app.register_blueprint(preuves_bp, url_prefix="/api")
    app.register_blueprint(notif_prmp_bp,url_prefix='/api')
    proteger_api(app)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)