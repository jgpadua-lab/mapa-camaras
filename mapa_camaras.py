import pandas as pd
import plotly.express as px
import streamlit as st
import requests
from io import BytesIO
import itertools

# ----------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA
# ----------------------------------------------------
st.set_page_config(page_title="Mapa Panorâmico de Sementes", layout="wide", page_icon="🌱")
st.title("🌱 Visão Panorâmica da Câmara Fria")
st.markdown("Visualize todas as estantes e caixas de uma câmara simultaneamente.")

# ----------------------------------------------------
# 2. CARREGAMENTO E LIMPEZA DOS DADOS
# ----------------------------------------------------
@st.cache_data(ttl=600)
def carregar_dados():
    # COLOQUE O SEU ID DO GOOGLE DRIVE AQUI
    arquivo_id = '1Z3obclZKYbSU1rydyG7nmaiRY_qL8v0G7a3Dm_L2Cx8' 
    url = f'https://docs.google.com/spreadsheets/d/{arquivo_id}/export?format=xlsx'
    
    resposta = requests.get(url)
    if resposta.status_code != 200 or b'html' in resposta.content[:100].lower():
        st.error("🚨 O Google Drive não liberou o download. Verifique o compartilhamento do link.")
        st.stop()
        
    df = pd.read_excel(BytesIO(resposta.content), engine='openpyxl')
    
    # Tratamento contra erros de digitação no cabeçalho
    df.columns = df.columns.str.strip()
    if 'Endereco' in df.columns:
        df = df.rename(columns={'Endereco': 'Endereço'})
        
    if 'Endereço' not in df.columns:
        st.error(f"🚨 Coluna 'Endereço' não encontrada! Encontradas: {list(df.columns)}")
        st.stop()
    
    # Extração das posições
    df = df.dropna(subset=['Endereço'])
    df[['Câmara', 'Estante', 'Caixa']] = df['Endereço'].str.extract(r'([A-Z])\[(\d+)\]\[(\d+)\]')
    
    df = df.dropna(subset=['Câmara', 'Estante', 'Caixa'])
    df['Estante'] = df['Estante'].astype(int)
    df['Caixa'] = df['Caixa'].astype(int)
    
    return df

try:
    df_dados = carregar_dados()
except Exception as e:
    st.error(f"Erro ao processar os dados: {e}")
    st.stop()

# ----------------------------------------------------
# 3. INTERFACE LATERAL (FILTROS)
# ----------------------------------------------------
st.sidebar.header("📍 Navegação")

camaras_disponiveis = sorted(df_dados['Câmara'].unique())
camara_selecionada = st.sidebar.selectbox("Selecione a Câmara", camaras_disponiveis)

# Filtra apenas pela Câmara
df_filtrado = df_dados[df_dados['Câmara'] == camara_selecionada]

# ----------------------------------------------------
# 4. CRIANDO O MOLDE PANORÂMICO (2.765 posições)
# ----------------------------------------------------
# Descobre a quantidade máxima de estantes (pelo menos 79)
max_estantes = max(79, df_filtrado['Estante'].max() if not df_filtrado.empty else 79)

# Cria todas as combinações possíveis: (Estante 1, Caixa 1), (Estante 1, Caixa 2)...
combinacoes = list(itertools.product(range(1, max_estantes + 1), range(1, 36)))
df_grid = pd.DataFrame(combinacoes, columns=['Estante', 'Caixa'])

# Junta o molde com os dados reais
df_plot = pd.merge(df_grid, df_filtrado[['Estante', 'Caixa', 'Gênero']], on=['Estante', 'Caixa'], how='left')

# Preenche os vazios
df_plot['Gênero'] = df_plot['Gênero'].fillna('Vazio (Livre)')

# Inverte o eixo Y matematicamente para a Caixa 1 ficar no topo do gráfico
df_plot['Posição (Y)'] = 36 - df_plot['Caixa']

# Cria a string do endereço completo para aparecer no mouse
df_plot['Endereço Completo'] = f"{camara_selecionada}[" + df_plot['Estante'].apply(lambda x: f"{x:02d}") + "][" + df_plot['Caixa'].apply(lambda x: f"{x:02d}") + "]"

# ----------------------------------------------------
# 5. DESENHANDO O GRÁFICO PANORÂMICO
# ----------------------------------------------------
st.subheader(f"🏢 Visão Geral — Câmara {camara_selecionada}")

ocupadas = df_plot[df_plot['Gênero'] != 'Vazio (Livre)'].shape[0]
total = len(df_plot)
st.markdown(f"**Ocupação Geral da Câmara:** {ocupadas} caixas em uso de um total de {total} posições.")

# Definir cor de fundo para o que é vazio
mapa_de_cores = {'Vazio (Livre)': '#e8e8e8'}

fig = px.scatter(
    df_plot,
    x="Estante",
    y="Posição (Y)",
    color="Gênero",
    hover_name="Gênero",
    hover_data={"Estante": False, "Posição (Y)": False, "Endereço Completo": True, "Caixa": False},
    color_discrete_map=mapa_de_cores,
    height=750 # Gráfico um pouco mais alto para comportar 35 caixas
)

# Configurando os quadradinhos menores (pois são muitas estantes)
fig.update_traces(marker=dict(symbol='square', size=13, line=dict(width=0.5, color='gray')))

# Arrumando os textos dos eixos para ficarem bonitos
valores_eixo_y = [36 - i for i in range(1, 36)]
textos_eixo_y = [str(i) for i in range(1, 36)]

fig.update_layout(
    xaxis=dict(
        title="<b>Número da Estante ➡️</b>", 
        tickmode='linear', dtick=2, # Mostra os números das estantes de 2 em 2 para não amontoar
        showgrid=False
    ),
    yaxis=dict(
        title="<b>⬅️ Número da Caixa</b>", 
        tickmode='array', tickvals=valores_eixo_y, ticktext=textos_eixo_y, # Garante que a 1 fique em cima e 35 embaixo
        showgrid=False
    ),
    plot_bgcolor='white',
    legend_title_text='Gêneros',
    margin=dict(l=20, r=20, t=30, b=20)
)

st.plotly_chart(fig, use_container_width=True)
