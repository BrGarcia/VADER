import streamlit as st
import pandas as pd
from src.ui.views.vadr import render_main
from src.ui.components.dtc_styles import aplicar_estilos

def render_completa() -> None:
    """Monta o esqueleto do Dashboard Integrado All-In-One."""
    st.markdown("<h2 style='text-align: center; color: #2196F3;'>🦅 Dashboard Integrado (All-In-One)</h2>", unsafe_allow_html=True)
    
    mapeamento = st.session_state.get("completa_map", {})
    
    # Barra de Ferramentas / Status
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Telemetria (VADR)", "✅ OK" if mapeamento.get("vadr_csv_path") else "❌ Ausente")
        c2.metric("Falhas (DTC)", f"✅ {len(mapeamento.get('dtc_files_paths', []))} arq." if mapeamento.get("dtc_files_paths") else "❌ Ausente")
        c3.metric("Vídeo HUD (CHVC)", f"✅ {len(mapeamento.get('chvc_video_paths', []))} arq." if mapeamento.get("chvc_video_paths") else "❌ Ausente")
        c4.metric("Vídeo MFD (EICAS)", f"✅ {len(mapeamento.get('eicas_video_paths', []))} arq." if mapeamento.get("eicas_video_paths") else "❌ Ausente")
        
    st.markdown("---")
    
    # Grid de Vídeos
    col_vid1, col_vid2 = st.columns([3, 5.2], gap="medium")
    
    with col_vid1:
        st.markdown("#### 🎥 EICAS (MFD)")
        vids_eicas = mapeamento.get("eicas_video_paths", [])
        if vids_eicas:
            opcoes_eicas = {f.name: str(f) for f in vids_eicas}
            frag_eicas = st.selectbox("Fragmento EICAS", options=list(opcoes_eicas.keys()), label_visibility="collapsed")
            if frag_eicas:
                video_path = opcoes_eicas[frag_eicas]
                if video_path.lower().endswith(('.mpg', '.mpeg')):
                    st.warning("⚠️ Formato MPG incompatível com o navegador.")
                    if st.button("Converter EICAS para MP4 (Rotacionar 90º)", key="btn_conv_eicas"):
                        from src.utils.video_converter import convert_video
                        from pathlib import Path
                        out_path = Path(video_path).with_suffix('.mp4')
                        with st.spinner("Convertendo vídeo... Isso levará alguns minutos. Aguarde..."):
                            sucesso = convert_video(video_path, out_path, rotate=True)
                        if sucesso:
                            st.success("Conversão concluída! Feche a inspeção e abra novamente.")
                        else:
                            st.error("Falha. Verifique se o tools/ffmpeg.exe está na pasta.")
                            
                    if st.button("Converter TODOS os EICAS da pasta", key="btn_conv_all_eicas"):
                        from src.utils.video_converter import convert_video
                        from pathlib import Path
                        with st.spinner("Convertendo TODOS os vídeos EICAS... Isso levará bastante tempo. Aguarde..."):
                            falhas = 0
                            for vp in vids_eicas:
                                vp_str = str(vp)
                                if vp_str.lower().endswith(('.mpg', '.mpeg')):
                                    out_p = Path(vp_str).with_suffix('.mp4')
                                    if not out_p.exists():
                                        suc = convert_video(vp_str, out_p, rotate=True)
                                        if not suc:
                                            falhas += 1
                            if falhas == 0:
                                st.success("Conversão em lote concluída! Feche a inspeção e abra novamente.")
                            else:
                                st.error(f"Falha ao converter {falhas} arquivos. Verifique se o tools/ffmpeg.exe está na pasta.")
                else:
                    st.video(video_path)
        else:
            st.warning("Sem gravação do EICAS")
            
    with col_vid2:
        st.markdown("#### 🎥 CHVC (HUD)")
        vids_chvc = mapeamento.get("chvc_video_paths", [])
        if vids_chvc:
            opcoes_chvc = {f.name: str(f) for f in vids_chvc}
            frag_chvc = st.selectbox("Fragmento HUD", options=list(opcoes_chvc.keys()), label_visibility="collapsed")
            if frag_chvc:
                video_path = opcoes_chvc[frag_chvc]
                if video_path.lower().endswith(('.mpg', '.mpeg')):
                    st.warning("⚠️ Formato MPG incompatível com o navegador.")
                    if st.button("Converter HUD para MP4", key="btn_conv_chvc"):
                        from src.utils.video_converter import convert_video
                        from pathlib import Path
                        out_path = Path(video_path).with_suffix('.mp4')
                        with st.spinner("Convertendo vídeo... Isso levará alguns minutos. Aguarde..."):
                            sucesso = convert_video(video_path, out_path, rotate=False)
                        if sucesso:
                            st.success("Conversão concluída! Feche a inspeção e abra novamente.")
                        else:
                            st.error("Falha. Verifique se o tools/ffmpeg.exe está na pasta.")
                            
                    if st.button("Converter TODOS os HUD da pasta", key="btn_conv_all_chvc"):
                        from src.utils.video_converter import convert_video
                        from pathlib import Path
                        with st.spinner("Convertendo TODOS os vídeos HUD... Isso levará bastante tempo. Aguarde..."):
                            falhas = 0
                            for vp in vids_chvc:
                                vp_str = str(vp)
                                if vp_str.lower().endswith(('.mpg', '.mpeg')):
                                    out_p = Path(vp_str).with_suffix('.mp4')
                                    if not out_p.exists():
                                        suc = convert_video(vp_str, out_p, rotate=False)
                                        if not suc:
                                            falhas += 1
                            if falhas == 0:
                                st.success("Conversão em lote concluída! Feche a inspeção e abra novamente.")
                            else:
                                st.error(f"Falha ao converter {falhas} arquivos. Verifique se o tools/ffmpeg.exe está na pasta.")
                else:
                    st.video(video_path)
        else:
            st.warning("Sem gravação do HUD")
            
    st.markdown("---")
    st.markdown("#### 🛠️ Alertas DTC (Pitch Trim Switch)")
    df_dtc = st.session_state.get("dtc_df")
    if df_dtc is not None and not df_dtc.empty:
        meta = df_dtc.attrs.get("metadata", {})

        falhas = meta.get("Falhas", [])
        if falhas:
            st.warning(
                f"⚠️ {len(falhas)} arquivo(s) DMP não puderam ser lidos e foram excluídos "
                f"desta análise: {', '.join(falhas)}"
            )

        v_a = meta.get('Disparos Aileron', 0)
        v_e = meta.get('Disparos Elevator', 0)
        
        c_a, c_e = st.columns(2)
        if v_a > 0:
            c_a.error(f"**Aileron:** {v_a} disparos detectados")
        else:
            c_a.success("**Aileron:** Nenhum disparo")
            
        if v_e > 0:
            c_e.error(f"**Elevator:** {v_e} disparos detectados")
        else:
            c_e.success("**Elevator:** Nenhum disparo")
            
        st.markdown("<br>", unsafe_allow_html=True)

        # --- Tabelas do DTC ---
        disparos_df = df_dtc[(df_dtc.get("Aileron_Test") == 1) | (df_dtc.get("Elevator_Test") == 1)]
        if not disparos_df.empty:
            with st.expander("🚨 Ocorrências de Disparo (Extrato Rápido)", expanded=True):
                st.markdown("<p style='font-size: 0.85rem; color: #bbb;'>Esta tabela mostra <b>apenas</b> os instantes exatos onde os alertas foram disparados. Analise os estados dos interruptores (Emer_ON, Stick) nestes momentos.</p>", unsafe_allow_html=True)
                st.dataframe(aplicar_estilos(disparos_df), use_container_width=True, hide_index=True)
                
        with st.expander("📋 Histórico Completo de Voo (DTC)", expanded=False):
            st.dataframe(aplicar_estilos(df_dtc), use_container_width=True, hide_index=True)
    else:
        st.info("Sem falhas DTC detectadas ou dados ausentes para este voo.")
            
    df_vadr = st.session_state.get("current_df")
    if df_vadr is not None:
        st.markdown("---")
        render_main(df_vadr, show_metadata=False)
    else:
        st.markdown("---")
        st.warning("Sem dados de telemetria VADR para plotar gráficos.")
        
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    if st.button("🔄  ENCERRAR INSPEÇÃO", use_container_width=True):
        st.session_state.pop("completa_map", None)
        st.session_state.pop("dtc_df", None)
        st.session_state.pop("current_df", None)
        st.session_state.modo_app = None
        st.rerun()
