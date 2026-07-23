# Adicionando seu Plugin ao Registry

1. Faça um fork deste repositório
2. Edite `registry.json`
3. Adicione sua entrada no array `plugins`:

```json
{
  "name": "meu-plugin",
  "repo": "seu-user/meu-plugin",
  "description": "Descrição curta do que seu plugin faz",
  "commands": ["comando1", "comando2"],
  "version": "1.0.0"
}
```

4. Abra um Pull Request

Requisitos:
- O repositório do plugin deve ter `karnel-plugin.json` na raiz
- O nome deve ser único no registry
- A descrição deve ser clara e concisa

Após aprovado, seu plugin aparecerá em `karnel plugin search`.
