"""
Point d'entrÃ©e Flask â€” configuration et enregistrement des routes.
"""
import os
from flask import Flask
from flask_cors import CORS
from extensions import db

def create_app(config=None):
    app = Flask(__name__)
    CORS(app)  # autorise les appels depuis React (ex: http://localhost:5173)

    try:
        from config_db import DATABASE_URI
    except ImportError:
        DATABASE_URI = "postgresql+psycopg2://postgres:2112@localhost:5432/controle_marches_publics"
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Dossier oÃ¹ sont stockÃ©s les fichiers uploadÃ©s (DAO, PV, contrats...)
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    if config:
        app.config.update(config)  # surcharge possible (tests)

    db.init_app(app)

    # crÃ©e la table des codes de vÃ©rification si elle n'existe pas encore (aucune migration manuelle nÃ©cessaire)
    with app.app_context():
        try:
            from models import CodeVerification
            CodeVerification.__table__.create(bind=db.engine, checkfirst=True)
        except Exception as e:  # base injoignable au dÃ©marrage : l'erreur apparaÃ®tra Ã  la premiÃ¨re requÃªte
            print("Avertissement : table codes_verification non vÃ©rifiÃ©e :", e)

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

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
