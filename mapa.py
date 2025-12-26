import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Coleção de pessoas
# col_pessoas = db["pessoas"]

# Coleção de projetos
col_projetos = db["projetos"]
df_projetos = pd.DataFrame(list(col_projetos.find()))

# Coleção de editais
col_editais = db["editais"]
df_editais = pd.DataFrame(list(col_editais.find()))



###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Mapa de projetos")

st.write('')



# ============================================
# FILTRO DE EDITAL
# ============================================


lista_editais = ["Todos"] + df_editais['codigo_edital'].tolist()
edital_selecionado = st.selectbox("Selecione o edital", lista_editais, width=300)

st.write('')

if edital_selecionado == "Todos":
    st.markdown("##### Todos os editais")
else:
    nome_edital = df_editais.loc[
        df_editais["codigo_edital"] == edital_selecionado,
        "nome_edital"
    ].values[0]

    st.markdown(f"##### {edital_selecionado} - {nome_edital}")


df_filtrado = df_projetos.copy()


if edital_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["edital"] == edital_selecionado]

# Se não há projetos no edital
if df_filtrado.empty:
    st.divider()
    st.warning("Nenhum projeto encontrado.")
    st.stop()






st.write('')

# ============================================================
# MAPA DOS PROJETOS
# ============================================================


pontos_mapa = []

# Coleta os dados
for _, projeto in df_projetos.iterrows():

    locais = projeto.get("locais", {})
    localidades = locais.get("localidades", [])

    for local in localidades:
        lat = local.get("latitude")
        lon = local.get("longitude")

        if lat is None or lon is None:
            continue

        pontos_mapa.append({
            "codigo": projeto.get("codigo"),
            "sigla": projeto.get("sigla"),
            "nome_projeto": projeto.get("nome_do_projeto"),
            "organizacao": projeto.get("organizacao"),  # 👈 NOVO
            "municipio": local.get("municipio"),
            "localidade": local.get("nome_localidade"),
            "latitude": lat,
            "longitude": lon
        })


# Caso não existam pontos
if not pontos_mapa:
    st.info("Nenhuma localidade com coordenadas cadastradas.")
else:
    df_mapa = pd.DataFrame(pontos_mapa)

    # Centraliza o mapa
    centro_lat = df_mapa["latitude"].mean()
    centro_lon = df_mapa["longitude"].mean()

    mapa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=4,
        tiles="OpenStreetMap"
    )

    # Adiciona marcadores
    for _, row in df_mapa.iterrows():

        popup_html = f"""
        <div style="width:300px">
            <b>Organização:</b> {row['organizacao']}<br>
            <b>Sigla:</b> {row['sigla']}<br>
            <b>Código:</b> {row['codigo']}<br>
            <b>Projeto:</b> {row['nome_projeto']}<br>
            <b>Município:</b> {row['municipio']}<br>
            <b>Localidade:</b> {row['localidade']}
        </div>
        """


        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup_html, max_width=500),
            icon=folium.Icon(
                color="red",
                prefix="fa"  # FontAwesome
            ),
        ).add_to(mapa)

    # Renderiza ocupando 100% da largura
    st_folium(mapa, width="100%", height=600)
