import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao, sidebar_projeto  # Função personalizada para conectar ao MongoDB
import pandas as pd
import streamlit_shadcn_ui as ui
import datetime
import time
import bson

###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Define as coleções específicas que serão utilizadas a partir do banco
# col_pessoas = db["pessoas"]

# Projetos
col_projetos = db["projetos"]


###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# TRATAMENTO DE DADOS
###########################################################################################################

# Carregamento do projeto -------------------------------------

# Projetos (somente o projeto atual)
col_projetos = db["projetos"]

codigo_projeto_atual = st.session_state.get("projeto_atual")

st.write(codigo_projeto_atual)

if not codigo_projeto_atual:
    st.error("Nenhum projeto selecionado.")
    st.stop()

df_projeto = pd.DataFrame(
    list(
        col_projetos.find(
            {"codigo": codigo_projeto_atual}
        )
    )
)

if df_projeto.empty:
    st.error("Projeto não encontrado no banco de dados.")
    st.stop()


# Transformar o id em string
df_projeto = df_projeto.copy()

if "_id" in df_projeto.columns:
    df_projeto["_id"] = df_projeto["_id"].astype(str)



###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################

# ???????????????????????
# with st.expander("Colunas do projeto"):
#     st.write(df_projeto.columns)


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')



# Código e sigla do projeto 
st.header(f"{df_projeto['sigla'].values[0]} - {df_projeto['codigo'].values[0]}")

# Edital
st.write(f"Edital: {df_projeto['edital'].values[0]}")

# Organização
st.write(f"Organização: {df_projeto['organizacao'].values[0]}")

# Nome do projeto
st.write(f"Nome: {df_projeto['nome_do_projeto'].values[0]}")

# Objetivo geral
st.write(f"Objetivo geral: {df_projeto['objetivo_geral'].values[0]}")

# Responsável (coordenador)
st.write(f"Responsável: {df_projeto['responsavel'].values[0]}")



st.divider()

st.write('*Bloco do cronograma de parcelas, relatórios e status*')

st.divider()

st.subheader('**Anotações**')


# ============================================================
# ANOTAÇÕES - DIÁLGO DE GERENCIAMENTO
# ============================================================


# Função do diálogo de gerenciar anotações  -------------------------------------
@st.dialog("Gerenciar anotações", width="medium")
def gerenciar_anotacoes():

    nova_tab, editar_tab = st.tabs(["Nova anotação", "Editar anotação"])

    # ========================================================
    # NOVA ANOTAÇÃO
    # ========================================================
    with nova_tab:

        texto_anotacao = st.text_area(
            "Escreva aqui a anotação",
            height=150
        )

        if st.button(
            "Salvar anotação",
            type="primary",
            icon=":material/save:"
        ):

            if not texto_anotacao.strip():
                st.warning("A anotação não pode estar vazia.")
                return

            anotacao = {
                "id": str(bson.ObjectId()),
                "data": datetime.datetime.now().strftime("%d/%m/%Y"),
                "autor": st.session_state.nome,
                "texto": texto_anotacao.strip(),
            }

            resultado = col_projetos.update_one(
                {"codigo": st.session_state.projeto_atual},
                {"$push": {"anotacoes": anotacao}}
            )

            if resultado.modified_count == 1:
                st.success("Anotação salva com sucesso!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Erro ao salvar anotação.")

    # ========================================================
    # EDITAR ANOTAÇÃO
    # ========================================================
    with editar_tab:

        anotacoes_local = (
            df_projeto["anotacoes"].values[0]
            if "anotacoes" in df_projeto.columns
            else []
        )

        # Filtrar somente anotações do usuário logado
        anotacoes_usuario = [
            a for a in anotacoes_local
            if a.get("autor") == st.session_state.nome
        ]

        if not anotacoes_usuario:
            st.write("Não há anotações de sua autoria para editar.")
            return

        # Selectbox amigável
        mapa_anotacoes = {
            f"{a['data']} — {a['texto'][:60]}": a
            for a in anotacoes_usuario
        }

        anotacao_label = st.selectbox(
            "Selecione a anotação",
            list(mapa_anotacoes.keys())
        )

        anotacao_selecionada = mapa_anotacoes[anotacao_label]

        novo_texto = st.text_area(
            "Editar anotação",
            value=anotacao_selecionada["texto"],
            height=150
        )

        if st.button(
            "Salvar alterações",
            type="primary",
            icon=":material/save:"
        ):

            if not novo_texto.strip():
                st.warning("A anotação não pode ficar vazia.")
                return

            resultado = col_projetos.update_one(
                {
                    "codigo": st.session_state.projeto_atual,
                    "anotacoes.id": anotacao_selecionada["id"],
                },
                {
                    "$set": {
                        "anotacoes.$.texto": novo_texto.strip()
                    }
                }
            )

            if resultado.modified_count == 1:
                st.success("Anotação atualizada com sucesso!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Erro ao atualizar anotação.")



with st.container(horizontal=True, horizontal_alignment="right"):
    if st.button(
        "Gerenciar anotações",
        icon=":material/notes:",
        type="secondary"
    ):
        gerenciar_anotacoes()



# ============================================================
# ANOTAÇÕES - LISTAGEM
# ============================================================


anotacoes = (
    df_projeto["anotacoes"].values[0]
    if "anotacoes" in df_projeto.columns and df_projeto["anotacoes"].values[0]
    else []
)

if not anotacoes:
    st.write("Não há anotações")
else:
    df_anotacoes = pd.DataFrame(anotacoes)
    df_anotacoes = df_anotacoes[["data", "texto", "autor"]]
    ui.table(data=df_anotacoes)


st.write('')
st.write('')


# Visitas 
st.subheader('**Visitas**')

# ============================================================
# VISITAS - DIÁLGO DE GERENCIAMENTO
# ============================================================

@st.dialog("Gerenciar visitas", width="medium")
def gerenciar_visitas():

    nova_tab, editar_tab = st.tabs(["Nova visita", "Editar visita"])

    # ========================================================
    # NOVA VISITA
    # ========================================================
    with nova_tab:

        data_visita = st.text_input(
            "Data da visita",
        )

        relato_visita = st.text_area(
            "Breve relato",
            height=150
        )

        if st.button(
            "Salvar visita",
            type="primary",
            icon=":material/save:"
        ):

            if not data_visita.strip() or not relato_visita.strip():
                st.warning("Preencha a data da visita e o relato.")
                return

            visita = {
                "id": str(bson.ObjectId()),
                "data_visita": data_visita.strip(),
                "relato": relato_visita.strip(),
                "autor": st.session_state.nome,
            }

            resultado = col_projetos.update_one(
                {"codigo": st.session_state.projeto_atual},
                {"$push": {"visitas": visita}}
            )

            if resultado.modified_count == 1:
                st.success("Visita registrada com sucesso!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Erro ao salvar visita.")

    # ========================================================
    # EDITAR VISITA
    # ========================================================
    with editar_tab:

        visitas_local = (
            df_projeto["visitas"].values[0]
            if "visitas" in df_projeto.columns
            else []
        )

        visitas_usuario = [
            v for v in visitas_local
            if v.get("autor") == st.session_state.nome
        ]

        if not visitas_usuario:
            st.write("Não há visitas de sua autoria para editar.")
            return

        mapa_visitas = {
            f"{v['data_visita']} — {v['relato'][:60]}": v
            for v in visitas_usuario
        }

        visita_label = st.selectbox(
            "Selecione a visita",
            list(mapa_visitas.keys())
        )

        visita_selecionada = mapa_visitas[visita_label]

        nova_data = st.text_input(
            "Data da visita (DD/MM/AAAA)",
            value=visita_selecionada["data_visita"]
        )

        novo_relato = st.text_area(
            "Editar breve relato",
            value=visita_selecionada["relato"],
            height=150
        )

        if st.button(
            "Salvar alterações",
            type="primary",
            icon=":material/save:"
        ):

            if not nova_data.strip() or not novo_relato.strip():
                st.warning("A data e o relato não podem ficar vazios.")
                return

            resultado = col_projetos.update_one(
                {
                    "codigo": st.session_state.projeto_atual,
                    "visitas.id": visita_selecionada["id"],
                },
                {
                    "$set": {
                        "visitas.$.data_visita": nova_data.strip(),
                        "visitas.$.relato": novo_relato.strip(),
                    }
                }
            )

            if resultado.modified_count == 1:
                st.success("Visita atualizada com sucesso!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Erro ao atualizar visita.")


# Botão para abrir o dialogo de gerenciar visitas

with st.container(horizontal=True, horizontal_alignment="right"):
    if st.button(
        "Gerenciar visitas",
        icon=":material/location_on:",
        type="secondary"
    ):
        gerenciar_visitas()



# ============================================================
# VISITAS — LISTAGEM
# ============================================================

visitas = (
    df_projeto["visitas"].values[0]
    if "visitas" in df_projeto.columns and df_projeto["visitas"].values[0]
    else []
)

if not visitas:
    st.write("Não há visitas registradas")
else:
    df_visitas = pd.DataFrame(visitas)
    df_visitas = df_visitas[["data_visita", "relato", "autor"]]
    ui.table(data=df_visitas)










# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()

