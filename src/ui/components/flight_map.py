import streamlit as st
import pandas as pd
import pydeck as pdk
import base64
from pathlib import Path

# Cache para não recarregar a imagem a cada frame
@st.cache_data
def get_image_base64(path: str) -> str:
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

class FlightMap:
    def __init__(self):
        self.img_path = Path("assets/a29_topview.png")
        if self.img_path.exists():
            self.icon_data = f"data:image/png;base64,{get_image_base64(str(self.img_path))}"
        else:
            self.icon_data = None

    def render(self, df: pd.DataFrame, snapshot: pd.Series) -> None:
        if "GPSLAT" not in df.columns or "GPSLONG" not in df.columns:
            st.info("Colunas GPSLAT / GPSLONG não encontradas na telemetria.")
            return

        lat = snapshot.get("GPSLAT", 0.0)
        lon = snapshot.get("GPSLONG", 0.0)
        
        # Validar dados GPS
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):  # BUG-01: except específico
            st.warning("Dados de GPS inválidos.")
            return
            
        curr_time = snapshot.get("TIME", 0)
        df_path = df[df["TIME"] <= curr_time].copy()
        
        # ── Validar e tratar falhas de GPS (Dropouts) ──
        # Se o GPS sumir (muito comum em manobras), usamos a última posição válida conhecida.
        # BUG-02: extraímos apenas lat/lon/heading sem reatribuir snapshot inteiro
        heading_source = snapshot  # referência para leitura de proa
        if pd.isna(lat) or pd.isna(lon) or (lat == 0 and lon == 0):
            valid_gps = df_path[(df_path["GPSLAT"].notna()) & (df_path["GPSLONG"].notna()) & (df_path["GPSLAT"] != 0) & (df_path["GPSLONG"] != 0)]
            if not valid_gps.empty:
                last_valid = valid_gps.iloc[-1]
                lat = float(last_valid["GPSLAT"])
                lon = float(last_valid["GPSLONG"])
                
                # Usa proa do último ponto GPS válido (não reatribui snapshot)
                heading_source = last_valid
            else:
                st.warning("Sem sinal GPS válido até este momento da gravação.")
                return

        # ── Lógica de Proa (Heading) ──
        # MAG_HDGV == 3 indica que a proa magnética é válida
        heading = 0.0
        if "MAG_HDG" in heading_source.index and "MAG_HDGV" in heading_source.index:
            try:
                hdg_v = float(heading_source.get("MAG_HDGV", 0))
                if hdg_v == 3.0: 
                    heading = float(heading_source.get("MAG_HDG", 0))
            except (ValueError, TypeError):  # BUG-01: except específico
                pass
                
        # O Pydeck usa rotação horária em graus, o que bate com a bússola.
        plane_data = pd.DataFrame({
            "lat": [lat],
            "lon": [lon],
            "heading": [heading] 
        })
        
        
        # Reduzir quantidade de pontos para não travar o navegador (max 300 pontos)
        if len(df_path) > 300:
            step = len(df_path) // 300
            df_path = df_path.iloc[::step]
            
        path_coords = df_path[["GPSLONG", "GPSLAT"]].dropna().values.tolist()

        layers = []
        
        # 1. Camada de Rastro (Linha vermelha)
        if len(path_coords) > 1:
            path_data = pd.DataFrame([{"path": path_coords}])
            layers.append(
                pdk.Layer(
                    "PathLayer",
                    path_data,
                    pickable=False,
                    get_color=[255, 75, 75], # Vermelho
                    width_scale=20,
                    width_min_pixels=3,
                    get_path="path",
                    get_width=5,
                )
            )

        # 2. Camada do Avião (Ícone)
        if self.icon_data:
            # AnchorX e AnchorY dependem de onde é o centro da sua imagem.
            # 256, 256 assume uma imagem quadrada de 512x512 onde o avião está no centro.
            icon_def = {
                "url": self.icon_data,
                "width": 512, 
                "height": 512,
                "anchorY": 256,
                "anchorX": 256
            }
            plane_data["icon"] = [icon_def]
            layers.append(
                pdk.Layer(
                    "IconLayer",
                    plane_data,
                    get_icon="icon",
                    get_size=4,
                    size_scale=15,
                    get_position=["lon", "lat"],
                    get_angle="heading", 
                    pickable=True,
                )
            )
        else:
            # Fallback se não achar a imagem: um círculo verde
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    plane_data,
                    get_position=["lon", "lat"],
                    get_color=[0, 255, 136],
                    get_radius=50,
                    radius_min_pixels=6,
                )
            )

        view_state = pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=12,
            pitch=0,
        )

        st.pydeck_chart(pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            map_style=None, # Usa o estilo nativo claro/escuro do Streamlit
            tooltip={"text": f"Lat: {lat:.5f}\\nLon: {lon:.5f}\\nProa: {heading:.1f}°"}
        ))
