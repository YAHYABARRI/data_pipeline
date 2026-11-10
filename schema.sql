create table client (
    id_client INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY ,
    nom VARCHAR(100) NOT NULL ,
    email VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
create table restaurants (
    id_restaurant INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY ,
    nom VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
create table order_summary(
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nbr_commandes INTEGER NOT NULL,
    somme NUMERIC(10,2) NOT NULL,
    moyenne NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

create table drivers (
    drivers_id INTEGER  GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    is_available BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

create table commandes(
    id_commande INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_client INTEGER REFERENCES client(id_client) NOT NULL,
    id_restaurant INTEGER REFERENCES restaurants(id_restaurant) NOT NULL,
    drivers_id INTEGER REFERENCES drivers(drivers_id),
    montant NUMERIC(10,2) CHECK (montant>=0) NOT NULL,
    statut VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
 );
