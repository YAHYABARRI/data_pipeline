# E-commerce Delivery Pipeline 2026

Pipeline Data Engineering Python, PostgreSQL 18, Airflow 3 et Docker basé sur le dataset Kaggle [E-Commerce Delivery and Shipping Data 2026](https://www.kaggle.com/datasets/datascikhan/e-commerce-delivery-and-shipping-data-2026).

## Dataset audité

- 50 000 commandes et 30 colonnes
- Période : 2026-01-01 au 2026-12-31
- 50 000 `order_id` distincts, aucun doublon exact et aucune valeur vide
- 6 348 clients, 17 pays, 10 entrepôts, 8 transporteurs et 12 catégories
- 28 162 commandes marquées en retard et 8 625 demandes de retour
- Fichier : `E-commerce_Delivery_Shipping_Data_2026.csv`
- SHA-256 : `ec8c8fc0decb5a110eb4987c262a866a26de4e9c2ad11befb2836b975046bf2b`

Le projet télécharge automatiquement le fichier public avec `kagglehub` s'il n'existe pas dans `datasets/raw/`.

## Architecture

- `etl/ecommerce_extract.py` : téléchargement Kaggle, audit, SHA-256 et ingestion par lots.
- `etl/ecommerce_transform.py` : validation, conversion des types et KPI quotidiens.
- `etl/ecommerce_pipeline.py` : transaction complète et rollback en cas d'erreur.
- `dags/delivery_pipeline.py` : orchestration Airflow sans données volumineuses dans XCom.
- `migrations/002_ecommerce_delivery.sql` : migration PostgreSQL additive.
- `tests/` : tests du CSV et de la migration.

Tables utilisées :

- `ecommerce_ingestion_runs` : suivi des fichiers par SHA-256.
- `ecommerce_orders_raw` : copie brute des 30 colonnes.
- `ecommerce_orders` : commandes nettoyées et typées.
- `ecommerce_daily_stats` : volumes, retards, retours, délais, valeur et coût par date.

Les anciennes tables LaDe ne sont pas supprimées automatiquement afin d'éviter toute perte de données.

## Exécution PowerShell

```powershell
cd C:\Users\yahya\Desktop\postgresql

$env:UV_PROJECT_ENVIRONMENT = '.venv-win'
uv sync --dev

docker compose up -d postgres
Get-Content -Raw .\migrations\002_ecommerce_delivery.sql |
    docker exec -i delivery-postgres psql -U postgres -d delivery_db -v ON_ERROR_STOP=1

uv run python .\main.py
uv run pytest -q
```

Sortie attendue :

```text
E-commerce pipeline completed: 50000 raw rows, 50000 valid rows, 0 invalid rows.
```

## Airflow

```powershell
docker compose up -d --build airflow
docker compose exec airflow airflow dags unpause delivery_pipeline
docker compose exec airflow airflow dags trigger delivery_pipeline
docker compose exec airflow airflow dags list-runs delivery_pipeline --limit 1
```

Le mode `standalone` initialise et migre automatiquement la base de métadonnées Airflow. Ne lancez pas `airflow db migrate` pendant que le conteneur `airflow` fonctionne.

Interface : `http://localhost:8080`. Utilisateur : `admin`.

```powershell
docker compose exec airflow sh -c "cat /opt/airflow/simple_auth_manager_passwords.json.generated"
```

## KPI SQL

```sql
SELECT COUNT(*) FROM ecommerce_orders;
SELECT * FROM ecommerce_daily_stats ORDER BY order_date;
SELECT carrier, COUNT(*) AS orders, ROUND(AVG(late_delivery::integer), 4) AS late_rate
FROM ecommerce_orders
GROUP BY carrier
ORDER BY late_rate DESC;
```
myp : 4SkqKX3bx9sg4TNF