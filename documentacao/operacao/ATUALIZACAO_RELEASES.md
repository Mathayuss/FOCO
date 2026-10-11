# FOCO — Atualização por Releases

## Objetivo

Atualizar a instalação localizada em `/opt/foco` sem depender de `git pull`, mantendo:

- atualização online por GitHub Releases;
- atualização local/offline por arquivo;
- interface visual no terminal;
- backup do código;
- backup lógico do PostgreSQL;
- validação SHA-256;
- migrations Alembic;
- rebuild dos containers;
- healthcheck;
- rollback em caso de falha.

## Arquitetura de distribuição

```text
Desenvolvimento
      |
      | git tag v0.3.2
      v
GitHub Actions
      |
      +-- testes SQLite
      +-- testes PostgreSQL/PostGIS
      +-- build e testes Playwright
      +-- validação do atualizador
      +-- pacote Docker de produção
      |
      v
GitHub Release v0.3.2
      |
      +-- FOCO-v0.3.2.tar.gz
      +-- FOCO-v0.3.2.tar.gz.sha256
              |
              v
      /opt/foco na VM
```

O servidor de produção não precisa possuir Git.

O gerador `infraestrutura/scripts/preparar_release.sh` substitui, somente dentro do pacote, os arquivos de desenvolvimento pelos artefatos de produção:

- `compose.producao.yml` torna-se `docker-compose.yml`;
- `frontend/Dockerfile.producao` torna-se o Dockerfile padrão;
- `.env.producao.example` torna-se `.env.example`;
- o `.env` real nunca entra no pacote.

Para validar localmente:

```bash
bash infraestrutura/atualizacao/testar-atualizador.sh
python3 -m unittest discover -s infraestrutura/tests -v
bash infraestrutura/scripts/preparar_release.sh 0.3.2 /tmp
```

## Instalação do atualizador

Copie `infraestrutura/atualizacao/` para a VM e execute:

```bash
cd infraestrutura/atualizacao
sudo ./instalar-atualizador.sh
```

Depois:

```bash
sudo foco-atualizar
```

## Menu visual

O comando sem argumentos abre a interface:

```text
FOCO
Central de Atualização de Releases

Versão instalada: 0.3.1

  1  Status da instalação
  2  Verificar atualização online
  3  Atualizar pela última release
  4  Instalar pacote local / offline
  5  Restaurar último backup
  6  Exibir log do atualizador
  0  Sair
```

## Comandos diretos

Verificar:

```bash
sudo foco-atualizar --verificar
```

Atualizar:

```bash
sudo foco-atualizar --atualizar
```

Pacote offline:

```bash
sudo foco-atualizar \
  --arquivo /tmp/FOCO-v0.3.2.tar.gz \
  --sha256 /tmp/FOCO-v0.3.2.tar.gz.sha256
```

Status:

```bash
sudo foco-atualizar --status
```

Restaurar último backup:

```bash
sudo foco-atualizar --restaurar-ultimo
```

## Modo sem acesso ao Git

Há dois cenários diferentes.

### Sem cliente Git, mas com acesso HTTPS ao GitHub

Use normalmente:

```bash
sudo foco-atualizar --atualizar
```

O script consulta a API de Releases e baixa por HTTPS usando `curl`.

Ele **não executa**:

```text
git clone
git fetch
git pull
```

### Sem acesso ao GitHub

Em outra máquina, baixe na página Releases:

```text
FOCO-vX.Y.Z.tar.gz
FOCO-vX.Y.Z.tar.gz.sha256
```

Transfira via SCP, SMB, NFS, pendrive ou outro meio.

Na VM:

```bash
sudo foco-atualizar \
  --arquivo /tmp/FOCO-vX.Y.Z.tar.gz \
  --sha256 /tmp/FOCO-vX.Y.Z.tar.gz.sha256
```

## Processo de atualização

Antes de alterar a aplicação o script:

1. valida dependências;
2. valida SHA-256;
3. valida o conteúdo do pacote;
4. compara versões;
5. cria backup do código;
6. executa `pg_dump`;
7. para API e interface;
8. aplica a nova release;
9. valida `docker compose config`;
10. reconstrói as imagens;
11. executa `alembic upgrade head`;
12. sobe os serviços;
13. testa API e interface.

Se a atualização falhar, o script restaura o backup anterior.

## Diretórios

```text
/opt/foco
/var/backups/foco
/var/cache/foco-atualizador
/var/log/foco-atualizador.log
/etc/foco-atualizador.conf
/usr/local/sbin/foco-atualizar
```

## Segurança

O `.env` local nunca é substituído pelo pacote.

O pacote de release deve ser acompanhado de SHA-256.

O atualizador rejeita caminhos absolutos e `../` dentro do TAR.

O banco é salvo antes das migrations.

## Publicação de uma release

O workflow `.github/workflows/publicar_release.yml` é acionado por uma tag SemVer.

Exemplo:

```bash
git tag -a v0.3.2 -m "FOCO v0.3.2"
git push origin v0.3.2
```

Se todos os testes passarem, o workflow publica automaticamente:

```text
FOCO-v0.3.2.tar.gz
FOCO-v0.3.2.tar.gz.sha256
```

## Observação sobre o repositório atual

No momento em que este pacote foi gerado, o repositório ainda não possuía GitHub Releases publicadas. O atualizador já trata esse caso e informa que não há release disponível.

A primeira tag/release recomendada para inaugurar o fluxo é a próxima versão estável após a integração deste mecanismo.
