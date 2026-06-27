import pandas as pd
import plotly.express as px
import streamlit as st
import requests
from io import BytesIO

# ----------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA
# ----------------------------------------------------
st.set_page_config(page_title="Mapa de Sementes", layout="wide", page_icon="🌱")
st.title("🌱 Mapa de Câmaras Frias - Sementes")
st.markdown("Visualize as caixas ocupadas e livres em cada estante, no estilo 'mapa de assentos'.")


# ----------------------------------------------------
# 2. CARREGAMENTO E LIMPEZA DOS DADOS
# ----------------------------------------------------
@st.cache_data(ttl=600)
def carregar_dados():
    # COLOQUE O SEU ID DO GOOGLE DRIVE AQUI
    arquivo_id = 'SEU_ID_AQUI'
    url = f'https://docs.google.com/spreadsheets/d/{arquivo_id}/export?format=xlsx'

    resposta = requests.get(url)
    if resposta.status_code != 200 or b'html' in resposta.content[:100].lower():
        st.error(
            "🚨 O Google Drive não liberou o download. Verifique se o arquivo está como 'Qualquer pessoa com o link'.")
        st.stop()

    df = pd.read_excel(BytesIO(resposta.content), engine='openpyxl')

    # Remove linhas vazias e extrai as informações do Endereço (ex: B[53][12])
    df = df.dropna(subset=['Endereço'])
    df[['Câmara', 'Estante', 'Caixa']] = df['Endereço'].str.extract(r'([A-Z])\[(\d+)\]\[(\d+)\]')

    # Remove linhas que não seguiram o padrão e converte para número
    df = df.dropna(subset=['Câmara', 'Estante', 'Caixa'])
    df['Estante'] = df['Estante'].astype(int)
    df['Caixa'] = df['Caixa'].astype(int)

    return df


# Tenta carregar os dados
try:
    df_dados = carregar_dados()
except Exception as e:
    st.error(f"Erro ao processar os dados: {e}")
    st.stop()

# ----------------------------------------------------
# 3. INTERFACE LATERAL (FILTROS)
# ----------------------------------------------------
st.sidebar.header("📍 Navegação")

# Seleção da Câmara (Descobre as câmaras que existem no arquivo)
camaras_disponiveis = sorted(df_dados['Câmara'].unique())
camara_selecionada = st.sidebar.selectbox("1. Selecione a Câmara", camaras_disponiveis)

# Seleção da Estante (1 a 79 conforme sua regra)
estante_selecionada = st.sidebar.selectbox("2. Selecione a Estante", list(range(1, 80)))

# Filtra os dados reais para a câmera e estante escolhidas
df_filtrado = df_dados[(df_dados['Câmara'] == camara_selecionada) & (df_dados['Estante'] == estante_selecionada)]

# ----------------------------------------------------
# 4. CRIANDO O "MAPA DE ASSENTOS" (Geração das 35 caixas)
# ----------------------------------------------------
# Cria um "molde" perfeito com 35 caixas, independente de estarem cheias ou não
df_grid = pd.DataFrame({'Caixa': range(1, 36)})

# Junta o molde com os dados reais
# Onde não tiver dado, vai ficar com valores vazios (NaN)
df_plot = pd.merge(df_grid, df_filtrado[['Caixa', 'Gênero']], on='Caixa', how='left')

# Preenche o Gênero das caixas vazias com a palavra "Livre"
df_plot['Gênero'] = df_plot['Gênero'].fillna('Vazio (Livre)')

# Lógica para desenhar o Grid de Caixas (5 colunas x 7 linhas)
# Calculamos coordenadas X e Y para o gráfico
df_plot['Coluna (X)'] = (df_plot['Caixa'] - 1) % 5
df_plot['Linha (Y)'] = (df_plot['Caixa'] - 1) // 5

# Invertemos a linha Y para a Caixa 1 começar no topo do gráfico
df_plot['Linha (Y)'] = df_plot['Linha (Y)'].max() - df_plot['Linha (Y)']

# Criação do Endereço Completo para o tooltip (quadradinho que aparece ao passar o mouse)
df_plot['Endereço Completo'] = f"{camara_selecionada}[{estante_selecionada:02d}][" + df_plot['Caixa'].apply(
    lambda x: f"{x:02d}") + "]"

# ----------------------------------------------------
# 5. DESENHANDO O GRÁFICO PLOTLY
# ----------------------------------------------------
st.subheader(f"📦 Visão da Câmara {camara_selecionada} — Estante {estante_selecionada:02d}")

# Calculando estatísticas para o resumo
caixas_ocupadas = df_plot[df_plot['Gênero'] != 'Vazio (Livre)'].shape[0]
st.write(f"**Ocupação:** {caixas_ocupadas}/35 caixas utilizadas.")

# Define que a cor "Vazio (Livre)" será sempre um cinza clarinho
mapa_de_cores = {'Vazio (Livre)': '#e0e0e0'}

fig = px.scatter(
    df_plot,
    x="Coluna (X)",
    y="Linha (Y)",
    color="Gênero",
    text="Caixa",
    hover_name="Gênero",
    hover_data={"Coluna (X)": False, "Linha (Y)": False, "Endereço Completo": True},
    color_discrete_map=mapa_de_cores,
    height=600
)

# Estilizando o gráfico para parecer com caixas físicas
fig.update_traces(
    marker=dict(symbol='square', size=65, line=dict(width=1, color='DarkSlateGrey')),
    textfont=dict(color='black', size=16, family="Arial Black")
)

# Escondendo as linhas de grade para ficar um visual limpo
fig.update_layout(
    xaxis=dict(showgrid=False, zeroline=False, visible=False),
    yaxis=dict(showgrid=False, zeroline=False, visible=False),
    plot_bgcolor='white',
    legend_title_text='Legenda de Gêneros'
)

# Renderiza o gráfico na tela
st.plotly_chart(fig, use_container_width=True)
