import re
import streamlit as st
from bson import ObjectId
import time

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

# Obtém todos os editais cadastrados
editais = list(
    db.editais.find(
        {},
        {
            "codigo_edital": 1
        }
    ).sort("codigo_edital", 1)
)


# Mapeamento do código do edital para o ID
mapa_editais = {
    edital["codigo_edital"]: str(edital["_id"])
    for edital in editais
}





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
        options=[""] + list(mapa_editais.keys())
    )

    st.write('')





with col2:

    st.write('')


    ###########################################################################################################
    # CONFIGURAÇÃO DO INTERVALO DE E-MAILS
    ###########################################################################################################

    # Obtém configuração salva
    config_intervalo = db.variaveis.find_one(
        {
            "nome_variavel": "intervalo_dias_mail_eventos"
        }
    )


    # Valor atual do intervalo
    intervalo_dias_mail_eventos = 0

    if config_intervalo:
        intervalo_dias_mail_eventos = config_intervalo.get(
            "dias",
            0
        )


    with st.container(horizontal=True, horizontal_alignment="right"):


        # Popover de configuração
        with st.popover(
            f"Lembrete enviado a cada **{intervalo_dias_mail_eventos}** dias",
            width=300
        ):

            # Input do intervalo
            intervalo_dias_input = st.number_input(
                "Intervalo de dias entre os e-mails de lembrete de cadastro de eventos",
                min_value=1,
                step=1,
                value=intervalo_dias_mail_eventos,
                width=300
            )



            # Botão de salvar
            if st.button(
                "Salvar intervalo",
                type="primary",
                width=200
            ):

                # Validação do input
                if not intervalo_dias_input:

                    st.warning(
                        "Insira um número."
                    )

                else:

                    # Atualiza configuração no banco
                    db.variaveis.update_one(
                        {
                            "nome_variavel": "intervalo_dias_mail_eventos"
                        },
                        {
                            "$set": {
                                "nome_variavel": "intervalo_dias_mail_eventos",
                                "dias": int(intervalo_dias_input)
                            }
                        },
                        upsert=True
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

# Executa apenas se houver edital selecionado
if codigo_edital_selecionado:

    st.write('')
    

    # Obtém o ID do edital selecionado
    id_edital = mapa_editais[codigo_edital_selecionado]

    # Busca o edital completo no banco
    edital = db.editais.find_one(
        {"_id": ObjectId(id_edital)}
    )

    # Obtém o iframe salvo no edital
    iframe_html = edital.get("eventos_iframe", "")

    # Renderiza apenas se existir iframe cadastrado
    if iframe_html:

        # Ajusta automaticamente largura e altura do iframe
        iframe_html = re.sub(
            r'width="[^"]*"',
            'width="100%"',
            iframe_html
        )

        iframe_html = re.sub(
            r'height="[^"]*"',
            'height="700"',
            iframe_html
        )




        # Renderização do calendário
        st.markdown(
            iframe_html,
            unsafe_allow_html=True
        )

    else:

        st.write('')
        
        st.caption(
            "Nenhum calendário foi cadastrado para este edital."
        )