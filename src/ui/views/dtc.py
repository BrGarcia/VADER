import streamlit as st
import pandas as pd

def render_dtc(df: pd.DataFrame) -> None:
    """Monta a visualização para os dados consolidados do DTC."""
    st.markdown("<h2 style='text-align: center; color: #FF9800;'>🛠️ Análise DTC (Pitch Trim Switch)</h2>", unsafe_allow_html=True)
    
    meta = df.attrs.get("metadata", {})
    status = meta.get("Status", "N/A")
    status_color = "#FF4B4B" if "SUSPEITA" in status else "#4CAF50"
    
    # Cabeçalho principal com Status fora da métrica para não cortar texto longo
    st.markdown(f"<h3 style='text-align: center; margin-top: 0px; color: {status_color};'>{status}</h3>", unsafe_allow_html=True)
    
    with st.container(border=True):
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        with col_kpi1:
            st.metric("Total de Arquivos", meta.get("Total de Arquivos", 0))
        with col_kpi2:
            st.metric("Total de Registros", meta.get("Total de Registros", 0))
        with col_kpi3:
            st.metric("Threshold Seguro (ms)", f"{meta.get('Threshold (ms)', 0)} ms")

    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>Análise de Movimento Não Comandado</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 0.9rem; color: #aaa;'>Um alerta ocorre quando a posição da superfície sofre um salto brusco (> 1 grau) num intervalo de tempo menor que o Threshold Seguro.</p>", unsafe_allow_html=True)

    col_a, col_e = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>Superfície Aileron</h4>", unsafe_allow_html=True)
            v_a = meta.get("Disparos Aileron", 0)
            c_a = "#FF4B4B" if v_a > 0 else "#4CAF50"
            st.markdown(f"<h1 style='text-align: center; color: {c_a}; margin-top: -10px;'>{v_a} alertas</h1>", unsafe_allow_html=True)
            if v_a == 0:
                st.markdown("<p style='text-align: center; color: #aaa; font-size: 0.8rem;'>Nenhuma anomalia matemática detectada.</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='text-align: center; color: #FF4B4B; font-size: 0.8rem; font-weight: bold;'>⚠️ Requer investigação imediata.</p>", unsafe_allow_html=True)
        
    with col_e:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>Superfície Elevator</h4>", unsafe_allow_html=True)
            v_e = meta.get("Disparos Elevator", 0)
            c_e = "#FF4B4B" if v_e > 0 else "#4CAF50"
            st.markdown(f"<h1 style='text-align: center; color: {c_e}; margin-top: -10px;'>{v_e} alertas</h1>", unsafe_allow_html=True)
            if v_e == 0:
                st.markdown("<p style='text-align: center; color: #aaa; font-size: 0.8rem;'>Nenhuma anomalia matemática detectada.</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='text-align: center; color: #FF4B4B; font-size: 0.8rem; font-weight: bold;'>⚠️ Requer investigação imediata.</p>", unsafe_allow_html=True)

    st.markdown("---")
    
    # Configuração de Estilos para as Tabelas
    def highlight_status_t(val):
        if str(val).strip().upper() == "T":
            return 'background-color: rgba(255, 152, 0, 0.4); color: white; font-weight: bold;'
        return ''

    def highlight_test_1(val):
        if str(val).strip() == "1":
            return 'background-color: rgba(255, 75, 75, 0.5); color: white; font-weight: bold;'
        return ''

    cols_t = [c for c in ["Emer_ON", "Emer_SW", "Stick_FWD", "Stick_AFT"] if c in df.columns]
    cols_1 = [c for c in ["Aileron_Test", "Elevator_Test"] if c in df.columns]

    def aplicar_estilos(data_frame):
        styler = data_frame.style
        if hasattr(styler, "map"):
            styler = styler.map(highlight_status_t, subset=cols_t)
            styler = styler.map(highlight_test_1, subset=cols_1)
        else:
            styler = styler.applymap(highlight_status_t, subset=cols_t)
            styler = styler.applymap(highlight_test_1, subset=cols_1)
        return styler

    # Extrato Rápido (Apenas Disparos)
    disparos_df = df[(df.get("Aileron_Test") == 1) | (df.get("Elevator_Test") == 1)]
    if not disparos_df.empty:
        st.markdown("### 🚨 Ocorrências de Disparo (Extrato Rápido)")
        st.markdown("<p style='font-size: 0.85rem; color: #bbb;'>Esta tabela mostra <b>apenas</b> os instantes exatos onde os alertas foram disparados. Analise os estados dos interruptores (Emer_ON, Stick) nestes momentos.</p>", unsafe_allow_html=True)
        st.dataframe(aplicar_estilos(disparos_df), use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Tabela Completa
    st.markdown("### 📋 Histórico Completo de Voo")
    st.dataframe(aplicar_estilos(df), use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        if st.button("🔄  VOLTAR AO MENU INICIAL", use_container_width=True):
            st.session_state.pop("dtc_df", None)
            st.session_state.modo_app = None
            st.rerun()
