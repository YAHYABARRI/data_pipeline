FROM python:3.12-slim

# Installer uv depuis l'image officielle
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

# Empêcher uv de télécharger un autre Python
ENV UV_PYTHON_DOWNLOADS=0

# Afficher directement les logs Python dans Docker
ENV PYTHONUNBUFFERED=1

# Dossier de travail dans le container
WORKDIR /app

# Copier d'abord les fichiers de dépendances
COPY pyproject.toml uv.lock .python-version ./

# Installer les dépendances sans installer encore notre projet
RUN uv sync --locked --no-install-project

# Copier le reste du projet
COPY . .

# Finaliser l'installation du projet
RUN uv sync --locked

# Commande exécutée lorsque le container démarre
CMD ["uv", "run", "main.py"]