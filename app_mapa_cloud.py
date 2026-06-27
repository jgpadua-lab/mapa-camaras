import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Mapa de Câmaras Frias", layout="wide")
st.title("🧊 Mapeamento das Câmaras Frias")


# --- 1. BUSCA DOS DADOS NO GOOGLE DRIVE ---
# O @st.cache_data faz com que o app não baixe o arquivo toda vez que você clicar em algo.
@st.cache_data(ttl=600)  # Atualiza o cache a cada 10 minutos (600 segundos) se houver mudança
def carregar_dados():
    # Cole APENAS o ID do arquivo do Google Drive aqui
    # Exemplo: se o link é drive.google.com/file/d/1ABCDEFG/view, o ID é 1ABCDEFG
    file_id = '1F_FT7Ygixc6ZBAqzZRy3l2iD7tNefFvM'
    url = f'https://drive.google.com/uc?id={file_id}'

    # Se o seu arquivo for CSV, troque read_excel por read_csv
    df = pd.read_excel(url)
    return df


# Carrega os dados
try:
    df_total = carregar_dados()
except Exception as e:
    st.error(
        f"Erro ao carregar os dados do Google Drive. Verifique o ID do arquivo e se o link está como 'Qualquer pessoa com o link'. Erro: {e}")
    st.stop()

# --- DEFINIÇÃO DE CORES (Ajuste conforme suas necessidades) ---
# Aqui mantemos a fidelidade ao seu código original que usava um color_discrete_map
cores_fixas = {
    'Phaseolus': '#1f77b4',  # Azul
    'Glycine': '#2ca02c',  # Verde
    'Zea': '#ff7f0e',  # Laranja
    'Vazio': '#d3d3d3',  # Cinza claro para espaços vazios
    'Outros': '#9467bd'  # Roxo
    # Adicione os outros gêneros aqui...
}

# --- 2. SELEÇÃO DO GÊNERO ---
st.markdown("### 🔍 Busca de Gênero")

# Pegar a lista de gêneros únicos e ordenar em ordem alfabética
lista_generos = sorted(df_total['Gênero_Real'].dropna().unique())

# Caixa de seleção
genero_selecionado = st.selectbox(
    'Selecione o Gênero que deseja localizar:',
    options=lista_generos
)

# --- 3. LÓGICA DE LOCALIZAÇÃO E GERAÇÃO DO MAPA ---
if genero_selecionado:
    # Filtra onde o gênero está
    df_genero = df_total[df_total['Gênero_Real'] == genero_selecionado]

    # Descobre em quais câmaras ele aparece
    camaras_encontradas = df_genero['Câmara'].unique()

    st.success(
        f"✅ O gênero **{genero_selecionado}** foi encontrado em {len(camaras_encontradas)} câmara(s): **{', '.join(map(str, camaras_encontradas))}**.")

    # Mostra um resumo rápido (Tabela) de onde exatamente estão as caixas
    st.markdown("#### Posições exatas:")
    st.dataframe(df_genero[['Câmara', 'Estante', 'Caixa', 'Qtd_Pacotes']], hide_index=True)

    st.markdown("---")

    # Para cada câmara encontrada, gera o mapa completo da câmara
    for camara in camaras_encontradas:
        st.subheader(f"📍 Mapa Completo - Câmara: {camara}")

        # Filtra os dados de TODA a câmara para desenhar o mapa completo
        df_camara_atual = df_total[df_total['Câmara'] == camara]

        # --- GERAÇÃO DO MAPA (Mantendo total fidelidade) ---
        fig = px.scatter(
            df_camara_atual,
            x='Estante',  # Estantes na horizontal (Eixo X)
            y='Caixa',  # Caixas na vertical (Eixo Y)
            color='Gênero_Mapa',
            color_discrete_map=cores_fixas,
            hover_name='Gênero_Real',  # No mouse, mostra o que REALMENTE tem na caixa
            hover_data={
                'Gênero_Mapa': False,
                'Qtd_Pacotes': True,
                'Estante': True,
                'Caixa': True
            },
            height=850
        )

        # Opcional: Inverte o eixo Y para a Caixa 1 ficar na base ou no topo (descomente se precisar)
        # fig.update_yaxes(autorange="reversed")

        # Opcional: Ajusta os eixos para ficarem com visualização apenas de números inteiros
        fig.update_xaxes(dtick=1)
        fig.update_yaxes(dtick=1)

        # Exibe o gráfico
        st.plotly_chart(fig, use_container_width=True)
