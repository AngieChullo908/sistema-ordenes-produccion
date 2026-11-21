import json
import os
from pathlib import Path

DIRECTORY = Path(os.environ.get('APPDATA', Path.home() / '.config')) / 'AVECESAR'
PATH = DIRECTORY / 'conexion.json'
DEFAULTS = dict(host='localhost', port='5432', dbname='avecesar_produccion', user='postgres', sslmode='prefer')

def load():
    try:
        data = json.loads(PATH.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            return DEFAULTS.copy()
        return {k: str(data.get(k, v)) for k, v in DEFAULTS.items()}
    except (OSError, ValueError, TypeError):
        return DEFAULTS.copy()

def save(values):
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps({k: values[k] for k in DEFAULTS}, indent=2), encoding='utf-8')
