import re
import streamlit as st
from bson import ObjectId
import time
from streamlit_calendar import calendar
import datetime

from funcoes_auxiliares import (
    conectar_mongo_cepf_gestao,
)





st.set_page_config(
    page_title="Eventos",
    page_icon=":material/event:"
)





###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB
db = conectar_mongo_cepf_gestao()





###########################################################################################################
# CARREGAMENTO DOS EDITAIS
###########################################################################################################

editais = list(
    db.editais.find(
        {},
        {
            "_id": 1,
            "codigo_edital": 1,
            "dias_intervalo_lembrete_eventos": 1
        }
    ).sort("codigo_edital", 1)
)


###########################################################################################################
# MAPEAMENTO DOS EDITAIS
###########################################################################################################

mapa_editais = {
    edital["codigo_edital"]: edital
    for edital in editais
}




###########################################################################################################
# TRATAMENTO DE DADOS
###########################################################################################################

###################################################################################################
# PALETA DE CORES DOS EDITAIS
###################################################################################################

cores_editais = [

    # Tons médios
    "#1F77B4",  # Azul
    "#2CA02C",  # Verde
    "#FF7F0E",  # Laranja
    "#D62728",  # Vermelho
    "#9467BD",  # Roxo
    "#17BECF",  # Ciano
    "#8C564B",  # Marrom

    # Tons claros
    "#A6CEE3",  # Azul
    "#B2DF8A",  # Verde
    "#FDBF6F",  # Laranja
    "#FB9A99",  # Vermelho
    "#CAB2D6",  # Roxo
    "#9EEDF2",  # Ciano
    "#D7B5A6",  # Marrom

    # Tons escuros
    "#0B4F8A",  # Azul
    "#1B7837",  # Verde
    "#C75B00",  # Laranja
    "#8B1E1E",  # Vermelho
    "#5E3C99",  # Roxo
    "#007C91",  # Ciano
    "#5D4037",  # Marrom

]

mapa_cores_editais = {}

for indice, codigo in enumerate(sorted(mapa_editais.keys())):

    mapa_cores_editais[codigo] = cores_editais[
        indice % len(cores_editais)
    ]


###########################################################################################################
# CARREGA AS ORGANIZAÇÕES
###########################################################################################################

organizacoes = {
    org["_id"]: org["nome_organizacao"]
    for org in db.organizacoes.find(
        {},
        {
            "nome_organizacao": 1
        }
    )
}





###########################################################################################################
# DIÁLOGO DO EVENTO
###########################################################################################################

@st.dialog(
    "Detalhes do evento",
    width="large"
)
def dialog_evento(evento):

    props = evento["extendedProps"]

    st.subheader(props["nome_evento"])

    st.write(
        f"{props['sigla']} - {props['organizacao']}"
    )

    st.write(f"**Edital:** {props['edital']}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**Período:** {props['data_inicio']} a {props['data_fim']}"
        )

    col1, col2 = st.columns(2)


    col1.write(
        f"**Local:** {props['local']}"
    )

    col2.write(
        f"**Município / UF:** {props['municipio_uf']}"
    )

    st.write("**Descrição**")

    st.write(props["descricao"])

    if props["links_divulgacao"]:

        st.write("**Links de divulgação**")

        for link in props["links_divulgacao"]:

            st.link_button(
                label=link,
                url=link,
                icon=":material/link:",
                type="tertiary"
            )

    if props["data_cadastro"]:

        st.caption(
            f"Cadastrado em {props['data_cadastro']}"
        )




###########################################################################################################
# MONTA OS EVENTOS DO CALENDÁRIO
###########################################################################################################

def montar_eventos_calendario(projetos):

    eventos = []

    for projeto in projetos:

        cor = mapa_cores_editais.get(
            projeto["edital"],
            "#1565C0"
        )

        nome_organizacao = organizacoes.get(
            projeto.get("id_organizacao"),
            ""
        )

        for evento in projeto.get("eventos", []):

            data_inicio = evento.get("data_inicio")
            data_fim = evento.get("data_fim")

            if not data_inicio or not data_fim:
                continue

            eventos.append({

                "id": str(evento["id"]),

                "title": (
                    f"{projeto['sigla']} - "
                    f"{evento['nome_evento']}"
                ),

                "start": data_inicio.date().isoformat(),

                "end": (
                    data_fim +
                    datetime.timedelta(days=1)
                ).date().isoformat(),

                "allDay": True,

                "backgroundColor": cor,

                "borderColor": cor,

                "extendedProps": {

                    "edital": projeto["edital"],

                    "sigla": projeto["sigla"],

                    "organizacao": nome_organizacao,

                    "nome_evento": evento["nome_evento"],

                    "descricao": evento["descricao"],

                    "data_inicio": data_inicio.strftime("%d/%m/%Y"),

                    "data_fim": data_fim.strftime("%d/%m/%Y"),

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

    return eventos






###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################

# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')

# Título da página e identificação
col_titulo, col_identificacao = st.columns([3, 2])

with col_titulo:
    st.header("Eventos")

st.write('')





col1, col2 = st.columns(2)


with col1:

    ###########################################################################################################
    # SELEÇÃO DO EDITAL
    ###########################################################################################################

    # Selectbox para seleção do edital
    codigo_edital_selecionado = st.selectbox(
        "Selecione o Edital",
        width=300,
        options=["Todos os editais"] + sorted(mapa_editais.keys())
    )

    st.write('')





with col2:

    st.write("")

    with st.container(horizontal=True, horizontal_alignment="right"):

        ###################################################################################################
        # POPOVER DE CONFIGURAÇÃO
        ###################################################################################################

        with st.popover(
            "Gerenciar lembretes",
            icon=":material/email:"
        ):

            ###################################################################################################
            # SELEÇÃO DO EDITAL
            ###################################################################################################

            codigo_edital_lembrete = st.selectbox(
                "Edital",
                options=sorted(mapa_editais.keys()),
                key="selectbox_edital_lembrete"
            )

            edital_selecionado = mapa_editais[
                codigo_edital_lembrete
            ]

            ###################################################################################################
            # CARREGA A CONFIGURAÇÃO DO EDITAL
            ###################################################################################################

            valor_intervalo = edital_selecionado.get(
                "dias_intervalo_lembrete_eventos",
                0
            )

            ###################################################################################################
            # SINCRONIZA O SESSION STATE
            ###################################################################################################

            if (
                st.session_state.get("edital_lembrete_atual")
                != codigo_edital_lembrete
            ):

                st.session_state["edital_lembrete_atual"] = (
                    codigo_edital_lembrete
                )

                st.session_state["intervalo_dias_mail_eventos"] = (
                    valor_intervalo
                )

            ###################################################################################################
            # INPUT DO INTERVALO
            ###################################################################################################

            intervalo_dias_input = st.number_input(
                "Intervalo de dias entre os e-mails de lembrete de cadastro de eventos",
                min_value=0,
                step=1,
                key="intervalo_dias_mail_eventos",
                width=300
            )

            st.caption("0 = desativado")

            ###################################################################################################
            # SALVA A CONFIGURAÇÃO
            ###################################################################################################

            if st.button(
                "Salvar intervalo",
                type="primary",
                width=200
            ):

                db.editais.update_one(

                    {
                        "_id": edital_selecionado["_id"]
                    },

                    {
                        "$set": {

                            "dias_intervalo_lembrete_eventos": int(
                                intervalo_dias_input
                            )

                        }

                    }

                )

                st.success(
                    "Intervalo salvo com sucesso.",
                    icon=":material/check:"
                )

                time.sleep(3)

                st.rerun()















###########################################################################################################
# RENDERIZAÇÃO DO CALENDÁRIO
###########################################################################################################

st.write("")

###################################################################################################
# CARREGAMENTO DOS PROJETOS
###################################################################################################

filtro = {}

if codigo_edital_selecionado != "Todos os editais":
    filtro["edital"] = codigo_edital_selecionado

projetos = list(
    db.projetos.find(
        filtro,
        {
            "codigo": 1,
            "sigla": 1,
            "edital": 1,
            "id_organizacao": 1,
            "eventos": 1
        }
    )
)

###################################################################################################
# LEGENDA DOS EDITAIS
###################################################################################################

if codigo_edital_selecionado == "Todos os editais":

    with st.container(horizontal=True):

        for edital in sorted(mapa_cores_editais.keys()):

            cor = mapa_cores_editais[edital]

            st.markdown(
                f"""
                <div style="display:flex;align-items:center;margin-right:20px;">
                    <div style="
                        width:14px;
                        height:14px;
                        border-radius:50%;
                        background:{cor};
                        margin-right:8px;">
                    </div>
                    {edital}
                </div>
                """,
                unsafe_allow_html=True
            )

    st.write("")

###################################################################################################
# EVENTOS
###################################################################################################

eventos = montar_eventos_calendario(projetos)

###################################################################################################
# CONFIGURAÇÃO DO CALENDÁRIO
###################################################################################################

calendar_options = {

    "locale": "pt-br",

    "height": 750,

    "initialView": "dayGridMonth",

    "editable": False,

    "selectable": False,

    "eventDisplay": "block",

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

    }

}

###################################################################################################
# CALENDÁRIO
###################################################################################################

estado = calendar(

    events=eventos,

    options=calendar_options,

    key="calendario_eventos_admin"

)

###################################################################################################
# ABERTURA DO DIÁLOGO
###################################################################################################

if estado.get("eventClick"):

    dialog_evento(
        estado["eventClick"]["event"]
    )