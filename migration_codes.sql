-- =====================================================================
-- MIGRATION COMPLÈTE : circuit directeur (ADMIN) -> chef de service -> CV / ACV
-- À exécuter dans pgAdmin / psql, en 3 blocs SÉPARÉS, dans l'ordre.
-- =====================================================================

-- ---------------------------------------------------------------------
-- BLOC 1 : nouveaux rôles (à exécuter SEUL, puis valider avant le bloc 2)
-- ---------------------------------------------------------------------
ALTER TYPE role_utilisateur ADD VALUE IF NOT EXISTS 'CHEF_SERVICE';
ALTER TYPE role_utilisateur ADD VALUE IF NOT EXISTS 'CV';    -- Contrôleur Vérificateur
ALTER TYPE role_utilisateur ADD VALUE IF NOT EXISTS 'ACV';   -- Assistant Contrôleur Vérificateur


-- ---------------------------------------------------------------------
-- BLOC 2 : services, comptes, marchés, contrôles
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS services (
  id  SERIAL PRIMARY KEY,
  nom VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO services (nom) VALUES ('Service A'), ('Service B'), ('Service C')
ON CONFLICT (nom) DO NOTHING;

-- service d'un compte (vide pour le directeur)
ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS id_service INT REFERENCES services(id);

-- un seul chef de service actif par service
CREATE UNIQUE INDEX IF NOT EXISTS uq_chef_par_service ON utilisateurs (id_service)
  WHERE role = 'CHEF_SERVICE' AND actif;

-- statut d'un marché (titre) : A_CONTROLER -> A_ENVOYER -> ENVOYE
ALTER TABLE marches ADD COLUMN IF NOT EXISTS statut_controle VARCHAR(20) NOT NULL DEFAULT 'A_CONTROLER';
-- les marchés qui ont déjà un contrôle sont considérés comme déjà envoyés
UPDATE marches SET statut_controle = 'ENVOYE' WHERE id IN (SELECT id_marche FROM controles);

-- envoi d'un contrôle : service destinataire, CV / ACV assigné, date d'envoi
ALTER TABLE controles ADD COLUMN IF NOT EXISTS id_service INT REFERENCES services(id);
ALTER TABLE controles ADD COLUMN IF NOT EXISTS id_utilisateur_assigne INT REFERENCES utilisateurs(id);
ALTER TABLE controles ADD COLUMN IF NOT EXISTS date_envoi TIMESTAMP;


-- ---------------------------------------------------------------------
-- BLOC 3 (seulement si pas déjà fait lors des étapes précédentes)
-- ---------------------------------------------------------------------
-- champ « Irrégularité » des constats
ALTER TABLE irregularites ADD COLUMN IF NOT EXISTS irregularite TEXT;

-- catalogue des observations par étape
CREATE TABLE IF NOT EXISTS observation_type (
  id SERIAL PRIMARY KEY,
  id_etape INT NOT NULL REFERENCES etapes(id),
  libelle VARCHAR(255) NOT NULL,
  UNIQUE (id_etape, libelle)
);