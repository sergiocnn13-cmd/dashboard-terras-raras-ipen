import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re

# Configuração da página
st.set_page_config(
    page_title="Evolução da Pesquisa em Terras Raras — IPEN",
    page_icon="⚛️",
    layout="wide"
)

# --- DICIONÁRIO DAS 17 TERRAS RARAS ---
TERRAS_RARAS = [
    {"z": 21, "simbolo": "Sc", "nome": "Escândio",    "en": "Scandium",     "massa": "44.96",  "grupo": "TRL"},
    {"z": 39, "simbolo": "Y",  "nome": "Ítrio",       "en": "Yttrium",      "massa": "88.91",  "grupo": "TRP"},
    {"z": 57, "simbolo": "La", "nome": "Lantânio",    "en": "Lanthanum",    "massa": "138.91", "grupo": "TRL"},
    {"z": 58, "simbolo": "Ce", "nome": "Cério",       "en": "Cerium",       "massa": "140.12", "grupo": "TRL"},
    {"z": 59, "simbolo": "Pr", "nome": "Praseodímio", "en": "Praseodymium", "massa": "140.91", "grupo": "TRL"},
    {"z": 60, "simbolo": "Nd", "nome": "Neodímio",    "en": "Neodymium",    "massa": "144.24", "grupo": "TRL"},
    {"z": 61, "simbolo": "Pm", "nome": "Promécio",    "en": "Promethium",   "massa": "(145)",  "grupo": "TRL"},
    {"z": 62, "simbolo": "Sm", "nome": "Samário",     "en": "Samarium",     "massa": "150.36", "grupo": "TRL"},
    {"z": 63, "simbolo": "Eu", "nome": "Európio",     "en": "Europium",     "massa": "151.96", "grupo": "TRL"},
    {"z": 64, "simbolo": "Gd", "nome": "Gadolínio",   "en": "Gadolinium",   "massa": "157.25", "grupo": "TRP"},
    {"z": 65, "simbolo": "Tb", "nome": "Térbio",      "en": "Terbium",      "massa": "158.93", "grupo": "TRP"},
    {"z": 66, "simbolo": "Dy", "nome": "Disprósio",   "en": "Dysprosium",   "massa": "162.50", "grupo": "TRP"},
    {"z": 67, "simbolo": "Ho", "nome": "Hólmio",      "en": "Holmium",      "massa": "164.93", "grupo": "TRP"},
    {"z": 68, "simbolo": "Er", "nome": "Érbio",       "en": "Erbium",       "massa": "167.26", "grupo": "TRP"},
    {"z": 69, "simbolo": "Tm", "nome": "Túlio",       "en": "Thulium",      "massa": "168.93", "grupo": "TRP"},
    {"z": 70, "simbolo": "Yb", "nome": "Itérbio",     "en": "Ytterbium",    "massa": "173.05", "grupo": "TRP"},
    {"z": 71, "simbolo": "Lu", "nome": "Lutécio",     "en": "Lutetium",     "massa": "174.97", "grupo": "TRP"},
]

MAPA_ELEMENTOS = {
    f"{el['z']} | {el['simbolo']} — {el['nome']} ({el['grupo']})": el
    for el in TERRAS_RARAS
}

def renderizar_card_elemento(el: dict) -> str:
    """Gera o card visual estilo Tabela Periódica com número atômico e massa atômica."""
    cor_badge = "#1B365D" if el["grupo"] == "TRL" else "#0F766E"
    return f"""
    <div style="
        width: 132px;
        border: 3px solid #2D3748;
        border-radius: 14px;
        background-color: #FFFFFF;
        color: #1A202C;
        text-align: center;
        padding: 8px 6px;
        font-family: 'Segoe UI', Arial, sans-serif;
        box-shadow: 0 2px 6px rgba(0,0,0,0.18);
        margin: 4px auto;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 4px;">
            <span style="font-size: 15px; font-weight: 700;">{el['z']}</span>
            <span style="font-size: 10px; font-weight: 700; color: #FFF; background: {cor_badge}; padding: 1px 5px; border-radius: 4px;">{el['grupo']}</span>
        </div>
        <div style="font-size: 36px; font-weight: 800; line-height: 1.05; margin: 2px 0;">{el['simbolo']}</div>
        <div style="font-size: 13px; font-weight: 600; margin-bottom: 2px;">{el['nome']}</div>
        <div style="font-size: 13px; color: #4A5568; font-weight: 500;">{el['massa']}</div>
    </div>
    """

@st.cache_data
def carregar_dados(caminho_arquivo: str) -> pd.DataFrame:
    df = pd.read_csv(caminho_arquivo, sep=";", low_memory=False)
    if df.shape[1] == 1:
        df = pd.read_csv(caminho_arquivo, sep=",", low_memory=False)
    
    df = df.dropna(subset=["Ano"]).copy()
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").astype(int)
    df["Decada"] = (df["Ano"] // 10) * 10
    df["Relevancia_Macro"] = df["Relevancia_Macro"].fillna("Não classificado").str.strip()
    
    # Mapeia os rótulos originais do CSV ("Direta" / "Indireta") para os novos termos
    df["Enfoque"] = df["Relevancia_Macro"].map({
        "Direta": "Específicos",
        "Indireta": "Adjacentes"
    }).fillna(df["Relevancia_Macro"])
    
    df["Tipo_Documento"] = df["Tipo_Documento"].fillna("Não informado").str.strip()
    df["Termos_Identificados"] = df["Termos_Identificados"].fillna("")
    df["Titulo"] = df["Titulo"].fillna("")
    return df

# Localização automática do CSV
PASTA_ATUAL = Path(__file__).parent
ARQUIVO_PADRAO = PASTA_ATUAL / "Repositorio_IPEN_Terras_Raras_4228.csv"

if ARQUIVO_PADRAO.exists():
    ARQUIVO_CSV = str(ARQUIVO_PADRAO)
else:
    csvs_encontrados = sorted(PASTA_ATUAL.glob("Repositorio_IPEN_Terras_Raras_*.csv"))
    ARQUIVO_CSV = str(csvs_encontrados[0]) if csvs_encontrados else "Repositorio_IPEN_Terras_Raras_4228.csv"

df = carregar_dados(ARQUIVO_CSV)

# --- CABEÇALHO ---
st.title("⚛️ Evolução da Pesquisa sobre Terras Raras no IPEN")
st.markdown(
    "Painel analítico da produção científica indexada no Repositório Institucional do IPEN "
    "(**4.228 registros** detectados entre **1961 e 2026**)."
)

# --- SELETOR PRINCIPAL DE ESCOPO DA PESQUISA ---
st.subheader("1. Selecione o Escopo da Pesquisa")
opcao_escopo = st.segmented_control(
    "Abordagem dos Trabalhos:",
    options=[
        "Ambos (Específicos + Adjacentes)",
        "Específicos",
        "Adjacentes"
    ],
    default="Ambos (Específicos + Adjacentes)",
    selection_mode="single"
)

if opcao_escopo is None:
    opcao_escopo = "Ambos (Específicos + Adjacentes)"

if opcao_escopo == "Específicos":
    df_filtrado = df[df["Enfoque"] == "Específicos"].copy()
elif opcao_escopo == "Adjacentes":
    df_filtrado = df[df["Enfoque"] == "Adjacentes"].copy()
else:
    df_filtrado = df.copy()

# --- BARRA LATERAL (FILTROS COMPLEMENTARES) ---
st.sidebar.header("Filtros Complementares")

ano_min, ano_max = int(df["Ano"].min()), int(df["Ano"].max())
faixa_anos = st.sidebar.slider(
    "Período (Ano)",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max)
)

# Seletor das 17 Terras Raras (TRL / TRP) com Cards Visuais
st.sidebar.markdown("---")
st.sidebar.subheader("Elementos de Terras Raras")

filtro_grupo = st.sidebar.radio(
    "Classificação Geoquímica:",
    options=["Todas (17)", "Terras Raras Leves (TRL)", "Terras Raras Pesadas (TRP)"],
    horizontal=False
)

if filtro_grupo == "Terras Raras Leves (TRL)":
    opcoes_elementos = [k for k, v in MAPA_ELEMENTOS.items() if v["grupo"] == "TRL"]
elif filtro_grupo == "Terras Raras Pesadas (TRP)":
    opcoes_elementos = [k for k, v in MAPA_ELEMENTOS.items() if v["grupo"] == "TRP"]
else:
    opcoes_elementos = list(MAPA_ELEMENTOS.keys())

elementos_selecionados = st.sidebar.multiselect(
    "Selecione o(s) elemento(s):",
    options=opcoes_elementos,
    default=[],
    placeholder="Ex: 57 | La — Lantânio..."
)

# Exibe os cards estilo Tabela Periódica na barra lateral
if elementos_selecionados:
    cols_cards = st.sidebar.columns(2)
    for idx, chave in enumerate(elementos_selecionados):
        el_info = MAPA_ELEMENTOS[chave]
        with cols_cards[idx % 2]:
            st.markdown(renderizar_card_elemento(el_info), unsafe_allow_html=True)

st.sidebar.markdown("---")

tipos_disponiveis = sorted(df_filtrado["Tipo_Documento"].unique().tolist())
tipos_selecionados = st.sidebar.multiselect(
    "Tipologia Documental",
    options=tipos_disponiveis,
    default=tipos_disponiveis
)

niveis_disponiveis = sorted(df_filtrado["Nivel_Relevancia"].unique().tolist())
niveis_selecionados = st.sidebar.multiselect(
    "Subnível de Relevância",
    options=niveis_disponiveis,
    default=niveis_disponiveis
)

# --- APLICAÇÃO DOS FILTROS ---
df_filtrado = df_filtrado[
    (df_filtrado["Ano"].between(faixa_anos[0], faixa_anos[1])) &
    (df_filtrado["Tipo_Documento"].isin(tipos_selecionados)) &
    (df_filtrado["Nivel_Relevancia"].isin(niveis_selecionados))
]

# Filtro por Grupo (TRL / TRP)
if filtro_grupo != "Todas (17)":
    grupo_alvo = "TRL" if "TRL" in filtro_grupo else "TRP"
    els_grupo = [el for el in TERRAS_RARAS if el["grupo"] == grupo_alvo]
    padroes_grupo = []
    for el in els_grupo:
        padroes_grupo.extend([
            rf"\b{re.escape(el['nome'].lower())}\b",
            rf"\b{re.escape(el['en'].lower())}\b",
            rf"(?<![A-Za-z]){re.escape(el['simbolo'])}(?![a-z])"
        ])
    regex_grupo = "|".join(padroes_grupo)
    df_filtrado = df_filtrado[
        df_filtrado["Termos_Identificados"].str.contains(regex_grupo, case=False, na=False, regex=True) |
        df_filtrado["Titulo"].str.contains(regex_grupo, case=False, na=False, regex=True)
    ]

# Filtro por Elementos Específicos escolhidos
if elementos_selecionados:
    padroes_el = []
    for chave in elementos_selecionados:
        el = MAPA_ELEMENTOS[chave]
        padroes_el.extend([
            rf"\b{re.escape(el['nome'].lower())}\b",
            rf"\b{re.escape(el['en'].lower())}\b",
            rf"(?<![A-Za-z]){re.escape(el['simbolo'])}(?![a-z])"
        ])
    regex_el = "|".join(padroes_el)
    df_filtrado = df_filtrado[
        df_filtrado["Termos_Identificados"].str.contains(regex_el, case=False, na=False, regex=True) |
        df_filtrado["Titulo"].str.contains(regex_el, case=False, na=False, regex=True)
    ]

# --- KPIS (INDICADORES) ---
col1, col2, col3, col4 = st.columns(4)
total_sel = len(df_filtrado)
qtd_especificos = int((df_filtrado["Enfoque"] == "Específicos").sum())
qtd_adjacentes = int((df_filtrado["Enfoque"] == "Adjacentes").sum())
ano_pico = (
    int(df_filtrado["Ano"].value_counts().idxmax())
    if total_sel > 0 else "-"
)

col1.metric("Total de Trabalhos Selecionados", f"{total_sel:,}".replace(",", "."))
col2.metric("Trabalhos Específicos", f"{qtd_especificos:,}".replace(",", "."))
col3.metric("Trabalhos Adjacentes", f"{qtd_adjacentes:,}".replace(",", "."))
col4.metric("Ano de Maior Produção", str(ano_pico))

st.divider()

# --- GRÁFICO PRINCIPAL: EVOLUÇÃO ANUAL ---
st.subheader(f"2. Evolução Temporal — {opcao_escopo}")

col_opt1, col_opt2 = st.columns([1, 3])
with col_opt1:
    modo_visualizacao = st.radio(
        "Formato do Gráfico Anual:",
        options=["Linhas (Tendência)", "Barras Empilhadas", "Área Acumulada"],
        horizontal=False
    )

CORES = {"Específicos": "#1B365D", "Adjacentes": "#D97706"}

if total_sel > 0:
    evolucao_ano = (
        df_filtrado.groupby(["Ano", "Enfoque"])
        .size()
        .reset_index(name="Publicacoes")
    )

    todos_anos = pd.MultiIndex.from_product(
        [range(faixa_anos[0], faixa_anos[1] + 1), evolucao_ano["Enfoque"].unique()],
        names=["Ano", "Enfoque"]
    )
    evolucao_ano = (
        evolucao_ano.set_index(["Ano", "Enfoque"])
        .reindex(todos_anos, fill_value=0)
        .reset_index()
    )

    if modo_visualizacao == "Linhas (Tendência)":
        fig_tempo = px.line(
            evolucao_ano,
            x="Ano",
            y="Publicacoes",
            color="Enfoque",
            markers=True,
            color_discrete_map=CORES,
            labels={"Publicacoes": "Nº de Publicações", "Enfoque": "Abordagem"}
        )
    elif modo_visualizacao == "Barras Empilhadas":
        fig_tempo = px.bar(
            evolucao_ano,
            x="Ano",
            y="Publicacoes",
            color="Enfoque",
            barmode="stack",
            color_discrete_map=CORES,
            labels={"Publicacoes": "Nº de Publicações", "Enfoque": "Abordagem"}
        )
    else:
        evolucao_ano["Acumulado"] = evolucao_ano.groupby("Enfoque")["Publicacoes"].cumsum()
        fig_tempo = px.area(
            evolucao_ano,
            x="Ano",
            y="Acumulado",
            color="Enfoque",
            color_discrete_map=CORES,
            labels={"Acumulado": "Publicações Acumuladas", "Enfoque": "Abordagem"}
        )

    fig_tempo.update_layout(
        hovermode="x unified",
        legend_title_text="Abordagem",
        height=430
    )
    st.plotly_chart(fig_tempo, use_container_width=True)
else:
    st.warning("Nenhum registro encontrado com os filtros atuais.")

# --- GRÁFICOS SECUNDÁRIOS: DÉCADA E TIPOLOGIA ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("3. Distribuição por Década")
    if total_sel > 0:
        por_decada = (
            df_filtrado.groupby(["Decada", "Enfoque"])
            .size()
            .reset_index(name="Publicacoes")
        )
        por_decada["Decada"] = por_decada["Decada"].astype(str) + "s"
        fig_dec = px.bar(
            por_decada,
            x="Decada",
            y="Publicacoes",
            color="Enfoque",
            barmode="group",
            text_auto=True,
            color_discrete_map=CORES,
            labels={"Publicacoes": "Nº de Publicações", "Decada": "Década", "Enfoque": "Abordagem"}
        )
        fig_dec.update_layout(height=380, legend_title_text="Abordagem")
        st.plotly_chart(fig_dec, use_container_width=True)

with col_g2:
    st.subheader("4. Distribuição por Tipologia Documental")
    if total_sel > 0:
        por_tipo = (
            df_filtrado.groupby(["Tipo_Documento", "Enfoque"])
            .size()
            .reset_index(name="Publicacoes")
        )
        ordem_tipos = (
            por_tipo.groupby("Tipo_Documento")["Publicacoes"]
            .sum()
            .sort_values(ascending=True)
            .index.tolist()
        )
        fig_tipo = px.bar(
            por_tipo,
            x="Publicacoes",
            y="Tipo_Documento",
            color="Enfoque",
            orientation="h",
            barmode="stack",
            category_orders={"Tipo_Documento": ordem_tipos},
            color_discrete_map=CORES,
            labels={"Publicacoes": "Nº de Publicações", "Tipo_Documento": "Tipologia", "Enfoque": "Abordagem"}
        )
        fig_tipo.update_layout(height=380, legend_title_text="Abordagem")
        st.plotly_chart(fig_tipo, use_container_width=True)

# --- TABELA EXPLORATÓRIA E DOWNLOAD ---
st.divider()
st.subheader("5. Base de Registros Filtrados")

colunas_exibir = [
    "Ano", "Enfoque", "Nivel_Relevancia", "Tipo_Documento",
    "Titulo", "Autores_IPEN", "Termos_Identificados", "Handle_URI"
]
colunas_existentes = [c for c in colunas_exibir if c in df_filtrado.columns]

st.dataframe(
    df_filtrado[colunas_existentes].sort_values(by=["Ano", "Titulo"], ascending=[False, True]),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Ano": st.column_config.NumberColumn("Ano", format="%d"),
        "Handle_URI": st.column_config.LinkColumn("Link DSpace", display_text="Abrir no Repositório")
    }
)

csv_export = df_filtrado.to_csv(index=False, sep=";", encoding="utf-8-sig")
st.download_button(
    label="📥 Baixar Recorte Atual (.CSV)",
    data=csv_export,
    file_name="recorte_terras_raras_ipen.csv",
    mime="text/csv"
)
