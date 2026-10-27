"""
Modèles SQLAlchemy — correspondent exactement aux tables du script PostgreSQL.
"""
from datetime import datetime, date
from extensions import db


class NatureMarche(db.Model):
    __tablename__ = "natures_marche"
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(60), nullable=False, unique=True)


class ModePassation(db.Model):
    __tablename__ = "modes_passation"
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(60), nullable=False, unique=True)


class Etape(db.Model):
    __tablename__ = "etapes"
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(80), nullable=False, unique=True)
    ordre = db.Column(db.SmallInteger, nullable=False, unique=True)


class TypeDocument(db.Model):
    __tablename__ = "types_document"
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(80), nullable=False, unique=True)
    id_etape = db.Column(db.Integer, db.ForeignKey("etapes.id"), nullable=True)
    etape = db.relationship("Etape")


class Entite(db.Model):
    __tablename__ = "entites"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150), nullable=False)
    type = db.Column(db.Enum("STD", "CTD", "EPN", name="type_entite"), nullable=False)
    region = db.Column(db.String(80))


class Prmp(db.Model):
    __tablename__ = "prmp"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    id_entite = db.Column(db.Integer, db.ForeignKey("entites.id"), nullable=False)
    entite = db.relationship("Entite")


class Utilisateur(db.Model):
    __tablename__ = "utilisateurs"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True)
    login = db.Column(db.String(60), nullable=False, unique=True)
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("ADMIN", "COLLECTE", "VERIFICATION", "ANALYSE", "VALIDATION", "PCNM", "ENTITE", "INVITE",
                             name="role_utilisateur"), nullable=False)
    id_entite = db.Column(db.Integer, db.ForeignKey("entites.id"), nullable=True)
    actif = db.Column(db.Boolean, nullable=False, default=True)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Marche(db.Model):
    __tablename__ = "marches"
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(60), nullable=False, unique=True)
    objet = db.Column(db.Text, nullable=False)
    id_entite = db.Column(db.Integer, db.ForeignKey("entites.id"), nullable=False)
    id_prmp = db.Column(db.Integer, db.ForeignKey("prmp.id"), nullable=True)
    id_nature = db.Column(db.Integer, db.ForeignKey("natures_marche.id"), nullable=False)
    id_mode_passation = db.Column(db.Integer, db.ForeignKey("modes_passation.id"), nullable=False)
    montant = db.Column(db.Numeric(16, 2), nullable=False)
    titulaire = db.Column(db.String(150))
    date_signature = db.Column(db.Date)
    date_approbation = db.Column(db.Date)
    date_notification = db.Column(db.Date)
    annee_exercice = db.Column(db.SmallInteger, nullable=False)
    hors_ppm = db.Column(db.Boolean, nullable=False, default=False)
    marche_regularisation = db.Column(db.Boolean, nullable=False, default=False)
    id_utilisateur_saisie = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=True)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    entite = db.relationship("Entite", backref="marches")
    prmp = db.relationship("Prmp")
    nature = db.relationship("NatureMarche")
    mode_passation = db.relationship("ModePassation")


class Controle(db.Model):
    __tablename__ = "controles"
    id = db.Column(db.Integer, primary_key=True)
    id_marche = db.Column(db.Integer, db.ForeignKey("marches.id"), nullable=False)
    date_controle = db.Column(db.Date, nullable=False, default=date.today)
    note_globale = db.Column(db.Numeric(3, 2), nullable=True)
    conclusion = db.Column(db.Enum("CONFORME", "NON_CONFORME", "EN_COURS", name="conclusion_controle"),
                           nullable=False, default="EN_COURS")
    id_utilisateur_validateur = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=True)
    date_validation = db.Column(db.DateTime, nullable=True)

    marche = db.relationship("Marche")


class ControleEtape(db.Model):
    __tablename__ = "controle_etapes"
    __table_args__ = (db.UniqueConstraint("id_controle", "id_etape"),)
    id = db.Column(db.Integer, primary_key=True)
    id_controle = db.Column(db.Integer, db.ForeignKey("controles.id"), nullable=False)
    id_etape = db.Column(db.Integer, db.ForeignKey("etapes.id"), nullable=False)
    note = db.Column(db.SmallInteger, nullable=True)  # 0 à 4
    observations = db.Column(db.Text)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=True)
    date_saisie = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    controle = db.relationship("Controle")
    etape = db.relationship("Etape")


class Irregularite(db.Model):
    __tablename__ = "irregularites"
    id = db.Column(db.Integer, primary_key=True)
    id_controle_etape = db.Column(db.Integer, db.ForeignKey("controle_etapes.id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    texte_applicable = db.Column(db.String(255))
    risque = db.Column(db.String(255))
    recommandation = db.Column(db.Text)
    impacte_attribution = db.Column(db.Boolean, nullable=False, default=False)


class Document(db.Model):
    __tablename__ = "documents"
    id = db.Column(db.Integer, primary_key=True)
    id_marche = db.Column(db.Integer, db.ForeignKey("marches.id"), nullable=False)
    id_type_document = db.Column(db.Integer, db.ForeignKey("types_document.id"), nullable=False)
    nom_fichier = db.Column(db.String(255), nullable=False)
    chemin_fichier = db.Column(db.String(500), nullable=False)
    taille_ko = db.Column(db.Integer)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=True)
    date_upload = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    type_document = db.relationship("TypeDocument")


class Recommandation(db.Model):
    __tablename__ = "recommandations"
    id = db.Column(db.Integer, primary_key=True)
    id_entite = db.Column(db.Integer, db.ForeignKey("entites.id"), nullable=False)
    id_controle = db.Column(db.Integer, db.ForeignKey("controles.id"), nullable=True)
    texte = db.Column(db.Text, nullable=False)
    statut = db.Column(db.Enum("EMISE", "EN_COURS", "APPLIQUEE", "NON_APPLIQUEE", name="statut_recommandation"),
                       nullable=False, default="EMISE")
    date_emission = db.Column(db.Date, nullable=False, default=date.today)
    date_relance = db.Column(db.Date, nullable=True)


class CodeVerification(db.Model):
    """Codes à 6 chiffres envoyés par e-mail (inscription, mot de passe oublié). Stockés hachés."""
    __tablename__ = "codes_verification"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, index=True)
    objet = db.Column(db.String(20), nullable=False)          # INSCRIPTION / REINITIALISATION
    code_hash = db.Column(db.String(255), nullable=False)
    donnees = db.Column(db.Text)                               # inscription en attente (JSON, mot de passe haché)
    expire_le = db.Column(db.DateTime, nullable=False)
    tentatives = db.Column(db.Integer, nullable=False, default=0)
    utilise = db.Column(db.Boolean, nullable=False, default=False)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
