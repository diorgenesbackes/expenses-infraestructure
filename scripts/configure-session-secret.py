"""Generate a private stable email-HMAC key without displaying it or replacing an existing key."""
import base64
import json
from pathlib import Path
import secrets
import subprocess
import xml.etree.ElementTree as ET

project = Path(__file__).resolve().parents[2] / 'expenses-service' / 'Expenses.Api'
identifier = ET.parse(project / 'Expenses.Api.csproj').findtext('.//UserSecretsId')
secret_file = Path.home() / '.microsoft/usersecrets' / identifier / 'secrets.json'
if secret_file.exists() and json.loads(secret_file.read_text(encoding='utf-8-sig')).get('Identity:EmailHmacKey'):
    print('Chave HMAC já configurada; preservada sem exibir o valor.')
else:
    payload = json.dumps({'Identity:EmailHmacKey': base64.b64encode(secrets.token_bytes(32)).decode('ascii')})
    result = subprocess.run(['dotnet', 'user-secrets', 'set', '--project', str(project)], input=payload,
                            text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode:
        raise SystemExit('Não foi possível configurar a chave HMAC privada.')
    print('Chave HMAC gerada e salva nos User Secrets; valor não exibido.')
