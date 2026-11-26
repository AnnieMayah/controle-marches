--
-- PostgreSQL database dump
--

\restrict lTcEEMpizaZkhBLmFwKWwOx9yUJDchpVNHw69yH65mbLzgvHVsaaD3gJOTtep3E

-- Dumped from database version 16.10
-- Dumped by pg_dump version 16.10

-- Started on 2026-11-26 15:27:45

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 883 (class 1247 OID 139384)
-- Name: conclusion_controle; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.conclusion_controle AS ENUM (
    'CONFORME',
    'NON_CONFORME',
    'EN_COURS'
);


ALTER TYPE public.conclusion_controle OWNER TO postgres;

--
-- TOC entry 946 (class 1247 OID 188587)
-- Name: role_utilisateur; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.role_utilisateur AS ENUM (
    'ADMIN',
    'PCNM',
    'ENTITE',
    'INVITE',
    'CHEF_SERVICE',
    'CV',
    'ACV'
);


ALTER TYPE public.role_utilisateur OWNER TO postgres;

--
-- TOC entry 886 (class 1247 OID 139392)
-- Name: statut_recommandation; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.statut_recommandation AS ENUM (
    'EMISE',
    'EN_COURS',
    'APPLIQUEE',
    'NON_APPLIQUEE'
);


ALTER TYPE public.statut_recommandation OWNER TO postgres;

--
-- TOC entry 880 (class 1247 OID 139376)
-- Name: type_entite; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.type_entite AS ENUM (
    'STD',
    'CTD',
    'EPN'
);


ALTER TYPE public.type_entite OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 245 (class 1259 OID 155742)
-- Name: codes_verification; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.codes_verification (
    id integer NOT NULL,
    email character varying(150) NOT NULL,
    objet character varying(20) NOT NULL,
    code_hash character varying(255) NOT NULL,
    donnees text,
    expire_le timestamp without time zone NOT NULL,
    tentatives integer NOT NULL,
    utilise boolean NOT NULL,
    date_creation timestamp without time zone NOT NULL
);


ALTER TABLE public.codes_verification OWNER TO postgres;

--
-- TOC entry 244 (class 1259 OID 155741)
-- Name: codes_verification_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.codes_verification_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.codes_verification_id_seq OWNER TO postgres;

--
-- TOC entry 5056 (class 0 OID 0)
-- Dependencies: 244
-- Name: codes_verification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.codes_verification_id_seq OWNED BY public.codes_verification.id;


--
-- TOC entry 236 (class 1259 OID 139545)
-- Name: controle_etapes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.controle_etapes (
    id integer NOT NULL,
    id_controle integer NOT NULL,
    id_etape integer NOT NULL,
    note smallint,
    observations text,
    id_utilisateur integer,
    date_saisie timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT controle_etapes_note_check CHECK (((note >= 0) AND (note <= 4)))
);


ALTER TABLE public.controle_etapes OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 139544)
-- Name: controle_etapes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.controle_etapes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.controle_etapes_id_seq OWNER TO postgres;

--
-- TOC entry 5057 (class 0 OID 0)
-- Dependencies: 235
-- Name: controle_etapes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.controle_etapes_id_seq OWNED BY public.controle_etapes.id;


--
-- TOC entry 234 (class 1259 OID 139525)
-- Name: controles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.controles (
    id integer NOT NULL,
    id_marche integer NOT NULL,
    date_controle date DEFAULT CURRENT_DATE NOT NULL,
    note_globale numeric(3,2),
    conclusion public.conclusion_controle DEFAULT 'EN_COURS'::public.conclusion_controle NOT NULL,
    id_utilisateur_validateur integer,
    date_validation timestamp without time zone,
    id_service integer,
    id_utilisateur_assigne integer,
    date_envoi timestamp without time zone
);


ALTER TABLE public.controles OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 139524)
-- Name: controles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.controles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.controles_id_seq OWNER TO postgres;

--
-- TOC entry 5058 (class 0 OID 0)
-- Dependencies: 233
-- Name: controles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.controles_id_seq OWNED BY public.controles.id;


--
-- TOC entry 240 (class 1259 OID 139588)
-- Name: documents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documents (
    id integer NOT NULL,
    id_marche integer NOT NULL,
    id_type_document integer NOT NULL,
    nom_fichier character varying(255) NOT NULL,
    chemin_fichier character varying(500) NOT NULL,
    taille_ko integer,
    id_utilisateur integer,
    date_upload timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.documents OWNER TO postgres;

--
-- TOC entry 239 (class 1259 OID 139587)
-- Name: documents_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.documents_id_seq OWNER TO postgres;

--
-- TOC entry 5059 (class 0 OID 0)
-- Dependencies: 239
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.documents_id_seq OWNED BY public.documents.id;


--
-- TOC entry 241 (class 1259 OID 139613)
-- Name: documents_irregularites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documents_irregularites (
    id_document integer NOT NULL,
    id_irregularite integer NOT NULL
);


ALTER TABLE public.documents_irregularites OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 139445)
-- Name: entites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.entites (
    id integer NOT NULL,
    nom character varying(150) NOT NULL,
    type public.type_entite NOT NULL,
    region character varying(80)
);


ALTER TABLE public.entites OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 139444)
-- Name: entites_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.entites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.entites_id_seq OWNER TO postgres;

--
-- TOC entry 5060 (class 0 OID 0)
-- Dependencies: 225
-- Name: entites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.entites_id_seq OWNED BY public.entites.id;


--
-- TOC entry 222 (class 1259 OID 139420)
-- Name: etapes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.etapes (
    id integer NOT NULL,
    libelle character varying(80) NOT NULL,
    ordre smallint NOT NULL
);


ALTER TABLE public.etapes OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 139419)
-- Name: etapes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.etapes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.etapes_id_seq OWNER TO postgres;

--
-- TOC entry 5061 (class 0 OID 0)
-- Dependencies: 221
-- Name: etapes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.etapes_id_seq OWNED BY public.etapes.id;


--
-- TOC entry 255 (class 1259 OID 204894)
-- Name: fiches_excel; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fiches_excel (
    id integer NOT NULL,
    id_controle integer NOT NULL,
    id_transfert integer,
    niveau_origine character varying(20),
    niveau_destination character varying(20),
    id_expediteur integer,
    id_destinataire integer,
    nom_fichier character varying(255) NOT NULL,
    chemin_fichier character varying(500) NOT NULL,
    taille_ko integer,
    date_creation timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.fiches_excel OWNER TO postgres;

--
-- TOC entry 254 (class 1259 OID 204893)
-- Name: fiches_excel_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fiches_excel_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fiches_excel_id_seq OWNER TO postgres;

--
-- TOC entry 5062 (class 0 OID 0)
-- Dependencies: 254
-- Name: fiches_excel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fiches_excel_id_seq OWNED BY public.fiches_excel.id;


--
-- TOC entry 238 (class 1259 OID 139573)
-- Name: irregularites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.irregularites (
    id integer NOT NULL,
    id_controle_etape integer NOT NULL,
    description text NOT NULL,
    texte_applicable text,
    risque character varying(255),
    recommandation text,
    impacte_attribution boolean DEFAULT false NOT NULL,
    irregularite text,
    observations_generales text,
    description_risque text,
    observation text
);


ALTER TABLE public.irregularites OWNER TO postgres;

--
-- TOC entry 237 (class 1259 OID 139572)
-- Name: irregularites_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.irregularites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.irregularites_id_seq OWNER TO postgres;

--
-- TOC entry 5063 (class 0 OID 0)
-- Dependencies: 237
-- Name: irregularites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.irregularites_id_seq OWNED BY public.irregularites.id;


--
-- TOC entry 232 (class 1259 OID 139484)
-- Name: marches; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.marches (
    id integer NOT NULL,
    reference character varying(60),
    objet text NOT NULL,
    id_entite integer NOT NULL,
    id_prmp integer,
    id_nature integer,
    id_mode_passation integer,
    montant numeric(16,2),
    titulaire character varying(150),
    date_signature date,
    date_approbation date,
    date_notification date,
    annee_exercice smallint,
    hors_ppm boolean DEFAULT false NOT NULL,
    marche_regularisation boolean DEFAULT false NOT NULL,
    id_utilisateur_saisie integer,
    date_creation timestamp without time zone DEFAULT now() NOT NULL,
    id_objet integer,
    numero_saisie character varying(30),
    direction_service character varying(150),
    forme_contrat character varying(20),
    montant_min numeric(16,2),
    montant_max numeric(16,2),
    montant_tef numeric(16,2),
    forme_prix character varying(20),
    delai_execution character varying(60),
    financement character varying(100),
    statut_controle character varying(20) DEFAULT 'A_CONTROLER'::character varying NOT NULL,
    CONSTRAINT marches_forme_contrat_check CHECK (((forme_contrat)::text = ANY ((ARRAY['QUANTITE_FIXE'::character varying, 'COMMANDES'::character varying])::text[]))),
    CONSTRAINT marches_forme_prix_check CHECK (((forme_prix)::text = ANY ((ARRAY['UNITAIRE'::character varying, 'FORFAITAIRE'::character varying])::text[])))
);


ALTER TABLE public.marches OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 139483)
-- Name: marches_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.marches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.marches_id_seq OWNER TO postgres;

--
-- TOC entry 5064 (class 0 OID 0)
-- Dependencies: 231
-- Name: marches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.marches_id_seq OWNED BY public.marches.id;


--
-- TOC entry 220 (class 1259 OID 139411)
-- Name: modes_passation; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.modes_passation (
    id integer NOT NULL,
    libelle character varying(60) NOT NULL
);


ALTER TABLE public.modes_passation OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 139410)
-- Name: modes_passation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.modes_passation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.modes_passation_id_seq OWNER TO postgres;

--
-- TOC entry 5065 (class 0 OID 0)
-- Dependencies: 219
-- Name: modes_passation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.modes_passation_id_seq OWNED BY public.modes_passation.id;


--
-- TOC entry 218 (class 1259 OID 139402)
-- Name: natures_marche; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.natures_marche (
    id integer NOT NULL,
    libelle character varying(60) NOT NULL
);


ALTER TABLE public.natures_marche OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 139401)
-- Name: natures_marche_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.natures_marche_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.natures_marche_id_seq OWNER TO postgres;

--
-- TOC entry 5066 (class 0 OID 0)
-- Dependencies: 217
-- Name: natures_marche_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.natures_marche_id_seq OWNED BY public.natures_marche.id;


--
-- TOC entry 247 (class 1259 OID 163934)
-- Name: objets_marche; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.objets_marche (
    id integer NOT NULL,
    compte character varying(10) NOT NULL,
    libelle text NOT NULL
);


ALTER TABLE public.objets_marche OWNER TO postgres;

--
-- TOC entry 246 (class 1259 OID 163933)
-- Name: objets_marche_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.objets_marche_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.objets_marche_id_seq OWNER TO postgres;

--
-- TOC entry 5067 (class 0 OID 0)
-- Dependencies: 246
-- Name: objets_marche_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.objets_marche_id_seq OWNED BY public.objets_marche.id;


--
-- TOC entry 251 (class 1259 OID 180318)
-- Name: observation_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.observation_type (
    id integer NOT NULL,
    id_etape integer NOT NULL,
    libelle character varying(255) NOT NULL
);


ALTER TABLE public.observation_type OWNER TO postgres;

--
-- TOC entry 250 (class 1259 OID 180317)
-- Name: observation_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.observation_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.observation_type_id_seq OWNER TO postgres;

--
-- TOC entry 5068 (class 0 OID 0)
-- Dependencies: 250
-- Name: observation_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.observation_type_id_seq OWNED BY public.observation_type.id;


--
-- TOC entry 228 (class 1259 OID 139452)
-- Name: prmp; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.prmp (
    id integer NOT NULL,
    nom character varying(120) NOT NULL,
    id_entite integer NOT NULL,
    email character varying(150)
);


ALTER TABLE public.prmp OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 139451)
-- Name: prmp_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.prmp_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.prmp_id_seq OWNER TO postgres;

--
-- TOC entry 5069 (class 0 OID 0)
-- Dependencies: 227
-- Name: prmp_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.prmp_id_seq OWNED BY public.prmp.id;


--
-- TOC entry 243 (class 1259 OID 139629)
-- Name: recommandations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.recommandations (
    id integer NOT NULL,
    id_entite integer NOT NULL,
    id_controle integer,
    texte text NOT NULL,
    statut public.statut_recommandation DEFAULT 'EMISE'::public.statut_recommandation NOT NULL,
    date_emission date DEFAULT CURRENT_DATE NOT NULL,
    date_relance date
);


ALTER TABLE public.recommandations OWNER TO postgres;

--
-- TOC entry 242 (class 1259 OID 139628)
-- Name: recommandations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.recommandations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.recommandations_id_seq OWNER TO postgres;

--
-- TOC entry 5070 (class 0 OID 0)
-- Dependencies: 242
-- Name: recommandations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.recommandations_id_seq OWNED BY public.recommandations.id;


--
-- TOC entry 253 (class 1259 OID 188556)
-- Name: services; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.services (
    id integer NOT NULL,
    nom character varying(50) NOT NULL
);


ALTER TABLE public.services OWNER TO postgres;

--
-- TOC entry 252 (class 1259 OID 188555)
-- Name: services_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.services_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.services_id_seq OWNER TO postgres;

--
-- TOC entry 5071 (class 0 OID 0)
-- Dependencies: 252
-- Name: services_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.services_id_seq OWNED BY public.services.id;


--
-- TOC entry 249 (class 1259 OID 172128)
-- Name: transferts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transferts (
    id integer NOT NULL,
    id_controle integer NOT NULL,
    niveau_depart character varying(20) NOT NULL,
    niveau_arrivee character varying(20) NOT NULL,
    action character varying(10) NOT NULL,
    motif text,
    id_utilisateur integer,
    date_transfert timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT transferts_action_check CHECK (((action)::text = ANY ((ARRAY['TRANSFERT'::character varying, 'RENVOI'::character varying])::text[])))
);


ALTER TABLE public.transferts OWNER TO postgres;

--
-- TOC entry 248 (class 1259 OID 172127)
-- Name: transferts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transferts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transferts_id_seq OWNER TO postgres;

--
-- TOC entry 5072 (class 0 OID 0)
-- Dependencies: 248
-- Name: transferts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transferts_id_seq OWNED BY public.transferts.id;


--
-- TOC entry 224 (class 1259 OID 139431)
-- Name: types_document; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.types_document (
    id integer NOT NULL,
    libelle character varying(80) NOT NULL,
    id_etape integer
);


ALTER TABLE public.types_document OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 139430)
-- Name: types_document_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.types_document_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.types_document_id_seq OWNER TO postgres;

--
-- TOC entry 5073 (class 0 OID 0)
-- Dependencies: 223
-- Name: types_document_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.types_document_id_seq OWNED BY public.types_document.id;


--
-- TOC entry 230 (class 1259 OID 139464)
-- Name: utilisateurs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.utilisateurs (
    id integer NOT NULL,
    nom character varying(100) NOT NULL,
    prenom character varying(100),
    email character varying(150),
    login character varying(60) NOT NULL,
    mot_de_passe_hash character varying(255) NOT NULL,
    role public.role_utilisateur DEFAULT 'INVITE'::public.role_utilisateur NOT NULL,
    id_entite integer,
    actif boolean DEFAULT true NOT NULL,
    date_creation timestamp without time zone DEFAULT now() NOT NULL,
    id_service integer
);


ALTER TABLE public.utilisateurs OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 139463)
-- Name: utilisateurs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.utilisateurs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.utilisateurs_id_seq OWNER TO postgres;

--
-- TOC entry 5074 (class 0 OID 0)
-- Dependencies: 229
-- Name: utilisateurs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.utilisateurs_id_seq OWNED BY public.utilisateurs.id;


--
-- TOC entry 4753 (class 2604 OID 155745)
-- Name: codes_verification id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codes_verification ALTER COLUMN id SET DEFAULT nextval('public.codes_verification_id_seq'::regclass);


--
-- TOC entry 4744 (class 2604 OID 139548)
-- Name: controle_etapes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controle_etapes ALTER COLUMN id SET DEFAULT nextval('public.controle_etapes_id_seq'::regclass);


--
-- TOC entry 4741 (class 2604 OID 139528)
-- Name: controles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles ALTER COLUMN id SET DEFAULT nextval('public.controles_id_seq'::regclass);


--
-- TOC entry 4748 (class 2604 OID 139591)
-- Name: documents id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents ALTER COLUMN id SET DEFAULT nextval('public.documents_id_seq'::regclass);


--
-- TOC entry 4730 (class 2604 OID 139448)
-- Name: entites id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entites ALTER COLUMN id SET DEFAULT nextval('public.entites_id_seq'::regclass);


--
-- TOC entry 4728 (class 2604 OID 139423)
-- Name: etapes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.etapes ALTER COLUMN id SET DEFAULT nextval('public.etapes_id_seq'::regclass);


--
-- TOC entry 4759 (class 2604 OID 204897)
-- Name: fiches_excel id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fiches_excel ALTER COLUMN id SET DEFAULT nextval('public.fiches_excel_id_seq'::regclass);


--
-- TOC entry 4746 (class 2604 OID 139576)
-- Name: irregularites id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.irregularites ALTER COLUMN id SET DEFAULT nextval('public.irregularites_id_seq'::regclass);


--
-- TOC entry 4736 (class 2604 OID 139487)
-- Name: marches id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marches ALTER COLUMN id SET DEFAULT nextval('public.marches_id_seq'::regclass);


--
-- TOC entry 4727 (class 2604 OID 139414)
-- Name: modes_passation id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.modes_passation ALTER COLUMN id SET DEFAULT nextval('public.modes_passation_id_seq'::regclass);


--
-- TOC entry 4726 (class 2604 OID 139405)
-- Name: natures_marche id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.natures_marche ALTER COLUMN id SET DEFAULT nextval('public.natures_marche_id_seq'::regclass);


--
-- TOC entry 4754 (class 2604 OID 163937)
-- Name: objets_marche id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.objets_marche ALTER COLUMN id SET DEFAULT nextval('public.objets_marche_id_seq'::regclass);


--
-- TOC entry 4757 (class 2604 OID 180321)
-- Name: observation_type id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.observation_type ALTER COLUMN id SET DEFAULT nextval('public.observation_type_id_seq'::regclass);


--
-- TOC entry 4731 (class 2604 OID 139455)
-- Name: prmp id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prmp ALTER COLUMN id SET DEFAULT nextval('public.prmp_id_seq'::regclass);


--
-- TOC entry 4750 (class 2604 OID 139632)
-- Name: recommandations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommandations ALTER COLUMN id SET DEFAULT nextval('public.recommandations_id_seq'::regclass);


--
-- TOC entry 4758 (class 2604 OID 188559)
-- Name: services id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.services ALTER COLUMN id SET DEFAULT nextval('public.services_id_seq'::regclass);


--
-- TOC entry 4755 (class 2604 OID 172131)
-- Name: transferts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transferts ALTER COLUMN id SET DEFAULT nextval('public.transferts_id_seq'::regclass);


--
-- TOC entry 4729 (class 2604 OID 139434)
-- Name: types_document id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.types_document ALTER COLUMN id SET DEFAULT nextval('public.types_document_id_seq'::regclass);


--
-- TOC entry 4732 (class 2604 OID 139467)
-- Name: utilisateurs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs ALTER COLUMN id SET DEFAULT nextval('public.utilisateurs_id_seq'::regclass);


--
-- TOC entry 5040 (class 0 OID 155742)
-- Dependencies: 245
-- Data for Name: codes_verification; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.codes_verification (id, email, objet, code_hash, donnees, expire_le, tentatives, utilise, date_creation) FROM stdin;
\.


--
-- TOC entry 5031 (class 0 OID 139545)
-- Dependencies: 236
-- Data for Name: controle_etapes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.controle_etapes (id, id_controle, id_etape, note, observations, id_utilisateur, date_saisie) FROM stdin;
5	5	5	4		5	2026-11-13 14:00:00
6	5	6	3		5	2026-11-14 15:00:00
7	5	7	3		5	2026-11-14 16:00:00
8	6	1	2		6	2026-11-12 11:00:00
9	6	2	3		6	2026-11-13 12:00:00
10	6	3	2		6	2026-11-13 13:00:00
11	7	1	3		5	2026-11-13 12:00:00
12	7	2	2		5	2026-11-14 13:00:00
13	7	3	3		5	2026-11-14 14:00:00
16	11	3	2		6	2026-11-18 12:00:00
18	11	5	2		6	2026-11-19 14:00:00
19	11	6	2		6	2026-11-20 15:00:00
21	14	1	3		7	2026-11-20 13:00:00
22	14	2	3		7	2026-11-21 14:00:00
23	14	3	1		7	2026-11-21 15:00:00
27	19	4	3		7	2026-11-09 17:00:00
29	19	6	4		7	2026-11-10 19:00:00
30	19	7	3		7	2026-11-10 20:00:00
1	5	1	3	["Recours au fractionnement abusif"]	5	2026-11-11 10:00:00
2	5	2	3	["Élaboration de spécifications techniques orientées, avec précision de marque ou technologie précises"]	5	2026-11-12 11:00:00
3	5	3	2	["Non respect du délai minimum de remise des offres (délai d’affichage)"]	5	2026-11-12 12:00:00
4	5	4	3	["Inexistence des documents justifiant la réception des offres des candidats"]	5	2026-11-13 13:00:00
14	11	1	2	["Utilisation de mode de passation non prévue par les textes"]	6	2026-11-17 10:00:00
15	11	2	1	["Critères de qualification tendant à limiter la concurrence"]	6	2026-11-18 11:00:00
17	11	4	1	["Défaut de remise d’un exemplaire du PV d’ouverture de plis à tous les candidats"]	6	2026-11-19 13:00:00
20	11	7	1	["Méconnaissance des règles sur la gestion contractuelle"]	6	2026-11-20 16:00:00
24	19	1	3	["Document de planification non transmis au CF et ou Trésor"]	7	2026-11-07 14:00:00
25	19	2	2	["Conditions de mise en concurrence insuffisantes"]	7	2026-11-08 15:00:00
26	19	3	3	["Non respect du délai minimum de remise des offres (délai d’affichage)"]	7	2026-11-08 16:00:00
28	19	5	2	["Évaluation des documents essentiels non exhaustive"]	7	2026-11-09 18:00:00
31	22	1	4	["Document de planification non transmis au CF et ou Trésor"]	5	2026-11-25 19:15:21.378072
32	22	2	2	["Modification du DAO après avis de la Commission des Marchés","Non respect des dispositions des documents types"]	5	2026-11-25 19:15:46.817032
33	22	3	3	["Non respect du délai minimum de remise des offres (délai d’affichage)"]	1	2026-11-25 19:30:35.942775
34	22	4	2	["Manipulation du PV d’ouverture de plis","Inexistence des documents justifiant la réception des offres des candidats"]	1	2026-11-26 05:40:58.097145
35	22	5	2	["Évaluation des spécifications techniques non exhaustive"]	1	2026-11-26 05:42:48.0013
36	22	6	4	["Défaut de publication de l’avis d’attribution"]	1	2026-11-26 07:57:11.509605
37	22	7	2	[]	1	2026-11-26 07:57:28.859788
\.


--
-- TOC entry 5029 (class 0 OID 139525)
-- Dependencies: 234
-- Data for Name: controles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.controles (id, id_marche, date_controle, note_globale, conclusion, id_utilisateur_validateur, date_validation, id_service, id_utilisateur_assigne, date_envoi) FROM stdin;
1	1	2026-11-05	\N	EN_COURS	\N	\N	1	\N	2026-11-05 09:00:00
2	2	2026-11-06	\N	EN_COURS	\N	\N	2	\N	2026-11-06 10:00:00
3	3	2026-11-07	\N	EN_COURS	\N	\N	1	\N	2026-11-07 11:00:00
4	4	2026-11-08	\N	EN_COURS	\N	\N	1	\N	2026-11-08 12:00:00
5	7	2026-11-11	3.00	CONFORME	2	2026-11-17 09:00:00	1	5	2026-11-11 09:00:00
6	8	2026-11-12	\N	EN_COURS	\N	\N	2	6	2026-11-12 10:00:00
7	9	2026-11-13	\N	EN_COURS	\N	\N	1	5	2026-11-13 11:00:00
8	10	2026-11-14	\N	EN_COURS	\N	\N	1	5	2026-11-14 12:00:00
9	11	2026-11-15	\N	EN_COURS	\N	\N	3	\N	2026-11-15 13:00:00
10	12	2026-11-16	\N	EN_COURS	\N	\N	3	\N	2026-11-16 08:00:00
11	13	2026-11-17	1.57	NON_CONFORME	3	2026-11-23 09:00:00	2	6	2026-11-17 09:00:00
12	14	2026-11-18	\N	EN_COURS	\N	\N	3	7	2026-11-18 10:00:00
13	15	2026-11-19	\N	EN_COURS	\N	\N	2	\N	2026-11-19 11:00:00
14	16	2026-11-20	\N	EN_COURS	\N	\N	3	7	2026-11-20 12:00:00
15	17	2026-11-21	\N	EN_COURS	\N	\N	2	\N	2026-11-21 13:00:00
16	18	2026-11-22	\N	EN_COURS	\N	\N	3	\N	2026-11-22 08:00:00
17	19	2026-11-23	\N	EN_COURS	\N	\N	2	6	2026-11-23 09:00:00
18	21	2026-11-05	\N	EN_COURS	\N	\N	3	\N	2026-11-05 11:00:00
19	23	2026-11-07	2.86	CONFORME	4	2026-11-13 13:00:00	3	7	2026-11-07 13:00:00
20	24	2026-11-08	\N	EN_COURS	\N	\N	2	\N	2026-11-08 08:00:00
21	25	2026-11-09	\N	EN_COURS	\N	\N	1	\N	2026-11-09 09:00:00
23	22	2026-11-26	\N	EN_COURS	\N	\N	2	\N	2026-11-26 05:43:21.769205
22	26	2026-11-25	2.71	CONFORME	\N	\N	1	5	2026-11-25 06:42:57.206471
24	20	2026-11-26	\N	EN_COURS	\N	\N	\N	\N	\N
\.


--
-- TOC entry 5035 (class 0 OID 139588)
-- Dependencies: 240
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.documents (id, id_marche, id_type_document, nom_fichier, chemin_fichier, taille_ko, id_utilisateur, date_upload) FROM stdin;
1	26	1	rapport_M2112_2026_4.docx	20edfabc5c5249f88720ed2698a17c51_rapport_M2112_2026_4.docx	36	\N	2026-11-26 09:29:29.942533
\.


--
-- TOC entry 5036 (class 0 OID 139613)
-- Dependencies: 241
-- Data for Name: documents_irregularites; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.documents_irregularites (id_document, id_irregularite) FROM stdin;
\.


--
-- TOC entry 5021 (class 0 OID 139445)
-- Dependencies: 226
-- Data for Name: entites; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.entites (id, nom, type, region) FROM stdin;
1	Direction Régionale des Travaux Publics	STD	Haute Matsiatra
2	Préfecture de Fianarantsoa et ses Districts rattachés	STD	Haute Matsiatra
3	Région Haute Matsiatra	CTD	Haute Matsiatra
4	Centre Hospitalier Universitaire Tambohobe	EPN	Haute Matsiatra
5	Paositra Malagasy - Direction Interrégionale de Fianarantsoa	EPN	Haute Matsiatra
6	Comission Régionale du Marché	EPN	Haute Matsiatra
\.


--
-- TOC entry 5017 (class 0 OID 139420)
-- Dependencies: 222
-- Data for Name: etapes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.etapes (id, libelle, ordre) FROM stdin;
1	Planification	1
2	Documents de mise en concurrence	2
3	Mise en concurrence	3
4	Ouverture des plis	4
5	Évaluation	5
6	Attribution	6
7	Gestion contractuelle	7
\.


--
-- TOC entry 5050 (class 0 OID 204894)
-- Dependencies: 255
-- Data for Name: fiches_excel; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fiches_excel (id, id_controle, id_transfert, niveau_origine, niveau_destination, id_expediteur, id_destinataire, nom_fichier, chemin_fichier, taille_ko, date_creation) FROM stdin;
1	22	\N	ANALYSE	ANALYSE	1	\N	Fiche_M2112_2026_ANALYSE_ANALYSE_20261126_111423.xlsx	D:\\projets\\controle-marches\\uploads\\fiches_excel\\Fiche_M2112_2026_ANALYSE_ANALYSE_20261126_111423.xlsx	7	2026-11-26 08:14:23.518782
2	22	\N	ANALYSE	ANALYSE	1	\N	Fiche_M2112_2026_ANALYSE_ANALYSE_20261126_112002.xlsx	D:\\projets\\controle-marches\\uploads\\fiches_excel\\Fiche_M2112_2026_ANALYSE_ANALYSE_20261126_112002.xlsx	7	2026-11-26 08:20:02.962774
3	22	\N	ANALYSE	ANALYSE	1	\N	Fiche_M2112_2026_ANALYSE_ANALYSE_20261126_120137.xlsx	D:\\projets\\controle-marches\\uploads\\fiches_excel\\Fiche_M2112_2026_ANALYSE_ANALYSE_20261126_120137.xlsx	8	2026-11-26 09:01:37.559664
4	22	\N	ANALYSE	ANALYSE	1	\N	Fiche_M2112_2026_ANALYSE_ANALYSE_20261126_120718.xlsx	D:\\projets\\controle-marches\\uploads\\fiches_excel\\Fiche_M2112_2026_ANALYSE_ANALYSE_20261126_120718.xlsx	8	2026-11-26 09:07:18.351562
5	22	\N	ANALYSE	ANALYSE	1	\N	Fiche_M2112_2026_ANALYSE_ANALYSE_20261126_143707.xlsx	D:\\projets\\controle-marches\\uploads\\fiches_excel\\Fiche_M2112_2026_ANALYSE_ANALYSE_20261126_143707.xlsx	8	2026-11-26 11:37:07.43853
\.


--
-- TOC entry 5033 (class 0 OID 139573)
-- Dependencies: 238
-- Data for Name: irregularites; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.irregularites (id, id_controle_etape, description, texte_applicable, risque, recommandation, impacte_attribution, irregularite, observations_generales, description_risque, observation) FROM stdin;
4	23	Pièce essentielle manquante ou non conforme au dossier.	Code des marchés publics (Loi n°2016-055)	Moyen	Régulariser le dossier et transmettre les pièces manquantes.	f	\N	\N	\N	\N
5	3	Constat relevé lors du contrôle : Non respect du délai minimum de remise des offres (délai d’affichage).	Code des marchés publics - publicité et délais de remise des offres	Moyen	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	f	Non respect du délai minimum de remise des offres (délai d’affichage)	\N	\N	\N
6	1	Constat relevé lors du contrôle : Recours au fractionnement abusif.	Code des marchés publics (Loi n°2016-055) - planification	Faible	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	f	Recours au fractionnement abusif	\N	\N	\N
7	2	Constat relevé lors du contrôle : Élaboration de spécifications techniques orientées, avec précision de marque ou technologie précises.	Code des marchés publics et documents types de passation	Faible	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	f	Élaboration de spécifications techniques orientées, avec précision de marque ou technologie précises	\N	\N	\N
8	4	Constat relevé lors du contrôle : Inexistence des documents justifiant la réception des offres des candidats.	Code des marchés publics - ouverture des plis	Faible	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	f	Inexistence des documents justifiant la réception des offres des candidats	\N	\N	\N
9	15	Constat relevé lors du contrôle : Critères de qualification tendant à limiter la concurrence.	Code des marchés publics et documents types de passation	Élevé	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	f	Critères de qualification tendant à limiter la concurrence	\N	\N	\N
10	17	Constat relevé lors du contrôle : Défaut de remise d’un exemplaire du PV d’ouverture de plis à tous les candidats.	Code des marchés publics - ouverture des plis	Élevé	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	f	Défaut de remise d’un exemplaire du PV d’ouverture de plis à tous les candidats	\N	\N	\N
11	20	Constat relevé lors du contrôle : Méconnaissance des règles sur la gestion contractuelle.	Code des marchés publics - exécution et gestion contractuelle	Élevé	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	f	Méconnaissance des règles sur la gestion contractuelle	\N	\N	\N
12	14	Constat relevé lors du contrôle : Utilisation de mode de passation non prévue par les textes.	Code des marchés publics (Loi n°2016-055) - planification	Moyen	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	f	Utilisation de mode de passation non prévue par les textes	\N	\N	\N
13	25	Constat relevé lors du contrôle : Conditions de mise en concurrence insuffisantes.	Code des marchés publics et documents types de passation	Moyen	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	f	Conditions de mise en concurrence insuffisantes	\N	\N	\N
14	28	Constat relevé lors du contrôle : Évaluation des documents essentiels non exhaustive.	Code des marchés publics - évaluation des offres	Moyen	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	t	Évaluation des documents essentiels non exhaustive	\N	\N	\N
15	24	Constat relevé lors du contrôle : Document de planification non transmis au CF et ou Trésor.	Code des marchés publics (Loi n°2016-055) - planification	Faible	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	f	Document de planification non transmis au CF et ou Trésor	\N	\N	\N
16	26	Constat relevé lors du contrôle : Non respect du délai minimum de remise des offres (délai d’affichage).	Code des marchés publics - publicité et délais de remise des offres	Faible	Se conformer aux dispositions applicables et corriger l’irrégularité relevée pour les prochaines procédures.	f	Non respect du délai minimum de remise des offres (délai d’affichage)	\N	\N	\N
19	33	Il faut respecter le règles	Artice 30  2026	Élevé	délai minimum doit au moins respectee	f	Non respect du délai minimum de remise des offres (délai d’affichage)	La commission d'ouverture des plis n'a pas été constituée conformément aux textes.	Risque de favoritisme ou d'atteinte au principe d'égalité de traitement des candidats.	Spécification technique orientée par la précision de la marque.
21	34	Le montant de l'offre a été modifié après l'ouverture des plis sans accord écrit du candidat.	Article 20, alinéa 1 du CMP : le candidat reste engagé par son offre	Élevé	: La PRMP doit obtenir l'accord écrit du candidat avant toute correction. Elle doit aussi justifier la correction dans le rapport d'évaluation.	f	Manipulation du PV d’ouverture de plis	Le montant retenu à l'attribution diffère de celui du PV d'ouverture, sans accord écrit du candidat.	Contentieux sur le processus d'évaluation. Risque d'annulation de l'attribution et de retard dans l'exécution du marché.	Modification du montant de l'offre du candidat sans son consentement
22	35	Aucune preuve de remise du PV d'ouverture à tous les candidats n'a été fournie.	Article 45, alinéa 2 du Code des marchés publics : une copie du PV est remise à chaque candidat.	Faible	Rappeler à la PRMP l'obligation de remettre une copie du PV à chaque candidat, contre décharge.	f	Évaluation des spécifications techniques non exhaustive	Les candidats présents ont signé la liste de présence, mais aucune copie du PV ne figure dans le dossier.	Contentieux sur l'ouverture des plis : contestation ou doute sur l'intégrité des offres.	Transmission de copie du PV d'ouverture des plis à tous les candidats non justifiée
17	31	HORS JEUX DE RECOMMANDATION	article 345JJ	Moyen	IL faut suivre  le proceduire	f	Document de planification non transmis au CF et ou Trésor	Le dossier est incomplet : plusieurs pièces obligatoires ne figurent pas dans le dossier transmis.	Risque de contestation ou de recours des soumissionnaires évincés.	PPM non transmis au Trésor Public.
18	32	Modification non respecte	Article 2026 NON IDENTIFIE	Faible	Fournir des piéces justificatives	f	Modification du DAO après avis de la Commission des Marchés	Les délais réglementaires de publication et de dépôt des offres n'ont pas été respectés.	Risque d'annulation de la procédure et de retard dans l'exécution du marché.	Avis spécifique non transmis à la CRM pour affichage.
20	32	Le marché a été exécuté avant l'approbation par l'autorité compétente.	Paragraphe I de l'Article 15 de l'Arreté N°11 406 /2019-MEF: "A cet effet, la PRMP publie l’avis d’appel public à la concurrence sous forme d’affichage\ndans un endroit	Élevé	Suivre le procédures	f	Non respect des dispositions des documents types	Le PV d'évaluation ne justifie pas le choix de l'attributaire.	Risque de paiement irrégulier refusé par le Trésor.	Absence de garantie de soumission dans le dossier d'appel d'offres.
23	36	 Le PPM validé par la CRM n'a pas été transmis au Trésor public avant le lancement de la procédure.	Article 5 de l'Arrêté n°7276-2016/MFB : le plan de passation des marchés doit être transmis…	Moyen	Transmettre le PPM validé au Trésor et au contrôle financier avant tout lancement. Conserver l'accusé de réception dans le dossier.	f	\N	Le dossier est incomplet. Aucune preuve de transmission du PPM validé au contrôle financier ni au Trésor.	Paiement du marché non inscrit dans le PPM. Risque de rejet de la dépense par le Trésor.	PPM non transmis au Trésor Public
\.


--
-- TOC entry 5027 (class 0 OID 139484)
-- Dependencies: 232
-- Data for Name: marches; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.marches (id, reference, objet, id_entite, id_prmp, id_nature, id_mode_passation, montant, titulaire, date_signature, date_approbation, date_notification, annee_exercice, hors_ppm, marche_regularisation, id_utilisateur_saisie, date_creation, id_objet, numero_saisie, direction_service, forme_contrat, montant_min, montant_max, montant_tef, forme_prix, delai_execution, financement, statut_controle) FROM stdin;
1	M-001/26	Fourniture et livraison des consommables informatiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	3	3	4	4	39100000.00	Vatomandry Construction	\N	\N	\N	2026	f	f	1	2026-11-04 09:00:00	4	2026-001	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
2	M-002/26	Fourniture et livraison des produits pharmaceutiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	5	5	4	1	176250000.00	Rova Construction	\N	\N	\N	2026	f	f	1	2026-11-05 10:00:00	5	2026-002	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
3	M-003/26	Location de matériel de transport de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa	5	5	4	4	216850000.00	Tech Madagascar SARL	\N	\N	\N	2026	f	f	1	2026-11-06 11:00:00	3	2026-003	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
4	M-004/26	Fourniture et livraison des outillages d’atelier ou fourniture de petits outillages d’atelier mécanique de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	4	4	4	5	214150000.00	Matsiatra Fournitures	\N	\N	\N	2026	f	f	1	2026-11-07 12:00:00	1	2026-004	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
5	M-005/26	Travaux d’entretien du bâtiment de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	5	5	2	2	22000000.00	Sanitas Distribution	\N	\N	\N	2026	f	f	1	2026-11-08 13:00:00	6	2026-005	\N	\N	\N	\N	\N	\N	\N	\N	A_CONTROLER
6	M-006/26	Fourniture et livraison des consommables informatiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	5	5	1	6	177850000.00	Garage Antsirabe Auto	\N	\N	\N	2026	f	f	1	2026-11-09 08:00:00	4	2026-006	\N	\N	\N	\N	\N	\N	\N	\N	A_CONTROLER
7	M-007/26	Travaux d’entretien du bâtiment de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	2	2	4	2	51950000.00	Info Concept	2026-10-08	2026-10-13	2026-10-17	2026	f	f	1	2026-11-10 09:00:00	6	2026-007	Direction Commerciale	COMMANDES	\N	\N	51950000.00	FORFAITAIRE	6 mois	Budget de la Région	ENVOYE
8	M-008/26	Travaux d’impression et de reliure de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa	3	3	4	4	179350000.00	Pharma Distribution Sud	2026-10-09	2026-10-14	2026-10-18	2026	f	f	1	2026-11-11 10:00:00	2	2026-008	Service Logistique	COMMANDES	\N	\N	179350000.00	UNITAIRE	30 jours	Budget de l'État	ENVOYE
9	M-009/26	Location de matériel de transport de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa	5	5	4	5	202500000.00	ElectroServ	2026-10-10	2026-10-15	2026-10-19	2026	f	f	1	2026-11-12 11:00:00	3	2026-009	Service Technique	COMMANDES	\N	\N	202500000.00	FORFAITAIRE	6 mois	Budget de la Région	ENVOYE
10	M-010/26	Location de matériel de transport de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa	4	4	4	5	15750000.00	Station Jovenna Fianarantsoa	2026-10-11	2026-10-16	2026-10-20	2026	f	f	1	2026-11-13 12:00:00	3	2026-010	Service Logistique	COMMANDES	\N	\N	15750000.00	UNITAIRE	6 mois	Budget de la Région	ENVOYE
11	M-011/26	Fourniture et livraison des consommables informatiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	5	5	3	4	76950000.00	SOMACO Services	\N	\N	\N	2026	f	f	1	2026-11-14 13:00:00	4	2026-011	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
12	M-012/26	Fourniture et livraison des consommables informatiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	4	4	1	6	111100000.00	Atelier Mandroso	\N	\N	\N	2026	f	f	1	2026-11-15 08:00:00	4	2026-012	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
13	M-013/26	Travaux d’impression et de reliure de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa	3	3	1	2	170450000.00	Entreprise Fitiavana BTP	2026-10-14	2026-10-19	2026-10-23	2026	f	f	1	2026-11-16 09:00:00	2	2026-013	Direction Commerciale	QUANTITE_FIXE	\N	\N	170450000.00	UNITAIRE	30 jours	Ressources propres	ENVOYE
14	M-014/26	Travaux d’impression et de reliure de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa	5	5	1	5	83400000.00	Cabinet Ravinala Conseil	2026-10-15	2026-10-20	2026-10-24	2026	f	f	1	2026-11-17 10:00:00	2	2026-014	Service Administratif et Financier	QUANTITE_FIXE	\N	\N	83400000.00	FORFAITAIRE	3 mois	Budget de l'État	ENVOYE
15	M-015/26	Fourniture et livraison des produits pharmaceutiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	1	1	3	6	240800000.00	Pharmacie Centrale FNR	\N	\N	\N	2026	f	f	1	2026-11-18 11:00:00	5	2026-015	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
16	M-016/26	Fourniture et livraison des consommables informatiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	4	4	2	5	93300000.00	Mobilier Plus	2026-10-17	2026-10-22	2026-10-26	2026	f	f	1	2026-11-19 12:00:00	4	2026-016	Service Technique	COMMANDES	\N	\N	93300000.00	UNITAIRE	6 mois	Budget de la Région	ENVOYE
17	M-017/26	Fourniture et livraison des produits pharmaceutiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	2	2	2	5	127300000.00	BTP Haute Terre	\N	\N	\N	2026	f	f	1	2026-11-20 13:00:00	5	2026-017	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
18	M-018/26	Travaux d’impression et de reliure de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa	4	4	4	2	215000000.00	Hery Logistique	\N	\N	\N	2026	f	f	1	2026-11-21 08:00:00	2	2026-018	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
19	M-019/26	Fourniture et livraison des outillages d’atelier ou fourniture de petits outillages d’atelier mécanique de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	4	4	1	1	161450000.00	Transports Betsileo	2026-10-20	2026-10-25	2026-10-29	2026	f	f	1	2026-11-22 09:00:00	1	2026-019	Service Administratif et Financier	COMMANDES	\N	\N	161450000.00	FORFAITAIRE	30 jours	Budget de l'État	ENVOYE
21	M-021/26	Fourniture et livraison des produits pharmaceutiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	3	3	1	4	193100000.00	BioMed Océan Indien	\N	\N	\N	2026	f	f	1	2026-11-04 11:00:00	5	2026-021	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
23	M-023/26	Fourniture et livraison des consommables informatiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	2	2	4	5	139750000.00	AgriMad	2026-10-24	2026-10-29	2026-11-02	2026	f	f	1	2026-11-06 13:00:00	4	2026-023	Service Technique	QUANTITE_FIXE	\N	\N	139750000.00	FORFAITAIRE	30 jours	Budget de l'État	ENVOYE
24	M-024/26	Fourniture et livraison des outillages d’atelier ou fourniture de petits outillages d’atelier mécanique de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	2	2	1	6	225100000.00	PostalTech	\N	\N	\N	2026	f	f	1	2026-11-07 08:00:00	1	2026-024	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
25	M-025/26	Travaux d’impression et de reliure de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa	4	4	2	4	10350000.00	Optima Bureautique	\N	\N	\N	2026	f	f	1	2026-11-08 09:00:00	2	2026-025	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
20	M-020/26	Fourniture et livraison des consommables informatiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	5	5	4	3	126350000.00	Papeterie Centrale	\N	\N	\N	2026	f	f	1	2026-11-03 10:00:00	4	2026-020	\N	\N	\N	\N	\N	\N	\N	\N	A_ENVOYER
26	M2112/2026	Location de matériel de transport de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa	6	\N	1	1	2000000.00	ONG SAHY	\N	\N	\N	2026	f	f	\N	2026-11-25 06:42:02.575538	3	2026-12	CRM	QUANTITE_FIXE	\N	\N	3450000.00	UNITAIRE	30	ONG HIFANOTSIKA	ENVOYE
22	M-022/26	Fourniture et livraison des produits pharmaceutiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)	5	5	2	2	244150000.00	Imprimerie Tsiry	\N	\N	\N	2026	f	f	1	2026-11-05 12:00:00	5	2026-022	\N	\N	\N	\N	\N	\N	\N	\N	ENVOYE
\.


--
-- TOC entry 5015 (class 0 OID 139411)
-- Dependencies: 220
-- Data for Name: modes_passation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.modes_passation (id, libelle) FROM stdin;
1	Appel d'offres ouvert
2	Appel d'offres restreint
3	Affichage / Consultation
4	Gré à gré
5	Achat direct
6	Appel à manifestation d'intérêt
\.


--
-- TOC entry 5013 (class 0 OID 139402)
-- Dependencies: 218
-- Data for Name: natures_marche; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.natures_marche (id, libelle) FROM stdin;
1	Travaux
2	Fournitures
3	Services
4	Prestations intellectuelles
\.


--
-- TOC entry 5042 (class 0 OID 163934)
-- Dependencies: 247
-- Data for Name: objets_marche; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.objets_marche (id, compte, libelle) FROM stdin;
1	6115	Fourniture et livraison des outillages d’atelier ou fourniture de petits outillages d’atelier mécanique de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)
2	6224	Travaux d’impression et de reliure de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa
3	6223	Location de matériel de transport de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa
4	6113	Fourniture et livraison des consommables informatiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)
5	6123	Fourniture et livraison des produits pharmaceutiques de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)
6	6211	Travaux d’entretien du bâtiment de la Direction Interrégionale des Mines et des Ressources Stratégiques de Fianarantsoa (à commande)
\.


--
-- TOC entry 5046 (class 0 OID 180318)
-- Dependencies: 251
-- Data for Name: observation_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.observation_type (id, id_etape, libelle) FROM stdin;
1	1	Document de planification non transmis au CF et ou Trésor
2	1	Recours au fractionnement abusif
3	1	Utilisation de mode de passation non prévue par les textes
4	1	Superposition ou doublon de marché
5	1	Mauvaise estimation des besoins
6	2	Non respect des dispositions des documents types
7	2	Conditions de mise en concurrence insuffisantes
8	2	Élaboration de spécifications techniques orientées, avec précision de marque ou technologie précises
9	2	Critères de qualification tendant à limiter la concurrence
10	2	Modification du DAO après avis de la Commission des Marchés
11	3	Non respect du délai minimum de remise des offres (délai d’affichage)
12	3	Non exhaustivité de la publication de l’avis d’appel à mise en concurrence
13	4	Manipulation du PV d’ouverture de plis
14	4	Inexistence des documents justifiant la réception des offres des candidats
15	4	Séance d’ouverture de plis non dirigée par la PRMP ou son représentant
16	4	Défaut de remise d’un exemplaire du PV d’ouverture de plis à tous les candidats
17	5	Évaluation des documents essentiels non exhaustive
18	5	Évaluation des spécifications techniques non exhaustive
19	5	Falsification du rapport d’évaluation pour faire passer un candidat : rendre conforme une offre non conforme ou rendre qualifié un candidat non qualifié
20	5	Non respect des étapes d’évaluation des offres
21	6	Défaut de publication de l’avis d’attribution
22	7	Avenant de régularisation
23	7	Utilisation d’un avenant pour contourner l’exigence des seuils de passation
24	7	Méconnaissance des règles sur la gestion contractuelle
25	7	Absence de PV de réception
\.


--
-- TOC entry 5023 (class 0 OID 139452)
-- Dependencies: 228
-- Data for Name: prmp; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.prmp (id, nom, id_entite, email) FROM stdin;
1	Rakoto Hery	1	rakoto.hery@example.com
3	Rabe Solo	3	rabe.solo@example.com
4	Andry Tiana	4	andry.tiana@example.com
5	Fanja Nirina	5	fanja.nirina@example.com
6	William Est	6	andrimamonjyannie@gmail.com
2	Razafy Miora	2	haingoniaina.annie@gmail.com
\.


--
-- TOC entry 5038 (class 0 OID 139629)
-- Dependencies: 243
-- Data for Name: recommandations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.recommandations (id, id_entite, id_controle, texte, statut, date_emission, date_relance) FROM stdin;
\.


--
-- TOC entry 5048 (class 0 OID 188556)
-- Dependencies: 253
-- Data for Name: services; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.services (id, nom) FROM stdin;
1	Service de Contrôle A
2	Service de Contrôle B
3	Service de Contrôle C
\.


--
-- TOC entry 5044 (class 0 OID 172128)
-- Dependencies: 249
-- Data for Name: transferts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.transferts (id, id_controle, niveau_depart, niveau_arrivee, action, motif, id_utilisateur, date_transfert) FROM stdin;
1	22	COLLECTE	VERIFICATION	TRANSFERT	\N	1	2026-11-26 05:59:55.76256
2	22	VERIFICATION	ANALYSE	TRANSFERT	\N	1	2026-11-26 06:00:27.084483
3	22	ANALYSE	VERIFICATION	RENVOI	nsnns	2	2026-11-26 07:08:05.50029
4	22	VERIFICATION	ANALYSE	TRANSFERT	\N	1	2026-11-26 07:09:16.742267
5	22	ANALYSE	VALIDATION	TRANSFERT	\N	2	2026-11-26 09:14:50.664019
6	22	VALIDATION	ANALYSE	RENVOI	hhhhh	1	2026-11-26 09:30:01.929904
\.


--
-- TOC entry 5019 (class 0 OID 139431)
-- Dependencies: 224
-- Data for Name: types_document; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.types_document (id, libelle, id_etape) FROM stdin;
1	Dossier d'Appel d'Offres (DAO)	2
2	Avis de publication	3
3	PV d'ouverture des plis	4
4	Rapport d'évaluation	5
5	Contrat	6
6	Ordre de service	7
7	PV de réception technique	7
8	PV de réception provisoire	7
9	PV de réception définitive	7
10	PV de carence	\N
\.


--
-- TOC entry 5025 (class 0 OID 139464)
-- Dependencies: 230
-- Data for Name: utilisateurs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.utilisateurs (id, nom, prenom, email, login, mot_de_passe_hash, role, id_entite, actif, date_creation, id_service) FROM stdin;
1	RAMILSON	Z. Amédé	\N	ramilson	scrypt:32768:8:1$gCzstvukfIeHgMTs$bde7ad726d0d32239c8ad9cce2b4c874435a152159cf6b75d2e82b1421d4cb24ed491dca2f7555138129d9f95622c15504be4f69705e4fb73c214561f0dd417e	ADMIN	\N	t	2026-11-25 09:04:44.16669	\N
2	ANDRIANANTENAINA	Harimisa J.	\N	andrianantenaina	scrypt:32768:8:1$gCzstvukfIeHgMTs$bde7ad726d0d32239c8ad9cce2b4c874435a152159cf6b75d2e82b1421d4cb24ed491dca2f7555138129d9f95622c15504be4f69705e4fb73c214561f0dd417e	CHEF_SERVICE	\N	t	2026-11-25 09:04:44.16669	1
3	RAKOTONDRAINY	J. Frédéric	\N	rakotondrainy	scrypt:32768:8:1$gCzstvukfIeHgMTs$bde7ad726d0d32239c8ad9cce2b4c874435a152159cf6b75d2e82b1421d4cb24ed491dca2f7555138129d9f95622c15504be4f69705e4fb73c214561f0dd417e	CHEF_SERVICE	\N	t	2026-11-25 09:04:44.16669	2
4	BEZAKA	Jessy Loréno	\N	bezaka	scrypt:32768:8:1$gCzstvukfIeHgMTs$bde7ad726d0d32239c8ad9cce2b4c874435a152159cf6b75d2e82b1421d4cb24ed491dca2f7555138129d9f95622c15504be4f69705e4fb73c214561f0dd417e	CHEF_SERVICE	\N	t	2026-11-25 09:04:44.16669	3
5	RAKOTOSALAMA	Lovasoa N. O.	\N	rakotosalama	scrypt:32768:8:1$gCzstvukfIeHgMTs$bde7ad726d0d32239c8ad9cce2b4c874435a152159cf6b75d2e82b1421d4cb24ed491dca2f7555138129d9f95622c15504be4f69705e4fb73c214561f0dd417e	CV	\N	t	2026-11-25 09:04:44.16669	1
6	ANDRIANOELINA	Voahangimbolana H.	\N	andrianoelina	scrypt:32768:8:1$gCzstvukfIeHgMTs$bde7ad726d0d32239c8ad9cce2b4c874435a152159cf6b75d2e82b1421d4cb24ed491dca2f7555138129d9f95622c15504be4f69705e4fb73c214561f0dd417e	CV	\N	t	2026-11-25 09:04:44.16669	2
7	RASOLONJATOVO	H. Patrick	\N	rasolonjatovo	scrypt:32768:8:1$gCzstvukfIeHgMTs$bde7ad726d0d32239c8ad9cce2b4c874435a152159cf6b75d2e82b1421d4cb24ed491dca2f7555138129d9f95622c15504be4f69705e4fb73c214561f0dd417e	CV	\N	t	2026-11-25 09:04:44.16669	3
12	RABENANDRAISANA	Miora T.	\N	rabenandraisana	scrypt:32768:8:1$gCzstvukfIeHgMTs$bde7ad726d0d32239c8ad9cce2b4c874435a152159cf6b75d2e82b1421d4cb24ed491dca2f7555138129d9f95622c15504be4f69705e4fb73c214561f0dd417e	INVITE	\N	t	2026-11-25 09:04:44.16669	\N
13	RANDRIATSALAMA	Harifetra	\N	randriatsalama	scrypt:32768:8:1$gCzstvukfIeHgMTs$bde7ad726d0d32239c8ad9cce2b4c874435a152159cf6b75d2e82b1421d4cb24ed491dca2f7555138129d9f95622c15504be4f69705e4fb73c214561f0dd417e	INVITE	\N	t	2026-11-25 09:04:44.16669	\N
14	ANDRIMAMONJY	Haingoniaina Annie	andrimamonjyannie@gmail.com	annie	scrypt:32768:8:1$gCzstvukfIeHgMTs$bde7ad726d0d32239c8ad9cce2b4c874435a152159cf6b75d2e82b1421d4cb24ed491dca2f7555138129d9f95622c15504be4f69705e4fb73c214561f0dd417e	ADMIN	\N	t	2026-11-25 09:04:44.16669	\N
11	RAKOTOMALALA	Haingosoa Lova	\N	rakotomalala	scrypt:32768:8:1$gCzstvukfIeHgMTs$bde7ad726d0d32239c8ad9cce2b4c874435a152159cf6b75d2e82b1421d4cb24ed491dca2f7555138129d9f95622c15504be4f69705e4fb73c214561f0dd417e	CV	\N	t	2026-11-25 09:04:44.16669	2
\.


--
-- TOC entry 5075 (class 0 OID 0)
-- Dependencies: 244
-- Name: codes_verification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.codes_verification_id_seq', 1, false);


--
-- TOC entry 5076 (class 0 OID 0)
-- Dependencies: 235
-- Name: controle_etapes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.controle_etapes_id_seq', 37, true);


--
-- TOC entry 5077 (class 0 OID 0)
-- Dependencies: 233
-- Name: controles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.controles_id_seq', 24, true);


--
-- TOC entry 5078 (class 0 OID 0)
-- Dependencies: 239
-- Name: documents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.documents_id_seq', 1, true);


--
-- TOC entry 5079 (class 0 OID 0)
-- Dependencies: 225
-- Name: entites_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.entites_id_seq', 6, true);


--
-- TOC entry 5080 (class 0 OID 0)
-- Dependencies: 221
-- Name: etapes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.etapes_id_seq', 7, true);


--
-- TOC entry 5081 (class 0 OID 0)
-- Dependencies: 254
-- Name: fiches_excel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fiches_excel_id_seq', 5, true);


--
-- TOC entry 5082 (class 0 OID 0)
-- Dependencies: 237
-- Name: irregularites_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.irregularites_id_seq', 23, true);


--
-- TOC entry 5083 (class 0 OID 0)
-- Dependencies: 231
-- Name: marches_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.marches_id_seq', 26, true);


--
-- TOC entry 5084 (class 0 OID 0)
-- Dependencies: 219
-- Name: modes_passation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.modes_passation_id_seq', 6, true);


--
-- TOC entry 5085 (class 0 OID 0)
-- Dependencies: 217
-- Name: natures_marche_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.natures_marche_id_seq', 4, true);


--
-- TOC entry 5086 (class 0 OID 0)
-- Dependencies: 246
-- Name: objets_marche_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.objets_marche_id_seq', 6, true);


--
-- TOC entry 5087 (class 0 OID 0)
-- Dependencies: 250
-- Name: observation_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.observation_type_id_seq', 25, true);


--
-- TOC entry 5088 (class 0 OID 0)
-- Dependencies: 227
-- Name: prmp_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.prmp_id_seq', 6, true);


--
-- TOC entry 5089 (class 0 OID 0)
-- Dependencies: 242
-- Name: recommandations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.recommandations_id_seq', 1, false);


--
-- TOC entry 5090 (class 0 OID 0)
-- Dependencies: 252
-- Name: services_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.services_id_seq', 3, true);


--
-- TOC entry 5091 (class 0 OID 0)
-- Dependencies: 248
-- Name: transferts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transferts_id_seq', 6, true);


--
-- TOC entry 5092 (class 0 OID 0)
-- Dependencies: 223
-- Name: types_document_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.types_document_id_seq', 10, true);


--
-- TOC entry 5093 (class 0 OID 0)
-- Dependencies: 229
-- Name: utilisateurs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.utilisateurs_id_seq', 14, true);


--
-- TOC entry 4818 (class 2606 OID 155749)
-- Name: codes_verification codes_verification_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.codes_verification
    ADD CONSTRAINT codes_verification_pkey PRIMARY KEY (id);


--
-- TOC entry 4804 (class 2606 OID 139556)
-- Name: controle_etapes controle_etapes_id_controle_id_etape_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controle_etapes
    ADD CONSTRAINT controle_etapes_id_controle_id_etape_key UNIQUE (id_controle, id_etape);


--
-- TOC entry 4806 (class 2606 OID 139554)
-- Name: controle_etapes controle_etapes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controle_etapes
    ADD CONSTRAINT controle_etapes_pkey PRIMARY KEY (id);


--
-- TOC entry 4801 (class 2606 OID 139532)
-- Name: controles controles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles
    ADD CONSTRAINT controles_pkey PRIMARY KEY (id);


--
-- TOC entry 4813 (class 2606 OID 139617)
-- Name: documents_irregularites documents_irregularites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents_irregularites
    ADD CONSTRAINT documents_irregularites_pkey PRIMARY KEY (id_document, id_irregularite);


--
-- TOC entry 4810 (class 2606 OID 139596)
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- TOC entry 4784 (class 2606 OID 139450)
-- Name: entites entites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entites
    ADD CONSTRAINT entites_pkey PRIMARY KEY (id);


--
-- TOC entry 4774 (class 2606 OID 139427)
-- Name: etapes etapes_libelle_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.etapes
    ADD CONSTRAINT etapes_libelle_key UNIQUE (libelle);


--
-- TOC entry 4776 (class 2606 OID 139429)
-- Name: etapes etapes_ordre_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.etapes
    ADD CONSTRAINT etapes_ordre_key UNIQUE (ordre);


--
-- TOC entry 4778 (class 2606 OID 139425)
-- Name: etapes etapes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.etapes
    ADD CONSTRAINT etapes_pkey PRIMARY KEY (id);


--
-- TOC entry 4836 (class 2606 OID 204902)
-- Name: fiches_excel fiches_excel_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fiches_excel
    ADD CONSTRAINT fiches_excel_pkey PRIMARY KEY (id);


--
-- TOC entry 4808 (class 2606 OID 139581)
-- Name: irregularites irregularites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.irregularites
    ADD CONSTRAINT irregularites_pkey PRIMARY KEY (id);


--
-- TOC entry 4797 (class 2606 OID 139494)
-- Name: marches marches_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marches
    ADD CONSTRAINT marches_pkey PRIMARY KEY (id);


--
-- TOC entry 4799 (class 2606 OID 139496)
-- Name: marches marches_reference_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marches
    ADD CONSTRAINT marches_reference_key UNIQUE (reference);


--
-- TOC entry 4770 (class 2606 OID 139418)
-- Name: modes_passation modes_passation_libelle_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.modes_passation
    ADD CONSTRAINT modes_passation_libelle_key UNIQUE (libelle);


--
-- TOC entry 4772 (class 2606 OID 139416)
-- Name: modes_passation modes_passation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.modes_passation
    ADD CONSTRAINT modes_passation_pkey PRIMARY KEY (id);


--
-- TOC entry 4766 (class 2606 OID 139409)
-- Name: natures_marche natures_marche_libelle_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.natures_marche
    ADD CONSTRAINT natures_marche_libelle_key UNIQUE (libelle);


--
-- TOC entry 4768 (class 2606 OID 139407)
-- Name: natures_marche natures_marche_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.natures_marche
    ADD CONSTRAINT natures_marche_pkey PRIMARY KEY (id);


--
-- TOC entry 4821 (class 2606 OID 163943)
-- Name: objets_marche objets_marche_libelle_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.objets_marche
    ADD CONSTRAINT objets_marche_libelle_key UNIQUE (libelle);


--
-- TOC entry 4823 (class 2606 OID 163941)
-- Name: objets_marche objets_marche_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.objets_marche
    ADD CONSTRAINT objets_marche_pkey PRIMARY KEY (id);


--
-- TOC entry 4828 (class 2606 OID 180325)
-- Name: observation_type observation_type_id_etape_libelle_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.observation_type
    ADD CONSTRAINT observation_type_id_etape_libelle_key UNIQUE (id_etape, libelle);


--
-- TOC entry 4830 (class 2606 OID 180323)
-- Name: observation_type observation_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.observation_type
    ADD CONSTRAINT observation_type_pkey PRIMARY KEY (id);


--
-- TOC entry 4786 (class 2606 OID 139457)
-- Name: prmp prmp_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prmp
    ADD CONSTRAINT prmp_pkey PRIMARY KEY (id);


--
-- TOC entry 4816 (class 2606 OID 139638)
-- Name: recommandations recommandations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommandations
    ADD CONSTRAINT recommandations_pkey PRIMARY KEY (id);


--
-- TOC entry 4832 (class 2606 OID 188563)
-- Name: services services_nom_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.services
    ADD CONSTRAINT services_nom_key UNIQUE (nom);


--
-- TOC entry 4834 (class 2606 OID 188561)
-- Name: services services_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.services
    ADD CONSTRAINT services_pkey PRIMARY KEY (id);


--
-- TOC entry 4826 (class 2606 OID 172137)
-- Name: transferts transferts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transferts
    ADD CONSTRAINT transferts_pkey PRIMARY KEY (id);


--
-- TOC entry 4780 (class 2606 OID 139438)
-- Name: types_document types_document_libelle_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.types_document
    ADD CONSTRAINT types_document_libelle_key UNIQUE (libelle);


--
-- TOC entry 4782 (class 2606 OID 139436)
-- Name: types_document types_document_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.types_document
    ADD CONSTRAINT types_document_pkey PRIMARY KEY (id);


--
-- TOC entry 4789 (class 2606 OID 139475)
-- Name: utilisateurs utilisateurs_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs
    ADD CONSTRAINT utilisateurs_email_key UNIQUE (email);


--
-- TOC entry 4791 (class 2606 OID 139477)
-- Name: utilisateurs utilisateurs_login_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs
    ADD CONSTRAINT utilisateurs_login_key UNIQUE (login);


--
-- TOC entry 4793 (class 2606 OID 139473)
-- Name: utilisateurs utilisateurs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs
    ADD CONSTRAINT utilisateurs_pkey PRIMARY KEY (id);


--
-- TOC entry 4802 (class 1259 OID 139543)
-- Name: idx_controles_marche; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_controles_marche ON public.controles USING btree (id_marche);


--
-- TOC entry 4811 (class 1259 OID 139612)
-- Name: idx_documents_marche; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documents_marche ON public.documents USING btree (id_marche);


--
-- TOC entry 4837 (class 1259 OID 204918)
-- Name: idx_fiches_excel_controle; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fiches_excel_controle ON public.fiches_excel USING btree (id_controle);


--
-- TOC entry 4794 (class 1259 OID 139523)
-- Name: idx_marches_annee; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_marches_annee ON public.marches USING btree (annee_exercice);


--
-- TOC entry 4795 (class 1259 OID 139522)
-- Name: idx_marches_entite; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_marches_entite ON public.marches USING btree (id_entite);


--
-- TOC entry 4814 (class 1259 OID 139649)
-- Name: idx_recommandations_entite; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_recommandations_entite ON public.recommandations USING btree (id_entite);


--
-- TOC entry 4824 (class 1259 OID 172148)
-- Name: idx_transferts_controle; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transferts_controle ON public.transferts USING btree (id_controle);


--
-- TOC entry 4819 (class 1259 OID 155750)
-- Name: ix_codes_verification_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_codes_verification_email ON public.codes_verification USING btree (email);


--
-- TOC entry 4787 (class 1259 OID 188610)
-- Name: uq_chef_par_service; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_chef_par_service ON public.utilisateurs USING btree (id_service) WHERE ((role = 'CHEF_SERVICE'::public.role_utilisateur) AND actif);


--
-- TOC entry 4852 (class 2606 OID 139557)
-- Name: controle_etapes controle_etapes_id_controle_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controle_etapes
    ADD CONSTRAINT controle_etapes_id_controle_fkey FOREIGN KEY (id_controle) REFERENCES public.controles(id) ON DELETE CASCADE;


--
-- TOC entry 4853 (class 2606 OID 139562)
-- Name: controle_etapes controle_etapes_id_etape_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controle_etapes
    ADD CONSTRAINT controle_etapes_id_etape_fkey FOREIGN KEY (id_etape) REFERENCES public.etapes(id);


--
-- TOC entry 4854 (class 2606 OID 139567)
-- Name: controle_etapes controle_etapes_id_utilisateur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controle_etapes
    ADD CONSTRAINT controle_etapes_id_utilisateur_fkey FOREIGN KEY (id_utilisateur) REFERENCES public.utilisateurs(id);


--
-- TOC entry 4848 (class 2606 OID 139533)
-- Name: controles controles_id_marche_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles
    ADD CONSTRAINT controles_id_marche_fkey FOREIGN KEY (id_marche) REFERENCES public.marches(id) ON DELETE CASCADE;


--
-- TOC entry 4849 (class 2606 OID 188570)
-- Name: controles controles_id_service_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles
    ADD CONSTRAINT controles_id_service_fkey FOREIGN KEY (id_service) REFERENCES public.services(id);


--
-- TOC entry 4850 (class 2606 OID 188575)
-- Name: controles controles_id_utilisateur_assigne_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles
    ADD CONSTRAINT controles_id_utilisateur_assigne_fkey FOREIGN KEY (id_utilisateur_assigne) REFERENCES public.utilisateurs(id);


--
-- TOC entry 4851 (class 2606 OID 139538)
-- Name: controles controles_id_utilisateur_validateur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles
    ADD CONSTRAINT controles_id_utilisateur_validateur_fkey FOREIGN KEY (id_utilisateur_validateur) REFERENCES public.utilisateurs(id);


--
-- TOC entry 4856 (class 2606 OID 139597)
-- Name: documents documents_id_marche_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_id_marche_fkey FOREIGN KEY (id_marche) REFERENCES public.marches(id) ON DELETE CASCADE;


--
-- TOC entry 4857 (class 2606 OID 139602)
-- Name: documents documents_id_type_document_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_id_type_document_fkey FOREIGN KEY (id_type_document) REFERENCES public.types_document(id);


--
-- TOC entry 4858 (class 2606 OID 139607)
-- Name: documents documents_id_utilisateur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_id_utilisateur_fkey FOREIGN KEY (id_utilisateur) REFERENCES public.utilisateurs(id);


--
-- TOC entry 4859 (class 2606 OID 139618)
-- Name: documents_irregularites documents_irregularites_id_document_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents_irregularites
    ADD CONSTRAINT documents_irregularites_id_document_fkey FOREIGN KEY (id_document) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- TOC entry 4860 (class 2606 OID 139623)
-- Name: documents_irregularites documents_irregularites_id_irregularite_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents_irregularites
    ADD CONSTRAINT documents_irregularites_id_irregularite_fkey FOREIGN KEY (id_irregularite) REFERENCES public.irregularites(id) ON DELETE CASCADE;


--
-- TOC entry 4866 (class 2606 OID 204903)
-- Name: fiches_excel fiches_excel_id_controle_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fiches_excel
    ADD CONSTRAINT fiches_excel_id_controle_fkey FOREIGN KEY (id_controle) REFERENCES public.controles(id) ON DELETE CASCADE;


--
-- TOC entry 4867 (class 2606 OID 204913)
-- Name: fiches_excel fiches_excel_id_destinataire_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fiches_excel
    ADD CONSTRAINT fiches_excel_id_destinataire_fkey FOREIGN KEY (id_destinataire) REFERENCES public.utilisateurs(id);


--
-- TOC entry 4868 (class 2606 OID 204908)
-- Name: fiches_excel fiches_excel_id_expediteur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fiches_excel
    ADD CONSTRAINT fiches_excel_id_expediteur_fkey FOREIGN KEY (id_expediteur) REFERENCES public.utilisateurs(id);


--
-- TOC entry 4855 (class 2606 OID 139582)
-- Name: irregularites irregularites_id_controle_etape_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.irregularites
    ADD CONSTRAINT irregularites_id_controle_etape_fkey FOREIGN KEY (id_controle_etape) REFERENCES public.controle_etapes(id) ON DELETE CASCADE;


--
-- TOC entry 4842 (class 2606 OID 139497)
-- Name: marches marches_id_entite_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marches
    ADD CONSTRAINT marches_id_entite_fkey FOREIGN KEY (id_entite) REFERENCES public.entites(id);


--
-- TOC entry 4843 (class 2606 OID 139512)
-- Name: marches marches_id_mode_passation_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marches
    ADD CONSTRAINT marches_id_mode_passation_fkey FOREIGN KEY (id_mode_passation) REFERENCES public.modes_passation(id);


--
-- TOC entry 4844 (class 2606 OID 139507)
-- Name: marches marches_id_nature_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marches
    ADD CONSTRAINT marches_id_nature_fkey FOREIGN KEY (id_nature) REFERENCES public.natures_marche(id);


--
-- TOC entry 4845 (class 2606 OID 163944)
-- Name: marches marches_id_objet_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marches
    ADD CONSTRAINT marches_id_objet_fkey FOREIGN KEY (id_objet) REFERENCES public.objets_marche(id);


--
-- TOC entry 4846 (class 2606 OID 139502)
-- Name: marches marches_id_prmp_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marches
    ADD CONSTRAINT marches_id_prmp_fkey FOREIGN KEY (id_prmp) REFERENCES public.prmp(id);


--
-- TOC entry 4847 (class 2606 OID 139517)
-- Name: marches marches_id_utilisateur_saisie_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marches
    ADD CONSTRAINT marches_id_utilisateur_saisie_fkey FOREIGN KEY (id_utilisateur_saisie) REFERENCES public.utilisateurs(id);


--
-- TOC entry 4865 (class 2606 OID 180326)
-- Name: observation_type observation_type_id_etape_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.observation_type
    ADD CONSTRAINT observation_type_id_etape_fkey FOREIGN KEY (id_etape) REFERENCES public.etapes(id);


--
-- TOC entry 4839 (class 2606 OID 139458)
-- Name: prmp prmp_id_entite_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prmp
    ADD CONSTRAINT prmp_id_entite_fkey FOREIGN KEY (id_entite) REFERENCES public.entites(id) ON DELETE CASCADE;


--
-- TOC entry 4861 (class 2606 OID 139644)
-- Name: recommandations recommandations_id_controle_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommandations
    ADD CONSTRAINT recommandations_id_controle_fkey FOREIGN KEY (id_controle) REFERENCES public.controles(id);


--
-- TOC entry 4862 (class 2606 OID 139639)
-- Name: recommandations recommandations_id_entite_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommandations
    ADD CONSTRAINT recommandations_id_entite_fkey FOREIGN KEY (id_entite) REFERENCES public.entites(id);


--
-- TOC entry 4863 (class 2606 OID 172138)
-- Name: transferts transferts_id_controle_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transferts
    ADD CONSTRAINT transferts_id_controle_fkey FOREIGN KEY (id_controle) REFERENCES public.controles(id) ON DELETE CASCADE;


--
-- TOC entry 4864 (class 2606 OID 172143)
-- Name: transferts transferts_id_utilisateur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transferts
    ADD CONSTRAINT transferts_id_utilisateur_fkey FOREIGN KEY (id_utilisateur) REFERENCES public.utilisateurs(id);


--
-- TOC entry 4838 (class 2606 OID 139439)
-- Name: types_document types_document_id_etape_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.types_document
    ADD CONSTRAINT types_document_id_etape_fkey FOREIGN KEY (id_etape) REFERENCES public.etapes(id);


--
-- TOC entry 4840 (class 2606 OID 139478)
-- Name: utilisateurs utilisateurs_id_entite_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs
    ADD CONSTRAINT utilisateurs_id_entite_fkey FOREIGN KEY (id_entite) REFERENCES public.entites(id);


--
-- TOC entry 4841 (class 2606 OID 188564)
-- Name: utilisateurs utilisateurs_id_service_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs
    ADD CONSTRAINT utilisateurs_id_service_fkey FOREIGN KEY (id_service) REFERENCES public.services(id);


-- Completed on 2026-11-26 15:27:49

--
-- PostgreSQL database dump complete
--

\unrestrict lTcEEMpizaZkhBLmFwKWwOx9yUJDchpVNHw69yH65mbLzgvHVsaaD3gJOTtep3E

