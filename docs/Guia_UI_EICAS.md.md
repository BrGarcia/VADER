# 🎛️ Guia de Interface e UX: Módulo EICAS
**Anexo às Diretrizes de Desenvolvimento do V.A.D.E.R.**

O Módulo EICAS (Engine Indicating and Crew Alerting System) é a interface de simulação do painel da aeronave. Ele deve reproduzir a experiência de leitura do piloto no MFD (Multi-Function Display), traduzindo as linhas frias do CSV em instrumentos dinâmicos.

Este módulo será construído com foco nas Fases 2 e 3 do projeto, conectando-se diretamente ao eixo do tempo da Fase 1 (Time Scrubbing).

---

## 1. Identidade Visual (Obrigatório)
Para imitar os displays aviônicos modernos e reduzir o cansaço visual:
* **Fundo (Background):** A área do EICAS deve ser **estritamente escura** (Dark Mode / `#0E1117` ou preto `#000000`).
* **Tipografia:** Usar fontes monoespaçadas (monospace) para números, garantindo que os dígitos não fiquem "dançando" lateralmente quando os valores mudarem rapidamente.

---

## 2. Instrumentos do Motor (Engine Gauges)
Para a plotagem dos instrumentos (Torque, Np, ITT, Ng), a equipe deve padronizar o uso do componente `go.Indicator` da biblioteca **Plotly Graph Objects**, configurado no modo `bullet` ou `gauge`.

### Regras Lógicas de Renderização:
Cada instrumento deve ter limites visuais (Thresholds) que mudam de cor dinamicamente com base no valor atual do CSV no segundo selecionado.

* **Padrão de Cores Dinâmicas:**
    * **Normal:** Verde ou Branco.
    * **Caution:** Amarelo (`#FFC107`).
    * **Warning:** Vermelho (`#FF4B4B`).

* **Mapeamento de Variáveis (Referência):**
    * **Q (Torque):** Barra principal.
    * **ITT (Temperatura):** Barra secundária. Se `ITT > Limite Operacional`, a cor da barra deve obrigatoriamente mudar para Vermelho.
    * **Np / Ng (Rotações):** Mostrar em percentual (%).

---

## 3. Janela CAS (Crew Alerting System)
O painel lateral (ou inferior) do EICAS será dedicado ao CAS. Não se trata de um gráfico, mas de um renderizador de texto formatado condicionalmente.

### Comportamento do CAS:
1. **Inatividade:** Se nenhuma variável discreta de erro estiver ativa (`== 0`) e `MWC_DATA == 00`, a caixa deve permanecer preta e vazia (simulando voo normal).
2. **Prioridade Visual:**
    * **WARNINGS** (Vermelho): Ficam sempre no topo da lista. (Ex: `FIRE` gerado pela coluna `ENGFIRE == 1`).
    * **CAUTIONS** (Amarelo): Listados logo abaixo dos Warnings.
3. **Tradução em Tempo Real:** O código deve traduzir o código numérico da coluna `MWC_DATA` (ex: `47`) para o texto correspondente (ex: `ENG FIRE`) antes de renderizar na tela.

---

## 4. O Motor de Sincronização (Time Scrubbing)
A mágica do V.A.D.E.R. acontece aqui. O EICAS não possui eixo de tempo próprio; ele é um "retrato" do instante atual.

* **Arquitetura de Atualização:** O Streamlit deve possuir uma variável de estado (`st.session_state.current_time`).
* Quando o usuário arrasta o controle de tempo no Gráfico de Voo (Fase 1), o painel EICAS deve ler a linha exata correspondente àquele milissegundo no Pandas DataFrame e injetar nos mostradores em tempo real.
* **Meta de Performance:** A transição dos gráficos tipo *Gauge* não deve ter atraso perceptível ao arrastar a linha do tempo.

---
**Resumo para os Desenvolvedores:** Vocês não estão apenas fazendo um dashboard gerencial; vocês estão construindo uma "caixa preta visual". A precisão e a reatividade deste módulo são a chave do sucesso do V.A.D.E.R.