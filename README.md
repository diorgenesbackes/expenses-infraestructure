# Infraestrutura local

Este diretório reúne o Compose e a configuração necessária para executar o Expenses
no Docker Desktop. Os Dockerfiles ficam em `expenses-service/` e `expenses-ui/`;
as migrations permanecem em `expenses-liquibase/`.

## Requisitos e configuração

- Docker Desktop em execução, com o contexto `desktop-linux` disponível.
- Docker Compose com suporte a `--wait`.
- Liquibase e Java no host para aplicar migrations. Node e .NET são necessários
  no host apenas quando as aplicações forem executadas fora dos containers.

A partir da raiz do projeto:

```bash
cd expenses-infrastructure
```

Em uma nova instalação, prepare o arquivo local e defina `POSTGRES_PASSWORD`
antes de iniciar os serviços. O comando preserva um `.env` existente:

```bash
cp -n .env.example .env
```

| Variável | Finalidade | Padrão no Compose |
| --- | --- | --- |
| `POSTGRES_DB` | Nome do banco. | `expenses` |
| `POSTGRES_USER` | Usuário PostgreSQL. | `admin` |
| `POSTGRES_PASSWORD` | Senha usada pelo banco e pela API. | Obrigatória. |
| `ASPNETCORE_ENVIRONMENT` | Ambiente da API. | `Development` |

O `.env` é ignorado pelo Git. O `.env.example` é o modelo versionado. O Compose
carrega o `.env` deste diretório; a API recebe a conexão por variável de ambiente.
User Secrets da máquina e o arquivo privado do Liquibase têm configuração própria.

## Iniciar e conferir os serviços

Todos os comandos Compose deste guia são executados em `expenses-infrastructure/`:

```bash
docker --context desktop-linux compose config --quiet
docker --context desktop-linux compose up -d --build --wait
docker --context desktop-linux compose ps
```

Os contextos de build são `../expenses-service` e `../expenses-ui`, relativos ao
arquivo [compose.yaml](compose.yaml). O comando dispensa `--project-directory`.
Se preferir permanecer na raiz do repositório, use o caminho explícito:

```bash
docker --context desktop-linux compose --env-file expenses-infrastructure/.env -f expenses-infrastructure/compose.yaml up -d --build --wait
```

| Serviço | Container | Acesso local |
| --- | --- | --- |
| Frontend React / Nginx | `expenses-frontend` | <http://localhost:5173> |
| Backend ASP.NET Core | `expenses-backend` | <http://localhost:5183> |
| Swagger em Development | Backend | <http://localhost:5183/swagger> |
| Health da API | Backend | <http://localhost:5183/health> |
| Health do banco pela API | Backend | <http://localhost:5183/health/db> |
| PostgreSQL | `expenses-postgres` | `127.0.0.1:5432` |

Os containers aparecem no grupo `expenses-local` no Docker Desktop. As portas são
publicadas apenas na interface local. Encerre processos `dotnet run` ou
`npm run dev` que estejam ocupando as mesmas portas antes de subir os containers.

A inicialização aguarda o PostgreSQL saudável antes do backend e o `/health/db`
saudável antes do frontend. O health check do frontend verifica a página inicial.

```bash
curl -i http://localhost:5183/health
curl -i http://localhost:5183/health/db
curl -i http://localhost:5173/api/health/db
```

## Banco e migrations

Para iniciar somente o PostgreSQL:

```bash
docker --context desktop-linux compose up -d --wait postgres
```

Em um banco novo, aplique os changelogs conforme o
[guia do Liquibase](../expenses-liquibase/README.md) antes de consultar usuários.
O `/health/db` verifica conectividade, sem validar a estrutura do banco. A API
não aplica migrations automaticamente.

Para abrir um terminal SQL solicitando a senha, com os valores padrão de usuário
e banco:

```bash
docker --context desktop-linux compose exec postgres psql -h 127.0.0.1 -U admin -d expenses -W
```

O `name: expenses-local` mantém a identidade do projeto Compose e o volume
`expenses-local_postgres_data`. Renomear o diretório não muda esse nome. Parar ou
recriar containers preserva o volume. As variáveis `POSTGRES_*` inicializam volumes
vazios; mudanças posteriores de senha precisam ser aplicadas também no banco.

## Build, comunicação e ambiente

Os builds usam múltiplas etapas: SDK .NET 10 publica a API em Release e Node 24
executa `npm ci` e compila o React. As imagens finais executam ASP.NET Core e Nginx
com usuários sem privilégios de root. Os arquivos `.dockerignore` excluem segredos
locais e artefatos da máquina dos contextos de build.

A API acessa `postgres:5432` pela rede do Compose. O Nginx encaminha `/api/` para
`backend:8080`, removendo o prefixo. Chamadas do React podem usar URLs relativas,
como `fetch('/api/health/db')`, mantendo a mesma origem. O frontend oferece fallback
para `index.html` nas rotas da aplicação e cache para os assets gerados pelo Vite.

O ambiente local é `Development` por padrão, habilitando Swagger e a listagem de
usuários. Ao definir `ASPNETCORE_ENVIRONMENT=Production` no `.env`, essas rotas são
desabilitadas; `/health` e `/health/db` permanecem disponíveis.

As imagens servem os arquivos publicados, sem hot reload. Após modificar código,
repita `compose up -d --build --wait`. Para construir sem iniciar os containers:

```bash
docker --context desktop-linux compose build backend frontend
```

## Logs e encerramento

```bash
docker --context desktop-linux compose logs -f backend frontend
docker --context desktop-linux compose stop
```

`stop` encerra os serviços preservando os containers e os dados. Para iniciar
novamente, execute `compose up -d --wait`.

## Problemas comuns

Se aparecer `docker-credential-desktop: executable file not found` no macOS,
adicione os executáveis do Docker Desktop ao `PATH` da sessão e repita o comando:

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
```

Se o Compose não encontrar a configuração, confira se o terminal está em
`expenses-infrastructure/` ou use o comando com `-f` mostrado acima. Para falhas
de conexão com o daemon, confira se o Docker Desktop está em execução.

Referências: [Docker Compose](https://docs.docker.com/reference/cli/docker/compose/),
[imagens .NET](https://github.com/dotnet/dotnet-docker),
[Nginx sem root](https://github.com/nginx/docker-nginx-unprivileged) e
[imagem PostgreSQL](https://hub.docker.com/_/postgres).
