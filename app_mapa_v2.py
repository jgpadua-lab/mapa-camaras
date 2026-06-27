import pandas as pd
import plotly.express as px
import streamlit as st
import requests
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Mapa de Sementes", layout="wide")
st.title("📦 Mapa de Câmaras Frias - Sementes")

# 1. Função para carregar os dados
@st.cache_data(ttl=600)
def carregar_dados():
    # Coloque o seu ID aqui novamente
    arquivo_id = 'COLOQUE_AQUI_O_ID_DO_SEU_ARQUIVO_DO_DRIVE'
    
    # O link precisa ter esse 'export=download' para forçar o Drive a baixar
    url = f'https://drive.google.com/uc?export=download&id={arquivo_id}'
    
    # Baixa o arquivo do Google Drive para a memória do servidor
    resposta = requests.get(url)
    
    # Lê o arquivo Excel a partir da memória, forçando o uso do openpyxl
    df = pd.read_excel(BytesIO(resposta.content), engine='openpyxl')
    
    # Extrai a Câmara, Estante e Caixa do texto (ex: B[53][12])
    df[['Câmara', 'Estante', 'Caixa']] = df['Endereço'].str.extract(r'([A-Z])\[(\d+)\]\[(\d+)\]')
    df['Estante'] = df['Estante'].astype(int)
    df['Caixa'] = df['Caixa'].astype(int)
    
    return df

df = carregar_dados()

# ... (Todo o resto do código para baixo continua EXATAMENTE igual) ...



# 2. Função modular para desenhar UM mapa de uma estante específica
def desenhar_mapa(df_completo, camara, estante):
    df_filtrado = df_completo[(df_completo['Câmara'] == camara) & (df_completo['Estante'] == estante)]

    grade = [{'Caixa': i, 'Linha': (i - 1) // 7 + 1, 'Coluna': (i - 1) % 7 + 1} for i in range(1, 36)]
    df_plot = pd.merge(pd.DataFrame(grade), df_filtrado, on='Caixa', how='left')
    df_plot['Gênero'] = df_plot['Gênero'].fillna('Vazia')

    fig = px.scatter(
        df_plot, x="Coluna", y="Linha", color="Gênero", text="Caixa",
        hover_name="Gênero", hover_data={"Coluna": False, "Linha": False, "Caixa": True},
        title=f"Câmara {camara} | Estante {estante:02d}", height=400
    )

    fig.update_traces(marker=dict(size=45, symbol="square"), textfont=dict(color="white", size=12))
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False, autorange="reversed"),
        plot_bgcolor="white", margin=dict(t=40, b=0, l=0, r=0)
    )
    return fig


# 3. Barra Lateral: Filtros e Modos de Uso
st.sidebar.header("Navegação")
modo = st.sidebar.radio("Como você quer pesquisar?", ["Navegar por Câmaras", "Buscar por Gênero"])

st.write("---")

# MODO 1: Navegação Livre
if modo == "Navegar por Câmaras":
    camara_selecionada = st.sidebar.selectbox("Selecione a Câmara", sorted(df['Câmara'].dropna().unique()))
    estantes_disponiveis = sorted(df[df['Câmara'] == camara_selecionada]['Estante'].dropna().unique())
    estante_selecionada = st.sidebar.selectbox("Selecione a Estante", estantes_disponiveis)

    figura = desenhar_mapa(df, camara_selecionada, estante_selecionada)
    st.plotly_chart(figura, use_container_width=True)

# MODO 2: Busca por Gênero
else:
    generos_disponiveis = sorted(df['Gênero'].dropna().unique())
    genero_selecionado = st.sidebar.selectbox("Qual Gênero deseja localizar?", generos_disponiveis)

    # Encontra todas as combinações únicas de Câmara e Estante onde esse Gênero existe
    locais_encontrados = df[df['Gênero'] == genero_selecionado][['Câmara', 'Estante']].drop_duplicates()
    locais_encontrados = locais_encontrados.sort_values(by=['Câmara', 'Estante'])

    st.subheader(f"🔎 O gênero **{genero_selecionado}** está presente em {len(locais_encontrados)} estante(s):")

    # Cria uma visualização em 2 colunas para exibir múltiplos mapas lado a lado
    colunas = st.columns(2)

    for indice, (_, linha_dados) in enumerate(locais_encontrados.iterrows()):
        cam = linha_dados['Câmara']
        est = linha_dados['Estante']
        figura = desenhar_mapa(df, cam, est)

        # Coloca o gráfico na coluna correspondente (par ou ímpar)
        colunas[indice % 2].plotly_chart(figura, use_container_width=True)
