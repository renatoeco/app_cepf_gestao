import streamlit as st
import pandas as pd
import streamlit_antd_components as sac
import time

from funcoes_auxiliares import (
    conectar_mongo_cepf_gestao,
    sidebar_projeto,
    # ajustar_altura_data_editor,

    # Google Drive
    obter_servico_drive,
    obter_ou_criar_pasta,
    obter_pasta_pesquisas,
    obter_pasta_projeto,
    enviar_arquivo_drive,
    gerar_link_drive
)



# Google Drive API
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload



###########################################################################################################
# CONFIGURAÇÕES DO STREAMLIT
###########################################################################################################


# Traduzindo o texto do st.file_uploader
# Texto interno
st.markdown("""
<style>
/* Esconde o texto padrão */
[data-testid="stFileUploaderDropzone"] div div::before {
    content: "";
    color: rgba(49, 51, 63, 0.7);
    font-size: 0.9rem;
    font-weight: 400;
    position: absolute;
    top: 50px;              /* fixa no topo */
    left: 50%;
    transform: translate(-50%, 10%);
    pointer-events: none;
}
/* Esconde o texto original */
[data-testid="stFileUploaderDropzone"] div div span {
    visibility: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# Traduzindo Botão do file_uploader
st.markdown("""
<style>
/* Alvo: apenas o botão dentro do componente de upload */
section[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] {
    font-size: 0px !important;   /* esconde o texto original */
    padding-left: 14px !important;
    padding-right: 14px !important;
    min-width: 160px !important;
}
/* Insere o texto traduzido */
section[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"]::after {
    content: "Selecionar arquivo";
    font-size: 14px !important;
    color: inherit;
}
</style>
""", unsafe_allow_html=True)


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

col_projetos = db["projetos"]

col_editais = db["editais"]



###########################################################################################################
# CARREGAMENTO DOS DADOS
###########################################################################################################

codigo_projeto_atual = st.session_state.projeto_atual

df_projeto = pd.DataFrame(
    list(
        col_projetos.find(
            {"codigo": codigo_projeto_atual}
        )
    )
)

if df_projeto.empty:
    st.error("Projeto não encontrado.")
    st.stop()

projeto = df_projeto.iloc[0]

relatorios = projeto.get("relatorios", [])

edital = col_editais.find_one({"codigo_edital": projeto["edital"]})

tipo_usuario = st.session_state.get("tipo_usuario")



# ?????????????????
# Nome do usuário
st.sidebar.write(st.session_state.get("nome"))



###########################################################################################################
# FUNÇÕES
###########################################################################################################





# Função para liberar o próximo relatório quando o relatório anterior for aprovado
def liberar_proximo_relatorio(projeto_codigo, relatorios):
    """
    Se um relatório estiver aprovado, libera o próximo
    caso ele esteja como 'aguardando'.
    """
    for i in range(len(relatorios) - 1):
        status_atual = relatorios[i].get("status_relatorio")
        status_proximo = relatorios[i + 1].get("status_relatorio")

        if status_atual == "aprovado" and status_proximo == "aguardando":
            col_projetos.update_one(
                {
                    "codigo": projeto_codigo,
                    "relatorios.numero": relatorios[i + 1]["numero"]
                },
                {
                    "$set": {
                        "relatorios.$.status_relatorio": "modo_edicao"
                    }
                }
            )






# Renderiza as perguntas em modo visualização
def renderizar_visualizacao(pergunta, resposta):
    """
    Renderiza pergunta em negrito e resposta em texto normal
    """
    st.markdown(f"**{pergunta}**")
    if resposta in [None, "", [], {}]:
        st.write("—")
    else:
        st.write(resposta)
    st.write("")






# Atualiza o status do relatório no banco de dados, apoiando o segmented_control

STATUS_UI_TO_DB = {
    "Modo edição": "modo_edicao",
    "Em análise": "em_analise",
    "Aprovado": "aprovado",
}

STATUS_DB_TO_UI = {v: k for k, v in STATUS_UI_TO_DB.items()}

def atualizar_status_relatorio(idx, relatorio_numero, projeto_codigo):
    """
    Atualiza o status do relatório no MongoDB quando o segmented_control muda
    """

    # Valor selecionado na interface (ex: "Em análise")
    status_ui = st.session_state.get(f"status_relatorio_{idx}")

    # Converte para o valor salvo no banco (ex: "em_analise")
    status_db = STATUS_UI_TO_DB.get(status_ui)

    if not status_db:
        return  # segurança extra

    # Atualiza somente o relatório correspondente
    col_projetos.update_one(
        {
            "codigo": projeto_codigo,
            "relatorios.numero": relatorio_numero
        },
        {
            "$set": {
                "relatorios.$.status_relatorio": status_db
            }
        }
    )




def extrair_atividades(projeto):
    atividades = []

    plano = projeto.get("plano_trabalho", {})
    componentes = plano.get("componentes", [])

    for componente in componentes:
        for entrega in componente.get("entregas", []):
            for atividade in entrega.get("atividades", []):
                atividades.append({
                    "id": atividade.get("id"),
                    "nome": atividade.get("atividade"),
                    "data_inicio": atividade.get("data_inicio"),
                    "data_fim": atividade.get("data_fim"),
                    "componente": componente.get("componente"),
                    "entrega": entrega.get("entrega"),
                })

    return atividades




def formatar_numero_br_dinamico(valor):
    """
    Formata número no padrão brasileiro:
    - Sem decimais → não mostra casas
    - 1 decimal → mostra 1 casa
    - 2+ decimais → mostra até 2 casas (sem zeros desnecessários)
    """
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return "—"

    # Verifica parte decimal
    inteiro = int(valor)
    decimal = abs(valor - inteiro)

    # Define casas decimais dinamicamente
    if decimal == 0:
        casas = 0
    elif round(decimal * 10) == decimal * 10:
        casas = 1
    else:
        casas = 2

    texto = f"{valor:,.{casas}f}"

    # Converte para padrão pt-BR
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")



###########################################################################################################
# TRATAMENTO DOS DADOS
###########################################################################################################


# Libera automaticamente o próximo relatório, se aplicável
liberar_proximo_relatorio(projeto["codigo"], relatorios)

# Recarrega o projeto para refletir possíveis mudanças
projeto = col_projetos.find_one({"codigo": projeto["codigo"]})
relatorios = projeto.get("relatorios", [])




# -------------------------------------------
# CONTROLE DE STEP DO RELATÓRIO
# -------------------------------------------

if "step_relatorio" not in st.session_state:
    st.session_state.step_relatorio = "Atividades"




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página e identificação
col_titulo, col_identificacao = st.columns([3, 2])

with col_titulo:
    st.header("Relatórios")

with col_identificacao:
    st.markdown(
        f"<div style='text-align: right; margin-top: 30px;'>{df_projeto['codigo'].values[0]} - {df_projeto['sigla'].values[0]}</div>",
        unsafe_allow_html=True
    )








###########################################################################################################
# UMA ABA PRA CADA RELATÓRIO
###########################################################################################################

steps_relatorio = [
    "Atividades",
    "Despesas",
    "Beneficiários",
    "Pesquisas",
    "Formulário"
]


if not relatorios:
    st.info("Este projeto ainda não possui relatórios cadastrados.")
    st.stop()


# Cria uma aba para cada relatório
abas = [f"Relatório {r.get('numero')}" for r in relatorios]
tabs = st.tabs(abas)




# Cria uma aba para cada relatório



for idx, (tab, relatorio) in enumerate(zip(tabs, relatorios)):
    with tab:

        relatorio_numero = relatorio["numero"]
        projeto_codigo = projeto["codigo"]

        # -------------------------------
        # STATUS ATUAL DO RELATÓRIO
        # -------------------------------
        status_atual_db = relatorio.get("status_relatorio", "modo_edicao")
        status_atual_ui = STATUS_DB_TO_UI.get(status_atual_db, "Modo edição")

        aguardando = False


        # -------------------------------
        # Controle central de permissão de edição
        # -------------------------------
        pode_editar_relatorio = (
            status_atual_db == "modo_edicao"
            and tipo_usuario == "beneficiario"
        )

        # -------------------------------
        # REGRA DE BLOQUEIO (a partir do 2º)
        # -------------------------------
        if idx > 0:
            status_anterior = relatorios[idx - 1].get("status_relatorio")

            if status_anterior != "aprovado":
                aguardando = True

                # força status aguardando no banco (sem loop)
                col_projetos.update_one(
                    {
                        "codigo": projeto_codigo,
                        "relatorios.numero": relatorio_numero,
                        "relatorios.status_relatorio": {"$ne": "aguardando"}
                    },
                    {
                        "$set": {
                            "relatorios.$.status_relatorio": "aguardando"
                        }
                    }
                )

                # UI fica travada, mas mantém um valor válido
                status_atual_ui = "Modo edição"




        ###########################################################################################################
        # MENSAGEM DE STATUS DO RELATÓRIO PARA BENEFICIÁRIO E VISITANTE
        ###########################################################################################################

        if tipo_usuario in ["beneficiario", "visitante"]:

            if status_atual_db == "em_analise":
                st.write('')
                st.warning("Relatório em análise. Aguarde o retorno.", icon=":material/manage_search:")

            elif status_atual_db == "aprovado":
                st.write('')
                st.success("Relatório aprovado", icon=":material/check:")







        # -------------------------------
        # INICIALIZA SESSION_STATE
        # -------------------------------
        if f"status_relatorio_{idx}" not in st.session_state:
            st.session_state[f"status_relatorio_{idx}"] = status_atual_ui

        # -------------------------------
        # SEGMENTED CONTROL somente para equipe interna
        # -------------------------------

        if tipo_usuario in ["equipe", "admin"]:
            with st.container(horizontal=True, horizontal_alignment="center"):
                st.segmented_control(
                    label="",
                    options=["Modo edição", "Em análise", "Aprovado"],
                    key=f"status_relatorio_{idx}",
                    disabled=aguardando,
                    on_change=atualizar_status_relatorio if not aguardando else None,
                    args=(idx, relatorio_numero, projeto_codigo) if not aguardando else None
                )

        if aguardando:
            st.write('')
            st.info(
                # ":material/hourglass_top: Aguardando a aprovação do relatório anterior."
                "Aguardando a aprovação do relatório anterior.",
                icon=":material/nest_clock_farsight_analog:"

            )


        st.write('')
        st.write('')


        if not aguardando:


            # STEPS funcionam como abas --------------------------
            step_key = f"steps_relatorio_{idx}"


            step = sac.steps(
                items=[sac.StepsItem(title=s) for s in steps_relatorio],
                index=steps_relatorio.index(st.session_state.step_relatorio),
                key=f"steps_relatorio_{idx}"
            )




            # ---------- ATIVIDADES ----------

            if step == "Atividades":

                # # Atualiza o estado global do step
                # if step != st.session_state.step_relatorio:
                #     st.session_state.step_relatorio = step


                atividades = []

                plano = projeto.get("plano_trabalho", {})
                componentes = plano.get("componentes", [])

                for componente in componentes:
                    for entrega in componente.get("entregas", []):
                        for atividade in entrega.get("atividades", []):
                            atividades.append({
                                "atividade": atividade.get("atividade"),
                                "componente": componente.get("componente"),
                                "entrega": entrega.get("entrega"),
                                "data_inicio": atividade.get("data_inicio"),
                                "data_fim": atividade.get("data_fim"),
                            })

                # SELECTBOX
                if atividades:
                    atividade_selecionada = st.selectbox(
                        "Atividades",
                        options=atividades,
                        format_func=lambda x: x["atividade"],
                        key=f"atividade_select_{idx}"
                    )

                    st.markdown("### Detalhes da atividade")

                    st.write(f"**Atividade:** {atividade_selecionada['atividade']}")
                    st.write(f"**Componente:** {atividade_selecionada['componente']}")
                    st.write(f"**Entrega:** {atividade_selecionada['entrega']}")

                    if atividade_selecionada["data_inicio"]:
                        st.write(f"**Início:** {atividade_selecionada['data_inicio']}")

                    if atividade_selecionada["data_fim"]:
                        st.write(f"**Fim:** {atividade_selecionada['data_fim']}")

                else:
                    st.info("Nenhuma atividade cadastrada.")





            # ---------- PESQUISAS ----------
            if step == "Pesquisas":

                # ============================
                # CONTROLE DE USUÁRIO
                # ============================

                usuario_admin = tipo_usuario == "admin"
                usuario_equipe = tipo_usuario == "equipe"
                usuario_beneficiario = tipo_usuario == "beneficiario"
                usuario_visitante = tipo_usuario not in ["visitante"]

                pode_editar = usuario_admin or usuario_equipe or usuario_beneficiario
                pode_verificar = usuario_admin or usuario_equipe

                # ============================
                # BUSCA DADOS
                # ============================
                pesquisas = edital.get("pesquisas_relatorio", []) if edital else []

                if not pesquisas:
                    st.caption("Nenhuma pesquisa cadastrada.")
                    st.stop()

                st.write('')
                st.markdown("##### Pesquisas / Ferramentas de Monitoramento")
                st.write('')

                pesquisas_projeto = projeto.get("pesquisas", [])
                status_map = {p["id_pesquisa"]: p for p in pesquisas_projeto}

                # # Ordena as pesquisas em ordem alfabética pelo nome
                # pesquisas = sorted(
                #     pesquisas,
                #     key=lambda p: p.get("nome_pesquisa", "").lower()
                # )


                # ============================
                # RENDERIZAÇÃO DAS LINHAS
                # ============================
                novos_status = []

                for pesquisa in pesquisas:

                    status = status_map.get(pesquisa["id"], {})

                    col1, col2, col3, col4 = st.columns([4, 3, 1, 1])

                    # -------- PESQUISA --------
                    with col1:
                        st.markdown(f"**{pesquisa['nome_pesquisa']}**")

                    # -------- ANEXO --------
                    with col2:
                        if pesquisa.get("upload_arquivo"):

                            arquivo_upload = st.file_uploader(
                                "Anexo",
                                key=f"upload_{relatorio_numero}_{pesquisa['id']}",
                                disabled=(
                                    not pode_editar
                                    or status_atual_db in ["em_analise", "aprovado"]
                                ),
                                help=(
                                    'Para inserir um link use "[texto_do_link](url_do_link)". '
                                    'Exemplo: Nome da pesquisa - [clique aqui](https://www.google.com)'
                                )
                            )



                    # -------- RESPONDIDA --------
                    with col3:
                        # Para beneficiários e visitantes, sempre que a pesquisa for verificara, desabilita o checkbox de respondida
                        respondida = st.checkbox(
                            "Respondida",

                            # Valor inicial do checkbox:
                            # - Usa o valor salvo no banco
                            # - Se não existir, assume False
                            value=status.get("respondida", False),

                            # Controle completo de bloqueio do checkbox
                            disabled=(

                                # REGRA GLOBAL DE STATUS DO RELATÓRIO
                                # Se o relatório NÃO estiver em modo de edição,
                                # ninguém pode alterar Respondida
                                status_atual_db in ["em_analise", "aprovado"]

                                # OU

                                or

                                # REGRA DE PERMISSÃO GERAL
                                # Se o usuário não pode editar pesquisas,
                                # o checkbox fica bloqueado
                                not pode_editar

                                # OU

                                or (

                                    # REGRA ESPECÍFICA PARA BENEFICIÁRIO / VISITANTE
                                    # Se o usuário for beneficiário ou visitante
                                    tipo_usuario in ["beneficiario", "visitante"]

                                    # E

                                    and

                                    # Se a pesquisa já estiver marcada como verificada
                                    # (ou seja, já passou pela conferência)
                                    status.get("verificada", False)
                                )
                            ),

                            # Chave única do checkbox no Streamlit
                            # Garante que cada linha tenha estado próprio
                            key=f"resp_{relatorio_numero}_{pesquisa['id']}"
                        )



                    # -------- VERIFICADA --------
                    with col4:
                        verificada = st.checkbox(
                            "Verificada",

                            # Valor inicial do checkbox
                            value=status.get("verificada", False),

                            # Controle de bloqueio
                            disabled=(

                                # REGRA GLOBAL DE STATUS DO RELATÓRIO
                                # Em análise ou aprovado → ninguém altera
                                status_atual_db in ["em_analise", "aprovado"]

                                # OU

                                or

                                # REGRA DE PERMISSÃO
                                # Apenas admin/equipe podem verificar
                                not pode_verificar
                            ),

                            # Chave única por pesquisa
                            key=f"verif_{relatorio_numero}_{pesquisa['id']}"
                        )


                    novos_status.append({
                        "id_pesquisa": pesquisa["id"],
                        "respondida": respondida,
                        "verificada": verificada
                    })

                    st.divider()

                # ============================
                # BOTÃO SALVAR
                # ============================
                if pode_editar:

                    if st.button(
                        "Salvar alterações",
                        type="primary",
                        icon=":material/save:",
                        key=f"salvar_pesquisas_{relatorio_numero}"
                    ):

                        with st.spinner("Salvando pesquisas e anexos..."):

                            # Conecta no Drive SOMENTE aqui
                            servico = obter_servico_drive()

                            # Pasta do projeto
                            pasta_projeto = obter_pasta_projeto(
                                servico,
                                projeto["codigo"],
                                projeto["sigla"]
                            )

                            # Subpasta "Pesquisas"
                            pasta_pesquisas = obter_pasta_pesquisas(
                                servico,
                                pasta_projeto
                            )

                            novos_status = []

                            # Loop por pesquisa
                            for pesquisa in pesquisas:

                                # Recupera estados dos checkboxes
                                respondida = st.session_state.get(
                                    f"resp_{relatorio_numero}_{pesquisa['id']}",
                                    False
                                )

                                verificada = st.session_state.get(
                                    f"verif_{relatorio_numero}_{pesquisa['id']}",
                                    False
                                )

                                dados = {
                                    "id_pesquisa": pesquisa["id"],
                                    "respondida": respondida,
                                    "verificada": verificada
                                }

                                # ------------------------------
                                # UPLOAD DE ARQUIVO (SE EXISTIR)
                                # ------------------------------
                                if pesquisa.get("upload_arquivo"):

                                    arquivo = st.session_state.get(
                                        f"upload_{relatorio_numero}_{pesquisa['id']}"
                                    )
                                    
                                    if arquivo is not None:
                                        id_drive = enviar_arquivo_drive(
                                            servico,
                                            pasta_pesquisas,
                                            arquivo
                                        )
                                    
                                    # if arquivo:
                                    #     # Envia para o Drive
                                    #     id_drive = enviar_arquivo_drive(
                                    #         servico,
                                    #         pasta_pesquisas,
                                    #         arquivo
                                    #     )

                                        # Salva URL no objeto da pesquisa
                                        dados["url_anexo"] = gerar_link_drive(id_drive)

                                novos_status.append(dados)

                            # ------------------------------
                            # ATUALIZA MONGODB
                            # ------------------------------
                            col_projetos.update_one(
                                {
                                    "codigo": codigo_projeto_atual,
                                    "relatorios.numero": relatorio_numero
                                },
                                {
                                    "$set": {
                                        "relatorios.$.pesquisas": novos_status
                                    }
                                }
                            )

                        st.success("Pesquisas salvas com sucesso!")
                        time.sleep(3)
                        st.rerun()








            # ---------- FORMULÁRIO ----------
            if step == "Formulário":

                ###########################################################################
                # 1. BUSCA O EDITAL CORRESPONDENTE AO PROJETO
                ###########################################################################

                edital = col_editais.find_one(
                    {"codigo_edital": projeto["edital"]}
                )

                if not edital:
                    st.error("Edital não encontrado para este projeto.")
                    st.stop()

                perguntas = edital.get("perguntas_relatorio", [])

                if not perguntas:
                    st.write('')
                    st.error("O edital não possui perguntas cadastradas.")
                    st.stop()

                # Ordena as perguntas pela ordem definida no edital
                perguntas = sorted(perguntas, key=lambda x: x.get("ordem", 0))


                ###########################################################################
                # 2. CONTROLE DE ESTADO POR RELATÓRIO (EVITA VAZAMENTO ENTRE ABAS)
                ###########################################################################

                # Identificador único do relatório atual
                relatorio_numero = relatorio["numero"]
                chave_relatorio_ativo = f"form_relatorio_{relatorio_numero}"

                # Se mudou de relatório, recarrega respostas do banco
                if st.session_state.get("form_relatorio_ativo") != chave_relatorio_ativo:
                    st.session_state.form_relatorio_ativo = chave_relatorio_ativo


                    # -------------------------------------------
                    # CARREGA RESPOSTAS DO RELATÓRIO (DICT DE OBJETOS)
                    # -------------------------------------------

                    # Identificador único do relatório
                    relatorio_numero = relatorio["numero"]

                    # Evita vazamento entre abas
                    if st.session_state.get("form_relatorio_ativo") != relatorio_numero:
                        st.session_state.form_relatorio_ativo = relatorio_numero

                        # Sempre trabalha com dict (novo modelo)
                        st.session_state.respostas_formulario = (
                            relatorio.get("respostas_formulario", {}).copy()
                        )



                ###########################################################################
                # 3. RENDERIZAÇÃO DO FORMULÁRIO
                ###########################################################################

                # st.markdown("### Formulário do Relatório")
                st.write("")
                st.write("")



                # respostas_formulario = []



                for pergunta in perguntas:
                    tipo = pergunta.get("tipo")
                    texto = pergunta.get("pergunta")
                    opcoes = pergunta.get("opcoes", [])
                    ordem = pergunta.get("ordem")

                    # Chave única da pergunta dentro do relatório
                    chave = f"pergunta_{ordem}"


                    # ---------------------------------------------------------------------
                    # TÍTULO (não salva resposta)
                    # ---------------------------------------------------------------------
                    if tipo == "titulo":
                        st.subheader(texto)
                        st.write("")


                        continue



                    # ---------------------------------------------------------------------
                    # SUBTÍTULO (não salva resposta)
                    # ---------------------------------------------------------------------
                    elif tipo == "subtitulo":
                        st.markdown(f"##### {texto}")
                        st.write("")


                        continue



                    # # ---------------------------------------------------------------------
                    # # DIVISÓRIA (não usa texto)
                    # # ---------------------------------------------------------------------
                    # elif tipo == "divisoria":
                    #     st.divider()

                    #     respostas_formulario.append({
                    #         "tipo": "divisoria",
                    #         "ordem": ordem
                    #     })
                    #     continue


                    # ---------------------------------------------------------------------
                    # PARÁGRAFO → apenas texto informativo
                    # ---------------------------------------------------------------------
                    elif tipo == "paragrafo":
                        st.write(texto)
                        st.write("")

                        continue


                    # ---------------------------------------------------------------------
                    # TEXTO CURTO
                    # ---------------------------------------------------------------------
                    elif tipo == "texto_curto":
                    
                    
                        resposta_atual = (
                            st.session_state.respostas_formulario
                            .get(chave, {})
                            .get("resposta", "")
                        )

                        if pode_editar_relatorio:
                            resposta = st.text_input(
                                label=texto,
                                value=resposta_atual,
                                key=f"input_{chave}"
                            )

                            st.session_state.respostas_formulario[chave] = {
                                "tipo": tipo,
                                "ordem": ordem,
                                "pergunta": texto,
                                "resposta": resposta
                            }
                        else:
                            renderizar_visualizacao(texto, resposta_atual)





                    # ---------------------------------------------------------------------
                    # TEXTO LONGO
                    # ---------------------------------------------------------------------
                    elif tipo == "texto_longo":
                    
                    
                        resposta_atual = (
                            st.session_state.respostas_formulario
                            .get(chave, {})
                            .get("resposta", "")
                        )

                        if pode_editar_relatorio:
                            resposta = st.text_area(
                                label=texto,
                                value=resposta_atual,
                                height=150,
                                key=f"input_{chave}"
                            )

                            st.session_state.respostas_formulario[chave] = {
                                "tipo": tipo,
                                "ordem": ordem,
                                "pergunta": texto,
                                "resposta": resposta
                            }
                        else:
                            renderizar_visualizacao(texto, resposta_atual)



                    # ---------------------------------------------------------------------
                    # NÚMERO
                    # ---------------------------------------------------------------------
                    elif tipo == "numero":
                    
                    
                        resposta_atual = (
                            st.session_state.respostas_formulario
                            .get(chave, {})
                            .get("resposta", 0)
                        )

                        if pode_editar_relatorio:
                            resposta = st.number_input(
                                label=texto,
                                value=float(resposta_atual),
                                step=1.0,
                                format="%g",
                                key=f"input_{chave}"
                            )

                            st.session_state.respostas_formulario[chave] = {
                                "tipo": tipo,
                                "ordem": ordem,
                                "pergunta": texto,
                                "resposta": resposta
                            }
                        else:
                            renderizar_visualizacao(
                                texto,
                                formatar_numero_br_dinamico(resposta_atual)
                            )




                    # ---------------------------------------------------------------------
                    # ESCOLHA ÚNICA
                    # ---------------------------------------------------------------------
                    elif tipo == "escolha_unica":
                    
                    
                        resposta_atual = (
                            st.session_state.respostas_formulario
                            .get(chave, {})
                            .get("resposta", opcoes[0] if opcoes else "")
                        )

                        if pode_editar_relatorio:
                            resposta = st.radio(
                                label=texto,
                                options=opcoes,
                                index=opcoes.index(resposta_atual) if resposta_atual in opcoes else 0,
                                key=f"input_{chave}"
                            )

                            st.session_state.respostas_formulario[chave] = {
                                "tipo": tipo,
                                "ordem": ordem,
                                "pergunta": texto,
                                "resposta": resposta
                            }
                        else:
                            renderizar_visualizacao(texto, resposta_atual)




                    # ---------------------------------------------------------------------
                    # MÚLTIPLA ESCOLHA
                    # ---------------------------------------------------------------------

                    elif tipo == "multipla_escolha":
                    
                    
                        resposta_atual = (
                            st.session_state.respostas_formulario
                            .get(chave, {})
                            .get("resposta", [])
                        )

                        if pode_editar_relatorio:
                            resposta = st.multiselect(
                                label=texto,
                                options=opcoes,
                                default=resposta_atual,
                                key=f"input_{chave}"
                            )

                            st.session_state.respostas_formulario[chave] = {
                                "tipo": tipo,
                                "ordem": ordem,
                                "pergunta": texto,
                                "resposta": resposta
                            }
                        else:
                            renderizar_visualizacao(
                                texto,
                                ", ".join(resposta_atual)
                            )






                    # ---------------------------------------------------------------------
                    # TIPO NÃO SUPORTADO
                    # ---------------------------------------------------------------------
                    else:
                        st.warning(f"Tipo de pergunta não suportado: {tipo}")

                    st.write("")  # Espaçamento entre perguntas






                ###########################################################################
                # 4. BOTÃO PARA SALVAR RESPOSTAS NO RELATÓRIO CORRETO (MONGODB)
                ###########################################################################
                if pode_editar_relatorio:
                    if st.button("Salvar formulário", type="primary", icon=":material/save:"):

                        col_projetos.update_one(
                            {
                                "codigo": projeto["codigo"],
                                "relatorios.numero": relatorio_numero
                            },
                            {
                                "$set": {
                                    "relatorios.$.respostas_formulario":
                                        st.session_state.respostas_formulario
                                }
                            }
                        )

                        st.success("Respostas salvas com sucesso!")
                        time.sleep(3)
                        st.rerun()




















# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()