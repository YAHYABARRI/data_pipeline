# Pipeline Data Engineering LaDe

Ce projet charge le fichier réel `Cainiao-AI/LaDe/delivery_five_cities.csv` dans PostgreSQL, le valide, le transforme et produit des agrégations quotidiennes orchestrées par Airflow 3.

## Audit du fichier fourni

Le fichier local audité fait 135 539 702 octets, contient 472 419 lignes et porte le SHA-256 `a22b49b57a0201a2b569f80a8282e9147d37db1c2cc374fdf6111aad3d9a3d97`.

Colonnes réelles :

```text
order_id, from_dipan_id, from_city_name, delivery_user_id,
poi_lng, poi_lat, aoi_id, typecode, receipt_time,
receipt_lng, receipt_lat, sign_time, sign_lng, sign_lat, ds
```

Constats principaux :

- Le grain est une commande/un événement de livraison, et non un point de trajectoire GPS.
- Les 472 419 `order_id` sont distincts ; 1 870 livreurs, 134 régions et 23 659 AOI sont présents.
- Le fichier nommé « five cities » ne contient ici que Hangzhou (185 589), Shanghai (165 583) et Chongqing (121 247).
- `sign_lng` et `sign_lat` sont vides à 100 %. `typecode` est vide sur 1 360 lignes (0,288 %).
- `ds` est un mois-jour `MMDD` sur 15 jours. `receipt_time` et `sign_time` utilisent `MM-DD HH:MM:SS`, sans année ni fuseau horaire.
- Les coordonnées ont des ordres de grandeur d'environ 8,8 à 10,6 millions et -7,8 à -7,4 millions. Elles ne sont pas des degrés WGS84. Le pipeline les conserve comme coordonnées projetées/anonymisées `x/y`, sans distance ni carte.

La fiche officielle LaDe décrit le jeu principal LaDe-D avec un autre schéma. Ce fichier précis, anciennement nommé `delivery_trajectory.csv`, doit donc être traité selon ses propres colonnes.

Sources : [dataset LaDe](https://huggingface.co/datasets/Cainiao-AI/LaDe), [fichier exact](https://huggingface.co/datasets/Cainiao-AI/LaDe/blob/main/delivery_five_cities.csv).

## Architecture

- `migrations/001_lade_delivery.sql` : migration additive, idempotente, sans suppression des anciennes tables.
- `migrations/001_lade_delivery_down.sql` : rollback explicite des seules tables LaDe.
- `etl/lade_extract.py` : contrôle du schéma, SHA-256, lecture UTF-8 et chargement par lots.
- `etl/lade_transform.py` : validation SQL, tables nettoyées et statistiques.
- `etl/lade_pipeline.py` : transaction du pipeline CLI.
- `dags/delivery_pipeline.py` : DAG Airflow avec branche fichier vide, XCom légers et contrôle qualité avant chargement analytique.
- `datasets/raw/` : emplacement du CSV, séparé des données PostgreSQL.

Tables ajoutées : `lade_ingestion_runs`, `lade_delivery_raw`, `lade_couriers`, `lade_delivery_events` et `lade_daily_city_stats`.

L'idempotence repose sur le SHA-256 du fichier et sur `order_id`. Un second lancement ne duplique ni les lignes brutes ni les événements ni les agrégats.

## Exécution sous PowerShell

Placez le fichier sous `datasets/raw/delivery_five_cities.csv`, puis :

```powershell
docker compose up -d postgres
Get-Content -Raw .\migrations\001_lade_delivery.sql | docker exec -i delivery-postgres psql -U postgres -d delivery_db -v ON_ERROR_STOP=1

$env:UV_PROJECT_ENVIRONMENT = '.venv-win'
uv sync --dev
uv run python .\main.py
uv run pytest -q
```

Pour Airflow :

```powershell
docker compose up -d --build airflow
docker compose exec airflow airflow dags list
docker compose exec airflow airflow dags trigger delivery_pipeline
```

Interface : `http://localhost:8080`. Le mot de passe du mode `standalone` est régénéré lors d'une nouvelle initialisation et se lit avec :

```powershell
docker compose exec airflow sh -c "cat /opt/airflow/simple_auth_manager_passwords.json.generated"
```

## KPI disponibles et limites

`lade_daily_city_stats` fournit le nombre de livraisons, livreurs, régions, AOI et types manquants par ville et `ds`. Les tables sources permettent aussi les volumes par livreur, AOI, région ou type.

Les distances, vitesses, retards et durées calendaires ne sont volontairement pas calculés : le CRS, l'année et le fuseau ne sont pas confirmés, et les coordonnées de signature sont absentes. Les fichiers LaDe-D normalisés permettraient ensuite l'analyse des durées acceptation-livraison, des trajectoires proches des événements et des modèles ETA/routage.

## Requêtes de contrôle

```sql
SELECT status, rows_seen, rows_inserted, source_sha256 FROM lade_ingestion_runs;
SELECT COUNT(*) FROM lade_delivery_raw;
SELECT COUNT(*) FROM lade_delivery_events;
SELECT * FROM lade_daily_city_stats ORDER BY ds, city_name;
```

Le rollback est disponible dans `migrations/001_lade_delivery_down.sql`, mais n'est jamais exécuté automatiquement.
