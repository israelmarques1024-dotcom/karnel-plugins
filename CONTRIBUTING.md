# Contribuindo com o Registry

Leia o [modelo de confiança](README.md#modelo-de-confiança) antes de submeter um
plugin. Um plugin Bash não é isolado: ele terá as permissões do usuário que o
instalar.

## Criar um Plugin

```bash
karnel plugin create meu-plugin
```

O comando cria um manifesto Schema v1, licença, comando mínimo e metadados
locais. Mantenha somente os comandos declarados no manifest:

```text
meu-plugin/
├── karnel-plugin.json
├── LICENSE
└── commands/
    └── meu-comando.sh
```

Cada `commands/meu-comando.sh` precisa definir `meu-comando_main()` com `{` na
mesma linha. Nomes de plugin e comando precisam seguir
`^[a-z][a-z0-9-]{0,62}$`. Symlinks não são aceitos no payload.

## Atualizar o Manifesto

O `karnel-plugin.json` tem campos obrigatórios:

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
  "capabilities": []
}
```

Não adicione campos não documentados. `capabilities` são apenas uma declaração
honesta do que o código pretende usar; não representam uma sandbox. Consulte o
[schema](schemas/karnel-plugin.schema.json) para o contrato completo.

Ao alterar scripts em `commands/`:

1. Atualize `version` seguindo SemVer.
2. Recalcule `checksum` conforme o algoritmo de payload completo no README.
3. Atualize a entrada correspondente em `registry.json`.
4. Execute `bash -n commands/*.sh` e ShellCheck.

## Adicionar ao Registry

1. Faça fork deste repositório.
2. Publique o plugin em um repositório GitHub com manifesto e licença na raiz.
3. Adicione uma entrada a `registry.json` usando o [schema](schemas/registry.schema.json).
4. Execute `python3 scripts/validate_registry.py --offline` antes do PR.
5. Abra o PR para `main` e aguarde a validação remota da CI.

Exemplo:

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
  "capabilities": []
}
```

`repo` deve ser exatamente `owner/repo`. Não use URLs, `.git`, caminhos
absolutos, `..` ou refs com caracteres especiais. A CI exige nomes e repositórios
únicos, source acessível, manifesto idêntico aos metadados, licença e arquivos
de comando exatos.

## Revisão

Não aprove o próprio PR de registry. Todo PR precisa passar pela CI e pelos
critérios em [REVIEW_POLICY.md](REVIEW_POLICY.md). Mantenedores devem configurar
proteção de branch no GitHub para exigir review e o workflow `Validate Registry`.
