# Visão Geral do Projeto (Vision)

## 1. Objetivo do Sistema
O **V.A.D.E.R.** (Visualizador Analítico de Dados de Engenharia e Rastreio) é uma aplicação web local focada na ingestão, processamento e visualização interativa de telemetria de voo extraída de equipamentos VADR.

## 2. Problema que Resolve
Atualmente, inspetores de manutenção da aeronave A-29 Super Tucano precisam visualizar enormes matrizes de dados gravados (arquivos CSV brutos com frequências de 8Hz a 32Hz). Encontrar parâmetros, deduzir eventos e cruzar informações de falhas com os instrumentos requer muito tempo e aumenta a probabilidade de falha humana no diagnóstico.
O VADER simplifica o *troubleshooting* ao integrar uma linha do tempo unificada com componentes visuais reativos (Gauges, Horizonte Artificial e Painel de Alertas).

## 3. Público-alvo
Inspetores de manutenção de aeronaves, mecânicos de linha de voo, engenheiros aeronáuticos e investigadores técnicos.

## 4. Funcionalidades Principais
- Ingestão robusta de CSV para formato Parquet, otimizando o carregamento recorrente.
- Componente de Linha do Tempo interativo e com busca de valores (Playback até 20fps).
- Emulação de EICAS (Painel do Motor) reativo baseado nos valores de telemetria daquele exato frame temporal.
- Sistema Central de Alertas (CAS) simulado, acendendo ou apagando as luzes de acordo com o código EICAS / MWC_DATA ativo.
- Verificadores dinâmicos de Carga G (excedência), Atitude e Subsistemas (Trem de pouso, Flaps).
