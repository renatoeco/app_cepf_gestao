import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import pandas as pd
from bson import ObjectId
import time
import streamlit_shadcn_ui as ui
from streamlit_sortables import sort_items
import uuid



###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Importa coleções e cria dataframes

# Beneficiários
col_publicos = db["publicos"]

# Benefícios
col_beneficios = db["beneficios"]

# Direções Estratégicas
# col_direcoes = db["direcoes_estrategicas"]

# Indicadores
# col_indicadores = db["indicadores"]

# Categorias de despesa
col_categorias_despesa = db["categorias_despesa"]

# Corredores
col_corredores = db["corredores"]

# KBAs
col_kbas = db["kbas"]

# Editais
col_editais = db["editais"]




###########################################################################################################
# TRATAMENTO DOS DADOS
###########################################################################################################

# Editais
df_editais = pd.DataFrame(list(col_editais.find()))

#  Converte id para string
df_editais["_id"] = df_editais["_id"].astype(str)





###########################################################################################################
# Funções
###########################################################################################################


# ==========================================================
# FUNÇÃO: FORMULÁRIO DE NOVA PERGUNTA
# ==========================================================


@st.fragment
def formulario_nova_pergunta(perguntas, edital_selecionado):

    # ------------------------------------------------------
    # ESPAÇAMENTO VISUAL
    # ------------------------------------------------------
    st.write("")

    # ------------------------------------------------------
    # TÍTULO
    # ------------------------------------------------------
    st.markdown("##### Cadastrar nova pergunta", help="Use asteriscos para **\**negrito**\** e para *\*itálico*\*.")

    # ------------------------------------------------------
    # TIPO DE PERGUNTA
    # ------------------------------------------------------
    tipo = st.selectbox(
        "Tipo de pergunta",
        [
            "Resposta curta",
            "Resposta longa",
            "Número",
            "Múltipla escolha",
            "Escolha única",
            "Upload de arquivos",  # 👈 NOVO
            "Título",
            "Subtítulo",
            "Parágrafo",
        ],
        key="tipo_pergunta_nova"
    )


    # ------------------------------------------------------
    # CAMPOS DINÂMICOS
    # ------------------------------------------------------
    pergunta = ""
    opcoes = []

    # Define rótulo do campo de texto
    label_texto = "Texto da pergunta"

    if tipo == "Título":
        label_texto = "Texto do título"
    elif tipo == "Subtítulo":
        label_texto = "Texto do subtítulo"
    elif tipo == "Parágrafo":
        label_texto = "Texto do parágrafo"

    # Tipos que exigem input de texto
    if tipo in [
        "Resposta curta",
        "Resposta longa",
        "Número",
        "Título",
        "Subtítulo",
        "Upload de arquivos",
    ]:
        pergunta = st.text_input(
            label_texto,
            key="texto_pergunta_nova"
        )
    elif tipo == "Parágrafo":
        pergunta = st.text_area(
            label_texto,
            key="texto_pergunta_nova"
        )

    # Tipos que exigem opções
    if tipo in ["Múltipla escolha", "Escolha única"]:
        pergunta = st.text_input(
            "Texto da pergunta",
            key="texto_pergunta_opcoes"
        )

        opcoes = st.text_area(
            "Opções (uma por linha)"
        ).split("\n")

    # ------------------------------------------------------
    # BOTÃO DE SALVAR
    # ------------------------------------------------------
    st.write("")

    if st.button("Salvar pergunta", type="primary", icon=":material/save:"):

        # ----------------------------
        # VALIDAÇÕES
        # ----------------------------

        # Campos obrigatórios
        # if tipo != "Linha divisória" and not pergunta.strip():
        if not pergunta.strip():
            st.warning("Preencha todas as informações.")
            return

        if tipo in ["Múltipla escolha", "Escolha única"]:
            if not [o for o in opcoes if o.strip()]:
                st.warning("Informe pelo menos uma opção.")
                return

        # --------------------------------------------------
        # MAPEAMENTO DE TIPO
        # --------------------------------------------------
        mapa_tipo = {
            "Resposta curta": "texto_curto",
            "Resposta longa": "texto_longo",
            "Número": "numero",
            "Múltipla escolha": "multipla_escolha",
            "Escolha única": "escolha_unica",
            "Título": "titulo",
            "Subtítulo": "subtitulo",
            "Upload de arquivos": "upload_arquivo",
            "Parágrafo": "paragrafo"
        }

        # --------------------------------------------------
        # MONTA OBJETO FINAL
        # --------------------------------------------------
        nova_pergunta = {
            "tipo": mapa_tipo[tipo],
            "ordem": len(perguntas) + 1
        }

        # Texto obrigatório
        nova_pergunta["pergunta"] = pergunta.strip()

        # # Texto obrigatório (exceto divisória)
        # if mapa_tipo[tipo] != "divisoria":
        #     nova_pergunta["pergunta"] = pergunta.strip()

        # # Texto fixo para divisória
        # if mapa_tipo[tipo] == "divisoria":
        #     nova_pergunta["pergunta"] = "Divisória"

        # Opções
        if mapa_tipo[tipo] in ["multipla_escolha", "escolha_unica"]:
            nova_pergunta["opcoes"] = [o.strip() for o in opcoes if o.strip()]

        # --------------------------------------------------
        # SALVA NO BANCO
        # --------------------------------------------------
        col_editais.update_one(
            {"codigo_edital": edital_selecionado},
            {"$push": {"perguntas_relatorio": nova_pergunta}}
        )


        # Feedback
        st.success("Pergunta adicionada com sucesso!", icon=":material/check:")
        time.sleep(3)

        # Limpa campos dinâmicos
        for chave in [
            "tipo_pergunta_nova",
            "texto_pergunta_nova",
            "texto_pergunta_opcoes"
        ]:
            if chave in st.session_state:
                del st.session_state[chave]

        st.rerun()




        # # Feedback
        # st.success("Pergunta adicionada com sucesso!")

        # # Mantém padrão
        # time.sleep(3)

        # # Recarrega
        # st.rerun()






# Diálogo de confirmação de exclusão de pergunta de relatório
@st.dialog("Confirmar exclusão", width="small")
def confirmar_exclusao_pergunta(pergunta_atual, perguntas, edital_selecionado):

    st.markdown("**Você tem certeza que deseja excluir esta pergunta?**")
    st.markdown(f"> {pergunta_atual['pergunta']}")

    st.write("")

    with st.container(horizontal=True):
        if st.button(":material/cancel: Cancelar"):
            st.rerun()

        if st.button(":material/delete: Excluir pergunta", type="primary"):

            # Remove a pergunta
            novas = [p for p in perguntas if p != pergunta_atual]

            # Reorganiza a ordem
            for i, p in enumerate(novas, start=1):
                p["ordem"] = i

            col_editais.update_one(
                {"codigo_edital": edital_selecionado},
                {"$set": {"perguntas_relatorio": novas}}
            )

            st.success("Pergunta excluída com sucesso!")
            time.sleep(3)
            st.rerun()


###########################################################################################################
# INTERFACE
###########################################################################################################


# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')

st.header('Cadastros auxiliares')

st.write('')



aba_perguntas, aba_pesquisas, aba_direcoes, aba_indicadores, aba_beneficiarios, aba_beneficios, aba_categorias_despesa, aba_corredores, aba_kbas = st.tabs([
# aba_perguntas, aba_pesquisas, aba_beneficiarios, aba_direcoes, aba_indicadores, aba_categorias_despesa, aba_corredores, aba_kbas, aba_tipos_manejo = st.tabs([
    'Perguntas do Relatório',
    'Pesquisas',
    'Direções Estratégicas',
    'Indicadores de portifólio',
    'Beneficiários',
    'Benefícios',
    'Categorias de despesa',
    'Corredores',
    'KBAs',
    # 'Tipos de manejo',
])





# ==========================================================
# ABA PERGUNTAS DO RELATÓRIO
# ==========================================================

with aba_perguntas:

    # ------------------------------------------------------
    # TÍTULO DA ABA
    # ------------------------------------------------------
    st.subheader("Perguntas do Relatório")
    st.write("")

    # ------------------------------------------------------
    # SELEÇÃO DO EDITAL
    # ------------------------------------------------------

    lista_editais = df_editais["codigo_edital"].unique().tolist()

    edital_selecionado_perguntas = st.selectbox(
        "Selecione o Edital:",
        options=[""] + lista_editais,
        index=0,
        width=300,
        key="edital_selecionado_perguntas"
    )

    # Se nenhum edital foi selecionado
    if not edital_selecionado_perguntas:
        st.caption("Selecione um edital para continuar.")

    else:
        # ------------------------------------------------------
        # BUSCA O EDITAL
        # ------------------------------------------------------

        edital_perguntas = col_editais.find_one(
            {"codigo_edital": edital_selecionado_perguntas}
        )

        perguntas = sorted(
            edital_perguntas.get("perguntas_relatorio", []),
            key=lambda x: x.get("ordem", 9999)
        )

        # ======================================================
        # ABAS INTERNAS
        # ======================================================

        aba_visualizar, aba_nova, aba_editar, aba_reordenar = st.tabs([
            "Perguntas cadastradas",
            "Nova pergunta",
            "Editar / Excluir",
            "Reordenar"
        ])

        # ======================================================
        # ABA 1 — VISUALIZAR
        # ======================================================

        with aba_visualizar:

            if not perguntas:
                st.caption("Nenhuma pergunta cadastrada.")
            else:
                for idx, p in enumerate(perguntas, start=1):
                    st.markdown(f"**{idx}. {p['pergunta']}**")

                    tipo_legivel = {
                        "texto_curto": "Resposta curta",
                        "texto_longo": "Resposta longa",
                        "numero": "Número",
                        "multipla_escolha": "Múltipla escolha",
                        "escolha_unica": "Escolha única",
                        "upload_arquivo": "Upload de arquivos",  # 👈
                        "titulo": "Título",
                        "subtitulo": "Subtítulo",
                        "paragrafo": "Parágrafo"
                    }.get(p["tipo"], p["tipo"])


                    # tipo_legivel = {
                    #     "texto_curto": "Resposta curta",
                    #     "texto_longo": "Resposta longa",
                    #     "numero": "Número",
                    #     "multipla_escolha": "Múltipla escolha",
                    #     "escolha_unica": "Escolha única"
                    # }.get(p["tipo"], p["tipo"])

                    st.caption(f"Tipo: {tipo_legivel}")

                    if p["tipo"] in ["multipla_escolha", "escolha_unica"]:
                        for opcao in p.get("opcoes", []):
                            st.write(f"• {opcao}")

                    st.write("")

        # ======================================================
        # ABA 2 — NOVA PERGUNTA
        # ======================================================

        with aba_nova:
            formulario_nova_pergunta(perguntas, edital_selecionado_perguntas)



        # ======================================================
        # ABA 3 — EDITAR / EXCLUIR
        # ======================================================

        with aba_editar:

            if not perguntas:
                st.caption("Nenhuma pergunta cadastrada.")

            else:
                st.markdown("##### Selecione uma pergunta para EDITAR ou EXCLUIR")

                # ----------------------------------------------
                # MAPA DE PERGUNTAS
                # ----------------------------------------------
                mapa_perguntas = {
                    f"{p['ordem']}. {p['pergunta']}": p
                    for p in perguntas
                }

                selecionada = st.selectbox(
                    "",
                    list(mapa_perguntas.keys())
                )

                # Garante que algo foi selecionado
                if selecionada:

                    pergunta_atual = mapa_perguntas[selecionada]

                    st.divider()

                    # ----------------------------------------------
                    # TIPO ATUAL
                    # ----------------------------------------------
                    mapa_tipo_inv = {
                        "texto_curto": "Resposta curta",
                        "texto_longo": "Resposta longa",
                        "numero": "Número",
                        "multipla_escolha": "Múltipla escolha",
                        "escolha_unica": "Escolha única",
                        "upload_arquivo": "Upload de arquivos",
                        "titulo": "Título",
                        "subtitulo": "Subtítulo",
                        "paragrafo": "Parágrafo"
                    }




                    # mapa_tipo_inv = {
                    #     "texto_curto": "Resposta curta",
                    #     "texto_longo": "Resposta longa",
                    #     "numero": "Número",
                    #     "multipla_escolha": "Múltipla escolha",
                    #     "escolha_unica": "Escolha única",
                    #     "titulo": "Título",
                    #     "subtitulo": "Subtítulo",
                    #     # "divisoria": "Linha divisória",
                    #     "paragrafo": "Parágrafo"
                    # }

                    tipo_atual = mapa_tipo_inv.get(pergunta_atual["tipo"])

                    tipo = st.selectbox(
                        "Tipo de pergunta",
                        list(mapa_tipo_inv.values()),
                        index=list(mapa_tipo_inv.values()).index(tipo_atual),
                        key=f"selectbox_tipo_{pergunta_atual['ordem']}"
                    )



                    # ----------------------------------------------
                    # CAMPOS DINÂMICOS
                    # ----------------------------------------------
                    texto = ""
                    opcoes = []

                    label_texto = "Texto da pergunta"

                    if tipo == "Título":
                        label_texto = "Texto do título"
                    elif tipo == "Subtítulo":
                        label_texto = "Texto do subtítulo"
                    elif tipo == "Parágrafo":
                        label_texto = "Texto do parágrafo"


                    if tipo in [
                        "Resposta curta",
                        "Resposta longa",
                        "Número",
                        "Upload de arquivos",
                        "Título",
                        "Subtítulo"
                    ]:
                        texto = st.text_input(
                            label_texto,
                            value=pergunta_atual.get("pergunta", "")
                        )



                    # if tipo in [
                    #     "Resposta curta",
                    #     "Resposta longa",
                    #     "Número",
                    #     "Título",
                    #     "Subtítulo"
                    # ]:
                    #     texto = st.text_input(
                    #         label_texto,
                    #         value=pergunta_atual.get("pergunta", "")
                    #     )

                    elif tipo == "Parágrafo":
                        texto = st.text_area(
                            label_texto,
                            value=pergunta_atual.get("pergunta", "")
                        )

                    elif tipo in ["Múltipla escolha", "Escolha única"]:
                        texto = st.text_input(
                            "Texto da pergunta",
                            value=pergunta_atual.get("pergunta", "")
                        )

                        opcoes = st.text_area(
                            "Opções (uma por linha)",
                            value="\n".join(pergunta_atual.get("opcoes", []))
                        ).split("\n")

                    # if tipo == "Linha divisória":
                    #     st.write("Este tipo não possui texto editável.")

                    st.write("")

                    # ----------------------------------------------
                    # BOTÕES DE AÇÃO
                    # ----------------------------------------------
                    with st.container(horizontal=True, horizontal_alignment="left"):

                        # -------- SALVAR --------
                        if st.button("Salvar alterações", type="primary", icon=":material/save:"):

                            # Validações
                            if not texto.strip():
                            # if tipo != "Linha divisória" and not texto.strip():
                                st.warning("O texto não pode ficar vazio.")
                            elif tipo in ["Múltipla escolha", "Escolha única"] and not any(o.strip() for o in opcoes):
                                st.warning("Informe pelo menos uma opção.")
                            else:
                                mapa_tipo = {
                                    "Resposta curta": "texto_curto",
                                    "Resposta longa": "texto_longo",
                                    "Número": "numero",
                                    "Múltipla escolha": "multipla_escolha",
                                    "Escolha única": "escolha_unica",
                                    "Título": "titulo",
                                    "Subtítulo": "subtitulo",
                                    "Upload de arquivos": "upload_arquivo",
                                    "Parágrafo": "paragrafo"
                                }

                                nova = {
                                    "tipo": mapa_tipo[tipo],
                                    "ordem": pergunta_atual["ordem"]
                                }
                                
                                nova["pergunta"] = texto.strip()
                                
                                # if mapa_tipo[tipo] != "divisoria":
                                #     nova["pergunta"] = texto.strip()
                                # else:
                                #     nova["pergunta"] = "Divisória"

                                if mapa_tipo[tipo] in ["multipla_escolha", "escolha_unica"]:
                                    nova["opcoes"] = [o.strip() for o in opcoes if o.strip()]

                                perguntas_atualizadas = [
                                    nova if p == pergunta_atual else p
                                    for p in perguntas
                                ]

                                col_editais.update_one(
                                    {"codigo_edital": edital_selecionado_perguntas},
                                    {"$set": {"perguntas_relatorio": perguntas_atualizadas}}
                                )

                                st.success(":material/check: Pergunta atualizada!")
                                time.sleep(3)
                                st.rerun()

                        # -------- EXCLUIR --------
                        if st.button("Excluir pergunta", icon=":material/delete:"):
                            confirmar_exclusao_pergunta(
                                pergunta_atual=pergunta_atual,
                                perguntas=perguntas,
                                edital_selecionado=edital_selecionado_perguntas
                            )



        # ======================================================
        # ABA 4 — REORDENAR
        # ======================================================

        with aba_reordenar:

            if not perguntas:
                st.caption("Nenhuma pergunta para ordenar.")
            else:
                st.write('')
                st.write('**Arraste para reordenar as perguntas**')

                estilo = """
                    .sortable-component {
                        background-color:white;
                        font-size: 16px;
                        counter-reset: item;
                    }
                    .sortable-item {
                        background-color: white;
                        color: black;
                    }
                """

                nova_ordem = sort_items(
                    items=[p["pergunta"] for p in perguntas],
                    direction="vertical",
                    custom_style=estilo
                )

                if st.button("Salvar nova ordem", type="primary", icon=":material/save:"):

                    novas_perguntas = []

                    for i, texto in enumerate(nova_ordem, start=1):
                        pergunta = next(p for p in perguntas if p["pergunta"] == texto)
                        pergunta["ordem"] = i
                        novas_perguntas.append(pergunta)

                    col_editais.update_one(
                        {"codigo_edital": edital_selecionado_perguntas},
                        {"$set": {"perguntas_relatorio": novas_perguntas}}
                    )

                    st.success(":material/check: Ordem atualizada com sucesso!")
                    time.sleep(3)
                    st.rerun()





# ==========================================================
# ABA PESQUISAS
# ==========================================================

with aba_pesquisas:

    # ------------------------------------------------------
    # TÍTULO DA ABA
    # ------------------------------------------------------
    st.subheader("Pesquisas / Ferramentas de Monitoramento")
    st.write("")

    # ------------------------------------------------------
    # SELEÇÃO DO EDITAL
    # ------------------------------------------------------

    lista_editais = df_editais["codigo_edital"].unique().tolist()

    edital_selecionado_pesquisas = st.selectbox(
        "Selecione o Edital:",
        options=[""] + lista_editais,
        index=0,
        key="edital_selecionado_pesquisas",
        width=300
    )


    # Caso nenhum edital seja selecionado
    if not edital_selecionado_pesquisas:
        st.caption("Selecione um edital para continuar.")

    else:

        st.write('')

        # ------------------------------------------------------
        # BUSCA DO EDITAL NO BANCO
        # ------------------------------------------------------

        edital_pesquisas = col_editais.find_one(
            {"codigo_edital": edital_selecionado_pesquisas}
        )

        pesquisas = sorted(
            edital_pesquisas.get("pesquisas_relatorio", []),
            key=lambda x: x.get("nome_pesquisa", "")
        )

        # ======================================================
        # ABAS INTERNAS
        # ======================================================

        aba_visualizar_pesquisas, aba_nova_pesquisa, aba_editar_pesquisa = st.tabs([
            "Pesquisas cadastradas",
            "Nova pesquisa",
            "Editar / Excluir"
        ])




        # ======================================================
        # ABA 1 — VISUALIZAR
        # ======================================================


        with aba_visualizar_pesquisas:

            if not pesquisas:
                st.caption("Nenhuma pesquisa cadastrada.")
            else:
                for idx, pesquisa in enumerate(pesquisas, start=1):

                    icone = ":material/attach_file:" if pesquisa.get("upload_arquivo") else ""

                    st.markdown(
                        f"**{idx}. {pesquisa.get('nome_pesquisa')}** {icone}"
                    )




        # ======================================================
        # ABA 2 — NOVA PESQUISA
        # ======================================================

        with aba_nova_pesquisa:

            with st.form("form_nova_pesquisa", border=False, clear_on_submit=True):

                # ----------------------------------------------
                # CAMPO: NOME DA PESQUISA
                # ----------------------------------------------
                nome_pesquisa = st.text_input(
                    "Nome da pesquisa",
                    help=(
                        'Para inserir um link use "nome_da_pesquisa - \\[texto_do_link\\](url_do_link)". '
                        'Exemplo: "Pesquisa de monitoramento final - \\[clique aqui para acessar o formulário\\](https://docs.google.com/forms)"'
                    )
                )

                # ----------------------------------------------
                # CAMPO: UPLOAD DE ARQUIVO
                # ----------------------------------------------
                upload_arquivo = st.checkbox(
                    "Haverá upload de arquivo?",
                    value=False
                )

                st.write("")

                # ----------------------------------------------
                # BOTÃO SALVAR
                # ----------------------------------------------
                salvar_pesquisa = st.form_submit_button(
                    "Adicionar pesquisa",
                    type="primary",
                    icon=":material/save:",
                    key="btn_salvar_pesquisa"
                )

                # ----------------------------------------------
                # AÇÃO AO SALVAR
                # ----------------------------------------------
                if salvar_pesquisa:

                    if not nome_pesquisa.strip():
                        st.warning("O nome da pesquisa não pode ficar vazio.")
                    else:
                        nova_pesquisa = {
                            "id": str(ObjectId()),
                            "nome_pesquisa": nome_pesquisa.strip(),
                            "upload_arquivo": upload_arquivo
                        }

                        col_editais.update_one(
                            {"codigo_edital": edital_selecionado_pesquisas},
                            {
                                "$push": {
                                    "pesquisas_relatorio": nova_pesquisa
                                }
                            }
                        )

                        st.success(":material/check: Pesquisa cadastrada com sucesso!")
                        time.sleep(3)
                        st.rerun()









        # ======================================================
        # ABA 3 — EDITAR / EXCLUIR
        # ======================================================

        with aba_editar_pesquisa:

            if not pesquisas:
                st.caption("Nenhuma pesquisa cadastrada.")

            else:
                st.markdown("##### Selecione uma pesquisa para EDITAR ou EXCLUIR")

                # ----------------------------------------------
                # MAPA DE PESQUISAS
                # ----------------------------------------------
                mapa_pesquisas = {
                    p["nome_pesquisa"]: p for p in pesquisas
                }

                selecionada = st.selectbox(
                    "",
                    list(mapa_pesquisas.keys())
                )

                # Pesquisa selecionada
                pesquisa_atual = mapa_pesquisas[selecionada]

                st.divider()

                # ----------------------------------------------
                # CAMPOS DE EDIÇÃO
                # ----------------------------------------------

                novo_nome = st.text_input(
                    "Nome da pesquisa",
                    value=pesquisa_atual.get("nome_pesquisa", "")
                )

                upload_arquivo = st.checkbox(
                    "Haverá upload de arquivo?",
                    value=pesquisa_atual.get("upload_arquivo", False)
                )

                st.write("")

                # ----------------------------------------------
                # BOTÕES DE AÇÃO
                # ----------------------------------------------
                with st.container(horizontal=True, horizontal_alignment="left"):

                    # -------- SALVAR --------
                    if st.button(
                        "Salvar alterações",
                        type="primary",
                        icon=":material/save:",
                        key="btn_editar_pesquisa"
                    ):

                        if not novo_nome.strip():
                            st.warning("O nome da pesquisa não pode ficar vazio.")
                        else:
                            pesquisas_atualizadas = [
                                {
                                    **p,
                                    "nome_pesquisa": novo_nome.strip(),
                                    "upload_arquivo": upload_arquivo
                                } if p["id"] == pesquisa_atual["id"] else p
                                for p in pesquisas
                            ]

                            col_editais.update_one(
                                {"codigo_edital": edital_selecionado_pesquisas},
                                {"$set": {"pesquisas_relatorio": pesquisas_atualizadas}}
                            )

                            st.success(":material/check: Pesquisa atualizada com sucesso!")
                            time.sleep(3)
                            st.rerun()

                    # -------- EXCLUIR --------
                    if st.button(
                        "Excluir pesquisa",
                        icon=":material/delete:",
                        key="btn_excluir_pesquisa"
                    ):

                        pesquisas_atualizadas = [
                            p for p in pesquisas
                            if p["id"] != pesquisa_atual["id"]
                        ]

                        col_editais.update_one(
                            {"codigo_edital": edital_selecionado_pesquisas},
                            {"$set": {"pesquisas_relatorio": pesquisas_atualizadas}}
                        )

                        st.success(":material/check: Pesquisa excluída com sucesso!")
                        time.sleep(3)
                        st.rerun()








# ==========================================================
# ABA DIREÇÕES ESTRATÉGICAS (POR EDITAL)
# ==========================================================

with aba_direcoes:

    st.subheader("Direções Estratégicas")
    st.write("")

    # ======================================================
    # SELEÇÃO DO EDITAL (PRIMEIRO PASSO)
    # ======================================================

    lista_editais = df_editais["codigo_edital"].unique().tolist()

    edital_selecionado_direcoes = st.selectbox(
        "Selecione o Edital:",
        options=[""] + lista_editais,
        index=0,
        key="edital_selecionado_direcoes",
        width=300
    )







    if not edital_selecionado_direcoes:
        st.caption("Selecione um edital para continuar.")

    else:

        st.write("")

        # # ======================================================
        # # RADIO DE MODO (APÓS SELECIONAR EDITAL)
        # # ======================================================

        # modo_gestao = st.radio(
        #     "Gerenciar:",
        #     options=["Direções estratégicas", "Subcategorias"],
        #     horizontal=True,
        #     index=0
        # )

        # st.write("")

        # # ======================================================
        # # BUSCA DO EDITAL NO BANCO
        # # ======================================================

        # edital_direcoes = col_editais.find_one(
        #     {"codigo_edital": edital_selecionado_direcoes}
        # )

        # direcoes = sorted(
        #     edital_direcoes.get("direcoes_estrategicas", []),
        #     key=lambda x: x.get("tema", "")
        # )

        # # 🔽 AQUI CONTINUA TODO O RESTO DA LÓGICA


















    # # Se nenhum edital for selecionado, para execução
    # if not edital_selecionado_direcoes:
    #     st.caption("Selecione um edital para continuar.")
    #     st.stop()

    # st.write("")

        # ======================================================
        # RADIO DE MODO (APÓS SELECIONAR EDITAL)
        # ======================================================

        modo_gestao = st.radio(
            "Gerenciar:",
            options=["Direções estratégicas", "Subcategorias"],
            horizontal=True,
            index=0
        )

        st.write("")

        # ======================================================
        # BUSCA DO EDITAL NO BANCO
        # ======================================================

        edital_direcoes = col_editais.find_one(
            {"codigo_edital": edital_selecionado_direcoes}
        )

        direcoes = sorted(
            edital_direcoes.get("direcoes_estrategicas", []),
            key=lambda x: x.get("tema", "")
        )

        # ======================================================
        # ======================================================
        # MODO 1 — DIREÇÕES ESTRATÉGICAS
        # ======================================================
        # ======================================================

        if modo_gestao == "Direções estratégicas":

            aba_visualizar_direcoes, aba_nova_direcao, aba_editar_direcao = st.tabs([
                "Direções cadastradas",
                "Nova direção estratégica",
                "Editar / Excluir"
            ])

            # -------------------------
            # VISUALIZAR
            # -------------------------

            with aba_visualizar_direcoes:

                if not direcoes:
                    st.caption("Nenhuma direção estratégica cadastrada.")
                else:
                    for idx, direcao in enumerate(direcoes, start=1):
                        st.markdown(f"**{idx}. {direcao.get('tema')}**")

            # -------------------------
            # NOVA DIREÇÃO
            # -------------------------

            with aba_nova_direcao:

                with st.form("form_nova_direcao", border=False, clear_on_submit=True):

                    tema_direcao = st.text_input("Direção estratégica")

                    st.write("")

                    salvar_direcao = st.form_submit_button(
                        "Adicionar direção estratégica",
                        type="primary",
                        icon=":material/save:"
                    )

                    if salvar_direcao:

                        if not tema_direcao.strip():
                            st.warning("A direção estratégica não pode ficar vazia.")
                        else:

                            nova_direcao = {
                                "id": str(ObjectId()),
                                "tema": tema_direcao.strip(),
                                "subcategorias": []
                            }

                            col_editais.update_one(
                                {"codigo_edital": edital_selecionado_direcoes},
                                {"$push": {"direcoes_estrategicas": nova_direcao}}
                            )

                            st.success("Direção estratégica cadastrada com sucesso!", icon=":material/check:")
                            time.sleep(2)
                            st.rerun()

            # -------------------------
            # EDITAR / EXCLUIR
            # -------------------------

            with aba_editar_direcao:

                if not direcoes:
                    st.caption("Nenhuma direção estratégica cadastrada.")
                else:

                    mapa_direcoes = {d["tema"]: d for d in direcoes}

                    selecionada = st.selectbox(
                        "Selecione a Direção estratégica para editar ou excluir:",
                        list(mapa_direcoes.keys())
                    )

                    direcao_atual = mapa_direcoes[selecionada]

                    st.write('')
                    novo_tema = st.text_input(
                        "Editar:",
                        value=direcao_atual.get("tema", "")
                    )

                    st.write("")




                    # --------------------------------------------------
                    # CONTROLE DE ESTADO DA CONFIRMAÇÃO
                    # --------------------------------------------------

                    confirm_key = f"confirmar_exclusao_{direcao_atual['id']}"

                    if confirm_key not in st.session_state:
                        st.session_state[confirm_key] = False


                    with st.container(horizontal=True):

                        # --------------------------------------------------
                        # BOTÃO SALVAR
                        # --------------------------------------------------

                        if st.button(
                            "Salvar alterações",
                            type="primary",
                            icon=":material/save:",
                            width=250
                        ):

                            if not novo_tema.strip():
                                st.warning("A direção estratégica não pode ficar vazia.")
                            else:

                                direcoes_atualizadas = [
                                    {
                                        **d,
                                        "tema": novo_tema.strip()
                                    } if d["id"] == direcao_atual["id"] else d
                                    for d in direcoes
                                ]

                                col_editais.update_one(
                                    {"codigo_edital": edital_selecionado_direcoes},
                                    {"$set": {"direcoes_estrategicas": direcoes_atualizadas}}
                                )

                                st.success("Direção estratégica atualizada com sucesso!", icon=":material/check:")
                                time.sleep(3)
                                st.rerun()

                        # --------------------------------------------------
                        # BOTÃO EXCLUIR (PASSO 1)
                        # --------------------------------------------------

                        if st.button(
                            "Excluir direção",
                            icon=":material/delete:",
                            width=250
                        ):
                            st.session_state[confirm_key] = True


                    # --------------------------------------------------
                    # CONFIRMAÇÃO (PASSO 2)
                    # --------------------------------------------------

                    if st.session_state[confirm_key]:

                        st.warning(
                            f"Tem certeza que deseja excluir a direção estratégica:\n\n**{direcao_atual.get('tema')}** ?"
                        )

                        with st.container(horizontal=True):

                            if st.button(
                                "Confirmar exclusão",
                                type="primary",
                                icon=":material/delete:",
                                key=f"confirmar_btn_{direcao_atual['id']}"
                            ):

                                direcoes_atualizadas = [
                                    d for d in direcoes
                                    if d["id"] != direcao_atual["id"]
                                ]

                                col_editais.update_one(
                                    {"codigo_edital": edital_selecionado_direcoes},
                                    {"$set": {"direcoes_estrategicas": direcoes_atualizadas}}
                                )

                                st.session_state[confirm_key] = False

                                st.success("Direção estratégica excluída com sucesso!", icon=":material/check:")
                                time.sleep(2)
                                st.rerun()

                            if st.button(
                                "Cancelar",
                                key=f"cancelar_btn_{direcao_atual['id']}"
                            ):
                                st.session_state[confirm_key] = False
                                time.sleep(3)
                                st.rerun()






        # ======================================================
        # ======================================================
        # MODO 2 — SUBCATEGORIAS
        # ======================================================
        # ======================================================

        if modo_gestao == "Subcategorias":

            if not direcoes:
                st.warning("Nenhuma direção estratégica cadastrada.")
                st.stop()

            # --------------------------------------------------
            # SELECIONAR DIREÇÃO
            # --------------------------------------------------

            mapa_direcoes = {d["tema"]: d for d in direcoes}

            direcao_selecionada_nome = st.selectbox(
                "Selecione a Direção Estratégica:",
                list(mapa_direcoes.keys())
            )

            direcao_selecionada = mapa_direcoes[direcao_selecionada_nome]

            st.write("")

            # --------------------------------------------------
            # CARREGAR SUBCATEGORIAS EXISTENTES
            # --------------------------------------------------

            subcategorias_existentes = direcao_selecionada.get("subcategorias", [])

            if subcategorias_existentes:
                df_sub = pd.DataFrame(subcategorias_existentes)
                df_sub = df_sub.rename(columns={
                    "nome_subcategoria": "Subcategorias da direção estratégica"
                })
            else:
                df_sub = pd.DataFrame({
                    "Subcategorias da direção estratégica": pd.Series(dtype="str")
                })

            # --------------------------------------------------
            # DATA EDITOR
            # --------------------------------------------------

            df_editado = st.data_editor(
                df_sub,
                num_rows="dynamic",
                hide_index=True
            )

            st.write("")

            # --------------------------------------------------
            # BOTÃO SALVAR
            # --------------------------------------------------

            if st.button(
                "Salvar",
                type="primary",
                icon=":material/save:",
                width=200
            ):

                # Normalização
                df_editado = df_editado.dropna()
                df_editado["Subcategorias da direção estratégica"] = (
                    df_editado["Subcategorias da direção estratégica"]
                    .astype(str)
                    .str.strip()
                )

                df_editado = df_editado[
                    df_editado["Subcategorias da direção estratégica"] != ""
                ]

                nova_lista_subcategorias = [
                    {"nome_subcategoria": row}
                    for row in df_editado["Subcategorias da direção estratégica"].tolist()
                ]

                # Atualiza apenas a direção selecionada
                direcoes_atualizadas = [
                    {
                        **d,
                        "subcategorias": nova_lista_subcategorias
                    } if d["id"] == direcao_selecionada["id"] else d
                    for d in direcoes
                ]

                col_editais.update_one(
                    {"codigo_edital": edital_selecionado_direcoes},
                    {"$set": {"direcoes_estrategicas": direcoes_atualizadas}}
                )

                st.success("Subcategorias atualizadas com sucesso!", icon=":material/check:")
                time.sleep(3)
                st.rerun()










# ==========================================================
# ABA INDICADORES (POR EDITAL)
# ==========================================================

with aba_indicadores:

    st.subheader("Indicadores de portifólio")
    st.write("")

    # ======================================================
    # SELEÇÃO DO EDITAL
    # ======================================================

    lista_editais = df_editais["codigo_edital"].unique().tolist()

    edital_selecionado_indicadores = st.selectbox(
        "Selecione o Edital:",
        options=[""] + lista_editais,
        index=0,
        key="edital_selecionado_indicadores",
        width=300
    )

    if not edital_selecionado_indicadores:
        st.caption("Selecione um edital para continuar.")

    else:

        st.write("")

        # ======================================================
        # BUSCA DO EDITAL
        # ======================================================

        edital_doc = col_editais.find_one(
            {"codigo_edital": edital_selecionado_indicadores}
        )

        indicadores = sorted(
            edital_doc.get("indicadores", []),
            key=lambda x: x.get("codigo_indicador", "")
        )

        df_indicadores = pd.DataFrame(indicadores)

        editar_indicadores = st.toggle(
            "Editar",
            key="editar_indicadores_por_edital"
        )

        st.write("")

        # ======================================================
        # MODO VISUALIZAÇÃO
        # ======================================================

        if not editar_indicadores:

            if df_indicadores.empty:
                st.caption("Nenhum indicador cadastrado para este edital.")
            else:

                df_visualizacao = (
                    df_indicadores[["codigo_indicador", "indicador"]]
                    .rename(columns={
                        "codigo_indicador": "Código",
                        "indicador": "Indicador"
                    })
                    .sort_values("Código")
                    .reset_index(drop=True)
                )

                st.dataframe(
                    df_visualizacao,
                    hide_index=True,
                    height="content",
                    column_config={
                        "Código": st.column_config.Column(
                            width=1  
                        ),
                        "Indicador": st.column_config.Column(
                            width=1000
                        )
                    }
                )                

        # ======================================================
        # MODO EDIÇÃO
        # ======================================================

        else:

            st.write("Edite, adicione e exclua linhas.")

            if df_indicadores.empty:
                df_editor = pd.DataFrame(
                    {
                        "codigo_indicador": pd.Series(dtype="str"),
                        "indicador": pd.Series(dtype="str"),
                    }
                )
            else:
                df_editor = df_indicadores[
                    ["codigo_indicador", "indicador"]
                ].copy()

            df_editado = st.data_editor(
                df_editor,
                num_rows="dynamic",
                hide_index=True,
                key="editor_indicadores_por_edital",
            )

            if st.button(
                "Salvar alterações",
                icon=":material/save:",
                type="primary",
                key="salvar_indicadores_por_edital"
            ):

                if (
                    "codigo_indicador" not in df_editado.columns or
                    "indicador" not in df_editado.columns
                ):
                    st.error("Dados inválidos.")
                    st.stop()

                # --------------------------------------------------
                # NORMALIZA
                # --------------------------------------------------

                df_editado["codigo_indicador"] = (
                    df_editado["codigo_indicador"]
                    .astype(str)
                    .str.strip()
                )

                df_editado["indicador"] = (
                    df_editado["indicador"]
                    .astype(str)
                    .str.strip()
                )

                # Remove linhas vazias
                df_editado = df_editado[
                    (df_editado["codigo_indicador"] != "") &
                    (df_editado["indicador"] != "")
                ]

                if df_editado.empty:
                    st.warning("Nenhum indicador informado.")
                    st.stop()

                # --------------------------------------------------
                # VALIDA DUPLICIDADE DE CÓDIGO
                # --------------------------------------------------

                lista_codigos = df_editado["codigo_indicador"].tolist()

                duplicados = {
                    x for x in lista_codigos if lista_codigos.count(x) > 1
                }

                if duplicados:
                    st.error(
                        f"Existem códigos duplicados: {', '.join(duplicados)}"
                    )
                    st.stop()

                # Ordena por código
                df_editado = df_editado.sort_values("codigo_indicador")

                # --------------------------------------------------
                # MONTA ESTRUTURA FINAL
                # --------------------------------------------------

                estrutura_final = df_editado.to_dict(orient="records")

                # --------------------------------------------------
                # ATUALIZA EDITAL
                # --------------------------------------------------

                col_editais.update_one(
                    {"codigo_edital": edital_selecionado_indicadores},
                    {"$set": {"indicadores": estrutura_final}}
                )

                st.success("Indicadores atualizados com sucesso!", icon=":material/check:")
                time.sleep(3)
                st.rerun()








# ==========================================================
# ABA BENEFICIÁRIOS
# ==========================================================


with aba_beneficiarios:

    st.subheader("Beneficiários")
    st.write('')

    # 1) Carrega documentos da coleção (ordenados)
    dados_publicos = list(
        col_publicos.find({}, {"publico": 1}).sort("publico", 1)
    )

    df_publicos = pd.DataFrame(dados_publicos)

    # Converte ObjectId para string
    if "_id" in df_publicos.columns:
        df_publicos["_id"] = df_publicos["_id"].astype(str)
    else:
        df_publicos["_id"] = ""

    editar_publicos = st.toggle("Editar", key="editar_publicos")
    st.write('')

    # -------------------------
    # MODO VISUALIZAÇÃO
    # -------------------------
    if not editar_publicos:
        if df_publicos.empty:
            st.caption("Nenhum tipo de beneficiário cadastrado.")
        else:
            st.dataframe(
                df_publicos[["publico"]].sort_values("publico"),
                hide_index=True,
                width=500
            )


    # -------------------------
    # MODO EDIÇÃO
    # -------------------------
    else:
        st.write("Edite, adicione e exclua linhas.")

        if df_publicos.empty:
            st.warning("Ainda não há tipos de beneficiário cadastrados. Você pode adicionar novos abaixo.")

            df_editor = pd.DataFrame(
                {"publico": pd.Series(dtype="str")}
            )
        else:
            df_editor = df_publicos[["publico"]].copy()
            df_editor["publico"] = df_editor["publico"].astype(str)

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_publicos",
            width=500
        )

        if st.button("Salvar alterações", icon=":material/save:", type="primary"):

            if "publico" not in df_editado.columns:
                st.error("Nenhum dado válido para salvar.")
                st.stop()

            # Normaliza e remove vazios
            df_editado["publico"] = df_editado["publico"].astype(str).str.strip()
            df_editado = df_editado[df_editado["publico"] != ""]

            if df_editado.empty:
                st.warning("Nenhum público informado.")
                st.stop()

            df_editado = df_editado.sort_values("publico")

            # ===========================
            # VERIFICAÇÃO DE DUPLICADOS
            # ===========================
            lista_editada = df_editado["publico"].tolist()
            duplicados_local = {
                x for x in lista_editada if lista_editada.count(x) > 1
            }

            if duplicados_local:
                st.error(
                    f"Existem valores duplicados na lista: {', '.join(duplicados_local)}"
                )
                st.stop()

            valores_orig = (
                set(df_publicos["publico"])
                if "publico" in df_publicos.columns
                else set()
            )
            valores_editados = set(lista_editada)

            # 1) Removidos
            for publico in valores_orig - valores_editados:
                col_publicos.delete_one({"publico": publico})

            # 2) Novos
            for publico in valores_editados - valores_orig:
                if col_publicos.find_one({"publico": publico}):
                    st.error(f"O valor '{publico}' já existe e não será inserido.")
                    st.stop()
                col_publicos.insert_one({"publico": publico})

            st.success("Beneficiários atualizados com sucesso!")
            time.sleep(3)
            st.rerun()











# ==========================================================
# ABA TIPOS DE BENEFÍCIO
# ==========================================================


with aba_beneficios:

    st.subheader("Tipos de benefício")
    st.write('')

    # 1) Carrega documentos da coleção (ordenados)
    dados_beneficios = list(
        col_beneficios.find({}, {"beneficio": 1}).sort("beneficio", 1)
    )

    df_beneficios = pd.DataFrame(dados_beneficios)

    # Converte ObjectId para string
    if "_id" in df_beneficios.columns:
        df_beneficios["_id"] = df_beneficios["_id"].astype(str)
    else:
        df_beneficios["_id"] = ""

    editar_beneficios = st.toggle("Editar", key="editar_beneficios")
    st.write('')

    # -------------------------
    # MODO VISUALIZAÇÃO
    # -------------------------
    if not editar_beneficios:
        if df_beneficios.empty:
            st.caption("Nenhum tipo de benefício cadastrado.")
        else:
            st.dataframe(
                df_beneficios[["beneficio"]].sort_values("beneficio"),
                hide_index=True,
                width=500
            )

    # -------------------------
    # MODO EDIÇÃO
    # -------------------------
    else:
        st.write("Edite, adicione e exclua linhas.")

        if df_beneficios.empty:
            
            df_editor = pd.DataFrame(
                {"beneficio": pd.Series(dtype="str")}
            )
        else:
            df_editor = df_beneficios[["beneficio"]].copy()
            df_editor["beneficio"] = df_editor["beneficio"].astype(str)

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_beneficios",
            width=500
        )

        if st.button("Salvar alterações", icon=":material/save:", type="primary"):

            if "beneficio" not in df_editado.columns:
                st.error("Nenhum dado válido para salvar.")
                st.stop()

            # -------------------------
            # NORMALIZAÇÃO
            # -------------------------
            df_editado["beneficio"] = (
                df_editado["beneficio"]
                .astype(str)
                .str.strip()
            )
            df_editado = df_editado[df_editado["beneficio"] != ""]

            if df_editado.empty:
                st.warning("Nenhum tipo de benefício informado.")
                st.stop()

            df_editado = df_editado.sort_values("beneficio")

            # -------------------------
            # VERIFICA DUPLICADOS
            # -------------------------
            lista_editada = df_editado["beneficio"].tolist()
            duplicados_local = {
                x for x in lista_editada if lista_editada.count(x) > 1
            }

            if duplicados_local:
                st.error(
                    f"Existem valores duplicados na lista: "
                    f"{', '.join(duplicados_local)}"
                )
                st.stop()

            valores_orig = (
                set(df_beneficios["beneficio"])
                if "beneficio" in df_beneficios.columns
                else set()
            )
            valores_editados = set(lista_editada)

            # -------------------------
            # REMOVIDOS
            # -------------------------
            for beneficio in valores_orig - valores_editados:
                col_beneficios.delete_one({"beneficio": beneficio})

            # -------------------------
            # NOVOS
            # -------------------------
            for beneficio in valores_editados - valores_orig:
                if col_beneficios.find_one({"beneficio": beneficio}):
                    st.error(
                        f"O valor '{beneficio}' já existe "
                        "e não será inserido."
                    )
                    st.stop()

                col_beneficios.insert_one({"beneficio": beneficio})

            st.success("Tipos de benefício atualizados com sucesso!")
            time.sleep(3)
            st.rerun()







# ==========================================================
# ABA CATEGORIAS DE DESPESA
# ==========================================================

with aba_categorias_despesa:

    st.subheader("Categorias de despesa")
    st.write("")

    # 1) Carrega documentos da coleção (ordenados)
    dados_categorias = list(
        col_categorias_despesa.find({}, {"categoria": 1}).sort("categoria", 1)
    )

    df_categorias = pd.DataFrame(dados_categorias)

    # Converte ObjectId para string
    if "_id" in df_categorias.columns:
        df_categorias["_id"] = df_categorias["_id"].astype(str)
    else:
        df_categorias["_id"] = ""

    editar_categorias = st.toggle("Editar", key="editar_categorias_despesa")
    st.write("")

    # -------------------------
    # MODO VISUALIZAÇÃO
    # -------------------------
    if not editar_categorias:

        if df_categorias.empty:
            st.caption("Nenhuma categoria de despesa cadastrada.")
        else:
            df_tabela = (
                df_categorias[["categoria"]]
                .sort_values("categoria")
                .reset_index(drop=True)
                .rename(columns={"categoria": "Categoria de despesa"})
            )

            st.dataframe(df_tabela,
                         hide_index=True,
                         width=500)

    # -------------------------
    # MODO EDIÇÃO
    # -------------------------
    else:

        st.write("Edite, adicione e exclua linhas.")

        if df_categorias.empty:
           
            df_editor = pd.DataFrame(
                {"categoria": pd.Series(dtype="str")}
            )
        else:
            df_editor = df_categorias[["categoria"]].copy()
            df_editor["categoria"] = df_editor["categoria"].astype(str)

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_categorias_despesa",
            width=500
        )

        if st.button(
            "Salvar alterações",
            icon=":material/save:",
            type="primary",
            key="salvar_categorias_despesa"
        ):

            if "categoria" not in df_editado.columns:
                st.error("Nenhum dado válido para salvar.")
                st.stop()

            # Normaliza e remove vazios
            df_editado["categoria"] = (
                df_editado["categoria"]
                .astype(str)
                .str.strip()
            )
            df_editado = df_editado[df_editado["categoria"] != ""]

            if df_editado.empty:
                st.warning("Nenhuma categoria informada.")
                st.stop()

            df_editado = df_editado.sort_values("categoria")

            # ===========================
            # VERIFICAÇÃO DE DUPLICADOS
            # ===========================
            lista_editada = df_editado["categoria"].tolist()
            duplicados_local = {
                x for x in lista_editada if lista_editada.count(x) > 1
            }

            if duplicados_local:
                st.error(
                    "Existem categorias duplicadas: "
                    f"{', '.join(duplicados_local)}"
                )
                st.stop()

            valores_orig = (
                set(df_categorias["categoria"])
                if "categoria" in df_categorias.columns
                else set()
            )
            valores_editados = set(lista_editada)

            # 1) Removidos
            for categoria in valores_orig - valores_editados:
                col_categorias_despesa.delete_one(
                    {"categoria": categoria}
                )

            # 2) Novos
            for categoria in valores_editados - valores_orig:
                if col_categorias_despesa.find_one(
                    {"categoria": categoria}
                ):
                    st.error(
                        f"A categoria '{categoria}' já existe "
                        "e não será inserida."
                    )
                    st.stop()

                col_categorias_despesa.insert_one(
                    {"categoria": categoria}
                )

            st.success("Categorias de despesa atualizadas com sucesso!")
            time.sleep(3)
            st.rerun()







# ==========================================================
# ABA CORREDORES
# ==========================================================

with aba_corredores:

    st.subheader("Corredores")
    st.write("")

    # -----------------------------------
    # Carregar dados da coleção
    # -----------------------------------
    dados_corredores = list(
        col_corredores.find(
            {},
            {"id_corredor": 1, "nome_corredor": 1}
        ).sort("nome_corredor", 1)
    )

    df_corredores = pd.DataFrame(dados_corredores)

    # Garante colunas
    if df_corredores.empty:
        df_corredores = pd.DataFrame(
            columns=["id_corredor", "nome_corredor"]
        )

    # Remove _id do Mongo (não será usado)
    if "_id" in df_corredores.columns:
        df_corredores = df_corredores.drop(columns=["_id"])

    editar_corredores = st.toggle(
        "Editar",
        key="editar_corredores"
    )

    st.write("")

    # ==================================================
    # MODO VISUALIZAÇÃO
    # ==================================================
    if not editar_corredores:

        if df_corredores.empty:
            st.caption("Nenhum corredor cadastrado.")
        else:

            df_tabela = (
                df_corredores
                .sort_values("nome_corredor")
                .reset_index(drop=True)
                .rename(columns={
                    "id_corredor": "ID do corredor",
                    "nome_corredor": "Nome do corredor"
                })
            )

            st.dataframe(df_tabela,
                         hide_index=True, 
                         )

    # ==================================================
    # MODO EDIÇÃO
    # ==================================================
    else:

        st.write("Edite, adicione e exclua corredores.")

        df_editor = df_corredores.copy()

        # Normalização defensiva
        df_editor["id_corredor"] = (
            df_editor["id_corredor"]
            .astype(str)
            .str.strip()
        )
        df_editor["nome_corredor"] = (
            df_editor["nome_corredor"]
            .astype(str)
            .str.strip()
        )

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_corredores",
            # width=700,
            column_config={
                "id_corredor": st.column_config.TextColumn(
                    "ID do corredor",
                    required=True,
                    help="Identificador único do corredor (texto livre)",
                    width=20
                ),
                "nome_corredor": st.column_config.TextColumn(
                    "Nome do corredor",
                    required=True,
                    width=900
                ),
            }
        )

        if st.button(
            "Salvar alterações",
            icon=":material/save:",
            type="primary"
        ):

            # Remove linhas vazias
            df_salvar = df_editado.copy()

            df_salvar["id_corredor"] = (
                df_salvar["id_corredor"]
                .astype(str)
                .str.strip()
            )
            df_salvar["nome_corredor"] = (
                df_salvar["nome_corredor"]
                .astype(str)
                .str.strip()
            )

            df_salvar = df_salvar[
                (df_salvar["id_corredor"] != "")
                & (df_salvar["nome_corredor"] != "")
            ]

            if df_salvar.empty:
                st.warning("Nenhum corredor válido para salvar.")
                st.stop()

            # ===========================
            # VALIDAÇÃO DE DUPLICADOS
            # ===========================
            duplicados_id = df_salvar[
                df_salvar["id_corredor"].duplicated()
            ]["id_corredor"].tolist()

            duplicados_nome = df_salvar[
                df_salvar["nome_corredor"].duplicated()
            ]["nome_corredor"].tolist()

            if duplicados_id:
                st.error(
                    "IDs de corredor duplicados: "
                    f"{', '.join(set(duplicados_id))}"
                )
                st.stop()

            if duplicados_nome:
                st.error(
                    "Nomes de corredor duplicados: "
                    f"{', '.join(set(duplicados_nome))}"
                )
                st.stop()

            # ===========================
            # SINCRONIZAÇÃO COM O BANCO
            # ===========================
            col_corredores.delete_many({})

            col_corredores.insert_many(
                df_salvar.to_dict(orient="records")
            )

            st.success("Corredores atualizados com sucesso!", icon=":material/check:")
            time.sleep(3)
            st.rerun()






# ==========================================================
# ABA KBAs
# ==========================================================

with aba_kbas:

    st.subheader("KBAs")
    st.write("")

    # -----------------------------------
    # Carregar dados da coleção
    # -----------------------------------
    dados_kbas = list(
        col_kbas.find(
            {},
            {"id_kba": 1, "nome_kba": 1}
        ).sort("nome_kba", 1)
    )

    df_kbas = pd.DataFrame(dados_kbas)

    # Garante colunas
    if df_kbas.empty:
        df_kbas = pd.DataFrame(
            columns=["id_kba", "nome_kba"]
        )

    # Remove _id do Mongo
    if "_id" in df_kbas.columns:
        df_kbas = df_kbas.drop(columns=["_id"])

    editar_kbas = st.toggle(
        "Editar",
        key="editar_kbas"
    )

    st.write("")

    # ==================================================
    # MODO VISUALIZAÇÃO
    # ==================================================
    if not editar_kbas:

        if df_kbas.empty:
            st.caption("Nenhuma KBA cadastrada.")
        else:

            df_tabela = (
                df_kbas
                .sort_values("nome_kba")
                .reset_index(drop=True)
                .rename(columns={
                    "id_kba": "ID da KBA",
                    "nome_kba": "Nome da KBA"
                })
            )

            st.dataframe(
                df_tabela,
                hide_index=True
            )

    # ==================================================
    # MODO EDIÇÃO
    # ==================================================
    else:

        st.write("Edite, adicione e exclua KBAs.")

        df_editor = df_kbas.copy()

        # Normalização defensiva
        df_editor["id_kba"] = (
            df_editor["id_kba"]
            .astype(str)
            .str.strip()
        )
        df_editor["nome_kba"] = (
            df_editor["nome_kba"]
            .astype(str)
            .str.strip()
        )

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_kbas",
            column_config={
                "id_kba": st.column_config.TextColumn(
                    "ID da KBA",
                    required=True,
                    help="Identificador único da KBA (texto livre)",
                    width=20
                ),
                "nome_kba": st.column_config.TextColumn(
                    "Nome da KBA",
                    required=True,
                    width=900
                ),
            }
        )

        if st.button(
            "Salvar alterações",
            icon=":material/save:",
            type="primary",
            key="salvar_kbas"
        ):


            # Remove linhas vazias
            df_salvar = df_editado.copy()

            df_salvar["id_kba"] = (
                df_salvar["id_kba"]
                .astype(str)
                .str.strip()
            )
            df_salvar["nome_kba"] = (
                df_salvar["nome_kba"]
                .astype(str)
                .str.strip()
            )

            df_salvar = df_salvar[
                (df_salvar["id_kba"] != "")
                & (df_salvar["nome_kba"] != "")
            ]

            if df_salvar.empty:
                st.warning("Nenhuma KBA válida para salvar.")
                st.stop()

            # ===========================
            # VALIDAÇÃO DE DUPLICADOS
            # ===========================
            duplicados_id = df_salvar[
                df_salvar["id_kba"].duplicated()
            ]["id_kba"].tolist()

            duplicados_nome = df_salvar[
                df_salvar["nome_kba"].duplicated()
            ]["nome_kba"].tolist()

            if duplicados_id:
                st.error(
                    "IDs de KBA duplicados: "
                    f"{', '.join(set(duplicados_id))}"
                )
                st.stop()

            if duplicados_nome:
                st.error(
                    "Nomes de KBA duplicados: "
                    f"{', '.join(set(duplicados_nome))}"
                )
                st.stop()

            # ===========================
            # SINCRONIZAÇÃO COM O BANCO
            # ===========================
            col_kbas.delete_many({})

            col_kbas.insert_many(
                df_salvar.to_dict(orient="records")
            )

            st.success("KBAs atualizadas com sucesso!")
            time.sleep(3)
            st.rerun()















# # ==========================================================
# # ABA TIPOS DE MANEJO
# # ==========================================================

# with aba_tipos_manejo:

#     # ------------------------------------------------------
#     # TÍTULO DA ABA
#     # ------------------------------------------------------
#     st.subheader("Tipos de manejo")
#     st.write("")

#     # ------------------------------------------------------
#     # SELEÇÃO DO EDITAL
#     # ------------------------------------------------------

#     lista_editais = df_editais["codigo_edital"].unique().tolist()

#     edital_selecionado_manejo = st.selectbox(
#         "Selecione o Edital:",
#         options=[""] + lista_editais,
#         index=0,
#         width=300,
#         key="edital_tipos_manejo"
#     )

#     # Caso nenhum edital seja selecionado
#     if not edital_selecionado_manejo:
#         st.caption("Selecione um edital para continuar.")

#     else:
#         # ------------------------------------------------------
#         # BUSCA O EDITAL NO BANCO
#         # ------------------------------------------------------

#         edital = col_editais.find_one(
#             {"codigo_edital": edital_selecionado_manejo}
#         )

#         # Recupera os tipos de manejo (se existirem)
#         tipos_manejo = edital.get("tipos_manejo", [])

#         # ======================================================
#         # CRIAÇÃO DAS ABAS INTERNAS
#         # ======================================================

#         aba_visualizar, aba_novo, aba_editar = st.tabs([
#             "Tipos de manejo",
#             "Novo",
#             "Editar / Excluir"
#         ])

#         # ======================================================
#         # ABA 1 — VISUALIZAR TIPOS
#         # ======================================================

#         with aba_visualizar:

#             if not tipos_manejo:
#                 st.caption("Nenhum tipo de manejo cadastrado.")
#             else:
#                 for idx, tipo in enumerate(tipos_manejo, start=1):
#                     st.markdown(f"**{idx}. {tipo['nome_tipo_manejo']}**")

#         # ======================================================
#         # ABA 2 — NOVO TIPO DE MANEJO
#         # ======================================================

#         with aba_novo:

#             st.markdown("##### Cadastrar novo tipo de manejo")

#             nome_tipo = st.text_input(
#                 "Nome do tipo de manejo",
#                 key="novo_tipo_manejo"
#             )

#             st.write('')
#             if st.button("Salvar tipo de manejo", type="primary", icon=":material/save:", key="btn_novo_tipo_manejo"):

#                 if not nome_tipo.strip():
#                     st.warning("O nome do tipo de manejo não pode estar vazio.")
#                 else:
#                     novo_tipo = {
#                         "nome_tipo_manejo": nome_tipo.strip()
#                     }

#                     col_editais.update_one(
#                         {"codigo_edital": edital_selecionado_manejo},
#                         {"$push": {"tipos_manejo": novo_tipo}}
#                     )

#                     st.success(":material/check: Tipo de manejo cadastrado com sucesso!")
#                     time.sleep(3)
#                     st.rerun()

#         # ======================================================
#         # ABA 3 — EDITAR / EXCLUIR
#         # ======================================================

#         with aba_editar:

#             if not tipos_manejo:
#                 st.caption("Nenhum tipo de manejo cadastrado.")
#             else:
#                 st.markdown("##### Selecione um tipo para editar ou excluir")

#                 mapa_tipos = {
#                     t["nome_tipo_manejo"]: t
#                     for t in tipos_manejo
#                 }

#                 selecionado = st.selectbox(
#                     "",
#                     list(mapa_tipos.keys()),
#                     key="select_tipo_manejo"
#                 )

#                 if selecionado:
#                     tipo_atual = mapa_tipos[selecionado]

#                     st.divider()

#                     novo_nome = st.text_input(
#                         "Nome do tipo de manejo",
#                         value=tipo_atual["nome_tipo_manejo"],
#                         key="editar_tipo_manejo"
#                     )

#                     st.write('')

#                     with st.container(horizontal=True):

                        
#                         # -------- SALVAR --------
#                         if st.button("Salvar alterações", type="primary", icon=":material/save:", key="btn_editar_tipo_manejo"):

#                             novo = {
#                                 "nome_tipo_manejo": novo_nome.strip()
#                             }

#                             tipos_atualizados = [
#                                 novo if t == tipo_atual else t
#                                 for t in tipos_manejo
#                             ]

#                             col_editais.update_one(
#                                 {"codigo_edital": edital_selecionado_manejo},
#                                 {"$set": {"tipos_manejo": tipos_atualizados}}
#                             )

#                             st.success(":material/check: Tipo de manejo atualizado com sucesso!")
#                             time.sleep(3)
#                             st.rerun()

#                         # -------- EXCLUIR --------
#                         if st.button("Excluir tipo", icon=":material/delete:", key="btn_excluir_tipo_manejo"):

#                             novos = [
#                                 t for t in tipos_manejo
#                                 if t != tipo_atual
#                             ]

#                             col_editais.update_one(
#                                 {"codigo_edital": edital_selecionado_manejo},
#                                 {"$set": {"tipos_manejo": novos}}
#                             )

#                             st.success("Tipo de manejo removido com sucesso!")
#                             time.sleep(3)
#                             st.rerun()
