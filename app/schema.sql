DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS creneau;
DROP TABLE IF EXISTS sondage;
DROP TABLE IF EXISTS creneau_sondage;
DROP TABLE IF EXISTS sondage_user;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE sondage (
  key TEXT UNIQUE NOT NULL,
  titre TEXT UNIQUE NOT NULL,
  date_entree DATETIME,
  date_maj DATETIME,
  lieu TEXT,
  description TEXT,
  liste_options TEXT NOT NULL
);

CREATE TABLE sondage_user (
  sondage_key TEXT UNIQUE NOT NULL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (sondage_key) REFERENCES sondage (key)
  FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE creneau (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  debut DATETIME,
  fin DATETIME
);

CREATE TABLE creneau_sondage (
  creneau_id INTEGER NOT NULL,
  sondage_key TEXT UNIQUE NOT NULL,
  FOREIGN KEY (creneau_id) REFERENCES creneau (id),
  FOREIGN KEY (sondage_key) REFERENCES sondage (key)
)
