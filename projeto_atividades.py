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

# Editais
col_editais = db["editais"]






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



# CARREGAR INDICADORES DO EDITAL VINCULADO AO PROJETO

# Obtém o nome do edital vinculado ao projeto
nome_edital_projeto = df_projeto["edital"].values[0]

# Busca o edital correspondente
edital_doc = col_editais.find_one({"codigo_edital": nome_edital_projeto})

# Verifica se encontrou o edital
if not edital_doc:
    st.error("Edital vinculado ao projeto não encontrado.")
    lista_indicadores_edital = []
else:
    # Extrai indicadores do edital
    indicadores_edital = edital_doc.get("indicadores", [])

    # Lista apenas os nomes dos indicadores
    lista_indicadores_edital = [
        ind.get("indicador") for ind in indicadores_edital
    ]

# Extrai indicadores do edital
indicadores_edital = edital_doc.get("indicadores", [])

# Lista apenas os nomes dos indicadores
lista_indicadores_edital = [
    ind.get("indicador") for ind in indicadores_edital
]




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

    # ===============================================================================================
    # NORMALIZAÇÃO SEGURA DOS DADOS DO PROJETO
    # ===============================================================================================

    projeto_dict = df_projeto.iloc[0].to_dict()

    plano_trabalho_dict = projeto_dict.get("plano_trabalho") or {}

    if not isinstance(plano_trabalho_dict, dict):
        plano_trabalho_dict = {}

    componentes = plano_trabalho_dict.get("componentes") or []

    if not isinstance(componentes, list):
        componentes = []


    # ===============================================================================================
    # PERMISSÃO
    # -----------------------------------------------------------------------------------------------
    # Apenas admin/equipe podem editar
    # ===============================================================================================

    usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]
    modo_edicao = False

    if usuario_interno:
        with st.container(horizontal=True, horizontal_alignment="right"):
            modo_edicao = st.toggle(
                "Modo de edição",
                key="editar_plano_trabalho"
            )

    st.write("")


    # ===============================================================================================
    # MODO VISUALIZAÇÃO
    # ===============================================================================================

    if not modo_edicao:

        # Caso não exista plano de trabalho
        if not componentes:
            st.caption("Este projeto não possui plano de trabalho cadastrado.")
        else:

            # Percorre componentes
            for componente in componentes:

                st.markdown(f"#### {componente.get('componente', 'Componente sem nome')}")

                # Percorre entregas
                for entrega in componente.get("entregas", []):

                    st.markdown(f"##### {entrega.get('entrega', 'Entrega sem nome')}")

                    atividades = entrega.get("atividades", [])

                    if not atividades:
                        st.caption("Nenhuma atividade cadastrada nesta entrega.")
                        continue

                    # Converte para DataFrame
                    df_atividades = pd.DataFrame(atividades)

                    df_atividades = df_atividades.rename(columns={
                        "atividade": "Atividade",
                        "data_inicio": "Data de início",
                        "data_fim": "Data de fim",
                    })

                    st.dataframe(
                        df_atividades[["Atividade", "Data de início", "Data de fim"]],
                        hide_index=True,
                        use_container_width=True
                    )

                    st.write("")


    # ===============================================================================================
    # MODO EDIÇÃO
    # ===============================================================================================

    else:

        # Escolha do que editar
        opcao_editar_pt = st.radio(
            "O que deseja editar?",
            ["Atividades", "Entregas", "Componentes"],
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
                st.caption("Nenhum componente cadastrado. Cadastre componentes antes de adicionar atividades.")
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

            # Converte para datetime (se houver valores)
            if not df_atividades.empty:

                df_atividades["data_inicio"] = pd.to_datetime(
                    df_atividades["data_inicio"],
                    format="%d/%m/%Y",
                    errors="coerce"
                )

                df_atividades["data_fim"] = pd.to_datetime(
                    df_atividades["data_fim"],
                    format="%d/%m/%Y",
                    errors="coerce"
                )


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

                    "data_inicio": st.column_config.DateColumn(
                        label="Data de início",
                        width=120,
                        format="DD/MM/YYYY"
                    ),

                    "data_fim": st.column_config.DateColumn(
                        label="Data de fim",
                        width=120,
                        format="DD/MM/YYYY"
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

                # ----------------------------------------------------------
                # Função de validação de data
                # ----------------------------------------------------------
                def valida_data(valor, linha, campo):

                    if pd.isna(valor):
                        erros.append(f"Linha {linha}: {campo} é obrigatória.")
                        return None

                    return valor



                # ----------------------------------------------------------
                # Validação linha a linha
                # ----------------------------------------------------------
                for idx, row in df_editado.iterrows():

                    atividade = str(row["atividade"]).strip()
                    data_inicio_raw = str(row["data_inicio"]).strip()
                    data_fim_raw = str(row["data_fim"]).strip()

                    if atividade == "":
                        erros.append(f"Linha {idx + 1}: o nome da atividade não pode estar vazio.")

                    data_inicio = valida_data(data_inicio_raw, idx + 1, "Data de início")
                    data_fim = valida_data(data_fim_raw, idx + 1, "Data de término")

                    if data_inicio and data_fim and atividade != "":
                        atividades_final.append({
                            "atividade": atividade,
                            "data_inicio": pd.to_datetime(data_inicio).strftime("%d/%m/%Y"),
                            "data_fim": pd.to_datetime(data_fim).strftime("%d/%m/%Y"),
                        })
                    


                # ----------------------------------------------------------
                # Se houver erros → apenas exibe
                # ----------------------------------------------------------
                if erros:

                    for e in erros:
                        st.error(e)

                else:

                    # ------------------------------------------------------
                    # Cria nova lista de atividades (sempre novos IDs)
                    # ------------------------------------------------------
                    nova_lista = []

                    for a in atividades_final:

                        nova_lista.append({
                            "id": str(bson.ObjectId()),
                            "atividade": a["atividade"],
                            "data_inicio": a["data_inicio"],
                            "data_fim": a["data_fim"],

                            # Campos padrão
                            "status_atividade": "prevista",
                            "porcentagem_atv": 0
                        })

                    # ------------------------------------------------------
                    # Atualiza apenas a entrega selecionada
                    # ------------------------------------------------------
                    entregas_atualizadas = []

                    for e in componente_sel["entregas"]:
                        if e["id"] == entrega_sel["id"]:
                            entregas_atualizadas.append({
                                **e,
                                "atividades": nova_lista
                            })
                        else:
                            entregas_atualizadas.append(e)

                    # ------------------------------------------------------
                    # Atualiza apenas o componente correspondente
                    # ------------------------------------------------------
                    componentes_atualizados = []

                    for c in componentes:
                        if c["id"] == componente_sel["id"]:
                            componentes_atualizados.append({
                                **c,
                                "entregas": entregas_atualizadas
                            })
                        else:
                            componentes_atualizados.append(c)

                    # ------------------------------------------------------
                    # Persistência no MongoDB
                    # ------------------------------------------------------
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






        # ===========================================================================================
        # EDIÇÃO DE ENTREGAS
        # ===========================================================================================

        if opcao_editar_pt == "Entregas":

            if not componentes:
                st.warning("Cadastre um componente primeiro.")
                st.stop()

            # Mapa nome → componente
            mapa = {c["componente"]: c for c in componentes}

            nome = st.selectbox("Componente", list(mapa.keys()))
            componente = mapa[nome]

            entregas_existentes = componente.get("entregas", [])


            # --------------------------------------------------
            # DataFrame para edição
            # --------------------------------------------------
            if entregas_existentes:

                df_entregas = pd.DataFrame({
                    "entrega": [e.get("entrega", "") for e in entregas_existentes],
                    "Indicadores": [e.get("indicadores_doador", []) for e in entregas_existentes]
                })

            else:

                df_entregas = pd.DataFrame({
                    "entrega": pd.Series(dtype="str"),
                    "Indicadores": pd.Series(dtype="object")  # precisa ser object para lista
                })





            df_editado = st.data_editor(
                df_entregas,
                num_rows="dynamic",
                hide_index=True,
                column_config={
                    "Indicadores": st.column_config.MultiselectColumn(
                        "Indicadores",
                        options=lista_indicadores_edital
                    )
                }
            )


            salvar = st.button(
                "Salvar entregas",
                icon=":material/save:",
                type="secondary"
            )

            if salvar:

                nova_lista = []
                erro_validacao = False

                # --------------------------------------------------
                # VALIDAÇÃO + MONTAGEM
                # --------------------------------------------------
                for _, row in df_editado.iterrows():

                    nome_entrega = str(row["entrega"]).strip()
                    indicadores_linha = row.get("Indicadores") or []

                    if not nome_entrega:
                        continue

                    if not indicadores_linha:
                        st.error(f"A entrega '{nome_entrega}' deve ter ao menos um indicador.")
                        erro_validacao = True
                        continue

                    nova_lista.append({
                        "id": str(bson.ObjectId()),
                        "entrega": nome_entrega,
                        "indicadores_doador": indicadores_linha
                    })

                # --------------------------------------------------
                # SÓ SALVA SE NÃO HOUVER ERRO
                # --------------------------------------------------
                if not erro_validacao:

                    for c in componentes:
                        if c["componente"] == nome:
                            c["entregas"] = nova_lista

                    col_projetos.update_one(
                        {"codigo": codigo_projeto_atual},
                        {"$set": {"plano_trabalho.componentes": componentes}}
                    )

                    st.success("Entregas atualizadas com sucesso!", icon=":material/check:")
                    time.sleep(3)
                    st.rerun()






        # ===========================================================================================
        # EDIÇÃO DE COMPONENTES
        # ===========================================================================================

        if opcao_editar_pt == "Componentes":

            st.write("")

            # Monta DataFrame apenas com nomes



            if componentes:
                df_componentes = pd.DataFrame({
                    "componente": [c.get("componente", "") for c in componentes]
                })
            else:
                # Força tipo string quando não houver componentes
                df_componentes = pd.DataFrame({
                    "componente": pd.Series(dtype="str")
                })

            # Garante que a coluna seja string
            df_componentes["componente"] = df_componentes["componente"].astype(str)


            df_editado = st.data_editor(
                df_componentes,
                num_rows="dynamic",
                hide_index=True,
                key="editor_componentes"
            )

            salvar = st.button(
                "Salvar componentes",
                icon=":material/save:",
                type="secondary"
            )

            if salvar:

                # Limpa nomes vazios
                df_editado["componente"] = df_editado["componente"].astype(str).str.strip()
                df_editado = df_editado[df_editado["componente"] != ""]

                novos_componentes = []

                # Cria nova lista com IDs novos
                for _, row in df_editado.iterrows():
                    novos_componentes.append({
                        "id": str(bson.ObjectId()),
                        "componente": row["componente"],
                        "entregas": []
                    })

                col_projetos.update_one(
                    {"codigo": codigo_projeto_atual},
                    {"$set": {"plano_trabalho.componentes": novos_componentes}}
                )

                st.success("Componentes atualizados com sucesso!", icon=":material/check:")
                time.sleep(3)
                st.rerun()

















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
                st.caption("Não há impactos de longo prazo cadastrados")
                

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
                    st.success("Impactos de longo prazo salvos com sucesso!", icon=":material/check:")
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
                st.caption("Não há impactos de curto prazo cadastrados")

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
                    st.success("Impactos de curto prazo salvos com sucesso!", icon=":material/check:")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("Erro ao salvar impactos.")









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

            # Mapeia codigo_indicador para nome do indicador
            mapa_indicadores = {
                ind["codigo_indicador"]: ind["indicador"]
                for ind in indicadores_edital
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


        # Texto introdutório da seção
        st.write("*Selecione os indicadores que serão acompanhados no projeto.*")

        # Aviso para o usuário lembrar de salvar
        st.markdown(
            "<span style='color:#2F5AA1;'>***Lembre-se de salvar cada indicador após editar.***</span>",
            unsafe_allow_html=True
        )

        st.write("")


        # --------------------------------------------------
        # INICIALIZA / NORMALIZA ESTADO
        # --------------------------------------------------
        # Cria o estado na sessão para armazenar os valores
        # dos indicadores já salvos no projeto

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
                    "resultado_intermediario": item.get("resultado_intermediario", ""),
                    "resultado_final": item.get("resultado_final", "")
                }

            st.session_state.valores_indicadores = estado


        # --------------------------------------------------
        # GARANTIA DE DADOS
        # --------------------------------------------------
        # Verifica se existem indicadores cadastrados no edital

        if not indicadores_edital:
            st.caption("Não há indicadores cadastrados neste edital.")

        else:

            # Configuração fixa das colunas da tabela
            colunas_indicadores = [5, 2, 4, 2, 2]

            # Cabeçalho da tabela
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
            # Cada indicador será renderizado em uma linha

            for ind in sorted(indicadores_edital, key=lambda x: x["indicador"]):

                id_indicador = ind["codigo_indicador"]
                nome_indicador = ind["indicador"]

                # Recupera dados existentes do indicador no estado
                dados_atual = st.session_state.valores_indicadores.get(
                    id_indicador,
                    {
                        "valor": 0,
                        "descricao": "",
                        "resultado_intermediario": "",
                        "resultado_final": ""
                    }
                )

                # Criação das colunas de inputs
                col_check, col_valor, col_desc, col_res_int, col_res_final = st.columns(colunas_indicadores)


                # --------------------------------------------------
                # CHECKBOX DO INDICADOR
                # --------------------------------------------------
                with col_check:

                    marcado = st.checkbox(
                        nome_indicador,
                        key=f"chk_{id_indicador}",
                        value=id_indicador in st.session_state.valores_indicadores
                    )


                # --------------------------------------------------
                # VALOR NUMÉRICO DA CONTRIBUIÇÃO
                # --------------------------------------------------
                with col_valor:

                    if marcado:

                        valor = st.number_input(
                            "",
                            step=1,
                            value=dados_atual["valor"],
                            key=f"num_{id_indicador}"
                        )


                # --------------------------------------------------
                # DESCRIÇÃO DA CONTRIBUIÇÃO
                # --------------------------------------------------
                with col_desc:

                    if marcado:

                        descricao = st.text_area(
                            "",
                            value=dados_atual["descricao"],
                            key=f"desc_{id_indicador}",
                            height=80
                        )


                # --------------------------------------------------
                # RESULTADO INTERMEDIÁRIO
                # --------------------------------------------------
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


                # --------------------------------------------------
                # RESULTADO FINAL
                # --------------------------------------------------
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


                # --------------------------------------------------
                # ATUALIZA ESTADO DA SESSÃO
                # --------------------------------------------------
                # Mantém os valores no estado enquanto o usuário edita

                if marcado:

                    st.session_state.valores_indicadores[id_indicador] = {
                        "valor": valor,
                        "descricao": descricao,
                        "resultado_intermediario": resultado_intermediario,
                        "resultado_final": resultado_final
                    }

                else:

                    st.session_state.valores_indicadores.pop(id_indicador, None)


                # --------------------------------------------------
                # BOTÃO DE SALVAR INDIVIDUAL
                # --------------------------------------------------
                # Cada indicador possui seu próprio botão


                with st.container(horizontal=True, horizontal_alignment="right"):

                    salvar_indicador = st.button(
                        "Salvar",
                        icon=":material/save:",
                        type="secondary",
                        key=f"save_{id_indicador}",
                        width=200
                    )


                # --------------------------------------------------
                # VALIDAÇÃO E SALVAMENTO DO INDICADOR
                # --------------------------------------------------
                if salvar_indicador:

                    if not marcado:

                        st.warning("Selecione o indicador antes de salvar.")

                    elif valor <= 0:

                        st.error("O valor deve ser maior que zero.")

                    elif not descricao.strip():

                        st.error("A descrição da contribuição esperada não pode estar vazia.")

                    else:

                        indicador_para_salvar = {
                            "id_indicador": id_indicador,
                            "valor": valor,
                            "descricao_contribuicao": descricao.strip(),
                            "resultado_intermediario": resultado_intermediario,
                            "resultado_final": resultado_final
                        }

                        # Busca projeto atual
                        projeto = col_projetos.find_one({"codigo": codigo_projeto_atual})

                        indicadores_existentes = projeto.get("indicadores", [])

                        # Remove indicador antigo se existir
                        indicadores_filtrados = [
                            i for i in indicadores_existentes
                            if i["id_indicador"] != id_indicador
                        ]

                        # Adiciona o indicador atualizado
                        indicadores_filtrados.append(indicador_para_salvar)

                        # Atualiza no banco
                        resultado = col_projetos.update_one(
                            {"codigo": codigo_projeto_atual},
                            {"$set": {"indicadores": indicadores_filtrados}}
                        )

                        # Mensagem de retorno
                        if resultado.matched_count == 1:

                            st.success("Indicador atualizado com sucesso!", icon=":material/check:")

                            time.sleep(3)

                            st.rerun()

                        else:

                            st.error("Erro ao salvar indicador.")


                # Separador visual entre indicadores
                st.divider()









# ###################################################################################################
# MONITORAMENTO
# ###################################################################################################









with monitoramento:

    # ------------------------------------------------------------------
    # Título principal
    # ------------------------------------------------------------------
    st.subheader("Plano de Monitoramento")

    # ------------------------------------------------------------------
    # NORMALIZAÇÃO SEGURA DO PLANO DE TRABALHO
    # ------------------------------------------------------------------
    # Nunca acessar df["plano_trabalho"] direto (pode não existir)
    # ------------------------------------------------------------------

    projeto_dict = df_projeto.iloc[0].to_dict()

    plano_trabalho_dict = projeto_dict.get("plano_trabalho") or {}

    if not isinstance(plano_trabalho_dict, dict):
        plano_trabalho_dict = {}

    componentes = plano_trabalho_dict.get("componentes") or []

    if not isinstance(componentes, list):
        componentes = []

    # ------------------------------------------------------------------
    # RENDERIZAÇÃO CONDICIONAL (SEM stop)
    # ------------------------------------------------------------------

    if not componentes:

        st.caption("Este projeto ainda não possui componentes cadastrados.")

    else:





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




