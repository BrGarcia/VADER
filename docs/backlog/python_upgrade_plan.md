# Backlog: Plano de Atualização da Versão do Python

Este documento descreve o plano para migrar o interpretador Python do projeto **V.A.D.E.R.** de sua versão atual (**Python 3.9**) para uma versão moderna e suportada (recomendado: **Python 3.11** ou **Python 3.12**).

---

## 🎯 Objetivos e Benefícios

1. **Performance Aprimorada**: O Python 3.11 é entre 10% a 60% mais rápido que o Python 3.9 devido ao projeto *Faster CPython*, o que otimiza o processamento de grandes arquivos de telemetria (.csv/.xlsx).
2. **Sintaxe Moderna Nativa**: Suporte pleno ao operador de união de tipos `|` (PEP 604) nativamente sem precisar de imports futuros, além de blocos estruturados como `match-case` (Python 3.10+).
3. **Melhor Rastreabilidade de Erros**: Mensagens de erro e Tracebacks muito mais precisos e visuais no console.
4. **Segurança e Suporte**: Garantia de compatibilidade contínua com as versões mais recentes do Streamlit, Pandas, Plotly e bibliotecas de geolocalização.

---

## 📋 Pré-requisitos

Antes de iniciar a migração, o desenvolvedor ou o usuário deve certificar-se de ter a versão desejada instalada no sistema operacional (macOS).

Verifique as versões disponíveis no Mac:
```bash
# Versão padrão do sistema
python3 --version

# Se utilizar o Homebrew
brew info python@3.11
```

Caso não esteja instalado, instale via Homebrew:
```bash
brew install python@3.11
```

---

## 🛠️ Passo a Passo para Implementação

Siga este passo a passo sequencial para realizar a migração do ambiente de desenvolvimento local:

### Passo 1: Limpeza do Ambiente Antigo
Remova o ambiente virtual (`venv`) antigo baseado em Python 3.9:
```bash
# Certifique-se de não estar com o venv ativo no terminal
deactivate 2>/dev/null

# Exclua a pasta do ambiente virtual antigo
rm -rf venv/
```

### Passo 2: Criação do Novo Ambiente Virtual (Python 3.11)
Crie o novo ambiente virtual explicitando o interpretador da versão atualizada:
```bash
# Criando venv apontando para o interpretador do Python 3.11 instalado via Brew
python3.11 -m venv venv
```

### Passo 3: Ativação e Atualização do Pip/SetupTools
Ative o novo ambiente e atualize os gerenciadores de pacotes básicos:
```bash
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### Passo 4: Instalação das Dependências do V.A.D.E.R.
Instale os pacotes definidos no projeto. Se necessário, compile as dependências nativas para a arquitetura do Mac (Apple Silicon / Intel):
```bash
pip install -r requirements.txt
```

---

## 🔍 Plano de Verificação e Testes

Para garantir a estabilidade do sistema após a migração, execute os seguintes passos de validação:

### 1. Compilação Completa das Fontes
Certifique-se de que nenhum arquivo possui incompatibilidade sintática:
```bash
python -m compileall src/
```

### 2. Validação de Execução Local
Inicie o dashboard do Streamlit utilizando o novo interpretador:
```bash
streamlit run app.py
```
* **O que verificar**:
  * Carregamento bem-sucedido dos dados de telemetria na página principal.
  * Funcionamento do slider de tempo no **MODO VADR** e atualização síncrona dos indicadores.
  * Ausência de warnings ou deprecations de tipos no terminal do Streamlit.

---

## ⚠️ Mitigação de Riscos e Gotchas no macOS

* **Gotcha de Compilação Nativa**: Algumas bibliotecas de análise de dados (como Pandas ou NumPy) em versões específicas podem exigir compilação local no macOS (especialmente em chips Apple M1/M2/M3). Certifique-se de que a ferramenta de linha de comando do Xcode está atualizada (`xcode-select --install`).
* **Paridade de Produção**: Certifique-se de que os arquivos de configuração de ambiente de nuvem ou arquivos Docker (se houver) sejam atualizados para a mesma versão do Python para manter a paridade exata.
