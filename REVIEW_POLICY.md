# Política de Revisão do Registry

Uma entrada no registry é uma recomendação de código Bash para usuários do
Karnel. Ela não é uma certificação de segurança nem cria isolamento.

## Critérios Obrigatórios

- O PR passa pelo workflow `Validate Registry`.
- O nome, repositório e comandos são únicos e não colidem com comandos nativos conhecidos.
- O repositório usa formato `owner/repo`, ref segura e manifesto Schema v1.
- Manifesto e registry coincidem em nome, versão, descrição, comandos, compatibilidade, licença, checksum e capabilities.
- O código declarado é revisado manualmente; arquivos Bash não declarados em `commands/` e qualquer symlink no payload são rejeitados.
- O plugin inclui licença e não adiciona segredos, payloads remotos, `eval`, downloads sem verificação ou comportamento oculto.
- Capabilities declaram de forma honesta uso de rede, filesystem, processos e ambiente.

## Atualizações

- Toda mudança de código exige nova versão SemVer, checksum e revisão.
- Prefira `commit` completo para fixar uma revisão imutável quando o fluxo de publicação permitir.
- `ref` mutável só é aceito quando o checksum no registry protege os comandos aprovados.
- Remoções urgentes ou revogações devem ser registradas em PR revisado e comunicadas em advisory de segurança quando necessário.

## Governança Recomendada

- Proteja `main` contra pushes diretos.
- Exija ao menos uma revisão de CODEOWNERS para `registry.json` e `schemas/`.
- Exija o workflow `Validate Registry` como status check.
- Mantenha permissões de GitHub Actions somente leitura e nunca use `pull_request_target` para validar contribuições.
