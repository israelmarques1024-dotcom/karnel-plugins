# Política de Segurança

Relate vulnerabilidades do registry, schemas, CI ou plugins oficiais de forma
privada. Não publique detalhes exploráveis em issue pública antes da correção.

Abra uma GitHub Security Advisory privada pelo separador **Security** deste
repositório, incluindo:

- impacto e pré-requisitos;
- passos mínimos de reprodução;
- versão do Karnel e do plugin;
- evidências sem credenciais, tokens ou dados pessoais;
- sugestão de mitigação, se houver.

Plugins Bash são código com as permissões do usuário. O registry revisa e valida
metadados, mas não fornece sandbox. Repositórios instalados com `--unsafe` não
fazem parte do escopo de aprovação do registry, embora falhas no cliente Karnel
que permitam burlar sua confirmação ou validação devam ser reportadas.

Após confirmação, a correção será tratada em privado, receberá teste de regressão
e será divulgada com orientação de atualização quando apropriado.
