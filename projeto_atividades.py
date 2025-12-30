import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao, sidebar_projeto  # Função personalizada para conectar ao MongoDB
import pandas as pd
import streamlit_shadcn_ui as ui
import datetime
import time
import bson
import os
import tempfile
import json
import io


# # Google Drive API
# from google.oauth2.service_account import Credentials
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaIoBaseUpload

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


# # Escopo mínimo necessário para Drive
# ESCOPO_DRIVE = ["https://www.googleapis.com/auth/drive"]

# @st.cache_resource
# def obter_servico_drive():
#     """
#     Retorna o cliente autenticado do Google Drive,
#     usando as credenciais armazenadas em st.secrets.
#     """
#     credenciais = Credentials.from_service_account_info(
#         st.secrets["gcp_service_account"],
#         scopes=ESCOPO_DRIVE
#     )
#     return build("drive", "v3", credentials=credenciais)





###########################################################################################################
# FUNÇÕES
###########################################################################################################




# # Função para selecionar ou criar a pasta do projeto no Drive
# def obter_ou_criar_pasta_projeto(servico, codigo, sigla):
#     nome_pasta = f"{codigo} - {sigla}"

#     id_drive = st.secrets["drive"]["drive_id"]      # Shared Drive
#     id_pasta_raiz = st.secrets["drive"]["pasta_raiz"]  # Pasta interna

#     consulta = (
#         f"name='{nome_pasta}' and "
#         f"'{id_pasta_raiz}' in parents and "
#         f"mimeType='application/vnd.google-apps.folder' and trashed=false"
#     )

#     resultado = servico.files().list(
#         q=consulta,
#         fields="files(id)",
#         corpora="drive",
#         driveId=id_drive,
#         includeItemsFromAllDrives=True,
#         supportsAllDrives=True
#     ).execute()

#     arquivos = resultado.get("files", [])
#     if arquivos:
#         return arquivos[0]["id"]

#     metadados = {
#         "name": nome_pasta,
#         "parents": [id_pasta_raiz],
#         "mimeType": "application/vnd.google-apps.folder"
#     }

#     pasta = servico.files().create(
#         body=metadados,
#         fields="id",
#         supportsAllDrives=True
#     ).execute()

#     return pasta["id"]




# # Criar ou obter subpastas ("anexos", "fotos")
# def obter_ou_criar_subpasta(servico, id_pasta_pai, nome_subpasta):
#     id_drive = st.secrets["drive"]["drive_id"]

#     consulta = (
#         f"'{id_pasta_pai}' in parents and "
#         f"name='{nome_subpasta}' and "
#         f"mimeType='application/vnd.google-apps.folder' and trashed=false"
#     )

#     resultado = servico.files().list(
#         q=consulta,
#         fields="files(id)",
#         corpora="drive",
#         driveId=id_drive,
#         includeItemsFromAllDrives=True,
#         supportsAllDrives=True
#     ).execute()

#     arquivos = resultado.get("files", [])
#     if arquivos:
#         return arquivos[0]["id"]

#     metadados = {
#         "name": nome_subpasta,
#         "parents": [id_pasta_pai],
#         "mimeType": "application/vnd.google-apps.folder"
#     }

#     pasta = servico.files().create(
#         body=metadados,
#         fields="id",
#         supportsAllDrives=True
#     ).execute()

#     return pasta["id"]





# # Upload de um arquivo individual
# def enviar_arquivo_drive(servico, id_pasta, arquivo):
#     metadados = {
#         "name": arquivo.name,
#         "parents": [id_pasta]
#     }

#     media = MediaIoBaseUpload(
#         io.BytesIO(arquivo.read()),
#         mimetype=arquivo.type,
#         resumable=False
#     )

#     arq = servico.files().create(
#         body=metadados,
#         media_body=media,
#         fields="id",
#         supportsAllDrives=True
#     ).execute()

#     return arq["id"]




# # Gerar link de acesso ao arquivo
# def gerar_link_drive(id_arquivo):
#     """
#     Retorna a URL padrão de visualização do arquivo no Drive.
#     """
#     return f"https://drive.google.com/file/d/{id_arquivo}/view"





# # Função para salvar o relato
# def salvar_relato():

#     # -------------------------------------------
#     # 0. CAMPOS DO FORMULÁRIO
#     # -------------------------------------------
#     texto_relato = st.session_state.get("campo_relato", "")
#     quando = st.session_state.get("campo_quando", "")
#     onde = st.session_state.get("campo_onde", "")
#     anexos = st.session_state.get("campo_anexos", [])
#     fotos = st.session_state.get("fotos_relato", [])

#     erros = []
#     if not texto_relato.strip():
#         erros.append("O campo **Relato** é obrigatório.")
#     if not quando.strip():
#         erros.append("O campo **Quando** é obrigatório.")

#     if erros:
#         for e in erros:
#             st.error(e)
#         return

#     # -------------------------------------------
#     # 1. CONEXÃO COM DRIVE
#     # -------------------------------------------
#     servico = obter_servico_drive()

#     projeto = df_projeto.iloc[0]
#     codigo = projeto["codigo"]
#     sigla = projeto["sigla"]

#     id_pasta_projeto = obter_ou_criar_pasta_projeto(servico, codigo, sigla)

#     # -------------------------------------------
#     # 2. ACTIVIDADE SELECIONADA
#     # -------------------------------------------
#     atividade = st.session_state.get("atividade_selecionada_drive")

#     if not atividade:
#         st.error("Erro interno: nenhuma atividade selecionada.")
#         return

#     id_atividade = atividade["id"]

#     # -------------------------------------------
#     # 3. LOCALIZAR ATIVIDADE NO MONGO
#     # -------------------------------------------
#     projeto_mongo = col_projetos.find_one({"codigo": codigo})
#     componentes = projeto_mongo["plano_trabalho"]["componentes"]

#     atividade_mongo = None

#     for comp in componentes:
#         for ent in comp["entregas"]:
#             # Pode vir "atividades" ou "atividade"
#             lista_ativ = ent.get("atividades") or ent.get("atividade") or []
#             for ativ in lista_ativ:
#                 if ativ["id"] == id_atividade:
#                     atividade_mongo = ativ

#     if atividade_mongo is None:
#         st.error("Erro interno: atividade não encontrada no banco de dados.")
#         return

#     # -------------------------------------------
#     # 4. GERAR ID DO RELATO
#     # -------------------------------------------
#     relatos_existentes = atividade_mongo.get("relatos", [])
#     numero = len(relatos_existentes) + 1
#     id_relato = f"relato_{numero:03d}"

#     # -------------------------------------------
#     # 5. CRIAR PASTAS DO RELATO NO DRIVE
#     # -------------------------------------------
#     id_pasta_relato = obter_ou_criar_subpasta(servico, id_pasta_projeto, id_relato)
#     id_pasta_anexos = obter_ou_criar_subpasta(servico, id_pasta_relato, "anexos")
#     id_pasta_fotos  = obter_ou_criar_subpasta(servico, id_pasta_relato, "fotos")

#     # -------------------------------------------
#     # 6. SALVAR ANEXOS (somente ID do arquivo)
#     # -------------------------------------------
#     lista_anexos = []
#     if anexos:
#         for arquivo in anexos:
#             id_arq = enviar_arquivo_drive(servico, id_pasta_anexos, arquivo)
#             lista_anexos.append({
#                 "nome_arquivo": arquivo.name,
#                 "id_arquivo": id_arq
#             })

#     # -------------------------------------------
#     # 7. SALVAR FOTOS (somente ID do arquivo)
#     # -------------------------------------------
#     lista_fotos = []
#     for foto in fotos:
#         arq = foto.get("arquivo")
#         if not arq:
#             continue

#         id_arq = enviar_arquivo_drive(servico, id_pasta_fotos, arq)

#         lista_fotos.append({
#             "nome_arquivo": arq.name,
#             "descricao": foto.get("descricao", ""),
#             "fotografo": foto.get("fotografo", ""),
#             "id_arquivo": id_arq
#         })

#     # -------------------------------------------
#     # 8. OBJETO FINAL DO RELATO
#     # -------------------------------------------
#     novo_relato = {
#         "id_relato": id_relato,
#         "relato": texto_relato.strip(),
#         "quando": quando.strip(),
#         "onde": onde.strip(),
#         "autor": st.session_state.get("nome", "Usuário"),
#         "anexos": lista_anexos,
#         "fotos": lista_fotos
#     }

#     # -------------------------------------------
#     # 9. SALVAR NO MONGO
#     # -------------------------------------------
#     atividade_mongo.setdefault("relatos", []).append(novo_relato)

#     col_projetos.update_one(
#         {"codigo": codigo},
#         {"$set": {"plano_trabalho.componentes": componentes}}
#     )

#     # -------------------------------------------
#     # 10. LIMPAR ESTADOS
#     # -------------------------------------------
#     st.session_state["fotos_relato"] = []
#     st.session_state["atividade_selecionada"] = None
#     st.session_state["atividade_selecionada_drive"] = None
#     st.session_state["atividade_selecionada_tabela_key"] = None
#     st.session_state["abrir_dialogo_atividade"] = False

#     # -------------------------------------------
#     # 11. FINALIZAR
#     # -------------------------------------------
#     st.success("Relato salvo com sucesso!")
#     time.sleep(3)
#     st.rerun()















# # Envia só a thumbnail / miniatura para o drive
# def upload_thumbnail_to_drive(local_path, nome_base, tipo):
#     """
#     Recebe um UploadedFile (Streamlit), cria thumbnail de 280px de largura 
#     com altura proporcional, salva temporariamente e envia ao Google Drive.
#     Retorna o link da miniatura enviada.
#     """
#     try:

#         drive = get_drive_service()

#         # 1. Salva o arquivo enviado (UploadedFile) em um arquivo temporário
#         ext = os.path.splitext(local_path.name)[1].lower()
#         temp_input_path = os.path.join(tempfile.gettempdir(), f"orig_{nome_base}{ext}")

#         with open(temp_input_path, "wb") as f:
#             f.write(local_path.getbuffer())

#         # 2. Pega a pasta correta no Drive
#         tipo_key = TIPO_PASTA_MAP.get(tipo)
#         parent_folder_id = st.secrets["pastas"].get(tipo_key)

#         if not parent_folder_id:
#             st.error(f"Pasta do tipo {tipo} não configurada no secrets.")
#             return None

#         # 3. Cria subpasta com timestamp
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         folder_name = f"{timestamp}_{nome_base}"

#         subfolder = drive.CreateFile({
#             'title': folder_name,
#             'mimeType': 'application/vnd.google-apps.folder',
#             'parents': [{'id': parent_folder_id}]
#         })
#         subfolder.Upload()
#         subfolder_id = subfolder['id']

#         # 4. Geração da miniatura (thumb)
#         thumb_name = f"miniatura_{nome_base}.png"
#         thumb_path = os.path.join(tempfile.gettempdir(), thumb_name)

#         # Se for imagem
#         if ext in ['.png', '.jpg', '.jpeg', '.webp']:
#             img = Image.open(temp_input_path)
#             w, h = img.size
#             new_height = int((280 / w) * h)
#             img = img.resize((280, new_height), Image.Resampling.LANCZOS)
#             img.save(thumb_path, "PNG")

#         # Se for PDF
#         elif ext == '.pdf':
#             pages = convert_from_path(temp_input_path, dpi=150, first_page=1, last_page=1)
#             if pages:
#                 img = pages[0]
#                 w, h = img.size
#                 new_height = int((280 / w) * h)
#                 img = img.resize((280, new_height), Image.Resampling.LANCZOS)
#                 img.save(thumb_path, "PNG")
#         else:
#             st.error("Formato não suportado para miniatura.")
#             return None

#         # 5. Upload da thumbnail para o Drive
#         thumb_file = drive.CreateFile({
#             'title': thumb_name,
#             'parents': [{'id': subfolder_id}]
#         })
#         thumb_file.SetContentFile(thumb_path)
#         thumb_file.Upload()

#         thumb_link = f"https://drive.google.com/file/d/{thumb_file['id']}/view"

#         # 6. Limpeza de arquivos temporários
#         if os.path.exists(thumb_path):
#             os.remove(thumb_path)
#         if os.path.exists(temp_input_path):
#             os.remove(temp_input_path)

#         return thumb_link

#     except Exception as e:
#         st.error(f"Erro ao enviar miniatura: {e}")
#         return None









# ==========================================================================================
# DIÁLOGO: VER RELATOS 
# ==========================================================================================

@st.dialog("Relatos de atividade", width="large")
def dialog_relatos():

    atividade = st.session_state.get("atividade_selecionada")

    # Se por algum motivo vier vazio/None
    if not isinstance(atividade, dict):
        st.warning("Nenhuma atividade selecionada. Feche o diálogo e selecione uma atividade na tabela.")
        return

    # Tenta pegar primeiro "atividade", depois "Atividade", depois usa texto padrão
    nome_atividade = (
        atividade.get("atividade")
        or atividade.get("Atividade")
        or "Atividade sem nome"
    )

    st.markdown(f"### {nome_atividade}")
    st.write("")



    # # ==========================================================
    # # Fragment para evitar rerun completo
    # # ==========================================================
    # @st.fragment
    # def corpo_dialogo():

    #     # ----------------------------------------------------------
    #     # FORMULÁRIO: EXPANDER "Novo relato"
    #     # ----------------------------------------------------------
    #     with st.expander("Novo relato", expanded=True):

    #         # CAMPO: texto principal
    #         texto_relato = st.text_area(
    #             "Relato",
    #             placeholder="Descreva o que foi feito",
    #             key="campo_relato"
    #         )

    #         # CAMPO: Quando ocorreu
    #         quando = st.text_input(
    #             "Quando?",
    #             placeholder="DD/MM/YYYY",
    #             key="campo_quando"
    #         )

    #         # CAMPO: Onde ocorreu
    #         onde = st.text_input(
    #             "Onde?",
    #             key="campo_onde"
    #         )

    #         st.divider()

    #         # ------------------------------------------------------
    #         # ANEXOS
    #         # ------------------------------------------------------
    #         st.markdown("### Anexos")
    #         anexos = st.file_uploader(
    #             "Inclua aqui listas de presença, materiais de comunicação, planilhas, relatórios, mapas etc.",
    #             type=["pdf", "docx", "xlsx", "csv", "jpg", "jpeg", "png"],
    #             accept_multiple_files=True,
    #             key="campo_anexos"
    #         )

    #         st.divider()

    #         # ------------------------------------------------------
    #         # FOTOGRAFIAS — LISTA DINÂMICA
    #         # ------------------------------------------------------
    #         st.subheader("Fotografias")

    #         if "fotos_relato" not in st.session_state:
    #             st.session_state["fotos_relato"] = []

    #         # Adicionar nova foto (não faz rerun geral)
    #         if st.button("➕ Adicionar fotografia", key="btn_adicionar_foto"):
    #             st.session_state["fotos_relato"].append({
    #                 "arquivo": None,
    #                 "descricao": "",
    #                 "fotografo": ""
    #             })

    #         # Campos de cada foto
    #         for i, foto in enumerate(st.session_state["fotos_relato"]):

    #             st.markdown(f"**Foto {i+1}**")

    #             # Arquivo da foto
    #             arquivo_foto = st.file_uploader(
    #                 f"Arquivo da foto {i+1}",
    #                 type=["jpg", "jpeg", "png"],
    #                 key=f"foto_arquivo_{i}"
    #             )

    #             desc_foto = st.text_input(
    #                 f"Descrição {i+1}",
    #                 key=f"foto_descricao_{i}"
    #             )

    #             autor_foto = st.text_input(
    #                 f"Fotógrafo(a) {i+1}",
    #                 key=f"foto_autor_{i}"
    #             )

    #             # Atualizar sessão
    #             foto["arquivo"] = arquivo_foto
    #             foto["descricao"] = desc_foto
    #             foto["fotografo"] = autor_foto

    #             # Botão para remover foto
    #             if st.button(f"Remover foto {i+1}", key=f"foto_remover_{i}"):
    #                 st.session_state["fotos_relato"].pop(i)
    #                 st.rerun()

    #             st.divider()

    #         # ------------------------------------------------------
    #         # BOTÃO SALVAR
    #         # ------------------------------------------------------
    #         if st.button("💾 Salvar relato", type="primary", key="btn_salvar_relato"):
    #             salvar_relato()  # chama a função da PARTE 3

    # # Renderiza o fragment do corpo
    # corpo_dialogo()





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

# ???????????????????????
# with st.expander("Colunas do projeto"):
#     st.write(df_projeto.columns)


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')



# Título da página e identificação
col_titulo, col_identificacao = st.columns([3, 2])

with col_titulo:
    st.header("Marco Lógico")

with col_identificacao:
    st.markdown(
        f"<div style='text-align: right; margin-top: 30px;'>{df_projeto['codigo'].values[0]} - {df_projeto['sigla'].values[0]}</div>",
        unsafe_allow_html=True
    )



plano_trabalho, impactos, indicadores, monitoramento = st.tabs(["Plano de trabalho", "Impactos", "Indicadores", "Monitoramento"])




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
                    st.write(f"**{entrega.get('entrega', 'Entrega sem nome')}**")

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

                    # # Garante colunas
                    # if "Data de início" not in df.columns:
                    #     df["Data de início"] = ""
                    # if "Data de fim" not in df.columns:
                    #     df["Data de fim"] = ""

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

                            # # Usada pelo salvar_relato
                            # st.session_state["atividade_selecionada_drive"] = atividade_escolhida

                            # # Para controle (se quiser usar no futuro)
                            # st.session_state["atividade_selecionada_tabela_key"] = chave_tabela

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

            st.write(lista_entregas)

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
                st.write("Não há impactos de longo prazo cadastrados.")
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
                st.write("Não há impactos de curto prazo cadastrados.")
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




















# with impactos:

#     @st.dialog("Editar impactos", width="medium")
#     def editar_impactos():

#         tab_cadastrar, tab_editar = st.tabs(["Cadastrar impacto", "Editar impactos"])

#         # ========================================================
#         # CADASTRAR IMPACTO
#         # ========================================================
#         with tab_cadastrar:

#             tipo = st.radio(
#                 "Tipo de impacto",
#                 ["Longo prazo", "Curto prazo"],
#                 horizontal=True
#             )

#             texto_impacto = st.text_area(
#                 "Descrição do impacto",
#                 height=150
#             )

#             if st.button(
#                 "Salvar impacto",
#                 type="primary",
#                 icon=":material/save:"
#             ):

#                 if not texto_impacto.strip():
#                     st.warning("O impacto não pode estar vazio.")
#                     return

#                 chave = (
#                     "impactos_longo_prazo"
#                     if tipo == "Longo prazo"
#                     else "impactos_curto_prazo"
#                 )

#                 impacto = {
#                     "id": str(bson.ObjectId()),
#                     "texto": texto_impacto.strip()
#                 }

#                 resultado = col_projetos.update_one(
#                     {"codigo": st.session_state.projeto_atual},
#                     {"$push": {chave: impacto}}
#                 )

#                 if resultado.modified_count == 1:
#                     st.success("Impacto salvo com sucesso!")
#                     time.sleep(2)
#                     st.rerun()
#                 else:
#                     st.error("Erro ao salvar impacto.")

#         # ========================================================
#         # EDITAR IMPACTO
#         # ========================================================
#         with tab_editar:

#             tipo = st.radio(
#                 "Tipo de impacto",
#                 ["Longo prazo", "Curto prazo"],
#                 horizontal=True,
#                 key="tipo_editar_impacto"
#             )

#             chave = (
#                 "impactos_longo_prazo"
#                 if tipo == "Longo prazo"
#                 else "impactos_curto_prazo"
#             )

#             impactos = (
#                 df_projeto[chave].values[0]
#                 if chave in df_projeto.columns
#                 else []
#             )

#             if not impactos:
#                 st.write("Não há impactos cadastrados.")
#                 return

#             mapa_impactos = {
#                 f"{i['texto'][:80]}": i
#                 for i in impactos
#             }

#             impacto_label = st.selectbox(
#                 "Selecione o impacto",
#                 list(mapa_impactos.keys())
#             )

#             impacto_selecionado = mapa_impactos[impacto_label]

#             novo_texto = st.text_area(
#                 "Editar impacto",
#                 value=impacto_selecionado["texto"],
#                 height=150
#             )

#             if st.button(
#                 "Salvar alterações",
#                 type="primary",
#                 icon=":material/save:"
#             ):

#                 if not novo_texto.strip():
#                     st.warning("O impacto não pode estar vazio.")
#                     return

#                 resultado = col_projetos.update_one(
#                     {
#                         "codigo": st.session_state.projeto_atual,
#                         f"{chave}.id": impacto_selecionado["id"],
#                     },
#                     {
#                         "$set": {
#                             f"{chave}.$.texto": novo_texto.strip()
#                         }
#                     }
#                 )

#                 if resultado.modified_count == 1:
#                     st.success("Impacto atualizado com sucesso!")
#                     time.sleep(2)
#                     st.rerun()
#                 else:
#                     st.error("Erro ao atualizar impacto.")

#     # st.write('')

#     # Toggle do modo de edição

#     if st.session_state.tipo_usuario in ["admin", "equipe"]:

#         with st.container(horizontal=True, horizontal_alignment="right"):
#             modo_edicao = st.toggle("Modo de edição", key="editar_impactos")



#     # LISTAGEM DOS IMPACTOS DE LONGO PRAZO E CURTO PRAZO

#     col_lp, col_cp = st.columns(2, gap="large")

#     with col_lp:
#         st.subheader("Impactos de longo prazo")
#         st.write('*Entre 3 a 5 anos após o final do projeto*')

#         # Botões de edição só para admin e equipe. Por isso o try.
#         try:
#             if modo_edicao:

#                 with st.container(horizontal=True):
#                     if st.button("Editar impactos", icon=":material/edit:", type="secondary"):
#                         editar_impactos()
#         except:
#             pass


#         st.write('')

#         impactos_lp = (
#             df_projeto["impactos_longo_prazo"].values[0]
#             if "impactos_longo_prazo" in df_projeto.columns
#             else []
#         )

#         if not impactos_lp:
#             st.write("Não há impactos de longo prazo cadastrados")
#         else:
#             for i, impacto in enumerate(impactos_lp, start=1):
#                 st.write(f"**{i}**. {impacto['texto']}")




#     with col_cp:
#         st.subheader("Impactos de curto prazo")
#         st.write("*Durante o projeto ou até o final da subvenção*")

#         # Botões de edição só para admin e equipe. Por isso o try.
#         try:
#             if modo_edicao:
#                 with st.container(horizontal=True):
#                     if st.button("Editar impactos", icon=":material/edit:", type="secondary", key="editar_impactos_cp"):
#                         editar_impactos()
#         except:
#             pass


#         st.write('')

#         impactos_cp = (
#             df_projeto["impactos_curto_prazo"].values[0]
#             if "impactos_curto_prazo" in df_projeto.columns
#             else []
#         )

#         if not impactos_cp:
#             st.write("Não há impactos de curto prazo cadastrados")
#         else:
#             for i, impacto in enumerate(impactos_cp, start=1):
#                 st.write(f"**{i}**. {impacto['texto']}")





# ###################################################################################################
# INDICADORES
# ###################################################################################################

with indicadores:


    # --------------------------------------------------
    # PERMISSÃO
    # --------------------------------------------------
    usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]

    # Valor padrão
    modo_edicao = False

    # --------------------------------------------------
    # TOGGLE (somente para quem pode)
    # --------------------------------------------------
    if usuario_interno:
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
            st.caption("Nenhum indicador associado a este projeto.")

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
            st.caption("Não há indicadores cadastrados.")

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

