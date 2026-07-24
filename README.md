<p align="center">
  <img src="https://raw.githubusercontent.com/israelmarques1024-dotcom/karnel-termux/main/assets/images/karnel-logo.png" alt="Karnel Termux" width="300">
</p>

<p align="center">
  <strong>Registry oficial de plugins revisados do <a href="https://github.com/israelmarques1024-dotcom/karnel-termux">Karnel Termux</a></strong>
</p>

<p align="center">
  <a href="https://github.com/israelmarques1024-dotcom/karnel-plugins/blob/main/registry.json">
    <img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fisraelmarques1024-dotcom%2Fkarnel-plugins%2Fmain%2Fregistry.json&amp;query=%24.plugins.length&amp;label=plugins&amp;color=0078D4&amp;style=for-the-badge" alt="Plugin count">
  </a>
  <a href="CONTRIBUTING.md">
    <img src="https://img.shields.io/badge/contributions-reviewed-brightgreen?style=for-the-badge" alt="Reviewed contributions">
  </a>
</p>

## Uso

```bash
# Descobrir plugins aprovados
karnel plugin search
karnel plugin search backup --compatible
karnel plugin search --command karnel-hello

# Instalar ou atualizar um plugin aprovado
karnel plugin install karnel-hello
karnel plugin update karnel-hello

# Listar ou remover
karnel plugin list
karnel plugin remove karnel-hello
```

`karnel plugin install <owner/repo>` continua existindo, mas repositórios que
não estejam neste registry exigem `--unsafe` e uma confirmação explícita:

```bash
karnel plugin install owner/repo --unsafe
```

## Modelo de Confiança

Plugins são arquivos Bash carregados pelo processo do Karnel. Eles executam com
as permissões do usuário atual e **não possuem sandbox real**.

- Entradas deste registry são revisadas e validadas pela CI antes de aparecerem em `search`.
- O cliente clona em staging, valida schema, licença, comandos, compatibilidade, checksum e colisões, e só então ativa o plugin com uma troca atômica.
- Atualizações clonam uma cópia nova e validam tudo outra vez. O cliente não usa `git pull`, portanto não cria merges inesperados.
- Repositórios arbitrários só são permitidos com `--unsafe` e confirmação. Essa opção não transforma o código em seguro.
- `capabilities` são declarações informativas para revisão. Bash não oferece isolamento de rede, filesystem, processos ou ambiente.

O registry reduz risco de cadeia de suprimentos, mas não substitui a revisão do
código. Leia plugins não aprovados antes de instalá-los.

## Contrato do Plugin

Todo plugin precisa ter `karnel-plugin.json`, `LICENSE` ou `LICENSE.md`, e os
arquivos declarados em `commands/`. Campos desconhecidos são rejeitados.

```text
meu-plugin/
├── karnel-plugin.json
├── LICENSE
└── commands/
    └── meu-comando.sh
```

```json
{
  "schemaVersion": 1,
  "name": "meu-plugin",
  "version": "1.0.0",
  "description": "Descrição curta e sem quebra de linha",
  "commands": ["meu-comando"],
  "minKarnelVersion": "4.11.6",
  "license": "MIT",
  "checksum": "sha256:<hash-do-payload-do-plugin>",
  "capabilities": ["network"]
}
```

`name` e cada comando usam `^[a-z][a-z0-9-]{0,62}$`. `version` e
`minKarnelVersion` usam SemVer. O arquivo `commands/meu-comando.sh` deve
declarar `meu-comando_main()` com `{` na mesma linha. Symlinks não são aceitos
em nenhum arquivo do payload.

O checksum é SHA-256 do payload completo do plugin: cada arquivo regular, exceto
`karnel-plugin.json`, `.karnel-install.json` e `.git/`, entra em ordem
lexicográfica como `caminho-relativo\0<sha256-do-arquivo>\0`. Isso protege
comandos, helpers, executáveis e licença que o registry aprovou. Ao alterar
qualquer arquivo do payload, atualize o checksum, a versão e a entrada do
registry.

Schemas versionados:

- [`schemas/karnel-plugin.schema.json`](schemas/karnel-plugin.schema.json)
- [`schemas/registry.schema.json`](schemas/registry.schema.json)

## Registry

Uma entrada aprovada declara fonte, ref, metadados e integridade do manifest:

```json
{
  "name": "meu-plugin",
  "repo": "owner/meu-plugin",
  "ref": "main",
  "version": "1.0.0",
  "description": "Descrição curta e sem quebra de linha",
  "commands": ["meu-comando"],
  "minKarnelVersion": "4.11.6",
  "license": "MIT",
  "checksum": "sha256:<hash-do-payload-do-plugin>",
  "capabilities": ["network"]
}
```

`path` permite manter um plugin em subdiretório de um repositório revisado.
`commit` opcional fixa um SHA Git completo; quando presente, o cliente e a CI o
comparam ao commit obtido. O cliente sempre registra repo, ref, commit e versão
instalada em metadados locais.

O plugin oficial mínimo [`karnel-hello`](plugins/karnel-hello) exercita o fluxo
completo de registry, manifesto, checksum e dispatcher.

## Revisão e Segurança

- Consulte [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir um PR.
- Consulte [REVIEW_POLICY.md](REVIEW_POLICY.md) para os critérios de aprovação.
- Consulte [SECURITY.md](SECURITY.md) para reportar vulnerabilidades de forma privada.

O workflow de CI valida JSON, schema semântico, nomes, comandos e repositórios
únicos, colisões com comandos nativos, SemVer, acessibilidade do repositório,
manifest correspondente, licença, symlinks, checksum de payload, Bash syntax e
ShellCheck sem executar o código do plugin.
