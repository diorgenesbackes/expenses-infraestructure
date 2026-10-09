"""Store the Cognito client secret in .NET User Secrets without shell history."""

import getpass
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main() -> int:
    if not sys.stdin.isatty():
        print("Execute este script em um terminal interativo.", file=sys.stderr)
        return 1
    dotnet = shutil.which("dotnet")
    if dotnet is None:
        print("O SDK .NET precisa estar instalado.", file=sys.stderr)
        return 1
    project = Path(__file__).resolve().parents[2] / "expenses-service" / "Expenses.Api"
    secret = getpass.getpass("Cole o Cognito Client Secret (entrada oculta): ")
    if not secret or secret.isspace():
        print("Valor vazio: nenhuma configuração foi alterada.", file=sys.stderr)
        return 1
    result = subprocess.run(
        [dotnet, "user-secrets", "set", "--project", str(project)],
        input=json.dumps({"Cognito:ClientSecret": secret}),
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        print("Não foi possível salvar o segredo. Confira o SDK e o acesso aos User Secrets.", file=sys.stderr)
        return 1
    print("Client Secret salvo nos User Secrets da API. O valor não foi exibido.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nOperação cancelada.", file=sys.stderr)
        sys.exit(1)
