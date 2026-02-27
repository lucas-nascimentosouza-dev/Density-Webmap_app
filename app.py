
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# AJUSTE PARA MOBILE (RESPONSIVO) CSS

st.markdown("""
<style>

/* MOBILE ONLY */
@media (max-width: 768px) {

    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .download-btn {
        width: 85% !important;
        justify-content: center !important;
    }

    h2 {
        font-size: 22px !important;
    }

}

</style>
""", unsafe_allow_html=True)

# ===============================
# CONFIGURAÇÕES
# ===============================
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSarjsfOxs3BgjK1sF8FWv8ExKj34P3k2AgjuC-4XKhrwK7xrjorPxCWeUmA4Z4JtKD_btojUjN8ZvS/pub?output=csv"
TEMPO_ATUALIZACAO = 60  # segundos

st.set_page_config(

    page_title="Mapa - Pessoas em Situação de Rua",
    layout="wide"
)

from datetime import datetime
from zoneinfo import ZoneInfo

col1, col2 = st.columns([1, 6])

with col1:
    st.image("LOGO_CENTRO_POP.png", width=200)

with col2:
    st.markdown(
        """
        <h2 style="
            margin-bottom: 0;
            font-size: 32px;
            font-weight: 600;
        ">
            Ourinhos-SP
        </h2>
        """,
        unsafe_allow_html=True
    )

    agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y | %H:%M")
    st.caption(f"Data e hora do acesso: {agora}")

st.title("Mapa das pessoas em situação de rua via Abordagem Social")
st.write("Mapeamento diário via abordagem das pessoas em situação de rua. E consulta por aplicativo, feito pela equipe de Abordagem, da Secretaria de Assistência e Desenvolvimento Social.")


# ===============================
# FUNÇÃO DE CARGA DE DADOS
# ===============================
@st.cache_data(ttl=TEMPO_ATUALIZACAO)
def carregar_dados():
    df = pd.read_csv(URL_CSV)

    # Correção na planilha de tipos na latitude "." e ","
    df["latitude"] = (
        df["latitude"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    df["longitude"] = (
        df["longitude"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    df["quantidade"] = df["quantidade"].astype(float)

# limpeza nos dados da planilha (p/ padrão migrante Sim ou Não)
    df["migrante"] = (
    df["migrante"]
    .astype(str)
    .str.strip()
)

    df["migrante"] = df["migrante"].replace({
    "SIM": "Sim",
    "sim": "Sim",
    "Sim": "Sim",
    "NÃO": "Não",
    "NAO": "Não",
    "Não": "Não",
    "nao": "Não"
})
    return df
    
# ===============================
# CARREGAR DADOS
# ===============================
df = carregar_dados()

# MAPA

fig = px.density_map(
    df,
    lat="latitude",
    lon="longitude",
    map_style="white-bg",
    z="quantidade",
    radius=15,
    zoom=12,
    color_continuous_scale="Inferno",
)

#AJUSTE DA POSIÇÃO DA LEGENDA DE INTENSIDADE RELATIVA

fig.update_layout(
    coloraxis_colorbar=dict(
        thickness=15,      # largura da barra (padrão ~30)
        len=0.75,          # altura relativa
        x=1.02,            # joga mais pra direita
        xanchor="left"
    )
)

# CORREÇÃO DO BASEMAP QUE ESTAVA SOBREPONDO AS VIAS SOB O HEATMAP

fig.update_layout(
    map_style="white-bg",
    map_layers=[
        {
            "below": "traces",
            "sourcetype": "raster",
            "source": [
                "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
            ]
        }
    ]
)

# MOSTRAR OS DADOS AO PASSAR O MOUSE NO MAPA (ISTO É UM SCATTERMAP INVISÍVEL)

fig.add_scattermap(
    lat=df["latitude"],
    lon=df["longitude"],
    mode="markers",
    marker=dict(size=8, opacity=0),
    customdata=df[["nome", "idade", "migrante"]],
    hovertemplate=
        "<b>%{customdata[0]}</b><br>" +
        "Idade: %{customdata[1]}<br>" +
        "Migrante: %{customdata[2]}<br>" +
        "Lat: %{lat:.4f}<br>" +
        "Lon: %{lon:.4f}<br>" +
        "<extra></extra>"
)

# LEGENDA DE INTENSIDADE RELATIVA

fig.update_layout(
    coloraxis=dict(
        cmin=0,
        cmax=df["quantidade"].max(),
        colorscale="Inferno",
        colorbar=dict(
            title="Intensidade relativa",
            tickmode="array",
            tickvals=[0, 0.5, 1],
            ticktext=["Baixa", "Média", "Alta"]
        )
    )
)

fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    height=450
)

from io import BytesIO

# EXPORTAÇÃO PARA EXCEL

def gerar_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

excel_file = gerar_excel(df)

st.plotly_chart(fig, use_container_width=True)

import base64

# Converte o arquivo Excel já gerado para base64

b64_excel = base64.b64encode(excel_file).decode()

st.markdown(f"""
<style>
.download-btn {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background-color: #1f4e79;
    color: white !important;
    padding: 10px 18px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 500;
    font-size: 15px;
    transition: all 0.2s ease-in-out;
}}
.download-btn:hover {{
    background-color: #163a5c;
    transform: translateY(-1px);
}}
.download-btn img {{
    filter: brightness(0) invert(1);
}}
</style>

<a download="base_pessoas_situacao_rua.xlsx"
   href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}"
   class="download-btn">
   <img src="https://raw.githubusercontent.com/lucas-nascimentosouza-dev/MEUS_SVGs/refs/heads/main/cloud-arrow-up-svgrepo-com.svg" width="18">
   Dados
</a>
""", unsafe_allow_html=True)

info_col, kpi_col = st.columns([3, 1.5])

# ================================
# INFO Nº TOTAL REGISTRS + TEXTO EXPLICATIVO 
# ===============================

with info_col:

    total_pessoas = int(df["quantidade"].sum())

    st.markdown(
    f"""
    <div style="
        border:1px solid #f0f0f0;
        border-radius:10px;
        padding:15px;
        background-color:#fafafa;
        margin-top:20px;
        max-width:900px;
    ">
        <h4 style="display:flex; align-items:center; gap:10px;">
            <img src="https://raw.githubusercontent.com/lucas-nascimentosouza-dev/MEUS_SVGs/refs/heads/main/electoral_17977484.svg" width="56">
            Sobre os dados
        </h4>

       <div style="font-size:26px; font-weight:700; color:#333;">
            {total_pessoas} <strong>Registros analisados</strong>
        </div>

       <div style="font-size:16px; font-weight:400; color:#666;">
            O mapa apresenta intensidade relativa de concentração espacial, com registros <strong>acumulativos de 90 dias </strong> conforme as abordagens são realizadas no município.
            Assim, o produto final é o mapa com a "mancha de calor" com incidência dos pontos onde as abordagens são registras num período de tempo (90 dias).
        </div>
        <div style="font-size:16px; font-weight:500; color:#666;">
            Também é gerado os dados gráficos de perfil das pessoas identificadas. E os Migrantes - refere-se as pessoas que estão em viagem e no trecho de Ourinhos. Essas pessoas estão de passagem pela cidade.
        </div>
    </div>    
    """,
    unsafe_allow_html=True
)

# ESPAÇO (NO MOBILE) ENTRE O BLOCO DE INFORMAÇÕES E O GRÁFICO DE BARRAS

st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)

with kpi_col:

# Padroniza

    df["migrante"] = df["migrante"].astype(str).str.strip()

    df_migrante = (
        df.groupby("migrante")
        .size()
        .reset_index(name="registros")
    )
    

    df_migrante["label"] = df_migrante["registros"].astype(str)

    fig_migrante = px.bar(
        df_migrante,
        x="migrante",
        y="registros",
        text="label",
        title="Migrantes"
    )

    cores = {
        "Sim": "#006b3e",
        "Não": "#cccccc"
    }

    fig_migrante.update_traces(
    marker_color=[
    cores.get(val, "#999999")
    for val in df_migrante["migrante"]
],
        textposition="outside"
    )

    max_valor = df_migrante["registros"].max()

    fig_migrante.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=0),
        xaxis_title="",
        yaxis_title="Registros",
        showlegend=False,
        yaxis=dict(
            range=[0, max_valor * 1.25],
            gridcolor="rgba(0,0,0,0.02)"
        )
    )

    st.plotly_chart(fig_migrante, use_container_width=True)


# ================================
# DADOS - GRÁFICO DE BARRAS (JÁ TINHA FEITO ESSE E DEPOIS CRIEI O GRÁFICO DE BARRAS % COMO CÓPIA DESSE BLOCO )
# ===============================
   
st.markdown("### Indicadores por perfil")

perfil = st.radio(
    "Visualizar por:",
    ["Gênero", "Raça/Cor", "Faixa Etária"],
    horizontal=True
)

mapa_colunas = {
    "Gênero": "genero",
    "Raça/Cor": "raca_cor",
    "Faixa Etária": "faixa_etaria"
}

coluna = mapa_colunas[perfil]
titulo = f"Distribuição por {perfil}"

df_percentual = (
    df[df[coluna].notna()]
    .groupby(coluna)
    .size()
    .reset_index(name="quantidade")
)

total = df_percentual["quantidade"].sum()

df_percentual["percentual"] = (
    df_percentual["quantidade"] / total * 100
).round(1)

df_percentual = df_percentual.sort_values(
    "percentual",
    ascending=False
)
fig = go.Figure()

cores_padrao = ["#006b3e", "#f39c12", "#1f77b4", "#e74c3c", "#8e44ad"]

for i, row in df_percentual.iterrows():
    fig.add_trace(
        go.Bar(
            x=[row["percentual"]],
            y=[""],
            orientation="h",
            name=row[coluna],
            text=f'{row["percentual"]:.1f}% ({int(row["quantidade"])})',
            textposition="inside",
            marker_color=cores_padrao[i % len(cores_padrao)]
        )
    )

fig.update_layout(
    barmode="stack",
    height=160,
    margin=dict(l=10, r=10, t=60, b=55),
    title=titulo,
    xaxis=dict(range=[0, 100], showticklabels=False),
    yaxis=dict(showticklabels=False),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.2,
        xanchor="center",
        x=0.5
    )
)

# OCULTA OPÇÕES pan, zoom, home, fullscreen (BOTOES EM CIMA DO GRÁFICO QUE NÃO SERVEM PRA NADA E DIFUCULTAM VIZUALIZAÇÃO)
st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)

# ESPAÇO VAZIO ENTRE O GRÁFICO DE BARRAS DE PERFIL E O BLOCO DE INFORMAÇÕES EXTRA (NO MOBILE)
st.write("")  

# INFO EXTRA
st.caption(f"Atualização diária automática: a cada 1 hora")

st.markdown(
    """
    <div style="
        background-color:#d4edda;
        padding:5px;
        border-radius:5px;
        color:#155724;
        font-weight:260;
    ">
        <span style="font-size:20px;">®</span>
        Webmap criado por Lucas Nascimento
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")  # espaço vazio

col_space1, col1, col2, col3, col_space2 = st.columns([3.9,0.7,0.7,0.7,0.1])

with col1:
    st.image("LOGO_NAIA.jpg", width=150)

with col2:
    st.image("LOGO_UNESP_preto.png", width=150)

with col3:
    st.image("LOGO_SMADS_2.jpeg", width=150)