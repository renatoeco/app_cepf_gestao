import streamlit as st
import pandas as pd
from st_rsuite import date_picker
import datetime
from bson import ObjectId
import time
from streamlit_calendar import calendar
import streamlit_antd_components as sac


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

# Coleção de organizações
col_organizacoes = db["organizacoes"]




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



###################################################################################################
# CARREGA TODOS OS PROJETOS DO EDITAL
###################################################################################################

codigo_edital = df_projeto["edital"].iloc[0]
projetos_edital = list(
    col_projetos.find(
        {
            "edital": codigo_edital
        },
        {
            "codigo": 1,
            "sigla": 1,
            "id_organizacao": 1,
            "eventos": 1
        }
    )
)


###################################################################################################
# CARREGA AS ORGANIZAÇÕES
###################################################################################################

organizacoes = {
    organizacao["_id"]: organizacao["nome_organizacao"]
    for organizacao in col_organizacoes.find(
        {},
        {
            "nome_organizacao": 1
        }
    )
}


###################################################################################################
# CARREGA O EDITAL DO PROJETO
###################################################################################################

edital = db.editais.find_one(
    {
        "codigo_edital": codigo_edital
    },
    {
        "codigo_edital": 1,
        "eventos_ieb": 1
    }
) or {}



###########################################################################################################
# FUNÇÕES
###########################################################################################################

# Função para montar os eventos do calendário
def montar_eventos_calendario():

    eventos_calendario = []

    for projeto in projetos_edital:

        codigo_projeto = projeto.get("codigo")
        sigla = projeto.get("sigla", codigo_projeto)


        id_organizacao = projeto.get("id_organizacao")

        nome_organizacao = organizacoes.get(
            id_organizacao,
            ""
        )

        ###################################################################################################
        # DEFINE A COR DO EVENTO
        ###################################################################################################

        cor = (
            cor_meu_projeto
            if codigo_projeto == codigo_projeto_atual
            else cor_demais_projetos
        )

        for evento in projeto.get("eventos", []):

            data_inicio = evento.get("data_inicio")
            data_fim = evento.get("data_fim")

            if not data_inicio or not data_fim:
                continue

            eventos_calendario.append({

                "id": evento["id"],

                "title": f"{sigla} - {evento['nome_evento']}",

                "start": data_inicio.date().isoformat(),

                # FullCalendar utiliza data final exclusiva
                "end": (
                    data_fim + datetime.timedelta(days=1)
                ).date().isoformat(),

                "allDay": True,

                "backgroundColor": cor,
                "borderColor": cor,

                "extendedProps": {

                    "codigo_projeto": codigo_projeto,
                    "sigla": sigla,

                    "organizacao": nome_organizacao,

                    "nome_evento": evento.get("nome_evento"),
                    "descricao": evento.get("descricao"),

                    "data_inicio": data_inicio.strftime("%d/%m/%Y"),
                    "data_fim": data_fim.strftime("%d/%m/%Y"),

                    "local": evento.get("local"),
                    "municipio_uf": evento.get("municipio_uf"),

                    "links_divulgacao": evento.get("links_divulgacao", []),

                    "data_cadastro": evento.get("data_cadastro").strftime("%d/%m/%Y %H:%M")
                    if evento.get("data_cadastro")
                    else ""
                }

            })


    ###################################################################################################
    # EVENTOS DO IEB
    ###################################################################################################

    for evento in edital.get(
        "eventos_ieb",
        []
    ):

        data_inicio = evento.get(
            "data_inicio"
        )

        data_fim = evento.get(
            "data_fim"
        )

        if not data_inicio or not data_fim:
            continue

        eventos_calendario.append({

            "id": evento["id"],

            "title": evento["nome_evento"],

            "start": data_inicio.date().isoformat(),

            "end": (
                data_fim +
                datetime.timedelta(days=1)
            ).date().isoformat(),

            "allDay": True,

            "backgroundColor": cor_evento_ieb,

            "borderColor": cor_evento_ieb,

            "extendedProps": {

                "sigla": "IEB",

                "organizacao": "Instituto Internacional de Educação do Brasil",

                "nome_evento": evento["nome_evento"],

                "descricao": evento["descricao"],

                "data_inicio": data_inicio.strftime(
                    "%d/%m/%Y"
                ),

                "data_fim": data_fim.strftime(
                    "%d/%m/%Y"
                ),

                "local": evento["local"],

                "municipio_uf": evento["municipio_uf"],

                "links_divulgacao": evento.get(
                    "links_divulgacao",
                    []
                ),

                "data_cadastro": (
                    evento["data_cadastro"].strftime(
                        "%d/%m/%Y %H:%M"
                    )
                    if evento.get("data_cadastro")
                    else ""
                )

            }

        })


    return eventos_calendario






###################################################################################################
# DIÁLOGO DE DETALHES DO EVENTO
###################################################################################################

@st.dialog("Detalhes do evento", width="large")
def dialog_evento(evento):

    props = evento["extendedProps"]

    st.subheader(props["nome_evento"])

    

    ###################################################################################################
    # INFORMAÇÕES DO PROJETO
    ###################################################################################################

    if props.get("codigo_projeto"):

        col1, col2 = st.columns(2)

        col1.write(
            f"**Projeto:** {props['sigla']}"
        )

        col2.write(
            f"**Organização:** {props['organizacao']}"
        )

    else:

        st.write(
            f"**Organização:** {props['organizacao']}"
        )




    st.divider()

    col1, col2 = st.columns(2)

    col1.write(
        f"**Período:** {props['data_inicio']} a {props['data_fim']}"
    )

    col1, col2 = st.columns(2)


    col1.write(f"**Local:** {props['local']}")

    col2.write(f"**Município / UF:** {props['municipio_uf']}")
    
    

    st.write("**Descrição**")

    st.write(props["descricao"])


    # RENDERIZA OS LINKS DE DIVULGAÇÃO
    if props["links_divulgacao"]:

        st.write("**Links de divulgação**")

        for link in props["links_divulgacao"]:

            link_exibicao = link.strip()

            url = link_exibicao

            if (
                url
                and not url.startswith("http://")
                and not url.startswith("https://")
            ):

                url = f"https://{url}"

            st.link_button(
                label=link_exibicao,
                url=url,
                icon=":material/link:",
                type="tertiary"
            )

    st.caption(
        f"Cadastrado em {props['data_cadastro']}"
    )




###########################################################################################################
# TRATAMENTO DE DADOS
###########################################################################################################

# Cores dos eventos do calendário
cor_evento_ieb = "#6B6B6B"

# Meu projeto (agora verde)
cor_meu_projeto = "#8fad4dff"

# Demais projetos (agora azul)
cor_demais_projetos = "#2F5BA1B2"





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

# Abas

aba_selecionada = sac.tabs(
    items=[
        sac.TabsItem(label="Agenda"),
        sac.TabsItem(label="Divulgar eventos")
    ],
    align="left",
    variant="outline",
    key="tabs_eventos"
)



if aba_selecionada == "Agenda":



    st.write("")

    st.subheader("Agenda de eventos do edital")



    ###################################################################################################
    # LEGENDA DOS EVENTOS
    ###################################################################################################

    st.write("")

    with st.container(horizontal=True):

        # Eventos do IEB
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;margin-right:24px;">
                <div style="
                    width:14px;
                    height:14px;
                    border-radius:50%;
                    background:{cor_evento_ieb};
                    margin-right:8px;">
                </div>
                Eventos do IEB
            </div>
            """,
            unsafe_allow_html=True
        )


        # Eventos do meu projeto
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;margin-right:24px;">
                <div style="
                    width:14px;
                    height:14px;
                    border-radius:50%;
                    background:{cor_meu_projeto};
                    margin-right:8px;">
                </div>
                Eventos do Meu Projeto
            </div>
            """,
            unsafe_allow_html=True
        )


        # Eventos dos demais projetos
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;">
                <div style="
                    width:14px;
                    height:14px;
                    border-radius:50%;
                    background:{cor_demais_projetos};
                    margin-right:8px;">
                </div>
                Eventos dos Demais Projetos
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")
    st.write("")




    eventos = montar_eventos_calendario()

    calendar_options = {

        "locale": "pt-br",

        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listMonth"
        },

        "buttonText": {
            "today": "Hoje",
            "month": "Mês",
            "week": "Semana",
            "list": "Lista"
        },

        "initialView": "dayGridMonth",

        "editable": False,

        "selectable": False,

        "height": 700
    }


    estado = calendar(
        events=eventos,
        options=calendar_options,
    )

    if estado.get("eventClick"):

        dialog_evento(
            estado["eventClick"]["event"]
        )






elif aba_selecionada == "Divulgar eventos":


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

        with st.form("form_cadastro_evento", border=False):

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








