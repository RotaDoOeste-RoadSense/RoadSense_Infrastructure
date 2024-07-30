# RoadSense_Infrastructure
Infraestrutura do Projeto RoadSense da Nova Rota do Oeste
Uma estratégia de ramificação bem definida para manter o código organizado, estável e fácil de gerenciar.

## Índice

- [Sobre](#sobre)
- [Filiais Principais](#filiais-principais)
- [Ramos de Suporte](#ramos-de-suporte)
- [Convenções de Nomes](#convenções-de-nomes)
- [Compromissos](#compromissos)
  - [Estilo de Mensagens de Commit](#estilo-de-mensagens-de-commit)
  - [Tipos de Commits](#tipos-de-commits)
  - [Exemplos de Mensagens de Commit](#exemplos-de-mensagens-de-commit)
- [Fluxo de Trabalho](#fluxo-de-trabalho)

## Sobre

Esta estratégia de ramificação do Git foi projetada para garantir um fluxo de desenvolvimento organizado e eficiente. As ramificações são estruturadas para separar o desenvolvimento de novas funcionalidades, correções de bugs e preparações para lançamentos.

## Filiais Principais

- **main**: A filial principal que sempre contém o código estável e pronto para produção.
- **develop**: Contém o código que está em desenvolvimento e será a base para outras ramificações de recurso.

## Ramos de Suporte

### feature/{nome-da-feature}

Usado para desenvolvimento de novas funcionalidades. Quando um recurso estiver completo e testado, ele deverá ser mesclado na ramificação develop.

#### Passo a Passo para Ramos de Suporte

1. Crie uma nova branch a partir de develop para adicionar uma nova funcionalidade:
   
bash
   git checkout -b feature/nova-funcionalidade develop


com este arquivo: 
# Fluxo de Trabalho com Git

## Desenvolvimento de Funcionalidade

1. **Crie uma nova branch para a funcionalidade**:
bash
    git checkout -b feature/nova-funcionalidade develop
    
2. **Desenvolva a funcionalidade e faça commits atômicos e claros**.

3. **Quando a funcionalidade estiver completa, abra um pull request para develop**.

4. **Após a revisão do código, faça merge da branch de funcionalidade em develop**:
bash
    git checkout develop
    git merge feature/nova-funcionalidade
    
## Correção de Bugs

### Correção de Bugs no Desenvolvimento

1. **Crie uma nova branch para corrigir um bug**:
bash
    git checkout -b bugfix/{descricao-do-bug} develop
    
2. **Corrija o bug e faça commits atômicos e claros**.

3. **Quando a correção estiver completa, abra um pull request para develop**.

4. **Após a revisão do código, faça merge da branch de correção em develop**:
bash
    git checkout develop
    git merge bugfix/{descricao-do-bug}
    
### Correção de Bugs Críticos em Produção

1. **Crie uma nova branch a partir de main para corrigir um bug crítico**:
bash
    git checkout -b hotfix/{descricao-do-hotfix} main
    
2. **Corrija o bug e faça commits atômicos e claros**.

3. **Quando a correção estiver completa, abra um pull request para main**.

4. **Após a revisão do código, faça merge da branch de hotfix em main**:
bash
    git checkout main
    git merge hotfix/{descricao-do-hotfix}
    
5. **Mescle as alterações de main para develop**:
bash
    git checkout develop
    git merge main
    
## Preparação de Lançamento

1. **Crie uma nova branch a partir de develop para preparar um lançamento**:
bash
    git checkout -b release/{version} develop
    
2. **Faça ajustes finais, correções de bugs e pequenas melhorias**.

3. **Quando tudo estiver pronto, abra um pull request para main**.

4. **Após a revisão do código, faça merge da branch de lançamento em main**:
bash
    git checkout main
    git merge release/{version}
    
5. **Mescle as alterações de main para develop**:
bash
    git checkout develop
    git merge main
    
## Convenções de Nomes

- Use letras minúsculas e hífens (-) em nomes de branches.
- Seja descritivo mas sucinto.

**Exemplos**:
- `feature/login-page`
- `bugfix/fix-login-error`
- `hotfix/critical-payment-bug`
- `release/1.0.0`

## Estilo de Mensagens de Commit

- **Prefixo e Descrição**: `[tipo]: descrição`
- **Mensagem estendida (opcional)**: Explicação mais detalhada do commit, se necessário.
- **Referência a Tarefa/Bug**: Referência à issue ou tarefa no sistema de gerenciamento de projetos.

### Tipos de Commits

- `feat`: Um novo recurso.
- `fix`: Correção de bug.
- `docs`: Mudanças na documentação.
- `style`: Mudanças que não afetam o código (espaços em branco, formatação, etc.).
- `refactor`: Refatoração de código.
- `perf`: Mudanças que melhoram a performance.
- `test`: Adição ou alteração de testes.
- `chore`: Atualizações de tarefas e manutenção (dependências, builds, scripts).

**Exemplos de Mensagens de Commit**:
- `feat: add user login functionality`
- `fix: correct login error when username is empty`
- `docs: update API documentation for the login endpoint`
- `style: fix indentation in LoginComponent`
- `refactor: extract login validation to a separate module`
- `perf: optimize image loading performance in login page`
- `test: add unit tests for login validation`
- `chore: update dependencies to latest versions`

## Fluxo de Trabalho

1. **Criar uma nova branch**: Baseia-se na branch anexada (develop para features e bugfixes, main para hotfixes).
bash
    git checkout -b feature/login-page develop
    
2. **Desenvolvimento**: Faça commits atômicos e com mensagens claras.
bash
    git add .
    git commit -m "feat: add user login functionality"
    
3. **Pull Request**: Abra um pull request (PR) para uma branch base (develop ou main).

4. **Revisão de Código**: Um colega de equipe revisará o código antes de fazer a mesclagem.

5. **Merge ou Rebase**: Após aprovação e testes, faça merge ou rebase na branch base.
bash
    git checkout develop
    git merge feature/login-page
    

