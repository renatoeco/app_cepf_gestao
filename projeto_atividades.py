import streamlit as st
import pandas as pd
import streamlit_shadcn_ui as ui
import datetime
import time
import bson

from funcoes_auxiliares import (
    conectar_mongo_cepf_gestao, 
    gerar_link_drive,
    sidebar_projeto
)








# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()



###########################################################################################################
# CONFIGURAÇÕES DO STREAMLIT
###########################################################################################################






###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Projetos
col_projetos = db["projetos"]

# Indicadores
col_indicadores = db["indicadores"]






# ###########################################################################################################
# # CONEXÃO COM GOOGLE DRIVE
# ###########################################################################################################






###########################################################################################################
# FUNÇÕES
###########################################################################################################


# Função auxiliar que salva lista de impactos no banco
def salvar_impactos(chave, impactos, codigo_projeto):
    """
    Salva lista de impactos no banco.
    """
    resultado = col_projetos.update_one(
        {"codigo": codigo_projeto},
        {"$set": {chave: impactos}}
    )

    return resultado.modified_count == 1


# DIÁLOGO: VER RELATOS 

@st.dialog("Relatos de atividade", width="large")
def dialog_relatos():

    atividade = st.session_state.get("atividade_selecionada")

    if not isinstance(atividade, dict):
        st.warning("Nenhuma atividade selecionada.")
        return

    nome_atividade = (
        atividade.get("atividade")
        or atividade.get("Atividade")
        or "Atividade sem nome"
    )

    st.markdown(f"## {nome_atividade}")
    st.write("")

    # ============================================================
    # BUSCAR RELATOS DA ATIVIDADE NO DOCUMENTO DO PROJETO
    # ============================================================
    projeto = df_projeto.iloc[0].to_dict()
    relatos_encontrados = []

    for componente in projeto.get("plano_trabalho", {}).get("componentes", []):
        for entrega in componente.get("entregas", []):
            for atv in entrega.get("atividades", []):
                if atv.get("id") == atividade.get("id"):
                    relatos_encontrados = atv.get("relatos", [])
                    break

    if not relatos_encontrados:
        st.info("Esta atividade ainda não possui relatos.")
        return

    # ============================================================
    # RENDERIZAÇÃO DOS RELATOS
    # ============================================================

    for relato in relatos_encontrados:

        with st.container(border=True):

            id_relato = relato.get("id_relato", "relato").upper()
            numero_relatorio = relato.get("relatorio_numero")

            # Cabeçalho
            st.markdown(
                f"#### {id_relato} "
                f"<span style='font-size: 0.9em; color: gray;'>(R{numero_relatorio})</span>",
                unsafe_allow_html=True
            )

            # Texto do relato
            st.write(relato.get("relato", ""))

            col1, col2 = st.columns([2, 3])
            col1.write(f"**Quando:** {relato.get('quando', '-')}")
            col2.write(f"**Onde:** {relato.get('onde', '-')}")

            # --------------------------------------------------
            # ANEXOS
            # --------------------------------------------------
            if relato.get("anexos"):
                with col1:
                    c1, c2 = st.columns([1, 5])
                    c1.write("**Anexos:**")
                    for a in relato["anexos"]:
                        if a.get("id_arquivo"):
                            link = gerar_link_drive(a["id_arquivo"])
                            c2.markdown(
                                f"[{a['nome_arquivo']}]({link})",
                                unsafe_allow_html=True
                            )

            # --------------------------------------------------
            # FOTOGRAFIAS
            # --------------------------------------------------
            if relato.get("fotos"):
                with col2:
                    c1, c2 = st.columns([1, 5])
                    c1.write("**Fotografias:**")
                    for f in relato["fotos"]:
                        if f.get("id_arquivo"):
                            link = gerar_link_drive(f["id_arquivo"])
                            linha = f"[{f['nome_arquivo']}]({link})"
                            if f.get("descricao"):
                                linha += f" | {f['descricao']}"
                            if f.get("fotografo"):
                                linha += f" | {f['fotografo']}"
                            c2.markdown(linha, unsafe_allow_html=True)

        # st.write('') # espaço entre os contaners












    # for relato in relatos_encontrados:

    #     id_relato = relato.get("id_relato", "relato").upper()
    #     numero_relatorio = relato.get("relatorio_numero")

    #     # Cabeçalho
    #     st.markdown(
    #         f"#### {id_relato} "
    #         f"<span style='font-size: 0.9em; color: gray;'>(R{numero_relatorio})</span>",
    #         unsafe_allow_html=True
    #     )

    #     # Texto do relato
    #     st.write(relato.get("relato", ""))

    #     col1, col2 = st.columns([2, 3])
    #     col1.write(f"**Quando:** {relato.get('quando', '-')}")
    #     col2.write(f"**Onde:** {relato.get('onde', '-')}")

    #     # --------------------------------------------------
    #     # ANEXOS
    #     # --------------------------------------------------
    #     if relato.get("anexos"):
    #         with col1:
    #             c1, c2 = st.columns([1, 5])
    #             c1.write("**Anexos:**")
    #             for a in relato["anexos"]:
    #                 if a.get("id_arquivo"):
    #                     link = gerar_link_drive(a["id_arquivo"])
    #                     c2.markdown(
    #                         f"[{a['nome_arquivo']}]({link})",
    #                         unsafe_allow_html=True
    #                     )

    #     # --------------------------------------------------
    #     # FOTOS
    #     # --------------------------------------------------
    #     if relato.get("fotos"):
    #         with col2:
    #             c1, c2 = st.columns([1, 5])
    #             c1.write("**Fotografias:**")
    #             for f in relato["fotos"]:
    #                 if f.get("id_arquivo"):
    #                     link = gerar_link_drive(f["id_arquivo"])
    #                     linha = f"[{f['nome_arquivo']}]({link})"
    #                     if f.get("descricao"):
    #                         linha += f" | {f['descricao']}"
    #                     if f.get("fotografo"):
    #                         linha += f" | {f['fotografo']}"
    #                     c2.markdown(linha, unsafe_allow_html=True)

    #     st.divider()










###########################################################################################################
# TRATAMENTO DE DADOS
###########################################################################################################


codigo_projeto_atual = st.session_state.get("projeto_atual")

if not codigo_projeto_atual:
    st.error("Nenhum projeto selecionado.")
    st.stop()

# Capturando o projeto atual no bd
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



df_indicadores = pd.DataFrame(
    list(
        col_indicadores.find()
    )
)

# Transformar o id em string
df_indicadores = df_indicadores.copy()
if "_id" in df_indicadores.columns:
    df_indicadores["_id"] = df_indicadores["_id"].astype(str)


###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################


# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')



# Título da página e identificação
col_titulo, col_identificacao = st.columns([3, 2])

with col_titulo:
    st.header("Marco Lógico")

with col_identificacao:
    st.markdown(
        f"<div style='text-align: right; margin-top: 30px;'>{df_projeto['codigo'].values[0]} - {df_projeto['sigla'].values[0]}</div>",
        unsafe_allow_html=True
    )



plano_trabalho, impactos, indicadores, monitoramento = st.tabs(["Plano de trabalho", "Impactos", "Indicadores", "Plano de Monitoramento"])




# ###################################################################################################
# PLANO DE TRABALHO
# ###################################################################################################


with plano_trabalho:

    # --------------------------------------------------
    # PERMISSÃO
    # --------------------------------------------------
    usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]

    # Valor padrão do modo edição
    modo_edicao = False

    # --------------------------------------------------
    # TOGGLE DE EDIÇÃO (somente para admin/equipe)
    # --------------------------------------------------
    if usuario_interno:
        with st.container(horizontal=True, horizontal_alignment="right"):
            modo_edicao = st.toggle(
                "Modo de edição",
                key="editar_plano_trabalho"
            )


    st.write("")

    # --------------------------------------------------
    # RENDERIZAÇÃO CONDICIONAL
    # --------------------------------------------------


        # --------------------------------------------------
        # MODO VISUALIZAÇÃO
        # --------------------------------------------------

    if not modo_edicao:


        # --------------------------------------------------
        # ESTADOS DO DIÁLOGO (inicialização segura, para garantir que o diálogo não abra ao desmarcar um checkbox)

        if "atividade_selecionada" not in st.session_state:
            st.session_state["atividade_selecionada"] = None

        if "atividade_selecionada_tabela_key" not in st.session_state:
            st.session_state["atividade_selecionada_tabela_key"] = None

        if "abrir_dialogo_atividade" not in st.session_state:
            st.session_state["abrir_dialogo_atividade"] = False



        # --------------------------------------------------
        # CONTEÚDO DO MODO VISUALIZAÇÃO
        # --------------------------------------------------

        projeto = df_projeto.iloc[0]
        plano_trabalho = projeto.get("plano_trabalho", {})
        componentes = plano_trabalho.get("componentes", [])

        if not componentes:
            st.caption("Este projeto não possui plano de trabalho cadastrado.")
        else:

            for componente in componentes:
                
                st.markdown(f"#### {componente.get('componente', 'Componente sem nome')}")

                for entrega in componente.get("entregas", []):

                    st.write("")
                    st.markdown(f"##### {entrega.get('entrega', 'Entrega sem nome')}")
                    
                    # st.write(f"**{entrega.get('entrega', 'Entrega sem nome')}**")

                    atividades = entrega.get("atividades", [])

                    # Se não houver atividades
                    if not atividades:
                        st.caption("Nenhuma atividade cadastrada nesta entrega.")
                        continue

                    # Converte lista em DataFrame
                    df_atividades = pd.DataFrame(atividades)

                    # Renomeia colunas
                    df_atividades = df_atividades.rename(columns={
                        "atividade": "Atividade",
                        "data_inicio": "Data de início",
                        "data_fim": "Data de fim",
                    })


                    # Ordem das colunas
                    colunas = ["Atividade", "Data de início", "Data de fim"]

                    # KEY ÚNICA PARA CADA ENTREGA
                    key_df = f"df_vis_atividades_{entrega['id']}"


                    # ============================================================================================
                    # FUNÇÃO QUE CRIA O CALLBACK DE SELEÇÃO PARA ESTA TABELA ESPECÍFICA
                    # 
                    # Por que precisamos disso?
                    # - Cada entrega tem sua própria tabela
                    # - Cada tabela precisa do seu próprio callback
                    # - O Streamlit executa o callback ANTES de saber qual entrega/tabela estamos
                    # 
                    # Este padrão (closure) "congela" o df_local e a key_local
                    # para que o callback saiba exatamente qual tabela chamou.
                    # ============================================================================================


                    # FUNÇÃO: criar callback de seleção
                    def criar_callback_selecao(dataframe_atividades, chave_tabela):
                        """
                        Retorna a função handle_selecao() configurada para esta tabela específica.
                        """

                        def handle_selecao():

                            estado_tabela = st.session_state.get(chave_tabela, {})
                            selecao = estado_tabela.get("selection", {})
                            linhas = selecao.get("rows", [])

                            if not linhas:
                                return

                            idx = linhas[0]
                            linha = dataframe_atividades.iloc[idx]

                            atividade_escolhida = {
                                "id": linha.get("id"),
                                "atividade": linha.get("Atividade", ""),        # Nome da atividade
                                "data_inicio": linha.get("Data de início", ""),
                                "data_fim": linha.get("Data de fim", "")
                            }

                            if not atividade_escolhida["id"]:
                                st.error("Atividade selecionada não possui campo 'id'.")
                                return

                            # Usada pelo diálogo para exibir o nome
                            st.session_state["atividade_selecionada"] = atividade_escolhida


                            # Dispara abertura do diálogo
                            st.session_state["abrir_dialogo_atividade"] = True

                        return handle_selecao







                    # -------------------------------------------
                    # TABELA INTERATIVA
                    # -------------------------------------------

                    # Criar o callback para esta tabela específica
                    callback_selecao = criar_callback_selecao(df_atividades, key_df)



                    st.dataframe(
                        df_atividades,
                        column_order=colunas,
                        hide_index=True,
                        selection_mode="single-row",
                        key=key_df,
                        on_select=callback_selecao,
                        column_config={
                            "Atividade": st.column_config.TextColumn(width=1000),
                            "Data de início": st.column_config.TextColumn(width=80),
                            "Data de fim": st.column_config.TextColumn(width=80),
                        }
                    )

                    st.write("")

                st.write('')

        # --------------------------------------------------
        # ABRIR O DIÁLOGO SE FOI SOLICITADO
        # Limpar estado logo após abrir
        # --------------------------------------------------

        if st.session_state.get("abrir_dialogo_atividade"):
            dialog_relatos()
            # Só desarma o gatilho
            st.session_state["abrir_dialogo_atividade"] = False




    # -------------------------
    # MODO EDIÇÃO - PLANO DE TRABALHO
    # -------------------------


    else:




        # Radio para escolher entre editar Componentes ou Atividades
        opcao_editar_pt = st.radio(
            "O que deseja editar?",
            ["Atividades",
            "Entregas", 
            "Componentes"],
            horizontal=True
        )


        if opcao_editar_pt == "Atividades":

            st.write("")
            st.write("")

            # ============================================================
            # Carregar plano de trabalho
            # ============================================================

            plano_trabalho = (
                df_projeto["plano_trabalho"].values[0]
                if "plano_trabalho" in df_projeto.columns else {}
            )

            componentes = plano_trabalho.get("componentes", [])

            if not componentes:
                st.warning("Nenhum componente cadastrado. Cadastre componentes antes de adicionar atividades.")
                st.stop()


            # ============================================================
            # Montar lista de entregas
            # ============================================================

            lista_entregas = []

            for comp in componentes:
                for ent in comp.get("entregas", []):
                    lista_entregas.append({
                        "label": ent["entrega"],
                        "componente": comp,
                        "entrega": ent
                    })

            if not lista_entregas:
                st.warning("Nenhuma entrega cadastrada. Cadastre entregas antes de adicionar atividades.")
                st.stop()

            lista_entregas = sorted(lista_entregas, key=lambda x: x["label"].lower())


            # ============================================================
            # Selectbox de entrega
            # ============================================================

            nome_entrega_sel = st.selectbox(
                "Selecione a entrega:",
                [item["label"] for item in lista_entregas],
                key="select_entrega_ativ"
            )

            item_sel = next(item for item in lista_entregas if item["label"] == nome_entrega_sel)

            componente_sel = item_sel["componente"]
            entrega_sel = item_sel["entrega"]

            st.write('')

            # ============================================================
            # Carregar atividades existentes
            # ============================================================

            atividades_exist = entrega_sel.get("atividades", [])

            lista_atividades = []
            for a in atividades_exist:
                # Agora as datas não serão convertidas aqui.
                lista_atividades.append({
                    "atividade": a.get("atividade", ""),
                    "data_inicio": a.get("data_inicio", ""),  # mantém string
                    "data_fim": a.get("data_fim", ""),        # mantém string
                })

            df_atividades = pd.DataFrame(lista_atividades)

            # Se estiver vazio, cria colunas vazias
            if df_atividades.empty:
                df_atividades = pd.DataFrame({
                    "atividade": pd.Series(dtype="str"),
                    "data_inicio": pd.Series(dtype="str"),
                    "data_fim": pd.Series(dtype="str"),
                })


            # ============================================================
            # Data Editor 
            # ============================================================

            df_editado = st.data_editor(
                df_atividades,
                num_rows="dynamic",
                hide_index=True,
                key="editor_atividades",
                column_config={

                    "atividade": st.column_config.TextColumn(
                        label="Atividade",
                        width=700
                    ),

                    "data_inicio": st.column_config.TextColumn(
                        label="Data de início",
                        width=120,
                        help="Formato obrigatório: DD/MM/YYYY"
                    ),

                    "data_fim": st.column_config.TextColumn(
                        label="Data de fim",
                        width=120,
                        help="Formato obrigatório: DD/MM/YYYY"
                    ),
                }
            )


            # ============================================================
            # Botão salvar
            # ============================================================

            salvar_ativ = st.button(
                "Salvar atividades",
                icon=":material/save:",
                type="secondary",
                key="btn_salvar_atividades"
            )


            # ============================================================
            # Validação + Salvamento
            # ============================================================

            if salvar_ativ:

                erros = []
                atividades_final = []

                def valida_data(valor, linha, campo):
                    if not valor or str(valor).strip() == "":
                        erros.append(f"Linha {linha}: {campo} é obrigatória.")
                        return None

                    try:
                        datetime.datetime.strptime(valor.strip(), "%d/%m/%Y")
                        return valor.strip()
                    except:
                        erros.append(f"Linha {linha}: data inválida em '{campo}': '{valor}'. Formato correto: DD/MM/YYYY")
                        return None

                # Validação linha a linha
                for idx, row in df_editado.iterrows():

                    atividade = str(row["atividade"]).strip()
                    data_inicio_raw = str(row["data_inicio"]).strip()
                    data_fim_raw = str(row["data_fim"]).strip()

                    if atividade == "":
                        erros.append(f"Linha {idx + 1}: o nome da atividade não pode estar vazio.")

                    # valida datas via função
                    data_inicio = valida_data(data_inicio_raw, idx + 1, "Data de início")
                    data_fim = valida_data(data_fim_raw, idx + 1, "Data de término")

                    # Se nenhuma validação falhou para esta linha
                    if data_inicio and data_fim and atividade != "":
                        atividades_final.append({
                            "atividade": atividade,
                            "data_inicio": data_inicio,
                            "data_fim": data_fim,
                        })

                # Se houver erros → exibir e parar
                if erros:
                    for e in erros:
                        st.error(e)
                    st.stop()

                # IDs antigos preservados
                ids_original = [a["id"] for a in atividades_exist]

                nova_lista = []
                for idx, a in enumerate(atividades_final):

                    if idx < len(ids_original):
                        id_usado = ids_original[idx]
                    else:
                        id_usado = str(bson.ObjectId())

                    nova_lista.append({
                        "id": id_usado,
                        **a
                    })

                # Atualizar entrega
                entregas_atualizadas = []
                for e in componente_sel["entregas"]:
                    if e["id"] == entrega_sel["id"]:
                        entregas_atualizadas.append({**e, "atividades": nova_lista})
                    else:
                        entregas_atualizadas.append(e)

                # Atualizar apenas o componente correspondente
                componentes_atualizados = []
                for c in componentes:
                    if c["id"] == componente_sel["id"]:
                        componentes_atualizados.append({**c, "entregas": entregas_atualizadas})
                    else:
                        componentes_atualizados.append(c)

                # Salvar no Mongo
                resultado = col_projetos.update_one(
                    {"codigo": codigo_projeto_atual},
                    {"$set": {"plano_trabalho.componentes": componentes_atualizados}}
                )

                if resultado.matched_count == 1:
                    st.success("Atividades atualizadas com sucesso!", icon=":material/check:")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("Erro ao atualizar atividades.")








        # --------------------------------------------------
        # MODO DE EDIÇÃO - ENTREGAS
        # --------------------------------------------------
                      
        
        if opcao_editar_pt == "Entregas":

            # ------------------------------------------------------------------
            # Carrega a lista de indicadores da coleção indicadores
            # Esses indicadores serão usados no multiselect do data_editor
            # ------------------------------------------------------------------
            df_indicadores = pd.DataFrame(list(col_indicadores.find()))

            # Garante que o campo _id é string
            if "_id" in df_indicadores.columns:
                df_indicadores["_id"] = df_indicadores["_id"].astype(str)

            # Lista de opções que aparecerão no multiselect
            # Você pode usar só o texto ou id + texto, aqui usei só o texto
            lista_indicadores = df_indicadores["indicador"].tolist()



            st.write("")
            st.write("")

            # 1) Carrega o plano de trabalho e componentes
            plano_trabalho = (
                df_projeto["plano_trabalho"].values[0]
                if "plano_trabalho" in df_projeto.columns else {}
            )

            componentes = plano_trabalho.get("componentes", [])

            if not componentes:
                st.warning("Nenhum componente cadastrado. Cadastre componentes antes de adicionar entregas.")
                st.stop()

            # 2) Usuário escolhe o componente ao qual deseja adicionar/editar entregas
            mapa_comp_por_nome = {c["componente"]: c for c in componentes}
            nomes_componentes = list(mapa_comp_por_nome.keys())

            nome_componente_selecionado = st.selectbox(
                "Selecione o componente:",
                nomes_componentes
            )

            componente = mapa_comp_por_nome[nome_componente_selecionado]

            # 3) Carrega entregas existentes do componente selecionado
            entregas_existentes = componente.get("entregas", [])



            # ------------------------------------------------------------------
            # Cria o DataFrame das entregas incluindo a coluna indicadores
            # ------------------------------------------------------------------
            if entregas_existentes:
                df_entregas = pd.DataFrame({
                    # Nome da entrega
                    "entrega": [e.get("entrega", "") for e in entregas_existentes],

                    # Lista de indicadores já associados à entrega (se existir)
                    "Indicadores": [
                        e.get("indicadores_doador", []) for e in entregas_existentes
                    ]
                })
            else:
                df_entregas = pd.DataFrame({
                    "entrega": pd.Series(dtype="str"),
                    "Indicadores": pd.Series(dtype="object")
                })



            # ------------------------------------------------------------------
            # Editor de dados com coluna multiselect para indicadores
            # ------------------------------------------------------------------
            df_editado = st.data_editor(
                df_entregas,
                num_rows="dynamic",
                hide_index=True,
                key="editor_entregas",
                column_config={
                    "Indicadores": st.column_config.MultiselectColumn(
                        "Indicadores",
                        options=lista_indicadores,
                        help="Selecione os indicadores do doador associados a esta entrega"
                    )
                }
            )



            # Botão salvar
            salvar_entregas = st.button(
                "Salvar entregas",
                icon=":material/save:",
                type="secondary",
                key="btn_salvar_entregas"
            )


            if salvar_entregas:

                # --------------------------------------------------------------
                # Remove linhas vazias
                # --------------------------------------------------------------
                df_editado["entrega"] = df_editado["entrega"].astype(str).str.strip()
                df_editado = df_editado[df_editado["entrega"] != ""]

                # --------------------------------------------------------------
                # VALIDAÇÃO: cada entrega deve ter ao menos um indicador
                # --------------------------------------------------------------
                erro_validacao = False

                for idx, row in df_editado.iterrows():

                    indicadores_linha = row.get("Indicadores")

                    if not indicadores_linha or not isinstance(indicadores_linha, list):
                        st.error(
                            f"A entrega '{row['entrega']}' deve ter pelo menos um indicador associado."
                        )
                        erro_validacao = True


                # --------------------------------------------------------------
                # SE NÃO HOUVER ERRO, CONTINUA O SALVAMENTO
                # --------------------------------------------------------------
                if not erro_validacao:

                    # ----------------------------------------------------------
                    # IDs originais para manter consistência
                    # ----------------------------------------------------------
                    ids_original = [e["id"] for e in entregas_existentes]

                    nova_lista = []

                    # ----------------------------------------------------------
                    # Monta nova lista de entregas SEM PERDER atividades
                    # ----------------------------------------------------------
                    for idx, row in df_editado.iterrows():

                        # Mantém ID antigo ou gera novo
                        if idx < len(ids_original):
                            id_usado = ids_original[idx]
                        else:
                            id_usado = str(bson.ObjectId())

                        # Busca a entrega original (se existir)
                        entrega_original = next(
                            (e for e in entregas_existentes if e["id"] == id_usado),
                            {}
                        )

                        # Cria nova entrega copiando tudo da original
                        nova_entrega = {
                            **entrega_original,   # preserva atividades
                            "id": id_usado,
                            "entrega": row["entrega"],
                            "indicadores_doador": row.get("Indicadores", [])
                        }

                        nova_lista.append(nova_entrega)

                    # ----------------------------------------------------------
                    # Atualiza apenas o componente selecionado
                    # ----------------------------------------------------------
                    componentes_atualizados = []

                    for comp in componentes:
                        if comp["componente"] == nome_componente_selecionado:
                            componentes_atualizados.append({
                                **comp,
                                "entregas": nova_lista
                            })
                        else:
                            componentes_atualizados.append(comp)

                    # ----------------------------------------------------------
                    # Persistência no MongoDB
                    # ----------------------------------------------------------
                    resultado = col_projetos.update_one(
                        {"codigo": codigo_projeto_atual},
                        {"$set": {"plano_trabalho.componentes": componentes_atualizados}}
                    )

                    if resultado.matched_count == 1:
                        st.success("Entregas atualizadas com sucesso.", icon=":material/check:")
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.error("Erro ao atualizar entregas.")





        # --------------------------------------------------
        # EDIÇÃO DE COMPONENTES
        # --------------------------------------------------
        if opcao_editar_pt == "Componentes":

            st.write("")
            # st.write("**Componentes** - Modo de Edição")
            st.write("")

            # 1) Carrega componentes diretamente do projeto
            plano_trabalho = (
                df_projeto["plano_trabalho"].values[0]
                if "plano_trabalho" in df_projeto.columns else {}
            )

            componentes_existentes = plano_trabalho.get("componentes", [])

            # 2) Criar DataFrame SOMENTE com 'componente'
            #    O ID não aparece no editor
            if componentes_existentes:
                df_componentes = pd.DataFrame({
                    "componente": [c.get("componente", "") for c in componentes_existentes]
                })
            else:
                df_componentes = pd.DataFrame({"componente": pd.Series(dtype="str")})

            # 3) Editor (somente coluna componente)
            df_editado = st.data_editor(
                df_componentes,
                num_rows="dynamic",
                hide_index=True,
                key="editor_componentes",
            )

            # -------------------------
            # BOTÃO SALVAR
            # -------------------------
            salvar = st.button(
                "Salvar componentes",
                icon=":material/save:",
                type="secondary",
                key="btn_salvar_componentes"
            )

            # -------------------------
            # SALVAMENTO
            # -------------------------
            if salvar:

                # Limpa linhas vazias
                df_editado["componente"] = df_editado["componente"].astype(str).str.strip()
                df_editado = df_editado[df_editado["componente"] != ""]

                novos_componentes = []
                existentes_por_nome = {c["componente"]: c for c in componentes_existentes}

                for _, row in df_editado.iterrows():
                    nome = row["componente"]

                    if nome in existentes_por_nome:
                        # componente já existia → mantém o ID
                        novos_componentes.append({
                            "id": existentes_por_nome[nome]["id"],
                            "componente": nome
                        })
                    else:
                        # novo componente → cria ID novo
                        novos_componentes.append({
                            "id": str(bson.ObjectId()),
                            "componente": nome
                        })

                # Salva no banco de dados
                resultado = col_projetos.update_one(
                    {"codigo": codigo_projeto_atual},
                    {"$set": {"plano_trabalho": {"componentes": novos_componentes}}}
                )

                if resultado.matched_count == 1:
                    st.success("Componentes atualizados com sucesso!")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("Erro ao atualizar o Plano de Trabalho.")










# ###################################################################################################
# IMPACTOS
# ###################################################################################################




with impactos:

    # ============================================================
    # CONTROLE DE MODO DE EDIÇÃO
    # ============================================================

    if st.session_state.tipo_usuario in ["admin", "equipe"]:
        with st.container(horizontal=True, horizontal_alignment="right"):
            modo_edicao = st.toggle("Modo de edição", key="editar_impactos")
    else:
        modo_edicao = False


    # ============================================================
    # COLUNAS
    # ============================================================

    col_lp, col_cp = st.columns(2, gap="large")

    # ============================================================
    # IMPACTOS DE LONGO PRAZO
    # ============================================================

    with col_lp:
        st.subheader("Impactos de longo prazo")
        st.write("*Entre 3 a 5 anos após o final do projeto*")

        impactos_lp = (
            df_projeto["impactos_longo_prazo"].values[0]
            if "impactos_longo_prazo" in df_projeto.columns
            else []
        )

        # ========================
        # MODO VISUALIZAÇÃO
        # ========================
        if not modo_edicao:

            if not impactos_lp:
                st.markdown(
                    "<span style='color:#c46a00; font-style:italic; '>Não há impactos de longo prazo cadastrados</span>",
                    unsafe_allow_html=True
                )
                

            else:
                for i, impacto in enumerate(impactos_lp, 1):
                    st.write(f"**{i}.** {impacto['texto']}")

        # ========================
        # MODO EDIÇÃO
        # ========================
        else:
            df_lp = pd.DataFrame(
                [{"texto": i["texto"]} for i in impactos_lp] or [{"texto": ""}]
            )

            # df_lp = pd.DataFrame(impactos_lp or [{"texto": ""}])

            df_editado_lp = st.data_editor(
                df_lp,
                num_rows="dynamic",
                hide_index=True,
                key="editor_lp",
                column_config={
                    "texto": st.column_config.TextColumn(
                        "Impacto de longo prazo",
                        width=600
                    )
                }
            )

            if st.button("Salvar", key="save_lp", icon=":material/save:"):
                impactos_salvar = []

                for i, row in df_editado_lp.iterrows():
                    texto = str(row["texto"]).strip()
                    if texto:
                        impacto_id = (
                            impactos_lp[i]["id"]
                            if i < len(impactos_lp)
                            else str(bson.ObjectId())
                        )

                        impactos_salvar.append({
                            "id": impacto_id,
                            "texto": texto
                        })

                if salvar_impactos("impactos_longo_prazo", impactos_salvar, st.session_state.projeto_atual):
                    st.success("Impactos de longo prazo salvos com sucesso!")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("Erro ao salvar impactos.")


    # ============================================================
    # IMPACTOS DE CURTO PRAZO
    # ============================================================

    with col_cp:
        st.subheader("Impactos de curto prazo")
        st.write("*Durante o projeto ou até o final da subvenção*")

        impactos_cp = (
            df_projeto["impactos_curto_prazo"].values[0]
            if "impactos_curto_prazo" in df_projeto.columns
            else []
        )

        # ========================
        # MODO VISUALIZAÇÃO
        # ========================
        if not modo_edicao:

            if not impactos_cp:
                st.markdown(
                    "<span style='color:#c46a00; font-style:italic; '>Não há impactos de curto prazo cadastrados</span>",
                    unsafe_allow_html=True
                )

            else:
                for i, impacto in enumerate(impactos_cp, 1):
                    st.write(f"**{i}.** {impacto['texto']}")

        # ========================
        # MODO EDIÇÃO
        # ========================
        else:

            df_cp = pd.DataFrame(
                [{"texto": i["texto"]} for i in impactos_cp] or [{"texto": ""}]
            )

            # df_cp = pd.DataFrame(impactos_cp or [{"texto": ""}])

            df_editado_cp = st.data_editor(
                df_cp,
                num_rows="dynamic",
                hide_index=True,
                key="editor_cp",
                column_config={
                    "texto": st.column_config.TextColumn(
                        "Impacto de curto prazo",
                        width=600
                    )
                }
            )

            if st.button("Salvar", key="save_cp", icon=":material/save:"):
                impactos_salvar = []

                for i, row in df_editado_cp.iterrows():
                    texto = str(row["texto"]).strip()
                    if texto:
                        impacto_id = (
                            impactos_cp[i]["id"]
                            if i < len(impactos_cp)
                            else str(bson.ObjectId())
                        )

                        impactos_salvar.append({
                            "id": impacto_id,
                            "texto": texto
                        })

                if salvar_impactos("impactos_curto_prazo", impactos_salvar, st.session_state.projeto_atual):
                    st.success("Impactos de curto prazo salvos com sucesso!")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("Erro ao salvar impactos.")








# ###################################################################################################
# INDICADORES
# ###################################################################################################



###########################################################################################################
# ABA INDICADORES
###########################################################################################################

with indicadores:

    # --------------------------------------------------
    # PERMISSÃO
    # --------------------------------------------------
    usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]
    modo_edicao = False

    if usuario_interno:
        with st.container(horizontal=True, horizontal_alignment="right"):
            modo_edicao = st.toggle(
                "Modo de edição",
                key="editar_indicadores"
            )

    st.subheader("Indicadores")

    #######################################################################################################
    # MODO VISUALIZAÇÃO
    #######################################################################################################
    if not modo_edicao:

        indicadores_projeto = (
            df_projeto["indicadores"].values[0]
            if "indicadores" in df_projeto.columns
            else []
        )

        if not indicadores_projeto:
            st.caption("Nenhum indicador associado a este projeto.")
        else:
            # Mapeia id do indicador para o nome
            mapa_indicadores = {
                row["_id"]: row["indicador"]
                for _, row in df_indicadores.iterrows()
            }

            dados_tabela = []

            for item in indicadores_projeto:
                dados_tabela.append({
                    "Indicadores": mapa_indicadores.get(
                        item.get("id_indicador"),
                        "Indicador não encontrado"
                    ),
                    "Contribuição esperada": item.get("valor"),
                    "Descrição da contribuição": item.get(
                        "descricao_contribuicao", ""
                    ),
                    "Resultado intermediário": item.get(
                        "resultado_intermediario", ""
                    ),
                    "Resultado final": item.get(
                        "resultado_final", ""
                    )
                })

            df_visualizacao = pd.DataFrame(dados_tabela)
            ui.table(df_visualizacao)

    #######################################################################################################
    # MODO EDIÇÃO
    #######################################################################################################
    else:

        st.write("*Selecione os indicadores que serão acompanhados no projeto.*")
        st.markdown(
            "<span style='color:#2F5AA1;'>***Lembre-se de salvar no final da página.***</span>",
            unsafe_allow_html=True
        )

        # st.write("*Lembre-se de salvar no final da página.*")

        st.write("")

        # --------------------------------------------------
        # INICIALIZA / NORMALIZA ESTADO
        # --------------------------------------------------
        if "valores_indicadores" not in st.session_state:

            indicadores_salvos = (
                df_projeto["indicadores"].values[0]
                if "indicadores" in df_projeto.columns
                else []
            )

            estado = {}

            for item in indicadores_salvos:
                estado[item["id_indicador"]] = {
                    "valor": item.get("valor", 0),
                    "descricao": item.get("descricao_contribuicao", ""),
                    "resultado_intermediario": item.get(
                        "resultado_intermediario", ""
                    ),
                    "resultado_final": item.get(
                        "resultado_final", ""
                    )
                }

            st.session_state.valores_indicadores = estado

        # --------------------------------------------------
        # GARANTIA DE DADOS
        # --------------------------------------------------
        if df_indicadores.empty:
            st.caption("Não há indicadores cadastrados.")
        else:


            # CONFIGURAÇÃO ÚNICA DAS COLUNAS
            colunas_indicadores = [5, 2, 4, 2, 2]

            # CABEÇALHO
            col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns(colunas_indicadores)

            with col_h1:
                st.markdown("**Indicadores do CEPF**")
            with col_h2:
                st.markdown("**Contribuição esperada**")
            with col_h3:
                st.markdown("**Descrição da contribuição esperada**")
            with col_h4:
                st.markdown("**Resultado intermediário**")
            with col_h5:
                st.markdown("**Resultado final**")

            st.write("")
            st.write("")

            # --------------------------------------------------
            # LISTAGEM DOS INDICADORES
            # --------------------------------------------------
            for _, row in df_indicadores.sort_values("indicador").iterrows():

                id_indicador = row["_id"]
                nome_indicador = row["indicador"]

                dados_atual = st.session_state.valores_indicadores.get(
                    id_indicador,
                    {
                        "valor": 0,
                        "descricao": "",
                        "resultado_intermediario": "",
                        "resultado_final": ""
                    }
                )

                col_check, col_valor, col_desc, col_res_int, col_res_final = st.columns(colunas_indicadores)

                # CHECKBOX
                with col_check:
                    marcado = st.checkbox(
                        nome_indicador,
                        key=f"chk_{id_indicador}",
                        value=id_indicador in st.session_state.valores_indicadores
                    )

                # VALOR NUMÉRICO
                with col_valor:
                    if marcado:
                        valor = st.number_input(
                            "",
                            step=1,
                            value=dados_atual["valor"],
                            key=f"num_{id_indicador}"
                        )

                # DESCRIÇÃO DA CONTRIBUIÇÃO
                with col_desc:
                    if marcado:
                        descricao = st.text_area(
                            "",
                            value=dados_atual["descricao"],
                            key=f"desc_{id_indicador}",
                            height=80
                        )


                # RESULTADO INTERMEDIÁRIO
                with col_res_int:
                    if marcado:
                        resultado_intermediario = st.number_input(
                            "",
                            step=1,
                            value=(
                                dados_atual.get("resultado_intermediario")
                                if isinstance(
                                    dados_atual.get("resultado_intermediario"), (int, float)
                                )
                                else 0
                            ),
                            key=f"res_int_{id_indicador}"
                        )



                # RESULTADO FINAL
                with col_res_final:
                    if marcado:
                        resultado_final = st.number_input(
                            "",
                            step=1,
                            value=(
                                dados_atual.get("resultado_final")
                                if isinstance(
                                    dados_atual.get("resultado_final"), (int, float)
                                )
                                else 0
                            ),
                            key=f"res_fin_{id_indicador}"
                        )


                # ATUALIZA ESTADO
                if marcado:
                    st.session_state.valores_indicadores[id_indicador] = {
                        "valor": valor,
                        "descricao": descricao,
                        "resultado_intermediario": resultado_intermediario,
                        "resultado_final": resultado_final
                    }
                else:
                    st.session_state.valores_indicadores.pop(id_indicador, None)

                st.divider()

            # --------------------------------------------------
            # BOTÃO SALVAR
            # --------------------------------------------------
            salvar = st.button(
                "Salvar indicadores",
                icon=":material/save:",
                type="primary"
            )

            # --------------------------------------------------
            # VALIDAÇÃO + SALVAMENTO
            # --------------------------------------------------
            if salvar:

                if not st.session_state.valores_indicadores:
                    st.warning("Selecione pelo menos um indicador.")
                    st.stop()

                for dados in st.session_state.valores_indicadores.values():

                    if dados["valor"] <= 0:
                        st.error(
                            "Todos os valores dos indicadores devem ser maiores que zero."
                        )
                        st.stop()

                    if not dados["descricao"].strip():
                        st.error(
                            "A descrição da contribuição esperada não pode estar vazia."
                        )
                        st.stop()


                indicadores_para_salvar = [
                    {
                        "id_indicador": id_indicador,
                        "valor": dados["valor"],
                        "descricao_contribuicao": dados["descricao"].strip(),
                        "resultado_intermediario": dados["resultado_intermediario"],
                        "resultado_final": dados["resultado_final"]
                    }
                    for id_indicador, dados in st.session_state.valores_indicadores.items()
                ]


                resultado = col_projetos.update_one(
                    {"codigo": codigo_projeto_atual},
                    {
                        "$set": {
                            "indicadores": indicadores_para_salvar
                        }
                    }
                )

                if resultado.matched_count == 1:
                    st.success("Indicadores atualizados com sucesso!", icon=":material/check:")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Erro ao salvar indicadores.")









# ###################################################################################################
# MONITORAMENTO
# ###################################################################################################








with monitoramento:
    # ------------------------------------------------------------------
    # Título principal da aba
    # ------------------------------------------------------------------
    st.subheader("Plano de Monitoramento")

    # ------------------------------------------------------------------
    # Recupera os componentes do plano de trabalho
    # ------------------------------------------------------------------
    componentes = df_projeto.iloc[0]["plano_trabalho"]["componentes"]

    # ------------------------------------------------------------------
    # Loop principal: percorre todos os componentes
    # ------------------------------------------------------------------
    for idx_comp, componente in enumerate(componentes, start=1):

        # --------------------------------------------------------------
        # Cabeçalho do componente
        # --------------------------------------------------------------
        st.markdown(f"##### {componente['componente']}")
        
        # st.markdown(f"##### Componente {idx_comp}: {componente['componente']}")

        entregas = componente.get("entregas", [])

        if not entregas:
            st.info("Este componente não possui entregas cadastradas.")
            continue

        # --------------------------------------------------------------
        # Loop secundário: percorre as entregas
        # --------------------------------------------------------------
        for idx_ent, entrega in enumerate(entregas, start=1):

            # ----------------------------------------------------------
            # Cada entrega tem seu próprio container visual
            # ----------------------------------------------------------
            with st.container(border=True):

                # ------------------------------------------------------
                # Título da entrega
                # ------------------------------------------------------
                st.markdown(f"###### {entrega['entrega']}")
                
                # st.markdown(f"###### Entrega {idx_ent}: {entrega['entrega']}")

                # ======================================================
                # 1) INDICADORES DO DOADOR EM DUAS COLUNAS
                # ======================================================

                col1, col2 = st.columns([1, 3])

                with col1:
                    st.markdown("Indicadores do doador associados:")

                with col2:
                    indicadores_doador = entrega.get("indicadores_doador", [])
                    if indicadores_doador:
                        for ind in indicadores_doador:
                            st.markdown(f"- {ind}")
                    else:
                        st.caption("Nenhum indicador associado.")

                # ======================================================
                # 2) DATA EDITOR DE INDICADORES DO PROJETO
                # ======================================================

                # ------------------------------------------------------
                # Recupera indicadores do projeto já salvos (se existirem)
                # ------------------------------------------------------
                dados_existentes = entrega.get("indicadores_projeto", [])

                # ------------------------------------------------------
                # Converte para DataFrame
                # ------------------------------------------------------
                if dados_existentes:
                    df_monitoramento = pd.DataFrame(dados_existentes)
                else:
                    df_monitoramento = pd.DataFrame(
                        columns=[
                            "indicador_projeto",
                            "linha_base",
                            "meta",
                            "resultado_atual",
                            "observacoes_coleta",
                            "unidade_medida",
                            "periodicidade",
                            "fonte_verificacao",
                            "responsavel",
                            "data_coleta"
                        ]
                    )

                # ------------------------------------------------------
                # Renomeia colunas para exibição
                # ------------------------------------------------------
                df_monitoramento = df_monitoramento.rename(columns={
                    "indicador_projeto": "Indicador do projeto",
                    "linha_base": "Linha de base",
                    "meta": "Meta",
                    "resultado_atual": "Resultado atual",
                    "observacoes_coleta": "Observações da coleta",
                    "unidade_medida": "Unidade de medida",
                    "periodicidade": "Periodicidade",
                    "fonte_verificacao": "Fonte de verificação",
                    "responsavel": "Responsável",
                    "data_coleta": "Data da coleta"
                })


                # ------------------------------------------------------
                # Reordena colunas para melhor UX
                # (colunas editáveis primeiro, bloqueadas no final)
                # ------------------------------------------------------
                ordem_colunas = [
                    "Indicador do projeto",
                    "Linha de base",
                    "Meta",
                    "Unidade de medida",
                    "Periodicidade",
                    "Fonte de verificação",
                    "Responsável",
                    "Resultado atual",
                    "Observações da coleta",
                    "Data da coleta"
                ]

                # Mantém apenas colunas que existem (segurança)
                ordem_colunas = [c for c in ordem_colunas if c in df_monitoramento.columns]

                df_monitoramento = df_monitoramento[ordem_colunas]



                # ------------------------------------------------------
                # Renderiza o data_editor
                # ------------------------------------------------------
                df_editado = st.data_editor(
                    df_monitoramento,
                    num_rows="dynamic",
                    hide_index=True,
                    key=f"editor_monitoramento_{componente['id']}_{entrega['id']}",
                    column_config={
                        "Indicador do projeto": st.column_config.TextColumn(),
                        "Linha de base": st.column_config.NumberColumn(
                            format="%.1f",
                            step=0.1
                        ),
                        "Meta": st.column_config.NumberColumn(
                            format="%.1f",
                            step=0.1
                        ),
                        "Resultado atual": st.column_config.TextColumn(disabled=True),
                        "Observações da coleta": st.column_config.TextColumn(disabled=True),
                        "Unidade de medida": st.column_config.TextColumn(),
                        "Periodicidade": st.column_config.TextColumn(),
                        "Fonte de verificação": st.column_config.TextColumn(),
                        "Responsável": st.column_config.TextColumn(),
                        "Data da coleta": st.column_config.DateColumn(disabled=True, format="DD/MM/YYYY")
                    }
                )

                # ======================================================
                # 3) BOTÃO DE SALVAR
                # ======================================================

                if st.button(
                    "Salvar indicadores do projeto",
                    icon=":material/save:",
                    key=f"btn_salvar_{componente['id']}_{entrega['id']}"
                ):

                    # --------------------------------------------------
                    # Limpa linhas vazias
                    # --------------------------------------------------
                    df_editado = df_editado.dropna(
                        how="all"
                    )


                    # --------------------------------------------------
                    # REMOVE ESPAÇOS EM BRANCO NO INÍCIO E FIM DOS TEXTOS
                    # --------------------------------------------------
                    colunas_texto = [
                        "Indicador do projeto",
                        "Observações da coleta",
                        "Unidade de medida",
                        "Periodicidade",
                        "Fonte de verificação",
                        "Responsável"
                    ]

                    for col in colunas_texto:
                        if col in df_editado.columns:
                            df_editado[col] = (
                                df_editado[col]
                                .astype(str)
                                .str.strip()
                                .replace("nan", "")
                            )

                    # --------------------------------------------------
                    # Renomeia colunas para o padrão do banco
                    # --------------------------------------------------
                    df_para_salvar = df_editado.rename(columns={
                        "Indicador do projeto": "indicador_projeto",
                        "Linha de base": "linha_base",
                        "Meta": "meta",
                        "Resultado atual": "resultado_atual",
                        "Observações da coleta": "observacoes_coleta",
                        "Unidade de medida": "unidade_medida",
                        "Periodicidade": "periodicidade",
                        "Fonte de verificação": "fonte_verificacao",
                        "Responsável": "responsavel",
                        "Data da coleta": "data_coleta"
                    })

                    # --------------------------------------------------
                    # Converte para lista de dicionários
                    # --------------------------------------------------
                    lista_indicadores_projeto = df_para_salvar.to_dict("records")

                    # --------------------------------------------------
                    # Atualiza apenas a entrega correta
                    # --------------------------------------------------
                    componentes_atualizados = []

                    for comp in componentes:
                        if comp["id"] == componente["id"]:
                            novas_entregas = []

                            for ent in comp.get("entregas", []):
                                if ent["id"] == entrega["id"]:
                                    novas_entregas.append({
                                        **ent,
                                        "indicadores_projeto": lista_indicadores_projeto
                                    })
                                else:
                                    novas_entregas.append(ent)

                            componentes_atualizados.append({
                                **comp,
                                "entregas": novas_entregas
                            })
                        else:
                            componentes_atualizados.append(comp)

                    # --------------------------------------------------
                    # Persistência no MongoDB
                    # --------------------------------------------------
                    resultado = col_projetos.update_one(
                        {"codigo": codigo_projeto_atual},
                        {"$set": {"plano_trabalho.componentes": componentes_atualizados}}
                    )

                    # --------------------------------------------------
                    # Feedback ao usuário
                    # --------------------------------------------------
                    if resultado.matched_count == 1:
                        st.success("Indicadores do projeto salvos com sucesso.", icon=":material/check:")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro ao salvar indicadores do projeto.")






















