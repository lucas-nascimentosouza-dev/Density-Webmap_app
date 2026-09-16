
import streamlit as st

st.set_page_config(

    page_title="Mapa - Pessoas em Situação de Rua",
    layout="wide"
)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from streamlit_js_eval import streamlit_js_eval

screen_width = streamlit_js_eval(js_expressions='window.innerWidth', key='SCR')

is_mobile = screen_width and screen_width < 768

# =============================
# AJUSTE PARA MOBILE (RESPONSIVO) CSS
# =============================
st.markdown("""
<style>

/* ===== AJUSTE GLOBAL RADIO (DESKTOP + MOBILE) ===== */
div[role="radiogroup"] {
    margin-bottom: -12px;
}

.stRadio > div {
    gap: 0.3rem;
}

.stRadio label {
    margin-bottom: 0px !important;
}

/* ===== MOBILE ONLY ===== */
@media (max-width: 768px) {

    /* Ajuste específico mobile (menos agressivo) */
    div[role="radiogroup"] {
        margin-bottom: -26px;
    }
            
    .stRadio {
    margin-bottom: -4px;
}
    /* Remove botões do Plotly */
    .modebar {
        display: none !important;
    }

    /* Ajusta padding lateral */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Ajusta botão download */
    .download-btn {
        width: 40% !important;
        margin: 0 auto !important;
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
URL_ABORDAGENS = "https://docs.google.com/spreadsheets/d/1-yYDDiqyAJ_oonv-0rL3p5_Z6WI-kUhm6E6n_BkyQfI/export?format=csv&gid=0"

URL_PESSOAS = "https://docs.google.com/spreadsheets/d/1-yYDDiqyAJ_oonv-0rL3p5_Z6WI-kUhm6E6n_BkyQfI/export?format=csv&gid=1396205253"

TEMPO_ATUALIZACAO = 60  # segundos

CARTO_API_KEY = "cb1_3lcl_1_cbd50d77f703c1bb879abbaf"

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

    # =============================
    # ABA ABORDAGENS
    # =============================
    df = pd.read_csv(URL_ABORDAGENS)

    # Limpeza dos nomes das colunas
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    # Latitude
    df["latitude"] = (
        df["latitude"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    # Longitude
    df["longitude"] = (
        df["longitude"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    # Quantidade
    df["quantidade"] = (
        pd.to_numeric(df["quantidade"], errors="coerce")
        .fillna(1)
    )

    # Migrante
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


# =============================
# CARREGAR PESSOAS
# =============================
@st.cache_data(ttl=TEMPO_ATUALIZACAO)
def carregar_pessoas():

    pessoas = pd.read_csv(URL_PESSOAS)

    pessoas.columns = (
        pessoas.columns
        .str.strip()
        .str.lower()
    )

    return pessoas
    
# ===============================
# CARREGAR DADOS
# ===============================
df = carregar_dados()
pessoas = carregar_pessoas()


# MAPA

fig = go.Figure(
    go.Densitymap(
        lat=df["latitude"],
        lon=df["longitude"],
        z=df["quantidade"],
        radius=12,
        coloraxis="coloraxis",
        opacity=0.9
    )
)

fig.update_layout(
    map=dict(
        style="white-bg",
        zoom=12,
        center=dict(
            lat=-22.98,
            lon=-49.87
        ),

        # CORREÇÃO DO BASEMAP QUE ESTAVA SOBREPONDO AS VIAS SOB O HEATMAP
        layers=[
            {
                "below": "traces",
                "sourcetype": "raster",
                "source": [
                    f"https://basemaps.cartocdn.com/rastertiles/light_all/{{z}}/{{x}}/{{y}}.png?key={CARTO_API_KEY}"
                ]
            }
        ]
    ),
    margin=dict(l=0, r=0, t=0, b=0),
    height=500
)

# SETA DO NORTE
import base64

def carregar_imagem_base64(caminho):
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_base64 = carregar_imagem_base64("seta_norte_wing.png")

fig.add_layout_image(
    dict(
        source=f"data:image/png;base64,{img_base64}",
        xref="paper",
        yref="paper",
        x=0.02,
        y=0.98,
        sizex=0.15,   # aumenta aqui (proporcional)👈
        sizey=0.15,   # aumenta aqui (proporcional)👈
        xanchor="left",
        yanchor="top",
        layer="above"
    )
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

# ==============================
# LEGENDA DE INTENSIDADE RELATIVA mobile  x desktop
# ==============================

valor_maximo = df["quantidade"].max()

if is_mobile:

    legenda_config = dict(
        title="Intensidade",
        thickness=9,
        len=0.40,
        tickmode="array",
        tickvals=[
            0,
            valor_maximo / 2,
            valor_maximo
        ],
        ticktext=[
            "Baixa",
            "Média",
            "Alta"
        ],
    )

else:

    legenda_config = dict(
        title="Intensidade Relativa",
        thickness=16,
        len=0.68,
        tickmode="array",
        tickvals=[
            0,
            valor_maximo / 2,
            valor_maximo
        ],
        ticktext=[
            "Baixa",
            "Média",
            "Alta"
        ],
        x=1.00,
        xanchor="left",
        y=0.55
    )

fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),

    coloraxis=dict(
        cmin=0,
        cmax=df["quantidade"].max(),
        colorscale="Inferno",
        colorbar=legenda_config
    )
)

st.plotly_chart(fig, use_container_width=True)


# BARRA DE ESCALA DINÂMICA (JS INJETADO) - AJUSTADO PARA MOBILE E DESKTOP
import streamlit.components.v1 as components

azul_marinho = "#1f4e79"

components.html(f"""
<script>
    const AZUL_MARINHO = "{azul_marinho}";
    
    function injectScaleBar() {{ // <--- Chave aberta corretamente aqui
        const plotEl = window.parent.document.querySelector('.js-plotly-plot');
        if (!plotEl) return false;

        let container = window.parent.document.getElementById('dynamic-gis-scale');
        
        if (!container) {{
            container = window.parent.document.createElement('div');
            container.id = 'dynamic-gis-scale';
            
            // Lógica de detecção de tela
            const isMobile = window.parent.innerWidth <= 768;
            const rightPos = isMobile ? "3px" : "173px";
            const bottomPos = isMobile ? "15px" : "5px";

            container.style.cssText = `
                position: absolute;
                bottom: ${{bottomPos}};
                right: ${{rightPos}};
                z-index: 99999;
                padding: 6px 12px;
                background: #f8f9fa; 
                border: 1px solid #c7ced8; 
                border-radius: 8px; 
                display: flex;
                flex-direction: column;
                align-items: center;
                pointer-events: none;
                font-family: sans-serif;
                box-shadow: 0px 2px 6px rgba(0,0,0,0.15);
            `;
            
            container.innerHTML = `
                <div style="color: #2C3E50; font-size: 11px; font-weight: bold; margin-bottom: 2px; text-transform: none !important;">Escala</div>
                <div id="gis-label" style="color: ${{AZUL_MARINHO}}; font-weight: bold; font-size: 13px; margin-bottom: 4px;">Calculando...</div>
                <div style="width: 80px; height: 5px; background: ${{AZUL_MARINHO}}; border-radius: 3px;"></div>
            `;
            
            plotEl.appendChild(container);
        }}

        const label = window.parent.document.getElementById('gis-label');

        const updateValue = () => {{
            const layout = plotEl.layout.map || plotEl.layout.mapbox;
            if (layout && layout.zoom) {{
                const zoom = layout.zoom;
                const lat = layout.center ? layout.center.lat : -22.9;
                const metersPerPx = (156543.03 * Math.cos(lat * Math.PI / 180)) / Math.pow(2, zoom);
                const totalMeters = metersPerPx * 80;

                label.innerText = totalMeters >= 1000 
                    ? (totalMeters / 1000).toFixed(2) + " km" 
                    : Math.round(totalMeters) + " m";
            }}
        }}; // <--- Chave do updateValue corrigida

        plotEl.on('plotly_relayout', updateValue);
        updateValue();
        return true;
    }} // <--- Chave da função principal corrigida

    const timer = setInterval(() => {{
        if (injectScaleBar()) clearInterval(timer);
    }}, 500);
</script>
""", height=0)

from io import BytesIO

# EXPORTAÇÃO PARA EXCEL
def gerar_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

excel_file = gerar_excel(df)


import base64

# BOTÃO DOWNLOAD - Converte o arquivo Excel já gerado para base64

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

info_col, kpi_col = st.columns([2.5, 1.2])

# ================================
# INFO Nº TOTAL REGISTRS + TEXTO EXPLICATIVO 
# ===============================

with info_col:

    total_pessoas = int(df["quantidade"].sum())

    total_cadastradas = (
        pessoas["id_pessoa"]
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

    st.markdown(
        f"""
<div style="border:1px solid #f0f0f0; border-radius:10px; padding:15px; background-color:#fafafa; margin-top:20px; max-width:900px;">

<h4 style="margin-top:0;">
<img src="https://raw.githubusercontent.com/lucas-nascimentosouza-dev/MEUS_SVGs/refs/heads/main/electoral_17977484.svg" width="56" style="vertical-align:middle; margin-right:10px;">
Sobre os dados
</h4>

<table style="width:100%; margin-bottom:15px;">
<tr>

<td style="width:50%; vertical-align:top;">
<div style="font-size:28px; font-weight:700; color:#333;">
{total_pessoas}
</div>
<div style="font-size:15px; font-weight:620; color:#666;">
Registros total de abordagens
</div>
</td>

<td style="width:50%; vertical-align:top; border-left:1px solid #ddd; padding-left:35px;">
<div style="font-size:28px; font-weight:700; color:#333;">
{total_cadastradas}
</div>
<div style="font-size:15px; font-weight:620; color:#666;">
Quantidade de pessoas cadastradas (sem duplicidade)
</div>
</td>

</tr>
</table>

<div style="text-align:justify; font-size:16px; font-weight:400; color:#666;">
O mapa apresenta intensidade relativa de concentração espacial, com registros <strong>acumulativos de 90 dias</strong> conforme as abordagens são realizadas no município.
Assim, o produto final é o mapa de "mancha de calor" com a intensidade dos pontos onde as abordagens são registradas num período de tempo (90 dias).
Enquanto os registros representam o número total de abordagens realizadas, podendo uma mesma pessoa ser registrada em diferentes pontos de abordagens ao longo do período, o número de pessoas cadastradas representa a quantidade de indivíduos, sem duplicidade.
</div>

<div style="text-align:justify; font-size:16px; font-weight:500; color:#666; margin-top:8px;">
Também são gerados dados gráficos de perfil das pessoas identificadas.
Os migrantes referem-se às pessoas que estão em viagem e no trecho de Ourinhos.
Essas pessoas estão de passagem pela cidade.
</div>

</div>
""",
        unsafe_allow_html=True
    )

# ESPAÇO (NO MOBILE) ENTRE O BLOCO DE INFORMAÇÕES E O GRÁFICO DE BARRAS

st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)

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
# AJUSTE DA MARGEM
if is_mobile:
    margin_top = 90
    legend_y = 0.97
    title_y = 0.90
else:
    margin_top = 60
    legend_y = 1.05


fig.update_layout(
    barmode="stack",
    height=120 if is_mobile else 97,
    margin=dict(l=10, r=10, t=margin_top, b=0),
    title=titulo,
    xaxis=dict(range=[0, 100], showticklabels=False),
    yaxis=dict(showticklabels=False),
    legend=dict(
    orientation="h",
    yanchor="bottom",
    y=legend_y,
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
st.caption(f"Atualização diária automática: a cada 1 minuto")

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

st.write("")  # Espaço entre o rodapé e os logos

col_space1, col1, col2, col3, col_space2 = st.columns([5.99,1.6,1.6,1.6,0.01])

with col1:
    st.image("LOGO_NAIA.jpg", width=150)

with col2:
    st.image("LOGO_UNESP_V2.png", width=150)

with col3:
    st.image("LOGO_SMADS_2.jpeg", width=150)