# FOCO — Segurança

## 1. Princípios
- menor privilégio;
- defesa em profundidade;
- segurança por padrão;
- secrets fora do código;
- auditoria;
- validação de entrada.

## 2. Autenticação
Planejada para v0.9.

Preferência:
1. OIDC institucional;
2. Active Directory/LDAP;
3. solução equivalente aprovada.

## 3. RBAC
Perfis iniciais:
- Administrador;
- Gestão;
- Comando;
- Unidade;
- Analista;
- Sala de Situação.

Permissões devem ser verificadas no backend.

## 4. Secrets
Nunca versionar:
- senhas;
- tokens;
- chaves;
- certificados privados;
- strings sensíveis.

## 5. API
Verificar:
- SQL Injection;
- IDOR;
- mass assignment;
- validação;
- autenticação;
- autorização;
- CORS.

## 6. Frontend
Verificar:
- XSS;
- exposição indevida;
- armazenamento inseguro de token;
- dependências vulneráveis.

## 7. Uploads
CSV/XLSX:
- limite de tamanho;
- extensão;
- MIME;
- nome sanitizado;
- armazenamento controlado;
- processamento seguro.

## 8. Banco
- usuário específico;
- menor privilégio;
- backup protegido;
- acesso administrativo restrito.

## 9. Docker
- evitar root;
- imagens mínimas;
- health checks;
- volumes controlados;
- secrets externos.

## 10. Logs
Nunca registrar senha, token ou segredo.

## 11. Auditoria
Registrar:
- login/logout;
- importações;
- alterações administrativas;
- integrações;
- mudança de permissão;
- exclusões.

## 12. Backup
Antes da v1.0:
- automatizado;
- retenção;
- restore testado;
- procedimento documentado.

## 13. Checklist pré-produção
- [ ] HTTPS
- [ ] autenticação
- [ ] autorização
- [ ] CORS restritivo
- [ ] migrations revisadas
- [ ] dependências verificadas
- [ ] backup testado
- [ ] logs revisados
- [ ] uploads validados
