import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import glob

# Configuração da página
st.set_page_config(
    page_title="Evolução da Pesquisa em Terras Raras — IPEN",
    page_icon="⚛️",
    layout="wide"
)

@st.cache_data
def carregar_dados(caminho_arquivo: str) -> pd.DataFrame:
    # Lê o CSV com separador ponto e vírgula (padrão gerado) ou vírgula como fallback
    df = pd.read_csv(caminho_arquivo, sep=";", low_memory=False)
    if df.shape[1] == 1:
        df = pd.read_csv(caminho_arquivo, sep=",", low_memory=False)
    
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").dropna().astype(int)
    df["Decada"] = (df["Ano"] // 10) * 10
    df["Relevancia_Macro"] = df["Relevancia_Macro"].fillna("Não classificado").str.strip()
    df["Tipo_Documento"] = df["Tipo_Documento"].fillna("Não informado").str.strip()
    df["Termos_Identificados"] = df["Termos_Identificados"].fillna("")
    return df

# Carregamento
# Carregamento
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

# --- SELETOR PRINCIPAL DE TIPO DE CITAÇÃO ---
st.subheader("1. Selecione o Escopo das Citações")
opcao_citacao = st.segmented_control(
    "Tipo de Citação:",
    options=[
        "Ambos (Direta + Indireta)",
        "Somente Direta",
        "Somente Indireta"
    ],
    default="Ambos (Direta + Indireta)",
    selection_mode="single"
)

# Fallback caso esteja usando versão antiga do Streamlit (< 1.40)
if opcao_citacao is None:
    opcao_citacao = "Ambos (Direta + Indireta)"

# Aplica o filtro principal
if opcao_citacao == "Somente Direta":
    df_filtrado = df[df["Relevancia_Macro"] == "Direta"].copy()
elif opcao_citacao == "Somente Indireta":
    df_filtrado = df[df["Relevancia_Macro"] == "Indireta"].copy()
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

busca_termo = st.sidebar.text_input(
    "Filtrar por elemento/termo (ex: cério, neodímio, monazita, Eu3+)",
    value=""
).strip()

# Aplicação dos filtros da barra lateral
df_filtrado = df_filtrado[
    (df_filtrado["Ano"].between(faixa_anos[0], faixa_anos[1])) &
    (df_filtrado["Tipo_Documento"].isin(tipos_selecionados)) &
    (df_filtrado["Nivel_Relevancia"].isin(niveis_selecionados))
]

if busca_termo:
    mask_termo = (
        df_filtrado["Termos_Identificados"].str.contains(busca_termo, case=False, na=False) |
        df_filtrado["Titulo"].str.contains(busca_termo, case=False, na=False)
    )
    df_filtrado = df_filtrado[mask_termo]

# --- KPIS (INDICADORES) ---
col1, col2, col3, col4 = st.columns(4)
total_sel = len(df_filtrado)
qtd_direta = int((df_filtrado["Relevancia_Macro"] == "Direta").sum())
qtd_indireta = int((df_filtrado["Relevancia_Macro"] == "Indireta").sum())
ano_pico = (
    int(df_filtrado["Ano"].value_counts().idxmax())
    if total_sel > 0 else "-"
)

col1.metric("Total de Trabalhos Selecionados", f"{total_sel:,}".replace(",", "."))
col2.metric("Citações Diretas", f"{qtd_direta:,}".replace(",", "."))
col3.metric("Citações Indiretas", f"{qtd_indireta:,}".replace(",", "."))
col4.metric("Ano de Maior Produção", str(ano_pico))

st.divider()

# --- GRÁFICO PRINCIPAL: EVOLUÇÃO ANUAL ---
st.subheader(f"2. Evolução Temporal — {opcao_citacao}")

col_opt1, col_opt2 = st.columns([1, 3])
with col_opt1:
    modo_visualizacao = st.radio(
        "Formato do Gráfico Anual:",
        options=["Linhas (Tendência)", "Barras Empilhadas", "Área Acumulada"],
        horizontal=False
    )

CORES = {"Direta": "#1B365D", "Indireta": "#D97706"}

if total_sel > 0:
    evolucao_ano = (
        df_filtrado.groupby(["Ano", "Relevancia_Macro"])
        .size()
        .reset_index(name="Publicacoes")
    )

    # Preenche anos sem publicação com 0 para continuidade visual da linha
    todos_anos = pd.MultiIndex.from_product(
        [range(faixa_anos[0], faixa_anos[1] + 1), evolucao_ano["Relevancia_Macro"].unique()],
        names=["Ano", "Relevancia_Macro"]
    )
    evolucao_ano = (
        evolucao_ano.set_index(["Ano", "Relevancia_Macro"])
        .reindex(todos_anos, fill_value=0)
        .reset_index()
    )

    if modo_visualizacao == "Linhas (Tendência)":
        fig_tempo = px.line(
            evolucao_ano,
            x="Ano",
            y="Publicacoes",
            color="Relevancia_Macro",
            markers=True,
            color_discrete_map=CORES,
            labels={"Publicacoes": "Nº de Publicações", "Relevancia_Macro": "Tipo de Citação"}
        )
    elif modo_visualizacao == "Barras Empilhadas":
        fig_tempo = px.bar(
            evolucao_ano,
            x="Ano",
            y="Publicacoes",
            color="Relevancia_Macro",
            barmode="stack",
            color_discrete_map=CORES,
            labels={"Publicacoes": "Nº de Publicações", "Relevancia_Macro": "Tipo de Citação"}
        )
    else:
        evolucao_ano["Acumulado"] = evolucao_ano.groupby("Relevancia_Macro")["Publicacoes"].cumsum()
        fig_tempo = px.area(
            evolucao_ano,
            x="Ano",
            y="Acumulado",
            color="Relevancia_Macro",
            color_discrete_map=CORES,
            labels={"Acumulado": "Publicações Acumuladas", "Relevancia_Macro": "Tipo de Citação"}
        )

    fig_tempo.update_layout(
        hovermode="x unified",
        legend_title_text="Classificação",
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
            df_filtrado.groupby(["Decada", "Relevancia_Macro"])
            .size()
            .reset_index(name="Publicacoes")
        )
        por_decada["Decada"] = por_decada["Decada"].astype(str) + "s"
        fig_dec = px.bar(
            por_decada,
            x="Decada",
            y="Publicacoes",
            color="Relevancia_Macro",
            barmode="group",
            text_auto=True,
            color_discrete_map=CORES,
            labels={"Publicacoes": "Nº de Publicações", "Decada": "Década"}
        )
        fig_dec.update_layout(height=380, legend_title_text="Classificação")
        st.plotly_chart(fig_dec, use_container_width=True)

with col_g2:
    st.subheader("4. Distribuição por Tipologia Documental")
    if total_sel > 0:
        por_tipo = (
            df_filtrado.groupby(["Tipo_Documento", "Relevancia_Macro"])
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
            color="Relevancia_Macro",
            orientation="h",
            barmode="stack",
            category_orders={"Tipo_Documento": ordem_tipos},
            color_discrete_map=CORES,
            labels={"Publicacoes": "Nº de Publicações", "Tipo_Documento": "Tipologia"}
        )
        fig_tipo.update_layout(height=380, legend_title_text="Classificação")
        st.plotly_chart(fig_tipo, use_container_width=True)

# --- TABELA EXPLORATÓRIA E DOWNLOAD ---
st.divider()
st.subheader("5. Base de Registros Filtrados")

colunas_exibir = [
    "Ano", "Relevancia_Macro", "Nivel_Relevancia", "Tipo_Documento",
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