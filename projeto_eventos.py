import streamlit as st
import pandas as pd
from st_rsuite import date_picker
import datetime
from bson import ObjectId
import time


from funcoes_auxiliares import (
    conectar_mongo_cepf_gestao,
    sidebar_projeto,
)


st.set_page_config(page_title="Eventos", page_icon=":material/event:")




# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()



###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Coleção de projetos
col_projetos = db["projetos"]




###########################################################################################################
# CARREGAMENTO DE DADOS
###########################################################################################################


# Capturando o código do projeto e os dados do projeto
codigo_projeto_atual = st.session_state.get("projeto_atual")


df_projeto = pd.DataFrame(
    list(
        col_projetos.find(
            {"codigo": codigo_projeto_atual}
        )
    )
)


projeto = col_projetos.find_one(
    {"codigo": codigo_projeto_atual},
    {
        "codigo": 1,
        "sigla": 1,
        "locais": 1,
        "eventos": 1
    }
) or {}







###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')

# Título da página e identificação
col_titulo, col_identificacao = st.columns([3, 2])

with col_titulo:
    st.header("Eventos")

with col_identificacao:
    st.markdown(
        f"<div style='text-align: right; margin-top: 30px;'>{df_projeto['codigo'].values[0]} - {df_projeto['sigla'].values[0]}</div>",
        unsafe_allow_html=True
    )


st.write('')




aba_calendario, aba_eventos = st.tabs(
    ["Agenda", "Divulgar eventos"]
)




with aba_calendario:

    st.write('')

    st.subheader("Agenda de eventos do edital")




with aba_eventos:

    st.write("")

    ###################################################################################################
    # LAYOUT DA ABA
    ###################################################################################################

    col_formulario, col_lista = st.columns(2, gap="large")



    ###################################################################################################
    # FORMULÁRIO DE CADASTRO
    ###################################################################################################

    with col_formulario:

        st.subheader("Divulgar evento")

        with st.form("form_cadastro_evento", border=False, clear_on_submit=True):

            nome_evento = st.text_input(
                "Nome do evento: *"
            )

            descricao_evento = st.text_area(
                "Descrição do evento: *",
                max_chars=800,
                height=180
            )

            col_data_inicio, col_data_fim = st.columns(2)

            with col_data_inicio:

                data_inicio = date_picker(
                    label="Data de início: *",
                    format="dd/MM/yyyy",
                    locale="pt_BR",
                    one_tap=True,
                    key="evento_data_inicio"
                )

            with col_data_fim:

                data_fim = date_picker(
                    label="Data de fim: *",
                    format="dd/MM/yyyy",
                    locale="pt_BR",
                    one_tap=True,
                    key="evento_data_fim"
                )

            local = st.text_input(
                "Local: *"
            )

            municipio_uf = st.text_input(
                "Município / UF: *"
            )

            links_divulgacao = st.text_area(
                "Links de divulgação (separados por vírgula):",
                height=120
            )

            st.write("")

            salvar_evento = st.form_submit_button(
                "Salvar evento",
                icon=":material/save:",
                type="primary"
            )



            if salvar_evento:

                ###################################################################################################
                # VALIDAÇÃO DOS CAMPOS OBRIGATÓRIOS
                ###################################################################################################

                if (
                    not nome_evento
                    or not descricao_evento
                    or not data_inicio
                    or not data_fim
                    or not local
                    or not municipio_uf
                ):
                    st.error("Todos os campos obrigatórios devem ser preenchidos.")

                elif data_fim < data_inicio:
                    st.error("A data de fim deve ser igual ou posterior à data de início.")

                else:

                    ###################################################################################################
                    # PREPARAÇÃO DOS DADOS DO EVENTO
                    ###################################################################################################

                    data_inicio_dt = datetime.datetime.combine(
                        data_inicio,
                        datetime.datetime.min.time()
                    )

                    data_fim_dt = datetime.datetime.combine(
                        data_fim,
                        datetime.datetime.min.time()
                    )

                    lista_links = [
                        link.strip()
                        for link in links_divulgacao.split(",")
                        if link.strip()
                    ]

                    novo_evento = {
                        "id": str(ObjectId()),
                        "nome_evento": nome_evento,
                        "descricao": descricao_evento,
                        "data_inicio": data_inicio_dt,
                        "data_fim": data_fim_dt,
                        "local": local,
                        "municipio_uf": municipio_uf,
                        "links_divulgacao": lista_links,
                        "registrado_por": st.session_state["id_usuario"],
                        "data_cadastro": datetime.datetime.now()
                    }

                    ###################################################################################################
                    # GRAVAÇÃO DO EVENTO NO PROJETO
                    ###################################################################################################

                    col_projetos.update_one(
                        {"codigo": codigo_projeto_atual},
                        {
                            "$push": {
                                "eventos": novo_evento
                            }
                        }
                    )

                    st.success(
                        "Evento cadastrado com sucesso!",
                        icon=":material/check:"
                    )

                    time.sleep(3)
                    st.rerun()








    ###################################################################################################
    # LISTA DE EVENTOS
    ###################################################################################################

    with col_lista:

        st.subheader("Eventos cadastrados")
        
        st.write('')

        # Obtém a lista de eventos cadastrados no projeto
        eventos = projeto.get("eventos", [])

        # Ordena os eventos pela data de início
        eventos = sorted(
            eventos,
            key=lambda evento: evento.get("data_inicio", datetime.datetime.max)
        )

        if not eventos:

            st.caption("Nenhum evento cadastrado.")

        else:

            for evento in eventos:

                col_nome, col_excluir = st.columns([8, 1])

                col_nome.write(f"**{evento["nome_evento"]}**")

                col_nome.write(f"{evento['data_inicio'].strftime('%d/%m/%Y')} a {evento['data_fim'].strftime('%d/%m/%Y')}")

                col_nome.write(f"{evento['descricao']}")

                # Local e município/uf
                col_nome.write(f"Local: {evento['local']} - {evento['municipio_uf']}")

                # Links de divulgação
                col_nome.write(f"Links de divulgação: {', '.join(evento['links_divulgacao'])}")

                with col_excluir:

                    with st.popover(
                        "",
                        icon=":material/delete:"
                    ):

                        st.write(
                            "Tem certeza que deseja excluir esse evento?"
                        )

                        excluir = st.button(
                            "Sim, excluir",
                            key=f"excluir_evento_{evento['id']}",
                            type="primary",
                            icon=":material/delete:"
                        )


                        if excluir:

                            ###################################################################################################
                            # EXCLUSÃO DO EVENTO
                            ###################################################################################################

                            col_projetos.update_one(
                                {"codigo": codigo_projeto_atual},
                                {
                                    "$pull": {
                                        "eventos": {
                                            "id": evento["id"]
                                        }
                                    }
                                }
                            )

                            st.success(
                                "Evento excluído com sucesso!",
                                icon=":material/check:"
                            )

                            time.sleep(3)
                            st.rerun()

                st.divider()    








