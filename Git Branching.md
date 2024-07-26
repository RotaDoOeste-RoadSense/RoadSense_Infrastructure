# Git Branching Strategy

## Branches Principais

- `main`: É a branch principal que sempre contém o código estável e pronto para produção.
- `develop`: Contém o código que está em desenvolvimento e será a base para outras branches de feature.

## Branches de Suporte

- `feature/{nome-da-feature}`: Usada para desenvolvimento de novas funcionalidades. Quando uma feature estiver completa e testada, ela deve ser mergida na branch `develop`.
- `bugfix/{descricao-curta-do-bug}`: Usada para corrigir bugs detectados durante o desenvolvimento. Estas branches são baseadas em `develop` e depois mergidas de volta a `develop`.
- `hotfix/{descricao-curta-do-hotfix}`: Usada para corrigir bugs críticos detectados em produção. Estas branches são baseadas em `main` e depois mergidas de volta a `main` e `develop`.
- `release/{version}`: Usada para preparar uma nova release para produção. Correções de bugs e tarefas menores são feitas aqui, e após tudo estar pronto, esta branch é mergida em `main` e `develop`.

### Convenções de Nomes

- Use letras minúsculas e hífens (`-`) em nomes de branches.
- Seja descritivo mas sucinto.
- Exemplos:
  - `feature/login-page`
  - `bugfix/fix-login-error`
  - `hotfix/critical-payment-bug`
  - `release/1.0.0`

# Commits

## Estilo de Mensagens de Commit

- **Prefixo e Descrição**: `[tipo]: descrição`
- **Mensagem Extendida** (opcional): Explicação mais detalhada do commit, se necessário.
- **Referência a Tarefa/Bug**: Referência à issue ou tarefa no sistema de gerenciamento de projetos.

## Tipos de Commits

- `feat`: Um novo recurso.
- `fix`: Correção de bug.
- `docs`: Mudanças na documentação.
- `style`: Mudanças que não afetam o código (espaços em branco, formatação, etc.).
- `refactor`: Refatoração de código.
- `perf`: Mudanças que melhoram a performance.
- `test`: Adição ou modificação de testes.
- `chore`: Atualizações de tarefas e manutenção (dependências, builds, scripts).

### Exemplos de Mensagens de Commit

```
feat: add user login functionality
fix: correct login error when username is empty
docs: update API documentation for the login endpoint
style: fix indentation in LoginComponent
refactor: extract login validation to a separate module
perf: optimize image loading performance in login page
test: add unit tests for login validation
chore: update dependencies to latest versions
```

# Fluxo de Trabalho

1. **Criar uma nova branch**: Baseia-se na branch apropriada (`develop` para features e bugfixes, `main` para hotfixes).
   ```
   git checkout -b feature/login-page develop
   ```

2. **Desenvolvimento**: Faça commits atômicos e com mensagens claras.
   ```
   git add .
   git commit -m "feat: add user login functionality"
   ```

3. **Pull Request**: Abra um pull request (PR) para a branch base (`develop` ou `main`).

4. **Revisão de Código**: Um colega de equipe revisará o código antes de fazer o merge.

5. **Merge ou Rebase**: Após aprovação e testes, faça merge ou rebase na branch base.
   ```
   git checkout develop
   git merge feature/login-page
   ```
```
