# 🧭 Guia de Orientações para Desenvolvimento
**Projeto:** V.A.D.E.R. (Visualizador Analítico de Dados de Engenharia e Rastreio)

Este documento estabelece as regras de trânsito, padrões de código e convenções de interface para todos os desenvolvedores que atuam no projeto V.A.D.E.R. O objetivo é garantir que o código seja legível, manutenível e que a interface final seja padronizada e intuitiva para os inspetores de manutenção do A-29.

---

## 1. Fluxo de Trabalho (Git Workflow)

Para garantir a estabilidade do sistema, operamos com um fluxo de trabalho rigoroso de controle de versão.

### 1.1. Regra de Ouro
**Nenhum desenvolvedor tem permissão para fazer `commit` direto na branch `main`.** A `main` deve conter sempre código funcional, testado e pronto para uso na linha de voo.

### 1.2. Nomenclatura de Branches
Todas as novas ramificações devem ser criadas a partir da `main` e seguir os prefixos abaixo:
* `feature/...` → Para novas funcionalidades ou blocos de código. (Ex: `feature/grafico-temperatura-itt`)
* `bugfix/...` → Para correção de erros em código já existente. (Ex: `bugfix/correcao-inversao-ldg`)
* `refactor/...` → Para melhorias de código sem mudança de funcionalidade. (Ex: `refactor/otimizacao-leitura-pandas`)
* `hotfix/...` → Para correções críticas e urgentes na `main`.

### 1.3. Padrão de Commits (Conventional Commits)
As mensagens de commit devem ser claras e descritivas:
* `feat: adiciona seletor de tempo no painel central`
* `fix: resolve erro de leitura de NaN na coluna MACH`
* `docs: atualiza dicionário de dados com variáveis MW`

### 1.4. Pull Requests (PR)
Ao finalizar uma tarefa, abra um Pull Request. O PR deve:
1. Conter uma breve descrição do que foi feito.
2. Ser revisado e aprovado por pelo menos 1 outro desenvolvedor ou pelo líder do projeto antes de realizar o *merge*.

---

## 2. Padrões de Arquitetura e Código Python

O código do V.A.D.E.R. deve priorizar a clareza e a performance, lidando com arquivos CSV densos (telemetria a 8Hz ou 32Hz).

### 2.1. Desacoplamento (Lógica vs. Interface)
**Nunca misture a lógica de processamento de dados com a lógica de renderização de tela.**
* **ERRADO:** Fazer a limpeza do DataFrame do Pandas dentro da função que desenha o gráfico no Streamlit.
* **CORRETO:** O arquivo `data_loader.py` faz a limpeza e exporta um DataFrame tratado. O arquivo `app.py` apenas chama esse DataFrame e plota o gráfico.

### 2.2. Tipagem e Docstrings
Documente o comportamento das funções complexas. Se uma função converte Nós (Knots) para Mach, deixe isso explícito.
```python
def converter_status_trem_de_pouso(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte o bit da coluna LDG para um status legível.
    Atenção à lógica invertida: 0 = Abaixado, 1 = Recolhido.
    """
    df['LDG_STATUS'] = df['LDG'].apply(lambda x: 'Abaixado' if x == 0 else 'Recolhido')
    return df