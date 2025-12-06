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

# Indicadores
col_indicadores = db["indicadores"]

###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# TRATAMENTO DE DADOS
###########################################################################################################


codigo_projeto_atual = st.session_state.get("projeto_atual")

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

# ???????????????????????
# with st.expander("Colunas do projeto"):
#     st.write(df_projeto.columns)


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')


# Título da página
st.header("Marco Lógico")


plano_trabalho, impactos, indicadores, monitoramento = st.tabs(["Plano de trabalho", "Impactos", "Indicadores", "Monitoramento"])




# ###################################################################################################
# PLANO DE TRABALHO
# ###################################################################################################


with plano_trabalho:

    # --------------------------------------------------
    # PERMISSÃO
    # --------------------------------------------------
    usuario_pode_editar = st.session_state.tipo_usuario in ["admin", "equipe"]

    # Valor padrão do modo edição
    modo_edicao = False

    # --------------------------------------------------
    # TOGGLE DE EDIÇÃO (somente para admin/equipe)
    # --------------------------------------------------
    if usuario_pode_editar:
        with st.container(horizontal=True, horizontal_alignment="right"):
            modo_edicao = st.toggle(
                "Modo de edição",
                key="editar_plano_trabalho"
            )

    # --------------------------------------------------
    # TÍTULO DA SUBPÁGINA
    # --------------------------------------------------
    # st.subheader("Plano de Trabalho")
    st.write("")

    # --------------------------------------------------
    # RENDERIZAÇÃO CONDICIONAL
    # --------------------------------------------------
    if not modo_edicao:

        # --------------------------------------------------
        # MODO VISUALIZAÇÃO
        # --------------------------------------------------

        # st.write("")

        

        # Pegando o projeto carregado
        projeto = df_projeto.iloc[0]

        # Acessando o plano de trabalho
        plano = projeto.get("plano_trabalho", {})
        componentes = plano.get("componentes", [])

        if not componentes:
            st.info("Este projeto não possui plano de trabalho cadastrado.")
        else:
            # ==========================================
            # Loop pelos componentes
            # ==========================================
            for componente in componentes:
                
                st.markdown(f"#### {componente.get('componente', 'Componente sem nome')}")

                entregas = componente.get("entregas", [])

                for entrega in entregas:

                    st.write('')
                    st.write(f"**{entrega.get('entrega', 'Entrega sem nome')}**")

                    atividades = entrega.get("atividades", [])

                    if atividades and isinstance(atividades, list):

                        # Cria DataFrame
                        df = pd.DataFrame(atividades)

                        # Renomeia colunas (apenas texto)
                        df = df.rename(columns={
                            "atividade": "Atividades",
                            "data_inicio": "Data de início",
                            "data_fim": "Data de fim",
                        })

                        # Mantém exatamente como string
                        # Garante que exista, mesmo se algum campo faltar
                        if "Data de início" not in df.columns:
                            df["Data de início"] = ""
                        if "Data de fim" not in df.columns:
                            df["Data de fim"] = ""

                        # Exibe tabela com as colunas desejadas
                        colunas = [c for c in ["Atividades", "Data de início", "Data de fim"] if c in df.columns]

                        st.dataframe(df[colunas],
                                     hide_index=True,
                                     column_config={
                                         "Atividades": st.column_config.TextColumn(
                                             width=1000
                                         ),
                                         "Data de início": st.column_config.TextColumn(
                                             width=80
                                         ),
                                         "Data de fim": st.column_config.TextColumn(
                                             width=80
                                         )
                                     })

                    else:
                        st.caption("Nenhuma atividade cadastrada nesta entrega.")

                    st.write('')








    else:


        # -------------------------
        # MODO EDIÇÃO - PLANO DE TRABALHO
        # -------------------------


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
                "Selecione a entrega",
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
            # Data Editor usando STRING, NÃO DateColumn
            # ============================================================

            df_editado = st.data_editor(
                df_atividades,
                num_rows="dynamic",
                hide_index=True,
                key="editor_atividades",
                column_config={

                    "atividade": st.column_config.TextColumn(
                        label="Atividade",
                        width=1000
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
                    st.success("Atividades atualizadas com sucesso!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Erro ao atualizar atividades.")




        # # -------------------------
        # # MODO EDIÇÃO - PLANO DE TRABALHO
        # # -------------------------


        # # Radio para escolher entre editar Componentes ou Atividades
        # opcao_editar_pt = st.radio(
        #     "O que deseja editar?",
        #     ["Atividades",
        #      "Entregas", 
        #      "Componentes"],
        #     horizontal=True
        # )


        # if opcao_editar_pt == "Atividades":


        #     # --------------------------------------------------
        #     # MODO DE EDIÇÃO — ATIVIDADES
        #     # --------------------------------------------------

        #     st.write("")
        #     st.write("")

        #     # ============================================================
        #     # Carregar plano de trabalho
        #     # ============================================================

        #     plano_trabalho = (
        #         df_projeto["plano_trabalho"].values[0]
        #         if "plano_trabalho" in df_projeto.columns else {}
        #     )

        #     componentes = plano_trabalho.get("componentes", [])

        #     if not componentes:
        #         st.warning("Nenhum componente cadastrado. Cadastre componentes antes de adicionar atividades.")
        #         st.stop()


        #     # ============================================================
        #     # Montar lista de entregas
        #     # ============================================================

        #     lista_entregas = []

        #     for comp in componentes:
        #         for ent in comp.get("entregas", []):
        #             lista_entregas.append({
        #                 "label": ent["entrega"],  # só o nome da entrega
        #                 "componente": comp,
        #                 "entrega": ent
        #             })

        #     if not lista_entregas:
        #         st.warning("Nenhuma entrega cadastrada. Cadastre entregas antes de adicionar atividades.")
        #         st.stop()

        #     lista_entregas = sorted(lista_entregas, key=lambda x: x["label"].lower())


        #     # ============================================================
        #     # Selectbox de entrega
        #     # ============================================================

        #     nome_entrega_sel = st.selectbox(
        #         "Selecione a entrega",
        #         [item["label"] for item in lista_entregas],
        #         key="select_entrega_ativ"
        #     )

        #     item_sel = next(item for item in lista_entregas if item["label"] == nome_entrega_sel)

        #     componente_sel = item_sel["componente"]
        #     entrega_sel = item_sel["entrega"]

        #     st.write('')

        #     # ============================================================
        #     # Carregar atividades existentes
        #     # ============================================================

        #     atividades_exist = entrega_sel.get("atividades", [])

        #     lista_atividades = []
        #     for a in atividades_exist:
        #         try:
        #             dt_inicio = datetime.datetime.strptime(a.get("data_inicio", ""), "%d/%m/%Y").date()
        #         except:
        #             dt_inicio = None

        #         try:
        #             dt_fim = datetime.datetime.strptime(a.get("data_fim", ""), "%d/%m/%Y").date()
        #         except:
        #             dt_fim = None

        #         lista_atividades.append({
        #             "atividade": a.get("atividade", ""),
        #             "data_inicio": dt_inicio,
        #             "data_fim": dt_fim,
        #         })

        #     df_atividades = pd.DataFrame(lista_atividades)

        #     # Se estiver vazio, cria colunas vazias
        #     if df_atividades.empty:
        #         df_atividades = pd.DataFrame({
        #             "atividade": pd.Series(dtype="str"),
        #             "data_inicio": pd.Series(dtype="datetime64[ns]"),
        #             "data_fim": pd.Series(dtype="datetime64[ns]"),
        #         })


        #     # ============================================================
        #     # Data Editor com DateColumn DD/MM/YYYY
        #     # ============================================================

        #     df_editado = st.data_editor(
        #         df_atividades,
        #         num_rows="dynamic",
        #         hide_index=True,
        #         key="editor_atividades",
        #         column_config={

        #             "atividade": st.column_config.Column(
        #                 label="Atividade",
        #                 width=1000
        #             ),
        #             "data_inicio": st.column_config.DateColumn(
        #                 label="Data início",
        #                 format="DD/MM/YYYY",
        #                 width=100
        #             ),
        #             "data_fim": st.column_config.DateColumn(
        #                 label="Data término",
        #                 format="DD/MM/YYYY",
        #                 width=100
        #             ),
        #         }
        #     )


        #     # ============================================================
        #     # Botão salvar
        #     # ============================================================

        #     salvar_ativ = st.button(
        #         "Salvar atividades",
        #         icon=":material/save:",
        #         type="secondary",
        #         key="btn_salvar_atividades"
        #     )


        #     # ============================================================
        #     # Validação + Salvamento
        #     # ============================================================

        #     if salvar_ativ:

        #         erros = []

        #         atividades_final = []

        #         # Validação linha a linha
        #         for idx, row in df_editado.iterrows():

        #             atividade = str(row["atividade"]).strip()
        #             dt_inicio = row["data_inicio"]
        #             dt_fim = row["data_fim"]

        #             if atividade == "":
        #                 erros.append(f"Linha {idx + 1}: o nome da atividade não pode estar vazio.")
        #             if dt_inicio is None:
        #                 erros.append(f"Linha {idx + 1}: a Data de início é obrigatória.")
        #             if dt_fim is None:
        #                 erros.append(f"Linha {idx + 1}: a Data de término é obrigatória.")

        #             # Se não houver erro, já preparo os dados finais
        #             if not erros:
        #                 atividades_final.append({
        #                     "atividade": atividade,
        #                     "data_inicio": dt_inicio.strftime("%d/%m/%Y"),
        #                     "data_fim": dt_fim.strftime("%d/%m/%Y"),
        #                 })

        #         # Se houver erros → exibir e não salvar
        #         if erros:
        #             for e in erros:
        #                 st.error(e)
        #             st.stop()

        #         # Agora garantimos IDs estáveis
        #         ids_original = [a["id"] for a in atividades_exist]

        #         nova_lista = []
        #         for idx, a in enumerate(atividades_final):

        #             if idx < len(ids_original):
        #                 id_usado = ids_original[idx]
        #             else:
        #                 id_usado = str(bson.ObjectId())

        #             nova_lista.append({
        #                 "id": id_usado,
        #                 **a
        #             })

        #         # Atualizar entrega
        #         entregas_atualizadas = []
        #         for e in componente_sel["entregas"]:
        #             if e["id"] == entrega_sel["id"]:
        #                 entregas_atualizadas.append({**e, "atividades": nova_lista})
        #             else:
        #                 entregas_atualizadas.append(e)

        #         # Atualizar apenas o componente correspondente
        #         componentes_atualizados = []
        #         for c in componentes:
        #             if c["id"] == componente_sel["id"]:
        #                 componentes_atualizados.append({**c, "entregas": entregas_atualizadas})
        #             else:
        #                 componentes_atualizados.append(c)

        #         # Salvar no Mongo
        #         resultado = col_projetos.update_one(
        #             {"codigo": codigo_projeto_atual},
        #             {"$set": {"plano_trabalho.componentes": componentes_atualizados}}
        #         )

        #         if resultado.matched_count == 1:
        #             st.success("Atividades atualizadas com sucesso!")
        #             time.sleep(1)
        #             st.rerun()
        #         else:
        #             st.error("Erro ao atualizar atividades.")





        # --------------------------------------------------
        # MODO DE EDIÇÃO — ENTREGAS
        # --------------------------------------------------
        if opcao_editar_pt == "Entregas":


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
                "Selecione o componente",
                nomes_componentes
            )

            componente = mapa_comp_por_nome[nome_componente_selecionado]

            # 3) Carrega entregas existentes do componente selecionado
            entregas_existentes = componente.get("entregas", [])

            # Cria um DataFrame SOMENTE com a coluna "entrega"
            if entregas_existentes:
                df_entregas = pd.DataFrame({
                    "entrega": [e.get("entrega", "") for e in entregas_existentes]
                })
            else:
                df_entregas = pd.DataFrame({"entrega": pd.Series(dtype="str")})

            # Mostra o editor
            df_editado = st.data_editor(
                df_entregas,
                num_rows="dynamic",
                hide_index=True,
                key="editor_entregas"
            )

            # Botão salvar
            salvar_entregas = st.button(
                "Salvar entregas",
                icon=":material/save:",
                type="secondary",
                key="btn_salvar_entregas"
            )

            if salvar_entregas:

                # Remove vazios
                df_editado["entrega"] = df_editado["entrega"].astype(str).str.strip()
                df_editado = df_editado[df_editado["entrega"] != ""]

                # IDs originais na ordem correta
                ids_original = [e["id"] for e in entregas_existentes]

                nova_lista = []
                import bson

                for idx, row in df_editado.iterrows():
                    nome = row["entrega"]

                    # Se existia antes, mantém ID
                    if idx < len(ids_original):
                        id_usado = ids_original[idx]
                    else:
                        id_usado = str(bson.ObjectId())  # ID novo

                    nova_lista.append({
                        "id": id_usado,
                        "entrega": nome
                    })

                # Atualizar SOMENTE o componente selecionado
                componentes_atualizados = []

                for comp in componentes:
                    if comp["componente"] == nome_componente_selecionado:
                        componentes_atualizados.append({
                            **comp,
                            "entregas": nova_lista
                        })
                    else:
                        componentes_atualizados.append(comp)

                # Salvar no banco de dados
                resultado = col_projetos.update_one(
                    {"codigo": codigo_projeto_atual},
                    {"$set": {"plano_trabalho.componentes": componentes_atualizados}}
                )

                if resultado.matched_count == 1:
                    st.success("Entregas atualizadas com sucesso!")
                    time.sleep(1)
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
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Erro ao atualizar o Plano de Trabalho.")










# ###################################################################################################
# IMPACTOS
# ###################################################################################################

with impactos:

    @st.dialog("Editar impactos", width="medium")
    def editar_impactos():

        tab_cadastrar, tab_editar = st.tabs(["Cadastrar impacto", "Editar impactos"])

        # ========================================================
        # CADASTRAR IMPACTO
        # ========================================================
        with tab_cadastrar:

            tipo = st.radio(
                "Tipo de impacto",
                ["Longo prazo", "Curto prazo"],
                horizontal=True
            )

            texto_impacto = st.text_area(
                "Descrição do impacto",
                height=150
            )

            if st.button(
                "Salvar impacto",
                type="primary",
                icon=":material/save:"
            ):

                if not texto_impacto.strip():
                    st.warning("O impacto não pode estar vazio.")
                    return

                chave = (
                    "impactos_longo_prazo"
                    if tipo == "Longo prazo"
                    else "impactos_curto_prazo"
                )

                impacto = {
                    "id": str(bson.ObjectId()),
                    "texto": texto_impacto.strip()
                }

                resultado = col_projetos.update_one(
                    {"codigo": st.session_state.projeto_atual},
                    {"$push": {chave: impacto}}
                )

                if resultado.modified_count == 1:
                    st.success("Impacto salvo com sucesso!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Erro ao salvar impacto.")

        # ========================================================
        # EDITAR IMPACTO
        # ========================================================
        with tab_editar:

            tipo = st.radio(
                "Tipo de impacto",
                ["Longo prazo", "Curto prazo"],
                horizontal=True,
                key="tipo_editar_impacto"
            )

            chave = (
                "impactos_longo_prazo"
                if tipo == "Longo prazo"
                else "impactos_curto_prazo"
            )

            impactos = (
                df_projeto[chave].values[0]
                if chave in df_projeto.columns
                else []
            )

            if not impactos:
                st.write("Não há impactos cadastrados.")
                return

            mapa_impactos = {
                f"{i['texto'][:80]}": i
                for i in impactos
            }

            impacto_label = st.selectbox(
                "Selecione o impacto",
                list(mapa_impactos.keys())
            )

            impacto_selecionado = mapa_impactos[impacto_label]

            novo_texto = st.text_area(
                "Editar impacto",
                value=impacto_selecionado["texto"],
                height=150
            )

            if st.button(
                "Salvar alterações",
                type="primary",
                icon=":material/save:"
            ):

                if not novo_texto.strip():
                    st.warning("O impacto não pode estar vazio.")
                    return

                resultado = col_projetos.update_one(
                    {
                        "codigo": st.session_state.projeto_atual,
                        f"{chave}.id": impacto_selecionado["id"],
                    },
                    {
                        "$set": {
                            f"{chave}.$.texto": novo_texto.strip()
                        }
                    }
                )

                if resultado.modified_count == 1:
                    st.success("Impacto atualizado com sucesso!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Erro ao atualizar impacto.")

    # st.write('')

    # Toggle do modo de edição

    if st.session_state.tipo_usuario in ["admin", "equipe"]:

        with st.container(horizontal=True, horizontal_alignment="right"):
            modo_edicao = st.toggle("Modo de edição", key="editar_impactos")



    # LISTAGEM DOS IMPACTOS DE LONGO PRAZO E CURTO PRAZO

    col_lp, col_cp = st.columns(2, gap="large")

    with col_lp:
        st.subheader("Impactos de longo prazo")
        st.write('*Entre 3 a 5 anos após o final do projeto*')

        # Botões de edição só para admin e equipe. Por isso o try.
        try:
            if modo_edicao:

                with st.container(horizontal=True):
                    if st.button("Editar impactos", icon=":material/edit:", type="secondary"):
                        editar_impactos()
        except:
            pass


        st.write('')

        impactos_lp = (
            df_projeto["impactos_longo_prazo"].values[0]
            if "impactos_longo_prazo" in df_projeto.columns
            else []
        )

        if not impactos_lp:
            st.write("Não há impactos de longo prazo cadastrados")
        else:
            for i, impacto in enumerate(impactos_lp, start=1):
                st.write(f"**{i}**. {impacto['texto']}")




    with col_cp:
        st.subheader("Impactos de curto prazo")
        st.write("*Durante o projeto ou até o final da subvenção*")

        # Botões de edição só para admin e equipe. Por isso o try.
        try:
            if modo_edicao:
                with st.container(horizontal=True):
                    if st.button("Editar impactos", icon=":material/edit:", type="secondary", key="editar_impactos_cp"):
                        editar_impactos()
        except:
            pass


        st.write('')

        impactos_cp = (
            df_projeto["impactos_curto_prazo"].values[0]
            if "impactos_curto_prazo" in df_projeto.columns
            else []
        )

        if not impactos_cp:
            st.write("Não há impactos de curto prazo cadastrados")
        else:
            for i, impacto in enumerate(impactos_cp, start=1):
                st.write(f"**{i}**. {impacto['texto']}")





# ###################################################################################################
# INDICADORES
# ###################################################################################################

with indicadores:


    # --------------------------------------------------
    # PERMISSÃO
    # --------------------------------------------------
    usuario_pode_editar = st.session_state.tipo_usuario in ["admin", "equipe"]

    # Valor padrão
    modo_edicao = False

    # --------------------------------------------------
    # TOGGLE (somente para quem pode)
    # --------------------------------------------------
    if usuario_pode_editar:
        with st.container(horizontal=True, horizontal_alignment="right"):
            modo_edicao = st.toggle(
                "Modo de edição",
                key="editar_indicadores"
            )


    # --------------------------------------------------
    # TÍTULO DA SUBPÁGINA
    # --------------------------------------------------
    st.subheader("Indicadores")



    # --------------------------------------------------
    # RENDERIZAÇÃO CONDICIONAL
    # --------------------------------------------------
    if not modo_edicao:


        # -------------------------
        # MODO VISUALIZAÇÃO — INDICADORES
        # -------------------------

        st.write("")

        # Recupera indicadores do projeto
        indicadores_projeto = (
            df_projeto["indicadores"].values[0]
            if "indicadores" in df_projeto.columns
            else []
        )

        if not indicadores_projeto:
            st.info("Nenhum indicador associado a este projeto.")

        else:
            # --------------------------------------------------
            # Mapeia id_indicador -> nome do indicador
            # --------------------------------------------------
            mapa_indicadores = {
                row["_id"]: row["indicador"]
                for _, row in df_indicadores.iterrows()
            }

            dados_tabela = []

            for item in indicadores_projeto:

                id_indicador = item.get("id_indicador")
                valor = item.get("valor")
                descricao = item.get("descricao_contribuicao", "")

                nome_indicador = mapa_indicadores.get(
                    id_indicador,
                    "Indicador não encontrado"
                )

                dados_tabela.append({
                    "Indicadores": nome_indicador,
                    "Contribuição esperada": valor,
                    "Descrição da contribuição": descricao
                })

            df_visualizacao = pd.DataFrame(dados_tabela)

            ui.table(df_visualizacao)


    else:


        # -------------------------
        # MODO EDIÇÃO — INDICADORES
        # -------------------------

        st.write("*Selecione os indicadores que serão acompanhados no projeto.*")
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
                    "descricao": item.get("descricao_contribuicao", "")
                }

            st.session_state.valores_indicadores = estado

        else:
            # NORMALIZA ESTADO ANTIGO (int → dict)
            for k, v in list(st.session_state.valores_indicadores.items()):
                if isinstance(v, int):
                    st.session_state.valores_indicadores[k] = {
                        "valor": v,
                        "descricao": ""
                    }

        # --------------------------------------------------
        # GARANTIA DE DADOS
        # --------------------------------------------------
        if df_indicadores.empty:
            st.info("Não há indicadores cadastrados.")

        else:
            # --------------------------------------------------
            # CABEÇALHO
            # --------------------------------------------------
            col_h1, col_h2, col_h3 = st.columns([6, 2, 4])

            with col_h1:
                st.markdown("**Indicadores do CEPF**")

            with col_h2:
                st.markdown("**Contribuição esperada**")

            with col_h3:
                st.markdown("**Descrição da contribuição esperada**")

            # st.divider()
            st.write('')

            # --------------------------------------------------
            # LISTAGEM DOS INDICADORES
            # --------------------------------------------------
            for _, row in df_indicadores.sort_values("indicador").iterrows():

                id_indicador = row["_id"]
                nome_indicador = row["indicador"]

                dados_atual = st.session_state.valores_indicadores.get(
                    id_indicador,
                    {"valor": 0, "descricao": ""}
                )

                valor_atual = dados_atual.get("valor", 0)
                descricao_atual = dados_atual.get("descricao", "")

                col_check, col_valor, col_desc = st.columns([6, 2, 4])

                # -------------------------
                # CHECKBOX
                # -------------------------
                with col_check:
                    marcado = st.checkbox(
                        nome_indicador,
                        key=f"chk_{id_indicador}",
                        value=id_indicador in st.session_state.valores_indicadores
                    )

                # -------------------------
                # VALOR NUMÉRICO
                # -------------------------
                with col_valor:
                    if marcado:
                        valor = st.number_input(
                            "",
                            step=1,
                            value=valor_atual,
                            key=f"num_{id_indicador}"
                        )

                # -------------------------
                # DESCRIÇÃO
                # -------------------------
                with col_desc:
                    if marcado:
                        descricao = st.text_area(
                            "",
                            value=descricao_atual,
                            key=f"desc_{id_indicador}",
                            height=80
                        )

                # -------------------------
                # ATUALIZA ESTADO
                # -------------------------
                if marcado:
                    st.session_state.valores_indicadores[id_indicador] = {
                        "valor": valor,
                        "descricao": descricao
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
                        "descricao_contribuicao": dados["descricao"].strip()
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
                    st.success("Indicadores atualizados com sucesso!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Erro ao salvar indicadores.")













# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()

