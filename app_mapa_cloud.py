import pandas as pd
import plotly.express as px
import streamlit as st

import streamlit as st
import pandas as pd


@st.cache_data
def carregar_dados_do_drive():
    # Substitua o ID abaixo pelo ID do seu arquivo
    file_id = '1F_FT7Ygixc6ZBAqzZRy3l2iD7tNefFvM'
    url_direta = f'https://drive.google.com/uc?id={file_id}'

    # Se for Excel:
    df = pd.read_excel(url_direta)
    # Se for CSV: df = pd.read_csv(url_direta)

    return df


# No seu código principal, você chama a função:
df_total = carregar_dados_do_drive()

# Configuração da página
st.set_page_config(page_title="Mapa das Câmaras", layout="wide")

st.title("🗄️ Mapa de Ocupação - Câmaras de Sementes")
st.markdown("Faça o upload da sua planilha, escolha a câmara e filtre pelos gêneros desejados.")


@st.cache_data
def carregar_dados(arquivo):
    df = pd.read_excel(arquivo)

    # Extrai Câmara, Estante e Caixa do campo 'Endereço'
    df[['Camara', 'Estante', 'Caixa']] = df['Endereço'].str.extract(r'([A-Z])\[(\d+)\]\[(\d+)\]')
    df['Estante'] = pd.to_numeric(df['Estante'])
    df['Caixa'] = pd.to_numeric(df['Caixa'])

    # Limpa possíveis espaços vazios nos nomes
    if 'Gênero' in df.columns:
        df['Gênero'] = df['Gênero'].astype(str).str.strip()

    return df


arquivo_excel = st.file_uploader("Selecione o arquivo Excel (ex: caixas.xlsx)", type=["xlsx", "xls"])

if arquivo_excel is not None:
    df_completo = carregar_dados(arquivo_excel)

    # --- ORGANIZAÇÃO DOS FILTROS EM DUAS COLUNAS ---
    col1, col2 = st.columns(2)

    with col1:
        camaras_disponiveis = sorted(df_completo['Camara'].dropna().unique())
        camara_selecionada = st.selectbox("1️⃣ Selecione a Câmara:", camaras_disponiveis)

    df_filtrado = df_completo[df_completo['Camara'] == camara_selecionada].copy()

    with col2:
        generos_disponiveis = sorted(df_filtrado['Gênero'].dropna().unique())
        # O multiselect permite escolher nenhum, um ou vários gêneros
        generos_selecionados = st.multiselect(
            "2️⃣ Filtrar por Gênero (deixe em branco para ver TODOS):",
            options=generos_disponiveis
        )

    # --- PROCESSAMENTO DOS DADOS ---
    # Agrupa pacotes que estão na mesma caixa
    df_agrupado = df_filtrado.groupby(['Estante', 'Caixa']).agg({
        'Gênero': lambda x: ', '.join(sorted(set(x))),
        'Endereço': 'count'
    }).rename(columns={'Endereço': 'Qtd_Pacotes'}).reset_index()

    # Cria a malha (grid) completa da câmara
    estantes = list(range(1, 80))
    caixas = list(range(1, 36))
    df_grid = pd.DataFrame([{'Estante': e, 'Caixa': c} for e in estantes for c in caixas])

    # Junta o grid vazio com os dados agrupados
    df_final = pd.merge(df_grid, df_agrupado, on=['Estante', 'Caixa'], how='left')
    df_final['Gênero_Real'] = df_final['Gênero'].fillna('Vazio')
    df_final['Qtd_Pacotes'] = df_final['Qtd_Pacotes'].fillna(0)


    # --- LÓGICA DO FILTRO DE GÊNEROS ---
    def aplicar_filtro(gen_str):
        if gen_str == 'Vazio':
            return 'Vazio'
        if not generos_selecionados:
            return gen_str  # Se não tem filtro, mostra tudo colorido normalmente

        # Se tem filtro, verifica se a caixa contém algum dos gêneros selecionados
        generos_na_caixa = [g.strip() for g in gen_str.split(',')]
        intersecao = [g for g in generos_na_caixa if g in generos_selecionados]

        if intersecao:
            return ', '.join(intersecao)  # Destaca o gênero selecionado
        else:
            return 'Outros (Oculto)'  # Mascara os outros gêneros


    # Aplica a regra de visualização
    df_final['Gênero_Mapa'] = df_final['Gênero_Real'].apply(aplicar_filtro)

    # Cria uma coluna de status só para a contagem final
    df_final['Status'] = df_final['Gênero_Mapa'].apply(
        lambda x: 'Vazio' if x == 'Vazio' else ('Oculto' if x == 'Outros (Oculto)' else 'Destacado')
    )

    # Mapa de cores: define cinza para vazios e ocultos; o resto o Plotly colore sozinho
    cores_fixas = {
        'Vazio': '#E0E0E0',  # Cinza padrão
        'Outros (Oculto)': '#F5F5F5'  # Cinza bem clarinho (quase invisível) para dar destaque à busca
    }

    # --- GERAÇÃO DO MAPA ---
    fig = px.scatter(
        df_final,
        x='Estante',
        y='Caixa',
        color='Gênero_Mapa',
        color_discrete_map=cores_fixas,
        hover_name='Gênero_Real',  # No mouse, sempre mostra o que REALMENTE tem na caixa
        hover_data={
            'Gênero_Mapa': False,
            'Qtd_Pacotes': True,
            'Estante': True,
            'Caixa': True
        },
        height=850
    )

    # Ajustes de visual da grade
    fig.update_traces(marker=dict(size=12, line=dict(width=1, color='lightgrey')))
    fig.update_yaxes(autorange="reversed", tickmode='linear', tick0=1, dtick=2, title="Estantes (1 a 79)")
    fig.update_xaxes(tickmode='linear', tick0=1, dtick=1, title="Caixas (1 a 35)")

    fig.update_layout(
        plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#EFEFEF'),
        yaxis=dict(showgrid=True, gridcolor='#EFEFEF'),
        legend_title="Legenda do Mapa"
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- RESUMO NO FINAL DA PÁGINA ---
    if generos_selecionados:
        caixas_destacadas = (df_final['Status'] == 'Destacado').sum()
        st.success(
            f"🔍 **Resultado da Busca:** Os gêneros selecionados estão presentes em **{caixas_destacadas}** caixas na Câmara {camara_selecionada}.")
    else:
        st.info(
            f"📊 **Resumo da Câmara {camara_selecionada}:** {int(df_final['Qtd_Pacotes'].sum())} pacotes armazenados em {(df_final['Status'] == 'Destacado').sum()} caixas ocupadas.")

else:
    st.info("Aguardando o upload do arquivo para gerar o mapa...")
