import re
import streamlit as st
from bson import ObjectId
import time
from streamlit_calendar import calendar
import datetime
import streamlit_antd_components as sac
from st_rsuite import date_picker


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


###################################################################################################
# CARREGAMENTO DE EVENTOS DO IEB
###################################################################################################

col_eventos_ieb = db.eventos_ieb


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

# Cor do evento IEB
cor_evento_ieb = "#6B6B6B"


# PALETA DE CORES DOS EDITAIS

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

    ###################################################################################################
    # EXIBE O EDITAL APENAS QUANDO EXISTIR
    ###################################################################################################

    if props.get("edital"):

        st.write(
            f"**Edital:** {props['edital']}"
        )


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


        ###################################################################################################
        # RENDERIZA OS LINKS DE DIVULGAÇÃO
        ###################################################################################################

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



    if props["data_cadastro"]:

        st.caption(
            f"Cadastrado em {props['data_cadastro']}"
        )




###########################################################################################################
# MONTA OS EVENTOS DO CALENDÁRIO
###########################################################################################################

def montar_eventos_calendario(
    projetos,
    eventos_ieb
):

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


    ###################################################################################################
    # EVENTOS DO IEB
    ###################################################################################################


    for evento in eventos_ieb:

        data_inicio = evento.get("data_inicio")
        data_fim = evento.get("data_fim")

        if not data_inicio or not data_fim:
            continue

        eventos.append({

            "id": str(evento["_id"]),

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




# #########################################################################################################
# ABA AGENDA 
# #########################################################################################################

if aba_selecionada == "Agenda":



    col1, col2 = st.columns(2)


    with col1:

        st.write('')

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
    # CARREGAMENTO DOS EVENTOS DO IEB
    ###################################################################################################

    eventos_ieb = list(
        db.eventos_ieb.find()
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

            ###################################################################################################
            # LEGENDA DOS EVENTOS DO IEB
            ###################################################################################################

            st.markdown(
                f"""
                <div style="display:flex;align-items:center;margin-right:20px;">
                    <div style="
                        width:14px;
                        height:14px;
                        border-radius:50%;
                        background:{cor_evento_ieb};
                        margin-right:8px;">
                    </div>
                    Evento do IEB
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("")

    ###################################################################################################
    # EVENTOS
    ###################################################################################################

    eventos = montar_eventos_calendario(
        projetos,
        eventos_ieb
        )

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






# #########################################################################################################
# ABA DE DIVULGAÇÃO DE EVENTOS
###########################################################################################################

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
                        "nome_evento": f"[EVENTO DO IEB] {nome_evento}",
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

                    col_eventos_ieb.insert_one(
                        novo_evento
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

        ###################################################################################################
        # CARREGAMENTO DOS EVENTOS DO IEB
        ###################################################################################################

        eventos = list(
            col_eventos_ieb.find()
        )

        # Ordena os eventos pela data de início
        eventos = sorted(
            eventos,
            key=lambda evento: evento.get(
                "data_inicio",
                datetime.datetime.max
            )
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
                            key=f"excluir_evento_{str(evento['_id'])}",
                            type="primary",
                            icon=":material/delete:"
                        )


                        if excluir:

                            
                            ###################################################################################################
                            # EXCLUSÃO DO EVENTO
                            ###################################################################################################

                            col_eventos_ieb.delete_one(
                                {
                                    "_id": evento["_id"]
                                }
                            )

                            st.success(
                                "Evento excluído com sucesso!",
                                icon=":material/check:"
                            )

                            time.sleep(3)
                            st.rerun()

                st.divider()    




