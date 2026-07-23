<p align="center">
  <img src="https://raw.githubusercontent.com/israelmarques1024-dotcom/karnel-termux/main/assets/images/karnel-logo.png" alt="Karnel Termux" width="300">
</p>

<p align="center">
  <strong>Official plugin registry for <a href="https://github.com/israelmarques1024-dotcom/karnel-termux">Karnel Termux</a></strong>
</p>

<p align="center">
  <a href="https://github.com/israelmarques1024-dotcom/karnel-plugins/blob/main/registry.json">
    <img src="https://img.shields.io/badge/plugins-0-0078D4?style=for-the-badge" alt="Plugins">
  </a>
  <a href="CONTRIBUTING.md">
    <img src="https://img.shields.io/badge/contributions-welcome-brightgreen?style=for-the-badge" alt="Contributions Welcome">
  </a>
</p>

---

Este repositório é o **registry oficial** de plugins do Karnel Termux. Aqui a comunidade publica extensões que qualquer usuário pode instalar com um comando.

## Para Usuários

Buscar plugins disponíveis:

```bash
karnel plugin search
```

Instalar um plugin:

```bash
karnel plugin install <user/repo>
```

Listar plugins instalados:

```bash
karnel plugin list
```

## Para Desenvolvedores

Quer criar e publicar seu próprio plugin?

1. Crie seu plugin com `karnel plugin create meu-plugin`
2. Desenvolva seus comandos em `commands/`
3. Publique em um repositório GitHub
4. Adicione seu plugin ao registry — veja [CONTRIBUTING.md](CONTRIBUTING.md)

### Estrutura de um Plugin

```
meu-plugin/
├── karnel-plugin.json   # Manifesto obrigatório
└── commands/            # Comandos descobertos automaticamente
    └── meu-comando.sh
```

Exemplo de `karnel-plugin.json`:

```json
{
  "name": "meu-plugin",
  "version": "1.0.0",
  "description": "Descrição do que ele faz",
  "commands": ["meu-comando"]
}
```

---

## Registry

O arquivo [`registry.json`](registry.json) contém a lista oficial de plugins. Para adicionar o seu, abra um Pull Request seguindo o [guia de contribuição](CONTRIBUTING.md).

```json
{
  "version": 1,
  "plugins": [
    {
      "name": "meu-plugin",
      "repo": "seu-user/meu-plugin",
      "description": "Descrição curta",
      "commands": ["comando1"]
    }
  ]
}
```

---

## Links

- [Karnel Termux](https://github.com/israelmarques1024-dotcom/karnel-termux)
- [Documentação oficial](https://karneltermux.vercel.app)
- [npm](https://www.npmjs.com/package/karnel-termux)
