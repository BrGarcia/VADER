import os
import html
from pathlib import PurePosixPath
import streamlit as st
import pandas as pd
from src.data.data_loader import DataLoader
from src.data.dtc_parser import DtcParser
from src.utils.local_scanner import get_available_flights, scan_flight_folder

_LOADER = DataLoader()

def _get_recent_files() -> list[str]:
    if not os.path.exists(DataLoader.RAW_DIR):
        return []
    files = [f for f in os.listdir(DataLoader.RAW_DIR) if f.endswith(".csv")]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(DataLoader.RAW_DIR, x)), reverse=True)
    return files

@st.cache_data(show_spinner="Processando telemetria...")
def _ingest(file_bytes: bytes, filename: str) -> pd.DataFrame:
    # SEC-02: sanitiza filename para evitar path traversal
    safe_name = PurePosixPath(filename).name
    raw_path = os.path.join(DataLoader.RAW_DIR, safe_name)
    os.makedirs(DataLoader.RAW_DIR, exist_ok=True)
    os.makedirs(DataLoader.PROCESSED_DIR, exist_ok=True)

    with open(raw_path, "wb") as fh:
        fh.write(file_bytes)

    return _LOADER.ingest(raw_path)

def render_landing() -> None:
    """Landing page: cabeçalho + box de upload + botão ENVIAR."""

    recent_files = _get_recent_files()

    # ── Cabeçalho centralizado ──
    _, col_mid, _ = st.columns([2, 1, 2])
    with col_mid:
        st.image("assets/a29_sideview.png", use_container_width=True)
        st.markdown("<h1 style='text-align: center; margin-top: -20px;'>V.A.D.E.R.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-style: italic; color: #888; font-size: 0.9em;'>Visualizador Analítico de Dados de Engenharia e Rastreio — A-29</p>", unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # ── Título dos Modos ──
    st.markdown("<h3 style='text-align: center; margin-bottom: 24px; color: #ddd;'>Selecione o Modo de Análise</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="large")

    # ── MODO VADR (Atual) ──
    with col1:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; color: #4CAF50; margin-bottom: 5px;'>📊 Modo VADR</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 0.8rem; text-align: center; color: #aaa; min-height: 40px;'>Análise clássica focada no arquivo CSV de telemetria.</p>", unsafe_allow_html=True)
            st.markdown("---")

            # Histórico
            if recent_files:
                st.markdown("<p style='font-size: 0.72rem; font-weight: bold; margin-bottom: 0px; text-align: center;'>📁 HISTÓRICO</p>", unsafe_allow_html=True)
                st.selectbox(
                    "Histórico",
                    options=["-- Selecione um voo recente --"] + recent_files,
                    index=0,
                    label_visibility="collapsed",
                    key="landing_history_select"
                )

            # Upload
            st.markdown("<p style='font-size: 0.72rem; font-weight: bold; margin-bottom: 0px; text-align: center; margin-top: 10px;'>⬆️ UPLOAD CSV</p>", unsafe_allow_html=True)
            st.file_uploader(
                "Upload CSV",
                type=["csv"],
                label_visibility="collapsed",
                key="landing_csv_uploader"
            )

            # Feedback de seleção
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            uploaded = st.session_state.get("landing_csv_uploader")
            selected_recent = st.session_state.get("landing_history_select")
            arquivo_pronto = uploaded is not None or (
                selected_recent and selected_recent != "-- Selecione um voo recente --"
            )

            if arquivo_pronto:
                nome = uploaded.name if uploaded else selected_recent
                nome_safe = html.escape(nome)  # SEC-01: sanitiza contra XSS
                st.markdown(f"<p style='font-size: 0.72rem; text-align: center; color: #4CAF50; margin-top: 2px;'>✅ {nome_safe}</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='font-size: 0.72rem; text-align: center; color: #888; margin-top: 2px;'>Selecione um arquivo CSV.</p>", unsafe_allow_html=True)

            # ── Botão ENVIAR ──
            enviar = st.button(
                "▶  INICIAR VADR",
                type="primary",
                use_container_width=True,
                key="landing_submit_btn",
                disabled=not arquivo_pronto,
            )

            if enviar:
                if uploaded is not None:
                    new_df = _ingest(uploaded.getvalue(), uploaded.name)
                    if new_df is not None:
                        st.session_state.current_df = new_df
                        st.session_state.current_filename = uploaded.name
                        st.rerun()
                    else:
                        st.error("❌ Falha ao processar o arquivo CSV.")
                elif selected_recent and selected_recent != "-- Selecione um voo recente --":
                    raw_path = os.path.join(DataLoader.RAW_DIR, selected_recent)
                    new_df = _LOADER.ingest(raw_path)
                    if new_df is not None:
                        st.session_state.current_df = new_df
                        st.session_state.current_filename = selected_recent
                        st.rerun()
                    else:
                        st.error("❌ Falha ao carregar o arquivo do histórico.")

    # ── MODO DTC (Ativo) ──
    with col2:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; color: #FF9800; margin-bottom: 5px;'>🛠️ Modo DTC</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 0.8rem; text-align: center; color: #aaa; min-height: 40px;'>Leitura e decodificação de arquivos TRIMM.DMP.</p>", unsafe_allow_html=True)
            st.markdown("---")
            
            # Upload
            st.markdown("<p style='font-size: 0.72rem; font-weight: bold; margin-bottom: 0px; text-align: center;'>⬆️ UPLOAD DMPs</p>", unsafe_allow_html=True)
            uploaded_dmps = st.file_uploader(
                "Upload DMP",
                type=["dmp", "txt", "csv"], 
                accept_multiple_files=True,
                label_visibility="collapsed",
                key="landing_dmp_uploader"
            )
            
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            if uploaded_dmps:
                st.markdown(f"<p style='font-size: 0.72rem; text-align: center; color: #FF9800; margin-top: 2px;'>✅ {len(uploaded_dmps)} arquivos</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='font-size: 0.72rem; text-align: center; color: #888; margin-top: 2px;'>Selecione os arquivos .DMP</p>", unsafe_allow_html=True)

            iniciar_dtc = st.button("▶  INICIAR DTC", disabled=not uploaded_dmps, type="primary", use_container_width=True, key="btn_dtc_start")
            
            if iniciar_dtc:
                with st.spinner("Processando arquivos TRIMM..."):
                    df_dtc = DtcParser.ingest_files(uploaded_dmps)
                    if not df_dtc.empty:
                        st.session_state.dtc_df = df_dtc
                        st.session_state.modo_app = "dtc"
                        st.rerun()
                    else:
                        st.error("❌ Falha ao processar arquivos DTC. Verifique se são DMPs válidos.")

    # ── MODO COMPLETO (Ativo) ──
    with col3:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; color: #2196F3; margin-bottom: 5px;'>🦅 Modo COMPLETA</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 0.8rem; text-align: center; color: #aaa; min-height: 40px;'>Dashboard All-in-One Integrado (HUD, EICAS, CSV e DTC).</p>", unsafe_allow_html=True)
            st.markdown("---")
            
            voos = get_available_flights()
            
            if not voos:
                st.markdown("<p style='font-size: 0.72rem; text-align: center; color: #888;'>Pasta 'Arquivos_para_analise/' vazia.</p>", unsafe_allow_html=True)
                st.button("▶  INICIAR COMPLETA", disabled=True, use_container_width=True, key="btn_completa_disabled")
            else:
                st.markdown("<p style='font-size: 0.72rem; font-weight: bold; margin-bottom: 0px; text-align: center;'>📁 SELECIONE O VOO</p>", unsafe_allow_html=True)
                voo_selecionado = st.selectbox(
                    "Voo Local",
                    options=voos,
                    label_visibility="collapsed",
                    key="landing_completa_select"
                )
                
                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                iniciar_completa = st.button("▶  INICIAR COMPLETA", type="primary", use_container_width=True, key="btn_completa_start")
                
                if iniciar_completa:
                    with st.spinner("Escaneando diretório e carregando módulos..."):
                        mapeamento = scan_flight_folder(voo_selecionado)
                        st.session_state.completa_map = mapeamento
                        
                        # Ingestão de VADR
                        if mapeamento.get("vadr_csv_path"):
                            df_vadr = _LOADER.ingest(str(mapeamento["vadr_csv_path"]))
                            st.session_state.current_df = df_vadr
                            st.session_state.current_filename = mapeamento["vadr_csv_path"].name
                        
                        # Ingestão de DTC
                        if mapeamento.get("dtc_files_paths"):
                            # Se os DMPs estiverem na pasta DTC, ou na raiz
                            dtc_pasta = str(mapeamento["dtc_files_paths"][0].parent)
                            df_dtc = DtcParser.processar_diretorio(dtc_pasta)
                            st.session_state.dtc_df = df_dtc
                            
                        st.session_state.modo_app = "completa"
                        st.rerun()
