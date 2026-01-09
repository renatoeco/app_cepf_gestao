import streamlit as st
import pandas as pd
from funcoes_auxiliares import conectar_mongo_cepf_gestao, sidebar_projeto, ajustar_altura_data_editor
import streamlit_antd_components as sac
import time




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


###########################################################################################################
# FUNÇÕES
###########################################################################################################

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


# Os relatórios seguintes ficam aguardando (bloqueados), até que o relatório anterior seja aprovado.
def forcar_status_aguardando(projeto_codigo, relatorio_numero):
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

        # -------------------------------
        # INICIALIZA SESSION_STATE
        # -------------------------------
        if f"status_relatorio_{idx}" not in st.session_state:
            st.session_state[f"status_relatorio_{idx}"] = status_atual_ui

        # -------------------------------
        # SEGMENTED CONTROL
        # -------------------------------
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
                ":material/nest_clock_farsight_analog: Aguardando a aprovação do relatório anterior."

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
                # usuario_visitante = tipo_usuario not in ["admin", "equipe", "beneficiario"]

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
                            st.file_uploader(
                                "Anexo",
                                disabled=not pode_editar,
                                key=f"upload_{pesquisa['id']}",
                                width=400
                            )

                    # -------- RESPONDIDA --------
                    with col3:
                        respondida = st.checkbox(
                            "Respondida",
                            value=status.get("respondida", False),
                            disabled=not pode_editar,
                            key=f"resp_{pesquisa['id']}"
                        )

                    # -------- VERIFICADA --------
                    with col4:
                        verificada = st.checkbox(
                            "Verificada",
                            value=status.get("verificada", False),
                            disabled=not pode_verificar,
                            key=f"verif_{pesquisa['id']}"
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
                    if st.button("Salvar alterações", type="primary", icon=":material/save:"):

                        col_projetos.update_one(
                            {"codigo": projeto["codigo"]},
                            {"$set": {"pesquisas": novos_status}}
                        )

                        st.success(":material/check: Pesquisas atualizadas com sucesso!")
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

                    # Carrega respostas já existentes ou inicializa vazio
                    st.session_state.respostas_formulario = (
                        relatorio.get("respostas_formulario", {}).copy()
                    )


                ###########################################################################
                # 3. RENDERIZAÇÃO DO FORMULÁRIO
                ###########################################################################

                # st.markdown("### Formulário do Relatório")
                st.write("")
                st.write("")



                respostas_formulario = []



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

                        respostas_formulario.append({
                            "tipo": "titulo",
                            "texto": texto,
                            "ordem": ordem
                        })
                        continue



                    # ---------------------------------------------------------------------
                    # SUBTÍTULO (não salva resposta)
                    # ---------------------------------------------------------------------
                    elif tipo == "subtitulo":
                        st.markdown(f"##### {texto}")
                        st.write("")

                        respostas_formulario.append({
                            "tipo": "subtitulo",
                            "texto": texto,
                            "ordem": ordem
                        })
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

                        respostas_formulario.append({
                            "tipo": "paragrafo",
                            "texto": texto,
                            "ordem": ordem
                        })
                        continue


                    # ---------------------------------------------------------------------
                    # TEXTO CURTO
                    # ---------------------------------------------------------------------
                    elif tipo == "texto_curto":

                        resposta = st.session_state.respostas_formulario.get(chave, "")

                        if status_atual_db == "modo_edicao":
                            resposta = st.text_input(
                                label=texto,
                                value=resposta,
                                key=chave
                            )
                        else:
                            renderizar_visualizacao(texto, resposta)

                        st.session_state.respostas_formulario[chave] = resposta

                        respostas_formulario.append({
                            "tipo": "texto_curto",
                            "ordem": ordem,
                            "pergunta": texto,
                            "resposta": resposta
                        })





                    # elif tipo == "texto_curto":
                    #     resposta = st.text_input(
                    #         label=texto,
                    #         value=st.session_state.respostas_formulario.get(chave, ""),
                    #         key=chave
                    #     )

                    #     st.session_state.respostas_formulario[chave] = resposta

                    #     respostas_formulario.append({
                    #         "tipo": "texto_curto",
                    #         "ordem": ordem,
                    #         "pergunta": texto,
                    #         "resposta": resposta
                    #     })



                    # ---------------------------------------------------------------------
                    # TEXTO LONGO
                    # ---------------------------------------------------------------------

                    elif tipo == "texto_longo":

                        resposta = st.session_state.respostas_formulario.get(chave, "")

                        if status_atual_db == "modo_edicao":
                            resposta = st.text_area(
                                label=texto,
                                value=resposta,
                                height=150,
                                key=chave
                            )
                        else:
                            renderizar_visualizacao(texto, resposta)

                        st.session_state.respostas_formulario[chave] = resposta

                        respostas_formulario.append({
                            "tipo": "texto_longo",
                            "ordem": ordem,
                            "pergunta": texto,
                            "resposta": resposta
                        })





                    # elif tipo == "texto_longo":
                    #     resposta = st.text_area(
                    #         label=texto,
                    #         value=st.session_state.respostas_formulario.get(chave, ""),
                    #         height=150,
                    #         key=chave
                    #     )

                    #     st.session_state.respostas_formulario[chave] = resposta

                    #     respostas_formulario.append({
                    #         "tipo": "texto_longo",
                    #         "ordem": ordem,
                    #         "pergunta": texto,
                    #         "resposta": resposta
                    #     })



                    # ---------------------------------------------------------------------
                    # NÚMERO
                    # ---------------------------------------------------------------------
                    elif tipo == "numero":

                        resposta = st.session_state.respostas_formulario.get(chave)

                        try:
                            valor_inicial = float(resposta)
                        except (TypeError, ValueError):
                            valor_inicial = 0.0

                        if status_atual_db == "modo_edicao":
                            resposta = st.number_input(
                                label=texto,
                                value=valor_inicial,
                                step=1.0,
                                format="%g",
                                key=chave
                            )
                        else:
                            renderizar_visualizacao(
                                texto,
                                formatar_numero_br_dinamico(resposta)
                            )

                        st.session_state.respostas_formulario[chave] = resposta








                    # # ---------------------------------------------------------------------
                    # # NÚMERO
                    # # ---------------------------------------------------------------------
                    # elif tipo == "numero":

                    #     valor_bruto = st.session_state.respostas_formulario.get(chave)

                    #     try:
                    #         valor_inicial = float(valor_bruto)
                    #     except (TypeError, ValueError):
                    #         valor_inicial = 0.0

                    #     resposta = st.number_input(
                    #         label=texto,
                    #         value=valor_inicial,
                    #         step=1.0,
                    #         format="%g",
                    #         key=chave
                    #     )


                    #     st.session_state.respostas_formulario[chave] = resposta

                    #     respostas_formulario.append({
                    #         "tipo": "numero",
                    #         "ordem": ordem,
                    #         "pergunta": texto,
                    #         "resposta": resposta
                    #     })



                    # ---------------------------------------------------------------------
                    # ESCOLHA ÚNICA
                    # ---------------------------------------------------------------------
                    elif tipo == "escolha_unica":

                        resposta = st.session_state.respostas_formulario.get(chave)

                        if status_atual_db == "modo_edicao":
                            index = opcoes.index(resposta) if resposta in opcoes else 0
                            resposta = st.radio(
                                label=texto,
                                options=opcoes,
                                index=index,
                                key=chave
                            )
                        else:
                            renderizar_visualizacao(texto, resposta)

                        st.session_state.respostas_formulario[chave] = resposta

                        respostas_formulario.append({
                            "tipo": "escolha_unica",
                            "ordem": ordem,
                            "pergunta": texto,
                            "opcoes": opcoes,
                            "resposta": resposta
                        })





                    # # ---------------------------------------------------------------------
                    # # ESCOLHA ÚNICA
                    # # ---------------------------------------------------------------------
                    # elif tipo == "escolha_unica":

                    #     resposta_atual = st.session_state.respostas_formulario.get(chave)
                    #     index = opcoes.index(resposta_atual) if resposta_atual in opcoes else 0

                    #     resposta = st.radio(
                    #         label=texto,
                    #         options=opcoes,
                    #         index=index,
                    #         key=chave
                    #     )

                    #     st.session_state.respostas_formulario[chave] = resposta

                    #     respostas_formulario.append({
                    #         "tipo": "escolha_unica",
                    #         "ordem": ordem,
                    #         "pergunta": texto,
                    #         "opcoes": opcoes,
                    #         "resposta": resposta
                    #     })



                    # ---------------------------------------------------------------------
                    # MÚLTIPLA ESCOLHA
                    # ---------------------------------------------------------------------
                    elif tipo == "multipla_escolha":

                        resposta = st.session_state.respostas_formulario.get(chave, [])

                        if status_atual_db == "modo_edicao":
                            resposta = st.multiselect(
                                label=texto,
                                options=opcoes,
                                default=resposta,
                                key=chave
                            )
                        else:
                            renderizar_visualizacao(
                                texto,
                                ", ".join(resposta) if resposta else ""
                            )

                        st.session_state.respostas_formulario[chave] = resposta

                        respostas_formulario.append({
                            "tipo": "multipla_escolha",
                            "ordem": ordem,
                            "pergunta": texto,
                            "opcoes": opcoes,
                            "resposta": resposta
                        })










                    # # ---------------------------------------------------------------------
                    # # MÚLTIPLA ESCOLHA
                    # # ---------------------------------------------------------------------
                    # elif tipo == "multipla_escolha":
                    #     resposta = st.multiselect(
                    #         label=texto,
                    #         options=opcoes,
                    #         default=st.session_state.respostas_formulario.get(chave, []),
                    #         key=chave
                    #     )

                    #     st.session_state.respostas_formulario[chave] = resposta

                    #     respostas_formulario.append({
                    #         "tipo": "multipla_escolha",
                    #         "ordem": ordem,
                    #         "pergunta": texto,
                    #         "opcoes": opcoes,
                    #         "resposta": resposta
                    #     })



                    # ---------------------------------------------------------------------
                    # TIPO NÃO SUPORTADO
                    # ---------------------------------------------------------------------
                    else:
                        st.warning(f"Tipo de pergunta não suportado: {tipo}")

                    st.write("")  # Espaçamento entre perguntas






                ###########################################################################
                # 4. BOTÃO PARA SALVAR RESPOSTAS NO RELATÓRIO CORRETO (MONGODB)
                ###########################################################################


                if st.button("Salvar formulário", type="primary", icon=":material/save:"):

                    col_projetos.update_one(
                        {
                            "codigo": projeto["codigo"],
                            "relatorios.numero": relatorio_numero
                        },
                        {
                            "$set": {
                                "relatorios.$.respostas_formulario": respostas_formulario
                            }
                        }
                    )

                    st.success(":material/check: Respostas salvas com sucesso!")
                    time.sleep(3)
                    st.rerun()





















# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()