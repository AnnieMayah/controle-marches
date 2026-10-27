-- ============================================================================
-- MLD — Application de contrôle a posteriori des marchés publics
-- Stack : PostgreSQL (SGBD) — consommé par Spring Boot / JPA
-- ============================================================================

-- ============================================================================
-- 1. TYPES ÉNUMÉRÉS
-- ============================================================================

CREATE TYPE role_utilisateur AS ENUM (
    'ADMIN', 'COLLECTE', 'VERIFICATION', 'ANALYSE', 'VALIDATION', 'PCNM', 'ENTITE', 'INVITE'
);

CREATE TYPE type_entite AS ENUM ('STD', 'CTD', 'EPN');

CREATE TYPE conclusion_controle AS ENUM ('CONFORME', 'NON_CONFORME', 'EN_COURS');

CREATE TYPE statut_recommandation AS ENUM ('EMISE', 'EN_COURS', 'APPLIQUEE', 'NON_APPLIQUEE');

-- ============================================================================
-- 2. RÉFÉRENTIELS (tables de base, peu de lignes, peu de changements)
-- ============================================================================

CREATE TABLE natures_marche (
    id          SERIAL PRIMARY KEY,
    libelle     VARCHAR(60) NOT NULL UNIQUE
);
-- Travaux, Fournitures, Services, Prestations intellectuelles

CREATE TABLE modes_passation (
    id          SERIAL PRIMARY KEY,
    libelle     VARCHAR(60) NOT NULL UNIQUE
);
-- Appel d'offres ouvert (AOO), Appel d'offres restreint (AOR), Affichage/Consultation,
-- Gré à gré (MGG), Achat direct, Appel à manifestation d'intérêt (AMI)

CREATE TABLE etapes (
    id          SERIAL PRIMARY KEY,
    libelle     VARCHAR(80) NOT NULL UNIQUE,
    ordre       SMALLINT NOT NULL UNIQUE
);
-- 1 Planification, 2 Documents de mise en concurrence, 3 Mise en concurrence,
-- 4 Ouverture des plis, 5 Évaluation, 6 Attribution, 7 Gestion contractuelle

CREATE TABLE types_document (
    id          SERIAL PRIMARY KEY,
    libelle     VARCHAR(80) NOT NULL UNIQUE,
    id_etape    INTEGER REFERENCES etapes(id)
);
-- DAO, Avis de publication, PV ouverture des plis, Rapport d'évaluation, Contrat,
-- Ordre de service, PV réception technique/provisoire/définitive, PV de carence

-- ============================================================================
-- 3. ENTITÉS MÉTIER PRINCIPALES
-- ============================================================================

CREATE TABLE entites (
    id          SERIAL PRIMARY KEY,
    nom         VARCHAR(150) NOT NULL,
    type        type_entite NOT NULL,
    region      VARCHAR(80)
);

CREATE TABLE prmp (
    id          SERIAL PRIMARY KEY,
    nom         VARCHAR(120) NOT NULL,
    id_entite   INTEGER NOT NULL REFERENCES entites(id) ON DELETE CASCADE
);

CREATE TABLE utilisateurs (
    id                SERIAL PRIMARY KEY,
    nom               VARCHAR(100) NOT NULL,
    prenom            VARCHAR(100),
    email             VARCHAR(150) UNIQUE,
    login             VARCHAR(60) NOT NULL UNIQUE,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    role              role_utilisateur NOT NULL,
    id_entite         INTEGER REFERENCES entites(id),  -- renseigné seulement pour le rôle ENTITE
    actif             BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation     TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE marches (
    id                    SERIAL PRIMARY KEY,
    reference             VARCHAR(60) NOT NULL UNIQUE,
    objet                 TEXT NOT NULL,
    id_entite             INTEGER NOT NULL REFERENCES entites(id),
    id_prmp               INTEGER REFERENCES prmp(id),
    id_nature             INTEGER NOT NULL REFERENCES natures_marche(id),
    id_mode_passation     INTEGER NOT NULL REFERENCES modes_passation(id),
    montant               NUMERIC(16,2) NOT NULL,
    titulaire             VARCHAR(150),
    date_signature        DATE,
    date_approbation      DATE,
    date_notification     DATE,
    annee_exercice        SMALLINT NOT NULL,
    hors_ppm              BOOLEAN NOT NULL DEFAULT FALSE,
    marche_regularisation BOOLEAN NOT NULL DEFAULT FALSE,
    id_utilisateur_saisie INTEGER REFERENCES utilisateurs(id),
    date_creation         TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_marches_entite ON marches(id_entite);
CREATE INDEX idx_marches_annee ON marches(annee_exercice);

-- ============================================================================
-- 4. CYCLE DE CONTRÔLE (workflow à 4 niveaux, notation par étape)
-- ============================================================================

CREATE TABLE controles (
    id                       SERIAL PRIMARY KEY,
    id_marche                INTEGER NOT NULL REFERENCES marches(id) ON DELETE CASCADE,
    date_controle             DATE NOT NULL DEFAULT CURRENT_DATE,
    note_globale              NUMERIC(3,2),              -- moyenne calculée des controle_etapes
    conclusion                conclusion_controle NOT NULL DEFAULT 'EN_COURS',
    id_utilisateur_validateur INTEGER REFERENCES utilisateurs(id),  -- PCNM qui valide
    date_validation            TIMESTAMP
);

CREATE INDEX idx_controles_marche ON controles(id_marche);

CREATE TABLE controle_etapes (
    id              SERIAL PRIMARY KEY,
    id_controle     INTEGER NOT NULL REFERENCES controles(id) ON DELETE CASCADE,
    id_etape        INTEGER NOT NULL REFERENCES etapes(id),
    note            SMALLINT CHECK (note BETWEEN 0 AND 4),
    observations    TEXT,
    id_utilisateur  INTEGER REFERENCES utilisateurs(id),  -- qui a saisi/analysé cette étape
    date_saisie     TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (id_controle, id_etape)
);

CREATE TABLE irregularites (
    id                   SERIAL PRIMARY KEY,
    id_controle_etape    INTEGER NOT NULL REFERENCES controle_etapes(id) ON DELETE CASCADE,
    description          TEXT NOT NULL,
    texte_applicable     VARCHAR(255),   -- référence réglementaire (ex: Loi n°2016-055, art. 45)
    risque               VARCHAR(255),
    recommandation       TEXT,
    impacte_attribution  BOOLEAN NOT NULL DEFAULT FALSE  -- déclenche non-conformité automatique
);

-- ============================================================================
-- 5. DOCUMENTS JUSTIFICATIFS
-- ============================================================================

CREATE TABLE documents (
    id                SERIAL PRIMARY KEY,
    id_marche         INTEGER NOT NULL REFERENCES marches(id) ON DELETE CASCADE,
    id_type_document  INTEGER NOT NULL REFERENCES types_document(id),
    nom_fichier       VARCHAR(255) NOT NULL,
    chemin_fichier    VARCHAR(500) NOT NULL,
    taille_ko         INTEGER,
    id_utilisateur    INTEGER REFERENCES utilisateurs(id),
    date_upload       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_documents_marche ON documents(id_marche);

-- Table de liaison : un document peut servir de preuve à plusieurs irrégularités
CREATE TABLE documents_irregularites (
    id_document     INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    id_irregularite INTEGER NOT NULL REFERENCES irregularites(id) ON DELETE CASCADE,
    PRIMARY KEY (id_document, id_irregularite)
);

-- ============================================================================
-- 6. RECOMMANDATIONS ET SUIVI
-- ============================================================================

CREATE TABLE recommandations (
    id              SERIAL PRIMARY KEY,
    id_entite       INTEGER NOT NULL REFERENCES entites(id),
    id_controle     INTEGER REFERENCES controles(id),
    texte           TEXT NOT NULL,
    statut          statut_recommandation NOT NULL DEFAULT 'EMISE',
    date_emission   DATE NOT NULL DEFAULT CURRENT_DATE,
    date_relance    DATE
);

CREATE INDEX idx_recommandations_entite ON recommandations(id_entite);

-- ============================================================================
-- 7. DONNÉES DE RÉFÉRENCE (seed) — à adapter si besoin
-- ============================================================================

INSERT INTO natures_marche (libelle) VALUES
    ('Travaux'), ('Fournitures'), ('Services'), ('Prestations intellectuelles');

INSERT INTO modes_passation (libelle) VALUES
    ('Appel d''offres ouvert'), ('Appel d''offres restreint'), ('Affichage / Consultation'),
    ('Gré à gré'), ('Achat direct'), ('Appel à manifestation d''intérêt');

INSERT INTO etapes (libelle, ordre) VALUES
    ('Planification', 1),
    ('Documents de mise en concurrence', 2),
    ('Mise en concurrence', 3),
    ('Ouverture des plis', 4),
    ('Évaluation', 5),
    ('Attribution', 6),
    ('Gestion contractuelle', 7);

INSERT INTO types_document (libelle, id_etape) VALUES
    ('Dossier d''Appel d''Offres (DAO)', 2),
    ('Avis de publication', 3),
    ('PV d''ouverture des plis', 4),
    ('Rapport d''évaluation', 5),
    ('Contrat', 6),
    ('Ordre de service', 7),
    ('PV de réception technique', 7),
    ('PV de réception provisoire', 7),
    ('PV de réception définitive', 7),
    ('PV de carence', NULL);

-- ============================================================================
-- Notes d'implémentation (logique métier à coder côté Spring Boot, pas en SQL) :
--
-- 1. note_globale d'un contrôle = AVG(controle_etapes.note) pour ce contrôle
-- 2. conclusion = 'NON_CONFORME' si :
--      marches.hors_ppm = TRUE
--      OU marches.marche_regularisation = TRUE
--      OU EXISTS (irrégularité liée avec impacte_attribution = TRUE)
--    sinon 'CONFORME' si note_globale >= 2, sinon 'NON_CONFORME'
-- 3. Un contrôle n'est clôturé (conclusion figée) qu'après validation par un
--    utilisateur de rôle PCNM (id_utilisateur_validateur renseigné)
-- ============================================================================
