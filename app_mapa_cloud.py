import streamlit as st
import pandas as pd

# Configuração da página (opcional, deixa o app mais bonito)
st.set_page_config(page_title="Mapa - Câmaras Frias", layout="wide")

st.title("📍 Localizações das Câmaras Frias")


# Função com cache para não carregar a planilha toda vez que você clicar em algo
@st.cache_data(ttl=600)
def carregar_dados_do_drive():
    # ⚠️ IMPORTANTE: Cole abaixo o link gerado no Google Sheets em:
    # Arquivo > Compartilhar > Publicar na Web > (Formato: Valores separados por vírgula .csv)
    url_publicada = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9yUsZCE-m2L-WnW10OEEdYcrCYWhWxwcyb25dK4BnKqD8rvfIsOeOn4a5tEnLdw/pub?output=csv"

    try:
        # Usa read_csv em vez de read_excel para não ser bloqueado pelo Google
        df = pd.read_csv(url_publicada)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")
        # Retorna um DataFrame vazio se der erro, para o app não quebrar
        return pd.DataFrame()


# Executa a função
df_total = carregar_dados_do_drive()

# Verifica se a tabela carregou corretamente
if not df_total.empty:
    st.success("✅ Dados carregados com sucesso da nuvem!")

    # Cria uma aba expansível para você visualizar os dados da planilha
    with st.expander("📊 Ver dados da planilha"):
        st.dataframe(df_total)

    st.subheader("Mapa das Câmaras")

    # O st.map precisa que as colunas de coordenadas se chamem:
    # 'lat' ou 'latitude' E 'lon' ou 'longitude'
    try:
        st.map(df_total)
    except Exception as e:
        st.warning(
            "⚠️ O Streamlit não encontrou as colunas de coordenadas. Certifique-se de que sua planilha possui colunas com os nomes 'lat' (ou 'latitude') e 'lon' (ou 'longitude').")

else:
    st.warning("Nenhum dado foi carregado. Verifique se o link da URL está correto e se foi publicado em formato CSV.")
