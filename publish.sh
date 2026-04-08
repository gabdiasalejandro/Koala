#!/usr/bin/env bash
set -euo pipefail

# Carga .env si existe
if [ -f ".env" ]; then
    set -o allexport
    source .env
    set +o allexport
fi

if [ -z "${PYPI_TOKEN:-}" ]; then
    echo "Error: PYPI_TOKEN no está definido." >&2
    echo "Crea un archivo .env con PYPI_TOKEN=pypi-..." >&2
    exit 1
fi

echo "Limpiando builds anteriores..."
rm -rf dist/ build/ *.egg-info/

echo "Construyendo distribución..."
python -m build

echo "Publicando en PyPI..."
python -m twine upload dist/* \
    --username __token__ \
    --password "$PYPI_TOKEN" \
    --non-interactive

echo "Publicado correctamente."
