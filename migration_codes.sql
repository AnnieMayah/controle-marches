-- Table des codes de vérification (inscription / mot de passe oublié).
-- Optionnel : le backend la crée automatiquement au démarrage si elle n'existe pas.
CREATE TABLE IF NOT EXISTS codes_verification (
    id             SERIAL PRIMARY KEY,
    email          VARCHAR(150) NOT NULL,
    objet          VARCHAR(20)  NOT NULL,          -- INSCRIPTION / REINITIALISATION
    code_hash      VARCHAR(255) NOT NULL,
    donnees        TEXT,
    expire_le      TIMESTAMP NOT NULL,
    tentatives     INTEGER NOT NULL DEFAULT 0,
    utilise        BOOLEAN NOT NULL DEFAULT FALSE,
    date_creation  TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_codes_verification_email ON codes_verification(email);
