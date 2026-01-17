import streamlit as st
import pandas as pd
import streamlit_antd_components as sac
import time
import datetime

from funcoes_auxiliares import (
    conectar_mongo_cepf_gestao,
    sidebar_projeto,
    # ajustar_altura_data_editor,

    # Google Drive
    obter_servico_drive,
    obter_ou_criar_pasta,
    obter_pasta_pesquisas,
    obter_pasta_projeto,
    obter_pasta_relatos_atividades,
    enviar_arquivo_drive,
    gerar_link_drive
)




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




###########################################################################################################
# CARREGAMENTO DOS DADOS
###########################################################################################################

col_projetos = db["projetos"]

col_editais = db["editais"]

col_beneficios = db["beneficios"]

col_publicos = db["publicos"]

lista_publicos = list(col_publicos.find({}, {"_id": 0, "publico": 1}))

# SEMPRE insere a opção Outros
opcoes_publicos = sorted({p["publico"] for p in lista_publicos} - {"Outros"})
opcoes_publicos.append("Outros")

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



# ==========================================================
# LOCALIZA UMA ATIVIDADE NO DOCUMENTO DO PROJETO
# ==========================================================
def obter_atividade_mongo(projeto, id_atividade):
    """
    Percorre plano_trabalho → componentes → entregas → atividades
    e retorna a atividade correspondente ao id informado.
    """

    componentes = projeto.get("plano_trabalho", {}).get("componentes", [])

    for componente in componentes:
        for entrega in componente.get("entregas", []):
            for atividade in entrega.get("atividades", []):
                if atividade.get("id") == id_atividade:
                    return atividade

    return None


# ==========================================================
# LISTA OS RELATOS DE UMA ATIVIDADE (UI)
# ==========================================================
def listar_relatos_atividade(atividade, relatorio_numero):
    """
    Lista os relatos cadastrados para a atividade,
    filtrando pelo relatório atual.
    """

    relatos = atividade.get("relatos", [])

    relatos = [
        r for r in relatos
        if r.get("relatorio_numero") == relatorio_numero
    ]

    if not relatos:
        st.info("Nenhum relato cadastrado para esta atividade neste relatório.")
        return

    for relato in relatos:
        with st.expander(
            f"{relato.get('id_relato')} — {relato.get('quando')}"
        ):
            st.write(f"Relato: {relato.get('relato')}")
            st.write(f"Onde: {relato.get('onde', '—')}")
            st.write(f"Autor: {relato.get('autor', '—')}")

            if relato.get("anexos"):
                st.write("Anexos:")
                for a in relato["anexos"]:
                    st.write(f"- {a['nome_arquivo']}")

            if relato.get("fotos"):
                st.write("Fotografias:")
                for f in relato["fotos"]:
                    st.write(
                        f"- {f.get('nome_arquivo')} | "
                        f"{f.get('descricao', '')} | "
                        f"{f.get('fotografo', '')}"
                    )




# # Função para salvar ou editar um relato de
# import uuid
# from datetime import datetime
# import time
# import streamlit as st

# def salvar_relato():
#     # 1. Recuperar referências do st.session_state
#     projeto = st.session_state.get("projeto_mongo")
#     relatorio_numero = st.session_state.get("relatorio_numero")
#     relato_em_edicao = st.session_state.get("relato_em_edicao")
#     atividade_selecionada = st.session_state.get("atividade_selecionada")
    
#     if not atividade_selecionada or not projeto:
#         st.error("Erro: Dados do projeto ou atividade não encontrados.")
#         return

#     # 2. Coletar dados dos campos de texto
#     relato_texto = st.session_state.get("campo_relato", "")
#     quando = st.session_state.get("campo_quando", "")
#     onde = st.session_state.get("campo_onde", "")

#     # 3. Preparar serviços e localizar a pasta correta no Drive
#     try:
#         service_drive = obter_servico_drive()
#         nome_projeto_str = projeto.get("nome_do_projeto")
        
#         if not nome_projeto_str:
#             st.error("Erro: A chave 'nome_do_projeto' não foi encontrada.")
#             return

#         # Chamada para obter a pasta de relatos
#         pasta_relatos_id = obter_pasta_relatos_atividades(service_drive, nome_projeto_str)
        
#         # VALIDAÇÃO CRÍTICA: Verifica se o ID retornado é um ID de Drive válido (string longa)
#         # Se retornar "2" ou algo muito curto, a função auxiliar está com bug.
#         if not pasta_relatos_id or len(str(pasta_relatos_id)) < 5:
#             st.error(f"Erro de ID de pasta inválido recebido do Drive: '{pasta_relatos_id}'. Verifique as pastas do projeto.")
#             return

#     except Exception as e:
#         st.error(f"Erro técnico ao acessar Google Drive: {e}")
#         return

#     # 4. TRATAR ARQUIVOS EXISTENTES (SOMENTE NO BANCO DE DADOS)
#     fotos_finais = []
#     anexos_finais = []

#     if relato_em_edicao:
#         # IDs marcados para remoção através do checkbox 🗑️
#         ids_remover = st.session_state.get("fotos_a_remover", [])
        
#         # Filtramos a lista (Remoção lógica no banco, arquivo físico preservado no Drive)
#         fotos_finais = [
#             f for f in relato_em_edicao.get("fotos", []) 
#             if f.get("id_arquivo") not in ids_remover
#         ]
#         anexos_finais = relato_em_edicao.get("anexos", [])

#     # 5. UPLOAD DE NOVOS ANEXOS
#     novos_anexos_input = st.session_state.get("campo_anexos")
#     if novos_anexos_input:
#         for arq in novos_anexos_input:
#             with st.spinner(f"Enviando anexo: {arq.name}..."):
#                 id_drive = enviar_arquivo_drive(service_drive, arq.getvalue(), arq.name, pasta_relatos_id)
#                 anexos_finais.append({
#                     "id_arquivo": id_drive,
#                     "nome_arquivo": arq.name
#                 })

#     # 6. UPLOAD DE NOVAS FOTOGRAFIAS (Lista dinâmica)
#     novas_fotos_input = st.session_state.get("fotos_relato", [])
#     for item in novas_fotos_input:
#         if item.get("arquivo") is not None:
#             arq = item["arquivo"]
#             with st.spinner(f"Enviando foto: {arq.name}..."):
#                 id_foto_drive = enviar_arquivo_drive(service_drive, arq.getvalue(), arq.name, pasta_relatos_id)
#                 fotos_finais.append({
#                     "id_arquivo": id_foto_drive,
#                     "nome_arquivo": arq.name,
#                     "descricao": item.get("descricao", ""),
#                     "fotografo": item.get("fotografo", "")
#                 })

#     # 7. MONTAR OBJETO FINAL PARA O MONGODB
#     if relato_em_edicao:
#         id_relato = relato_em_edicao.get("id_relato")
#         relato_final_obj = relato_em_edicao.copy()
#         relato_final_obj.update({
#             "relato": relato_texto, "quando": quando, "onde": onde,
#             "fotos": fotos_finais, "anexos": anexos_finais,
#             "data_ultima_edicao": datetime.now()
#         })
#     else:
#         id_relato = str(uuid.uuid4())[:8].upper()
#         relato_final_obj = {
#             "id_relato": id_relato,
#             "relatorio_numero": relatorio_numero,
#             "relato": relato_texto, "quando": quando, "onde": onde,
#             "fotos": fotos_finais, "anexos": anexos_finais,
#             "status_relato": "Enviado", "data_criacao": datetime.now()
#         }

#     # 8. PERSISTÊNCIA NO MONGODB
#     try:
#         db = conectar_mongo_cepf_gestao()
        
#         if relato_em_edicao:
#             db.projetos.update_one(
#                 {"_id": projeto["_id"]},
#                 {"$set": {"plano_trabalho.componentes.$[].entregas.$[].atividades.$[atv].relatos.$[rel]": relato_final_obj}},
#                 array_filters=[
#                     {"atv.atividade": atividade_selecionada["atividade"]},
#                     {"rel.id_relato": id_relato}
#                 ]
#             )
#         else:
#             db.projetos.update_one(
#                 {"_id": projeto["_id"], "plano_trabalho.componentes.entregas.atividades.atividade": atividade_selecionada["atividade"]},
#                 {"$push": {"plano_trabalho.componentes.$[].entregas.$[].atividades.$[atv].relatos": relato_final_obj}},
#                 array_filters=[{"atv.atividade": atividade_selecionada["atividade"]}]
#             )

#         st.success("Relato salvo com sucesso!")
        
#         # 9. Limpeza de estados
#         for key in ["relato_em_edicao", "relato_edicao_inicializado", "fotos_a_remover", "fotos_relato"]:
#             st.session_state[key] = None if "em_edicao" in key else []
        
#         time.sleep(1)
#         st.rerun()

#     except Exception as e:
#         st.error(f"Erro ao salvar no banco de dados: {e}")


















# def salvar_relato():
#     """
#     Salva ou edita um relato de atividade.

#     - Se NÃO houver relato_em_edicao:
#         cria novo relato
#     - Se houver relato_em_edicao:
#         edita relato existente

#     Em ambos os casos:
#     - valida campos obrigatórios
#     - envia anexos e fotos ao Google Drive
#     - grava no MongoDB
#     - limpa o session_state
#     - executa rerun ao final
#     """

#     # --------------------------------------------------
#     # 1. CAMPOS DO FORMULÁRIO
#     # --------------------------------------------------
#     texto_relato = st.session_state.get("campo_relato", "")
#     quando = st.session_state.get("campo_quando", "")
#     onde = st.session_state.get("campo_onde", "")
#     anexos = st.session_state.get("campo_anexos", [])
#     fotos = st.session_state.get("fotos_relato", [])

#     relato_em_edicao = st.session_state.get("relato_em_edicao")

#     # --------------------------------------------------
#     # 2. VALIDAÇÕES
#     # --------------------------------------------------
#     erros = []
#     if not texto_relato.strip():
#         erros.append("O campo Relato é obrigatório.")
#     if not quando.strip():
#         erros.append("O campo Quando é obrigatório.")
#     if not onde.strip():
#         erros.append("O campo Onde é obrigatório.")

#     if erros:
#         for e in erros:
#             st.error(e)
#         return

#     # --------------------------------------------------
#     # 3. CONEXÃO COM GOOGLE DRIVE
#     # --------------------------------------------------
#     servico = obter_servico_drive()

#     projeto = st.session_state.get("projeto_mongo")
#     if not projeto:
#         st.error("Projeto não encontrado na sessão.")
#         return

#     codigo = projeto["codigo"]
#     sigla = projeto["sigla"]

#     pasta_projeto_id = obter_pasta_projeto(
#         servico,
#         codigo,
#         sigla
#     )

#     pasta_relatos_id = obter_ou_criar_pasta(
#         servico,
#         "Relatos_atividades",
#         pasta_projeto_id
#     )

#     # --------------------------------------------------
#     # 4. ATIVIDADE SELECIONADA
#     # --------------------------------------------------
#     atividade = st.session_state.get("atividade_selecionada_drive")
#     if not atividade:
#         st.error("Atividade não selecionada.")
#         return

#     id_atividade = atividade.get("id")

#     atividade_mongo = obter_atividade_mongo(projeto, id_atividade)
#     if not atividade_mongo:
#         st.error("Atividade não encontrada no banco de dados.")
#         return

#     # --------------------------------------------------
#     # 5. DEFINE ID DO RELATO E PASTA
#     # --------------------------------------------------
#     if relato_em_edicao:
#         # EDIÇÃO
#         id_relato = relato_em_edicao["id_relato"]
#     else:
#         # CRIAÇÃO — gera ID globalmente único
#         maior_numero = 0

#         for componente in projeto["plano_trabalho"]["componentes"]:
#             for entrega in componente["entregas"]:
#                 for atividade_tmp in entrega["atividades"]:
#                     for r in atividade_tmp.get("relatos", []):
#                         rid = r.get("id_relato", "")
#                         if rid.startswith("relato_"):
#                             try:
#                                 n = int(rid.replace("relato_", ""))
#                                 maior_numero = max(maior_numero, n)
#                             except ValueError:
#                                 pass

#         id_relato = f"relato_{maior_numero + 1:03d}"

#     pasta_relato_id = obter_ou_criar_pasta(
#         servico,
#         id_relato,
#         pasta_relatos_id
#     )

#     # --------------------------------------------------
#     # 6. UPLOAD DE ANEXOS
#     # --------------------------------------------------
#     lista_anexos = []

#     if anexos:
#         pasta_anexos_id = obter_ou_criar_pasta(
#             servico,
#             "anexos",
#             pasta_relato_id
#         )

#         for arq in anexos:
#             id_drive = enviar_arquivo_drive(servico, pasta_anexos_id, arq)
#             if id_drive:
#                 lista_anexos.append({
#                     "nome_arquivo": arq.name,
#                     "id_arquivo": id_drive
#                 })

#     # --------------------------------------------------
#     # 7. UPLOAD DE FOTOGRAFIAS
#     # --------------------------------------------------
#     lista_fotos = []

#     fotos_validas = [
#         f for f in fotos
#         if f.get("arquivo") is not None
#     ]

#     if fotos_validas:
#         pasta_fotos_id = obter_ou_criar_pasta(
#             servico,
#             "fotos",
#             pasta_relato_id
#         )

#         for foto in fotos_validas:
#             arq = foto["arquivo"]
#             id_drive = enviar_arquivo_drive(servico, pasta_fotos_id, arq)

#             if id_drive:
#                 lista_fotos.append({
#                     "nome_arquivo": arq.name,
#                     "descricao": foto.get("descricao", ""),
#                     "fotografo": foto.get("fotografo", ""),
#                     "id_arquivo": id_drive
#                 })

#     # --------------------------------------------------
#     # 8. CRIA OU ATUALIZA RELATO
#     # --------------------------------------------------
#     if relato_em_edicao:
#         # Atualiza relato existente
#         relato_em_edicao["relato"] = texto_relato.strip()
#         relato_em_edicao["quando"] = quando.strip()
#         relato_em_edicao["onde"] = onde.strip()

#         if lista_anexos:
#             relato_em_edicao.setdefault("anexos", []).extend(lista_anexos)

#         if lista_fotos:
#             relato_em_edicao.setdefault("fotos", []).extend(lista_fotos)

#     else:
#         # Cria novo relato
#         novo_relato = {
#             "id_relato": id_relato,
#             "status_relato": "aberto",
#             "relatorio_numero": st.session_state.get("relatorio_numero"),
#             "relato": texto_relato.strip(),
#             "quando": quando.strip(),
#             "onde": onde.strip(),
#             "autor": st.session_state.get("nome", "Usuário")
#         }

#         if lista_anexos:
#             novo_relato["anexos"] = lista_anexos

#         if lista_fotos:
#             novo_relato["fotos"] = lista_fotos

#         atividade_mongo.setdefault("relatos", []).append(novo_relato)

#     # --------------------------------------------------
#     # 9. SALVA NO MONGO
#     # --------------------------------------------------
#     col_projetos.update_one(
#         {"codigo": codigo},
#         {
#             "$set": {
#                 "plano_trabalho.componentes": projeto["plano_trabalho"]["componentes"]
#             }
#         }
#     )

#     # --------------------------------------------------
#     # 10. LIMPEZA DO SESSION_STATE
#     # --------------------------------------------------
#     for chave in [
#         "campo_relato",
#         "campo_quando",
#         "campo_onde",
#         "campo_anexos",
#         "fotos_relato",
#         "relato_em_edicao"
#     ]:
#         if chave in st.session_state:
#             del st.session_state[chave]

#     for k in list(st.session_state.keys()):
#         if k.startswith("foto_"):
#             del st.session_state[k]

#     # --------------------------------------------------
#     # 11. FINALIZAÇÃO
#     # --------------------------------------------------
#     st.success("Relato salvo com sucesso.", icon=":material/check:")
#     time.sleep(3)
#     st.rerun()






















# Função para salvar o relato
def salvar_relato():
    """
    Salva um relato de atividade:
    - valida campos obrigatórios
    - cria pastas no Google Drive (Relatos_atividades/relato_xxx)
    - envia anexos e fotos
    - grava no MongoDB
    - limpa o session_state
    - executa rerun ao final
    """

    # --------------------------------------------------
    # 1. CAMPOS DO FORMULÁRIO
    # --------------------------------------------------
    texto_relato = st.session_state.get("campo_relato", "")
    quando = st.session_state.get("campo_quando", "")
    onde = st.session_state.get("campo_onde", "")
    anexos = st.session_state.get("campo_anexos", [])
    fotos = st.session_state.get("fotos_relato", [])

    # --------------------------------------------------
    # 2. VALIDAÇÕES
    # --------------------------------------------------
    erros = []
    if not texto_relato.strip():
        erros.append("O campo Relato é obrigatório.")
    if not quando.strip():
        erros.append("O campo Quando é obrigatório.")

    if erros:
        for e in erros:
            st.error(e)
        return

    # --------------------------------------------------
    # 3. CONEXÃO COM GOOGLE DRIVE
    # --------------------------------------------------
    servico = obter_servico_drive()

    projeto = st.session_state.get("projeto_mongo")
    if not projeto:
        st.error("Projeto não encontrado na sessão.")
        return

    codigo = projeto["codigo"]
    sigla = projeto["sigla"]

    # Pasta do projeto (padrão já usado em Locais)
    pasta_projeto_id = obter_pasta_projeto(
        servico,
        codigo,
        sigla
    )

    # Pasta Relatos_atividades
    pasta_relatos_id = obter_ou_criar_pasta(
        servico,
        "Relatos_atividades",
        pasta_projeto_id
    )

    # --------------------------------------------------
    # 4. ATIVIDADE SELECIONADA
    # --------------------------------------------------
    atividade = st.session_state.get("atividade_selecionada_drive")
    if not atividade:
        st.error("Atividade não selecionada.")
        return

    id_atividade = atividade.get("id")

    # --------------------------------------------------
    # 5. LOCALIZA ATIVIDADE NO MONGO
    # --------------------------------------------------
    atividade_mongo = obter_atividade_mongo(projeto, id_atividade)
    if not atividade_mongo:
        st.error("Atividade não encontrada no banco de dados.")
        return

    # relatos_existentes = atividade_mongo.get("relatos", [])
    # numero = len(relatos_existentes) + 1
    # id_relato = f"relato_{numero:03d}"

    # --------------------------------------------------
    # GERA ID DE RELATO GLOBALMENTE ÚNICO
    # --------------------------------------------------
    maior_numero = 0

    for componente in projeto["plano_trabalho"]["componentes"]:
        for entrega in componente["entregas"]:
            for atividade in entrega["atividades"]:
                for relato in atividade.get("relatos", []):
                    id_existente = relato.get("id_relato", "")
                    if id_existente.startswith("relato_"):
                        try:
                            numero = int(id_existente.replace("relato_", ""))
                            maior_numero = max(maior_numero, numero)
                        except ValueError:
                            pass

    # Próximo número disponível
    novo_numero = maior_numero + 1
    id_relato = f"relato_{novo_numero:03d}"




    # --------------------------------------------------
    # 6. PASTA DO RELATO (DIRETAMENTE EM Relatos_atividades)
    # --------------------------------------------------
    pasta_relato_id = obter_ou_criar_pasta(
        servico,
        id_relato,
        pasta_relatos_id
    )


    # --------------------------------------------------
    # 7. UPLOAD DE ANEXOS
    # --------------------------------------------------
    lista_anexos = []

    if anexos:
        pasta_anexos_id = obter_ou_criar_pasta(
            servico,
            "anexos",
            pasta_relato_id
        )

        for arq in anexos:
            id_drive = enviar_arquivo_drive(
                servico,
                pasta_anexos_id,
                arq
            )

            if id_drive:
                lista_anexos.append({
                    "nome_arquivo": arq.name,
                    "id_arquivo": id_drive
                })



    # --------------------------------------------------
    # 8. UPLOAD DE FOTOGRAFIAS
    # --------------------------------------------------
    lista_fotos = []

    fotos_validas = [
        f for f in fotos
        if f.get("arquivo") is not None
    ]



    if fotos_validas:

        # --------------------------------------------------
        # CRIA PASTA FOTOS (SE NÃO EXISTIR)
        # --------------------------------------------------
        # Verifica se já existe antes
        consulta = (
            f"name='fotos' and "
            f"'{pasta_relato_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and trashed=false"
        )

        resultado = servico.files().list(
            q=consulta,
            fields="files(id)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        arquivos = resultado.get("files", [])

        if arquivos:
            pasta_fotos_id = arquivos[0]["id"]
        else:
            # Cria pasta
            pasta_fotos_id = obter_ou_criar_pasta(
                servico,
                "fotos",
                pasta_relato_id
            )

            # DEFINE PERMISSÃO PÚBLICA (SÓ NA CRIAÇÃO)
            garantir_permissao_publica_leitura(servico, pasta_fotos_id)




    # if fotos_validas:
    #     pasta_fotos_id = obter_ou_criar_pasta(
    #         servico,
    #         "fotos",
    #         pasta_relato_id
    #     )

        for foto in fotos_validas:
            arq = foto["arquivo"]

            id_drive = enviar_arquivo_drive(
                servico,
                pasta_fotos_id,
                arq
            )

            if id_drive:
                lista_fotos.append({
                    "nome_arquivo": arq.name,
                    "descricao": foto.get("descricao", ""),
                    "fotografo": foto.get("fotografo", ""),
                    "id_arquivo": id_drive
                })




    # --------------------------------------------------
    # 9. OBJETO FINAL DO RELATO
    # --------------------------------------------------
    novo_relato = {
        "id_relato": id_relato,
        "status_relato": "aberto",  # status inicial do relato
        "relatorio_numero": st.session_state.get("relatorio_numero"),
        "relato": texto_relato.strip(),
        "quando": quando.strip(),
        "onde": onde.strip(),
        "autor": st.session_state.get("nome", "Usuário")
    }

    if lista_anexos:
        novo_relato["anexos"] = lista_anexos

    if lista_fotos:
        novo_relato["fotos"] = lista_fotos

    atividade_mongo.setdefault("relatos", []).append(novo_relato)

    col_projetos.update_one(
        {"codigo": codigo},
        {
            "$set": {
                "plano_trabalho.componentes": projeto["plano_trabalho"]["componentes"]
            }
        }
    )

    # --------------------------------------------------
    # 10. LIMPEZA DO SESSION_STATE (CRÍTICO)
    # --------------------------------------------------
    for chave in [
        "campo_relato",
        "campo_quando",
        "campo_onde",
        "campo_anexos",
        "fotos_relato"
    ]:
        if chave in st.session_state:
            del st.session_state[chave]

    # Remove chaves dinâmicas das fotos
    for k in list(st.session_state.keys()):
        if k.startswith("foto_"):
            del st.session_state[k]

    # --------------------------------------------------
    # 11. FINALIZAÇÃO
    # --------------------------------------------------
    st.success("Relato salvo com sucesso.", icon=":material/check:")
    time.sleep(3)
    st.rerun()

# Função auxiliar para o salvar_relato, que dá permissão de leitura pública para a pasta de fotos no ato da criação da pasta no drivce
def garantir_permissao_publica_leitura(servico, pasta_id):
    """
    Define permissão:
    Qualquer pessoa com o link → Leitor
    (somente se ainda não existir)
    """

    try:
        servico.permissions().create(
            fileId=pasta_id,
            body={
                "type": "anyone",
                "role": "reader"
            },
            supportsAllDrives=True
        ).execute()
    except Exception:
        # Silencioso: se já existir ou falhar, não quebra o fluxo
        pass




# ==========================================================================================
# DIÁLOGO: RELATAR / EDITAR ATIVIDADE
# ==========================================================================================



# import streamlit as st

# @st.dialog("Relatar atividade", width="large")
# def dialog_relatos():
#     # 1. INICIALIZAÇÃO OBRIGATÓRIA (Não reseta o que já existe)
#     if "fotos_relato" not in st.session_state:
#         st.session_state["fotos_relato"] = []
#     if "fotos_a_remover" not in st.session_state:
#         st.session_state["fotos_a_remover"] = []
    
#     projeto = st.session_state.get("projeto_mongo")
#     if not projeto:
#         st.error("Projeto não encontrado.")
#         return

#     relato_em_edicao = st.session_state.get("relato_em_edicao")

#     # ==================================================
#     # 2. SELEÇÃO DE ATIVIDADE (Ajustado para capturar sempre)
#     # ==================================================
#     if not relato_em_edicao:
#         atividades = []
#         for comp in projeto.get("plano_trabalho", {}).get("componentes", []):
#             for ent in comp.get("entregas", []):
#                 for atv in ent.get("atividades", []):
#                     atividades.append(atv)

#         # FUNÇÃO DE SUPORTE: Localiza o index da atividade já selecionada
#         def get_atv_index():
#             sel = st.session_state.get("atividade_selecionada")
#             if sel and sel in atividades:
#                 return atividades.index(sel) + 1
#             return 0

#         # O SELECTBOX ATUALIZA A KEY "atividade_selecionada" DIRETAMENTE
#         st.selectbox(
#             "Selecione a atividade",
#             options=[None] + atividades,
#             format_func=lambda x: "— selecione —" if x is None else x["atividade"],
#             index=get_atv_index(),
#             key="atividade_selecionada", # Salvamos direto na chave que o código usa
#         )

#         # VALIDAÇÃO: Se a chave ainda for None, paramos aqui
#         if st.session_state.get("atividade_selecionada") is None:
#             st.warning("⚠️ Selecione uma atividade na lista acima.")
#             return
#     else:
#         # MODO EDIÇÃO: Forçamos a atividade que veio do banco
#         if "atividade_selecionada" not in st.session_state:
#              st.session_state["atividade_selecionada"] = relato_em_edicao.get("atividade_ref")
        
#         atv_nome = st.session_state["atividade_selecionada"].get("atividade", "Atividade")
#         st.info(f"Editando relato da atividade: **{atv_nome}**")

#     st.divider()

#     # ==================================================
#     # 3. RESTANTE DO FORMULÁRIO (Só renderiza após a validação acima)
#     # ==================================================
#     # PRÉ-CARREGAMENTO DE CAMPOS NA EDIÇÃO
#     if relato_em_edicao and not st.session_state.get("relato_edicao_inicializado"):
#         st.session_state["campo_relato"] = relato_em_edicao.get("relato", "")
#         st.session_state["campo_quando"] = relato_em_edicao.get("quando", "")
#         st.session_state["campo_onde"] = relato_em_edicao.get("onde", "")
#         st.session_state["relato_edicao_inicializado"] = True

#     st.text_area("Relato", placeholder="Descreva o que foi feito", key="campo_relato")

#     col_q, col_o = st.columns(2)
#     with col_q:
#         st.text_input("Quando?", key="campo_quando")
#     with col_o:
#         st.text_input("Onde?", key="campo_onde")

#     st.divider()

#     # ==================================================
#     # 4. ANEXOS E NOVAS FOTOS
#     # ==================================================
#     st.markdown("### Anexos")
#     st.file_uploader("Arquivos", accept_multiple_files=True, key="campo_anexos")

#     st.subheader("Novas Fotografias")
#     if st.button("Adicionar campo de foto", icon=":material/add_a_photo:"):
#         st.session_state["fotos_relato"].append({"arquivo": None, "descricao": "", "fotografo": ""})

#     for i, foto_item in enumerate(st.session_state["fotos_relato"]):
#         with st.container(border=True):
#             st.session_state["fotos_relato"][i]["arquivo"] = st.file_uploader(f"Foto {i+1}", type=["jpg","png"], key=f"f_arq_{i}")
#             c1, c2 = st.columns([0.6, 0.4])
#             st.session_state["fotos_relato"][i]["descricao"] = c1.text_input("Descrição", key=f"f_desc_{i}")
#             st.session_state["fotos_relato"][i]["fotografo"] = c2.text_input("Fotógrafo(a)", key=f"f_autor_{i}")

#     if st.button("Salvar relato", type="primary", use_container_width=True):
#         salvar_relato()



















# @st.dialog("Relatar atividade", width="large")
# def dialog_relatos():
#     # 1. Validações Iniciais
#     projeto = st.session_state.get("projeto_mongo")
#     if not projeto:
#         st.error("Projeto não encontrado.")
#         return

#     relato_em_edicao = st.session_state.get("relato_em_edicao")

#     # ==================================================
#     # 0. PRÉ-CARREGAMENTO (LOGICA DE EDIÇÃO)
#     # ==================================================
#     if relato_em_edicao and not st.session_state.get("relato_edicao_inicializado"):
#         # Injetamos os valores do banco diretamente nas chaves dos widgets
#         st.session_state["campo_relato"] = relato_em_edicao.get("relato", "")
#         st.session_state["campo_quando"] = relato_em_edicao.get("quando", "")
#         st.session_state["campo_onde"] = relato_em_edicao.get("onde", "")
        
#         # Inicializamos a lista de controle de remoção de fotos e novas fotos
#         st.session_state["fotos_a_remover"] = []
#         st.session_state["fotos_relato"] = []
        
#         # Travamos a inicialização para permitir que o usuário edite sem ser sobrescrito
#         st.session_state["relato_edicao_inicializado"] = True

#     # ==================================================
#     # 1. SELEÇÃO DE ATIVIDADE
#     # ==================================================
#     if not relato_em_edicao:
#         # MODO CRIAÇÃO → usuário escolhe a atividade
#         atividades = []
#         for componente in projeto["plano_trabalho"]["componentes"]:
#             for entrega in componente["entregas"]:
#                 for atividade in entrega["atividades"]:
#                     atividades.append(atividade)

#         if not atividades:
#             st.info("Nenhuma atividade cadastrada.")
#             return

#         atividade_selecionada = st.selectbox(
#             "Selecione a atividade",
#             options=[None] + atividades,
#             format_func=lambda x: "— selecione —" if x is None else x["atividade"],
#             key="atividade_select_dialog"
#         )

#         if atividade_selecionada is None:
#             st.info("Selecione uma atividade para continuar.")
#             return

#         st.session_state["atividade_selecionada"] = atividade_selecionada
#     else:
#         # MODO EDIÇÃO → Exibe apenas qual atividade está sendo editada
#         atv_nome = st.session_state.get("atividade_selecionada", {}).get("atividade", "Atividade")
#         st.info(f"Editando relato da atividade: **{atv_nome}**")

#     st.divider()

#     # ==================================================
#     # 2. CAMPOS PRINCIPAIS
#     # ==================================================
#     st.text_area(
#         "Relato",
#         placeholder="Descreva o que foi feito",
#         key="campo_relato" # Já preenchido pelo session_state no passo 0
#     )

#     col_q, col_o = st.columns(2)
#     with col_q:
#         st.text_input("Quando?", key="campo_quando")
#     with col_o:
#         st.text_input("Onde?", key="campo_onde")

#     st.divider()

#     # ==================================================
#     # 3. ANEXOS (UPLOAD E EXISTENTES)
#     # ==================================================
#     st.markdown("### Anexos")
    
#     # Exibir anexos que já estão no Drive (apenas visualização)
#     if relato_em_edicao and "anexos" in relato_em_edicao:
#         anexos_existentes = relato_em_edicao.get("anexos", [])
#         if anexos_existentes:
#             with st.expander("Ver anexos já enviados", expanded=False):
#                 for a in anexos_existentes:
#                     link = gerar_link_drive(a.get("id_arquivo"))
#                     st.markdown(f"📎 [{a.get('nome_arquivo','arquivo')}]({link})")

#     st.file_uploader(
#         "Adicionar novos anexos (PDF, Word, Excel, etc)",
#         type=["pdf", "docx", "xlsx", "csv", "jpg", "jpeg", "png"],
#         accept_multiple_files=True,
#         key="campo_anexos"
#     )

#     st.divider()

#     # ==================================================
#     # 4. FOTOGRAFIAS EXISTENTES (COM OPÇÃO DE REMOVER REGISTRO)
#     # ==================================================
#     if relato_em_edicao and "fotos" in relato_em_edicao:
#         fotos_existentes = relato_em_edicao.get("fotos", [])
#         if fotos_existentes:
#             st.subheader("Fotografias já enviadas")
#             st.caption("Marque o checkbox para remover o registro da foto ao salvar.")

#             # Inicializa lista de remoção se não existir por segurança
#             if "fotos_a_remover" not in st.session_state:
#                 st.session_state["fotos_a_remover"] = []

#             for f in fotos_existentes:
#                 id_arq = f.get("id_arquivo")
#                 if not id_arq: continue
                
#                 with st.container(border=True):
#                     c_info, c_del = st.columns([0.85, 0.15])
                    
#                     nome = f.get("nome_arquivo", "foto")
#                     link = gerar_link_drive(id_arq)
                    
#                     c_info.markdown(f"🖼️ **[{nome}]({link})**")
#                     if f.get("descricao"): c_info.caption(f.get("descricao"))
                    
#                     # Logica de marcação para remoção
#                     remover = c_del.checkbox("🗑️", key=f"del_foto_{id_arq}", help="Remover registro")
#                     if remover:
#                         if id_arq not in st.session_state["fotos_a_remover"]:
#                             st.session_state["fotos_a_remover"].append(id_arq)
#                     else:
#                         if id_arq in st.session_state["fotos_a_remover"]:
#                             st.session_state["fotos_a_remover"].remove(id_arq)

#     # ==================================================
#     # 5. NOVAS FOTOGRAFIAS (UPLOAD)
#     # ==================================================
#     st.subheader("Adicionar novas fotos")

#     if st.button("Adicionar campo de fotografia", icon=":material/add_a_photo:"):
#         st.session_state["fotos_relato"].append({
#             "arquivo": None, "descricao": "", "fotografo": ""
#         })

#     for i, foto in enumerate(st.session_state["fotos_relato"]):
#         with st.container(border=True):
#             foto["arquivo"] = st.file_uploader(f"Arquivo da foto {i+1}", type=["jpg", "jpeg", "png"], key=f"nova_foto_{i}")
#             foto["descricao"] = st.text_input("Descrição", key=f"nova_desc_{i}")
#             foto["fotografo"] = st.text_input("Fotógrafo(a)", key=f"nova_autor_{i}")

#     st.divider()

#     # ==================================================
#     # 6. AÇÃO FINAL
#     # ==================================================
#     if st.button("Salvar relato", type="primary", icon=":material/save:", width="stretch"):
#         # A função salvar_relato deve ler st.session_state["fotos_a_remover"]
#         # para filtrar a lista original de fotos antes de fazer o update no Mongo.
#         salvar_relato()
















@st.dialog("Relatar atividade", width="large")
def dialog_relatos():

    projeto = st.session_state.get("projeto_mongo")
    if not projeto:
        st.error("Projeto não encontrado.")
        return

    relato_em_edicao = st.session_state.get("relato_em_edicao")

    # ==================================================
    # 0. PRÉ-CARREGAMENTO (ANTES DE QUALQUER WIDGET)
    # ==================================================
    if relato_em_edicao and not st.session_state.get("relato_edicao_inicializado"):

        # Campos de texto
        st.session_state["campo_relato"] = relato_em_edicao.get("relato", "")
        st.session_state["campo_quando"] = relato_em_edicao.get("quando", "")
        st.session_state["campo_onde"] = relato_em_edicao.get("onde", "")

        # Inicializa estrutura de novas fotos (upload)
        st.session_state["fotos_relato"] = []

        st.session_state["relato_edicao_inicializado"] = True

    # ==================================================
    # 1. SELEÇÃO DE ATIVIDADE
    # ==================================================
    if not relato_em_edicao:
        # MODO CRIAÇÃO
        atividades = []

        for componente in projeto["plano_trabalho"]["componentes"]:
            for entrega in componente["entregas"]:
                for atividade in entrega["atividades"]:
                    atividades.append(atividade)

        if not atividades:
            st.info("Nenhuma atividade cadastrada.")
            time.sleep(3)
            return

        atividade_selecionada = st.selectbox(
            "Selecione a atividade",
            options=[None] + atividades,
            format_func=lambda x: "— selecione —" if x is None else x["atividade"],
            key="atividade_select_dialog"
        )

        if atividade_selecionada is None:
            st.info("Selecione uma atividade para continuar.")
            return

        st.session_state["atividade_selecionada"] = atividade_selecionada
        st.session_state["atividade_selecionada_drive"] = atividade_selecionada

    else:
        # MODO EDIÇÃO — atividade já definida
        atividade_selecionada = st.session_state.get("atividade_selecionada")

    st.divider()

    # ==================================================
    # 2. CAMPOS PRINCIPAIS
    # ==================================================
    st.text_area(
        "Relato",
        placeholder="Descreva o que foi feito",
        key="campo_relato"
    )

    st.text_input(
        "Quando?",
        key="campo_quando"
    )

    st.text_input(
        "Onde?",
        key="campo_onde"
    )

    st.divider()

    # ==================================================
    # 3. ANEXOS (INPUT ORIGINAL)
    # ==================================================
    st.markdown("Anexos")

    st.file_uploader(
        "Arquivos",
        type=["pdf", "docx", "xlsx", "csv", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="campo_anexos"
    )

    # Anexos já existentes (somente visualização)
    if relato_em_edicao and "anexos" in relato_em_edicao:
        anexos_existentes = relato_em_edicao.get("anexos", [])
        if anexos_existentes:
            st.markdown("**Anexos já enviados:**")
            for a in anexos_existentes:
                id_arquivo = a.get("id_arquivo")
                if not id_arquivo:
                    continue
                link = gerar_link_drive(id_arquivo)
                st.markdown(
                    f"- [{a.get('nome_arquivo','arquivo')}]({link})",
                    unsafe_allow_html=True
                )

    st.divider()

    # ==================================================
    # 4. FOTOGRAFIAS (INPUT ORIGINAL)
    # ==================================================
    st.subheader("Fotografias")

    if "fotos_relato" not in st.session_state:
        st.session_state["fotos_relato"] = []

    if st.button("Adicionar fotografia", icon=":material/add_a_photo:"):
        st.session_state["fotos_relato"].append({
            "arquivo": None,
            "descricao": "",
            "fotografo": ""
        })

    for i, foto in enumerate(st.session_state["fotos_relato"]):
        with st.container(border=True):

            foto["arquivo"] = st.file_uploader(
                "Selecione a foto",
                type=["jpg", "jpeg", "png"],
                key=f"foto_arquivo_{i}"
            )

            foto["descricao"] = st.text_input(
                "Descrição da foto",
                key=f"foto_descricao_{i}"
            )

            foto["fotografo"] = st.text_input(
                "Nome do(a) fotógrafo(a)",
                key=f"foto_autor_{i}"
            )

    # Fotografias já existentes (somente visualização)
    if relato_em_edicao and "fotos" in relato_em_edicao:

        fotos_existentes = relato_em_edicao.get("fotos", [])

        if fotos_existentes:
            st.markdown("**Fotografias já enviadas:**")

            for f in fotos_existentes:
                id_arquivo = f.get("id_arquivo")
                if not id_arquivo:
                    continue

                link = gerar_link_drive(id_arquivo)

                nome = f.get("nome_arquivo", "")
                descricao = f.get("descricao", "")
                fotografo = f.get("fotografo", "")

                linha = f"[{nome}]({link})"
                if descricao:
                    linha += f" | {descricao}"
                if fotografo:
                    linha += f" | {fotografo}"

                st.markdown(f"- {linha}", unsafe_allow_html=True)

    st.divider()

    # ==================================================
    # 5. AÇÃO FINAL
    # ==================================================
    if st.button(
        "Salvar relato",
        type="primary",
        icon=":material/save:",
        width="stretch"
    ):
        salvar_relato()























# # ==========================================================================================
# # DIÁLOGO: RELATAR ATIVIDADE
# # ==========================================================================================
# @st.dialog("Relatar atividade", width="large")
# def dialog_relatos():

#     projeto = st.session_state.get("projeto_mongo")
#     if not projeto:
#         st.error("Projeto não encontrado.")
#         return

#     # --------------------------------------------------
#     # 1. MONTA LISTA DE ATIVIDADES
#     # --------------------------------------------------
#     atividades = []

#     for componente in projeto["plano_trabalho"]["componentes"]:
#         for entrega in componente["entregas"]:
#             for atividade in entrega["atividades"]:
#                 atividades.append({
#                     "id": atividade["id"],
#                     "atividade": atividade["atividade"],
#                     "componente": componente["componente"],
#                     "entrega": entrega["entrega"],
#                     "data_inicio": atividade.get("data_inicio"),
#                     "data_fim": atividade.get("data_fim"),
#                     "relatos": atividade.get("relatos", [])
#                 })

#     if not atividades:
#         st.info("Nenhuma atividade cadastrada.")
#         time.sleep(3)
#         return

#     # --------------------------------------------------
#     # 2. SELECTBOX COM OPÇÃO VAZIA
#     # --------------------------------------------------
#     atividades_com_placeholder = (
#         [{"id": None, "atividade": ""}]
#         + atividades
#     )

#     atividade_selecionada = st.selectbox(
#         "Selecione a atividade",
#         atividades_com_placeholder,
#         format_func=lambda x: x["atividade"],
#         key="atividade_select_dialog"
#     )

#     # Salva no session_state (mesmo vazia, para validação)
#     st.session_state["atividade_selecionada"] = atividade_selecionada
#     st.session_state["atividade_selecionada_drive"] = atividade_selecionada

#     # ==================================================
#     # 3. FORMULÁRIO DO RELATO
#     # ==================================================
#     @st.fragment
#     def corpo_formulario():

#         # -----------------------------
#         # CAMPOS BÁSICOS
#         # -----------------------------
#         st.text_area(
#             "Relato",
#             placeholder="Descreva o que foi feito",
#             key="campo_relato"
#         )

#         st.text_input(
#             "Quando?",
#             key="campo_quando"
#         )

#         st.text_input(
#             "Onde?",
#             key="campo_onde"
#         )

#         st.divider()

#         # -----------------------------
#         # ANEXOS
#         # -----------------------------
#         st.markdown("Anexos")
#         st.file_uploader(
#             "Selecione todos os arquivos relevantes para esse relato: listas de presença, relatórios, publicações, etc.",
#             type=["pdf", "docx", "xlsx", "csv", "jpg", "jpeg", "png"],
#             accept_multiple_files=True,
#             key="campo_anexos"
#         )

#         st.divider()


#         # -----------------------------
#         # FOTOGRAFIAS
#         # -----------------------------
#         st.write("Fotografias")

#         if "fotos_relato" not in st.session_state:
#             st.session_state["fotos_relato"] = []

#         # Botão para adicionar
#         if st.button("Adicionar fotografia", icon=":material/add_a_photo:"):
#             # Usamos um ID único para cada foto em vez de apenas o índice
#             import uuid
#             st.session_state["fotos_relato"].append({
#                 "id": str(uuid.uuid4()), 
#                 "arquivo": None,
#                 "descricao": "",
#                 "fotografo": ""
#             })
#             st.rerun(scope="fragment") # Atualiza APENAS o fragmento

#         # Iteramos sobre uma cópia da lista para evitar erros de índice ao deletar
#         for i, foto in enumerate(st.session_state["fotos_relato"]):
#             # Criamos uma chave única baseada no ID gerado, não apenas no índice i
#             # Isso evita que o Streamlit confunda os campos após uma remoção
#             foto_id = foto["id"]
            
#             with st.container(border=True):
#                 col_info, col_delete = st.columns([8, 2])
#                 col_info.write(f"Fotografia {i+1}")
                

#                 with col_delete.container(horizontal=True, horizontal_alignment="right"):

#                     if st.button("", 
#                                         key=f"btn_del_{foto_id}", 
#                                         help="Remover foto", 
#                                         icon=":material/close:",
#                                         type="tertiary"):
                        
#                         st.session_state["fotos_relato"].pop(i)
#                         st.rerun(scope="fragment") # O "pulo do gato": atualiza só o fragmento

#                 arquivo_foto = st.file_uploader(
#                     "Selecione a foto",
#                     type=["jpg", "jpeg", "png"],
#                     key=f"file_{foto_id}"
#                 )

#                 descricao = st.text_input(
#                     "Descrição da foto",
#                     key=f"desc_{foto_id}"
#                 )

#                 fotografo = st.text_input(
#                     "Nome do(a) fotógrafo(a)",
#                     key=f"autor_{foto_id}"
#                 )

#             # Sincronização
#             foto["arquivo"] = arquivo_foto
#             foto["descricao"] = descricao
#             foto["fotografo"] = fotografo





#         # --------------------------------------------------
#         # AÇÕES FINAIS: BOTÃO + VALIDAÇÃO + SPINNER
#         # --------------------------------------------------
#         col_btn, col_status = st.columns([1, 4])
#         status_placeholder = col_status.empty()

#         with col_btn:
#             salvar = st.button(
#                 "Salvar relato",
#                 width="stretch",
#                 type="primary",
#                 icon=":material/save:"
#             )

#         if salvar:

#             erros = []

#             # Valida atividade
#             if not atividade_selecionada.get("id"):
#                 erros.append("Selecione uma atividade.")

#             # Valida campos obrigatórios
#             if not st.session_state.get("campo_relato", "").strip():
#                 erros.append("O campo Relato é obrigatório.")

#             if not st.session_state.get("campo_quando", "").strip():
#                 erros.append("O campo Quando é obrigatório.")

#             if not st.session_state.get("campo_onde", "").strip():
#                 erros.append("O campo Onde é obrigatório.")

#             if erros:
#                 with status_placeholder:
#                     for e in erros:
#                         st.error(e)
#                 return

#             # Se passou na validação, salva
#             with status_placeholder:
#                 with st.spinner("Salvando, aguarde..."):
#                     salvar_relato()

#             status_placeholder.success("Relato salvo com sucesso.")

#     corpo_formulario()






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
    Atualiza o status do relatório no MongoDB quando o segmented_control muda.

    Regras de sincronização dos relatos:

    A) Se o relatório voltar de 'em_analise' ou 'aprovado' para 'modo_edicao':
       - relatos deste relatório com status 'em_analise' voltam para 'aberto'

    B) Se o relatório sair de 'modo_edicao' para 'em_analise' ou 'aprovado':
       - relatos deste relatório com status 'aberto' passam para 'em_analise'
    """

    # --------------------------------------------------
    # 1. STATUS SELECIONADO NA UI
    # --------------------------------------------------
    status_ui = st.session_state.get(f"status_relatorio_{idx}")
    status_novo = STATUS_UI_TO_DB.get(status_ui)

    if not status_novo:
        return  # segurança extra

    # --------------------------------------------------
    # 2. BUSCA STATUS ATUAL DO RELATÓRIO NO BANCO
    # --------------------------------------------------
    projeto = col_projetos.find_one(
        {
            "codigo": projeto_codigo,
            "relatorios.numero": relatorio_numero
        },
        {
            "relatorios.$": 1
        }
    )

    if not projeto or "relatorios" not in projeto:
        return

    relatorio = projeto["relatorios"][0]
    status_anterior = relatorio.get("status_relatorio")

    # --------------------------------------------------
    # 3. ATUALIZA STATUS DO RELATÓRIO
    # --------------------------------------------------
    col_projetos.update_one(
        {
            "codigo": projeto_codigo,
            "relatorios.numero": relatorio_numero
        },
        {
            "$set": {
                "relatorios.$.status_relatorio": status_novo
            }
        }
    )

    # --------------------------------------------------
    # 4. VERIFICA SE ALGUMA REGRA DE RELATOS SE APLICA
    # --------------------------------------------------
    aplica_regra_a = (
        status_novo == "modo_edicao"
        and status_anterior in ["em_analise", "aprovado"]
    )

    aplica_regra_b = (
        status_anterior == "modo_edicao"
        and status_novo in ["em_analise", "aprovado"]
    )

    if not (aplica_regra_a or aplica_regra_b):
        return  # nada a fazer nos relatos

    # --------------------------------------------------
    # 5. RECARREGA O PROJETO COMPLETO
    # --------------------------------------------------
    projeto_atualizado = col_projetos.find_one(
        {"codigo": projeto_codigo}
    )

    componentes = projeto_atualizado["plano_trabalho"]["componentes"]
    houve_alteracao = False

    # --------------------------------------------------
    # 6. APLICA AS REGRAS NOS RELATOS
    # --------------------------------------------------
    for componente in componentes:
        for entrega in componente["entregas"]:
            for atividade in entrega["atividades"]:
                for relato in atividade.get("relatos", []):

                    # Apenas relatos do relatório atual
                    if relato.get("relatorio_numero") != relatorio_numero:
                        continue

                    # Regra A: em_analise/aprovado → modo_edicao
                    if aplica_regra_a and relato.get("status_relato") == "em_analise":
                        relato["status_relato"] = "aberto"
                        houve_alteracao = True

                    # Regra B: modo_edicao → em_analise/aprovado
                    if aplica_regra_b and relato.get("status_relato") == "aberto":
                        relato["status_relato"] = "em_analise"
                        houve_alteracao = True

    # --------------------------------------------------
    # 7. SALVA NO BANCO APENAS SE HOUVE ALTERAÇÃO
    # --------------------------------------------------
    if houve_alteracao:
        col_projetos.update_one(
            {"codigo": projeto_codigo},
            {
                "$set": {
                    "plano_trabalho.componentes": componentes
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



# Função para formatar números no padrão brasileiro, com poucas casas decimais (dinamicamente)
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
# TRATAMENTO DOS DADOS E CONTROLES DE SESSÃO
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
    "Formulário",
    "Enviar"
]


if not relatorios:
    st.warning("Este projeto ainda não possui relatórios cadastrados.")
    st.stop()


# Cria uma aba para cada relatório
abas = [f"Relatório {r.get('numero')}" for r in relatorios]
tabs = st.tabs(abas)


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

        # -------------------------------------------
        # CONTROLE DE ESTADO – NOVA COMUNIDADE NO STEP "Beneficiários"
        # -------------------------------------------
        if f"mostrar_nova_comunidade_{idx}" not in st.session_state:
            st.session_state[f"mostrar_nova_comunidade_{idx}"] = False


        # -------------------------------
        # REGRA DE BLOQUEIO (a partir do 2º relatório)
        # -------------------------------
        # A partir do segundo relatório (idx > 0),
        # este relatório só pode ser liberado se o anterior estiver APROVADO.
        if idx > 0:

            # Recupera o status do relatório imediatamente anterior
            status_anterior = relatorios[idx - 1].get("status_relatorio")

            # Se o relatório anterior NÃO estiver aprovado,
            # este relatório deve ficar bloqueado
            if status_anterior != "aprovado":

                # Flag usada pela UI para:
                # - desabilitar o segmented_control
                # - impedir edição do conteúdo
                aguardando = True

                # Força o status "aguardando" no banco de dados
                # Apenas se ainda não estiver como "aguardando"
                # (evita update desnecessário e loop de escrita)
                col_projetos.update_one(
                    {
                        "codigo": projeto_codigo,                   # projeto atual
                        "relatorios.numero": relatorio_numero,       # relatório atual
                        "relatorios.status_relatorio": {"$ne": "aguardando"}
                    },
                    {
                        "$set": {
                            "relatorios.$.status_relatorio": "aguardando"
                        }
                    }
                )

                # Na interface:
                # - o segmented_control fica travado
                # - mas precisa exibir um valor válido
                # - "Modo edição" é apenas visual (não altera o banco)
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
        # SINCRONIZA STATUS DO RELATÓRIO COM A UI
        # -------------------------------

        status_key = f"status_relatorio_{idx}"

        # Converte SEMPRE o status do banco para o rótulo da interface
        status_atual_ui = STATUS_DB_TO_UI.get(status_atual_db, "Modo edição")

        # Se o valor salvo no session_state estiver diferente do banco,
        # atualiza para manter o segmented_control sincronizado
        if st.session_state.get(status_key) != status_atual_ui:
            st.session_state[status_key] = status_atual_ui



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

                # Guarda para uso no diálogo e no salvar_relato
                st.session_state["projeto_mongo"] = projeto
                st.session_state["relatorio_numero"] = relatorio_numero

                st.write("")
                st.write("")

                st.markdown(f"### Relatos de atividades do Relatório {relatorio_numero}")
                st.write('')


                # Botão que abre o diálogo de relatar atividade, só para beneficiários

                with st.container(horizontal=True, horizontal_alignment="right"):

                    # Botão abre o diálogo
                    if pode_editar_relatorio:
                        if st.button("Relatar atividade", type="primary", key=f"btn_relatar_{idx}", icon=":material/edit:"):
                            # Limpamos os dados antigos para o modal vir vazio
                            st.session_state["relato_em_edicao"] = None
                            st.session_state["relato_edicao_inicializado"] = False
                            st.session_state["campo_relato"] = ""
                            st.session_state["campo_quando"] = ""
                            st.session_state["campo_onde"] = ""
                            dialog_relatos()


                    # if pode_editar_relatorio:
                    #     if st.button("Relatar atividade",
                    #                 type="primary",
                    #                 key=f"btn_relatar_atividade_{idx}",
                    #                 icon=":material/edit:",
                    #                 width=300):
                    #         dialog_relatos()
                

                # --------------------------------------------------
                # LISTAGEM DE TODOS OS RELATOS DO RELATÓRIO
                # AGRUPADOS POR ATIVIDADE
                # --------------------------------------------------

                tem_relato = False

                for componente in projeto["plano_trabalho"]["componentes"]:
                    for entrega in componente["entregas"]:
                        for atividade in entrega["atividades"]:

                            relatos = atividade.get("relatos", [])


                            # Filtra apenas relatos do relatório atual
                            relatos = [
                                r for r in relatos
                                if r.get("relatorio_numero") == relatorio_numero
                            ]

                            if not relatos:
                                continue

                            tem_relato = True

                            st.write('')
                            # Título da atividade
                            st.markdown(f"#### {atividade['atividade']}")

                            # Lista de relatos
                            for relato in relatos:

                                with st.container(border=True):
                                    st.write(relato.get("status_relato"))

                                    # Relato
                                    st.write(f"**{(relato.get('id_relato')).upper()}:** {relato.get('relato')}")

                                    col1, col2 = st.columns([2, 3])
                                    
                                    # Quando
                                    col1.write(f"**Quando:** {relato.get('quando')}")

                                    # Onde
                                    col2.write(f"**Onde:** {relato.get('onde')}")

                                    # Anexos
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




                                    # Fotografias
                                    if relato.get("fotos"):

                                        with col2:
                                            c1, c2 = st.columns([1, 5])
                                            c1.write("**Fotografias:**")

                                            for f in relato["fotos"]:
                                                if f.get("id_arquivo"):
                                                    link = gerar_link_drive(f["id_arquivo"])

                                                    nome = f.get("nome_arquivo", "")
                                                    descricao = f.get("descricao", "")
                                                    fotografo = f.get("fotografo", "")

                                                    # Monta a linha com pipe
                                                    linha = f"[{nome}]({link})"

                                                    if descricao:
                                                        linha += f" | {descricao}"

                                                    if fotografo:
                                                        linha += f" | {fotografo}"

                                                    c2.markdown(linha, unsafe_allow_html=True)

                                    # --------------------------------------------------
                                    # BOTÃO EDITAR RELATO (APENAS SE PODE EDITAR)
                                    # --------------------------------------------------
                                    if pode_editar_relatorio:
                                        if st.button("Editar relato", key=f"editar_relato_{relato['id_relato']}", icon=":material/edit:"):
                                            # 1. Avisa que estamos editando e reseta a trava de inicialização
                                            st.session_state["relato_em_edicao"] = relato
                                            st.session_state["relato_edicao_inicializado"] = False
                                            
                                            # 2. Define a atividade pai
                                            st.session_state["atividade_selecionada"] = atividade
                                            
                                            # 3. Abre o diálogo
                                            dialog_relatos()



                                    # if pode_editar_relatorio:
                                    #     if st.button(
                                    #         "Editar relato",
                                    #         key=f"editar_relato_{relato['id_relato']}",
                                    #         icon=":material/edit:"
                                    #     ):
                                    #         # Guarda o relato em edição
                                    #         st.session_state["relato_em_edicao"] = relato

                                    #         # Guarda a atividade associada ao relato
                                    #         st.session_state["atividade_selecionada"] = atividade
                                    #         st.session_state["atividade_selecionada_drive"] = atividade

                                    #         # Abre o diálogo
                                    #         dialog_relatos()


                                

                            # st.divider()

                if not tem_relato:
                    st.caption("Nenhum relato cadastrado neste relatório.")





            # ---------- DESPESAS ----------




            # ---------- BENEFÍCIOS ----------

            if step == "Beneficiários":


                # =====================================================
                # CARREGA TIPOS DE BENEFÍCIO DO BANCO
                # =====================================================

                dados_beneficios = list(
                    col_beneficios.find({}, {"beneficio": 1}).sort("beneficio", 1)
                )

                OPCOES_BENEFICIOS = [
                    d["beneficio"]
                    for d in dados_beneficios
                    if d.get("beneficio")
                ]


                # ============================================
                # CONTROLE DE USUÁRIO / STATUS DO RELATÓRIO
                # ============================================

                usuario_admin = tipo_usuario == "admin"
                usuario_equipe = tipo_usuario == "equipe"
                usuario_beneficiario = tipo_usuario == "beneficiario"
                usuario_visitante = tipo_usuario == "visitante"

                # Se o relatório NÃO estiver em modo_edicao,
                # força modo VISUALIZAÇÃO dos beneficiários
                if status_atual_db != "modo_edicao":
                    modo_edicao_benef = False
                    modo_visualizacao_benef = True
                else:
                    modo_edicao_benef = usuario_beneficiario
                    modo_visualizacao_benef = not usuario_beneficiario





                # PARTE 1 - QUANTITATIVO DE BENEFICIÁRIOS ---------------------------------------------------------------------------------------------------------------------------
                st.write('')
                st.write('')




                # ======================================================
                # INICIALIZAÇÃO DO ESTADO DA MATRIZ DE BENEFICIÁRIOS
                # ======================================================

                if "beneficiarios_quant" not in st.session_state:
                    st.session_state.beneficiarios_quant = (
                        relatorio.get("beneficiarios_quant") or {
                            "mulheres": {
                                "jovens": 0,
                                "adultas": 0,
                                "idosas": 0
                            },
                            "homens": {
                                "jovens": 0,
                                "adultos": 0,
                                "idosos": 0
                            },
                            "nao_binarios": {
                                "jovens": 0,
                                "adultos": 0,
                                "idosos": 0
                            }
                        }
                    )


                # ======================================================
                # TÍTULO DO BLOCO
                # ======================================================

                st.markdown("##### Número de beneficiários por gênero e faixa etária")

                st.write("")


                # ======================================================
                # MODO EDIÇÃO
                # ======================================================

                if pode_editar_relatorio:


                    # Coluna à esquerda para diminuir a largura dos inputs de beneficiários
                    content, vazio_d = st.columns([7, 6])

                    # -------------------------------
                    # LINHA: JOVENS
                    # -------------------------------
                    col_m, col_h, col_nb = content.columns(3)

                    with col_m:
                        st.session_state.beneficiarios_quant["mulheres"]["jovens"] = st.number_input(
                            "Mulheres – Jovens (até 24 anos)",
                            min_value=0,
                            step=1,
                            value=st.session_state.beneficiarios_quant["mulheres"]["jovens"],
                            key="bq_mulheres_jovens"
                        )

                    with col_h:
                        st.session_state.beneficiarios_quant["homens"]["jovens"] = st.number_input(
                            "Homens – Jovens (até 24 anos)",
                            min_value=0,
                            step=1,
                            value=st.session_state.beneficiarios_quant["homens"]["jovens"],
                            key="bq_homens_jovens"
                        )

                    with col_nb:
                        st.session_state.beneficiarios_quant["nao_binarios"]["jovens"] = st.number_input(
                            "Não-binários – Jovens (até 24 anos)",
                            min_value=0,
                            step=1,
                            value=st.session_state.beneficiarios_quant["nao_binarios"]["jovens"],
                            key="bq_nb_jovens"
                        )

                    # -------------------------------
                    # LINHA: ADULTOS
                    # -------------------------------
                    col_m, col_h, col_nb = content.columns(3)

                    with col_m:
                        st.session_state.beneficiarios_quant["mulheres"]["adultas"] = st.number_input(
                            "Mulheres – Adultas",
                            min_value=0,
                            step=1,
                            value=st.session_state.beneficiarios_quant["mulheres"]["adultas"],
                            key="bq_mulheres_adultas"
                        )

                    with col_h:
                        st.session_state.beneficiarios_quant["homens"]["adultos"] = st.number_input(
                            "Homens – Adultos",
                            min_value=0,
                            step=1,
                            value=st.session_state.beneficiarios_quant["homens"]["adultos"],
                            key="bq_homens_adultos"
                        )

                    with col_nb:
                        st.session_state.beneficiarios_quant["nao_binarios"]["adultos"] = st.number_input(
                            "Não-binários – Adultos",
                            min_value=0,
                            step=1,
                            value=st.session_state.beneficiarios_quant["nao_binarios"]["adultos"],
                            key="bq_nb_adultos"
                        )

                    # -------------------------------
                    # LINHA: IDOSOS
                    # -------------------------------
                    col_m, col_h, col_nb = content.columns(3)

                    with col_m:
                        st.session_state.beneficiarios_quant["mulheres"]["idosas"] = st.number_input(
                            "Mulheres – Idosas (60+ anos)",
                            min_value=0,
                            step=1,
                            value=st.session_state.beneficiarios_quant["mulheres"]["idosas"],
                            key="bq_mulheres_idosas"
                        )

                    with col_h:
                        st.session_state.beneficiarios_quant["homens"]["idosos"] = st.number_input(
                            "Homens – Idosos (60+ anos)",
                            min_value=0,
                            step=1,
                            value=st.session_state.beneficiarios_quant["homens"]["idosos"],
                            key="bq_homens_idosos"
                        )

                    with col_nb:
                        st.session_state.beneficiarios_quant["nao_binarios"]["idosos"] = st.number_input(
                            "Não-binários – Idosos (60+ anos)",
                            min_value=0,
                            step=1,
                            value=st.session_state.beneficiarios_quant["nao_binarios"]["idosos"],
                            key="bq_nb_idosos"
                        )




                    # ======================================================
                    # BOTÃO DE SALVAR EXCLUSIVO DA MATRIZ
                    # ======================================================
                    # Este botão salva SOMENTE a matriz de quantitativos

                    if pode_editar_relatorio:

                        st.write("")

                        salvar_matriz = st.button(
                            "Atualizar beneficiários",
                            type="primary",
                            key=f"salvar_beneficiarios_quant_{relatorio_numero}",
                            icon=":material/save:"
                        )

                        if salvar_matriz:

                            # Atualiza apenas a chave 'beneficiarios_quant' no relatório correto
                            col_projetos.update_one(
                                {
                                    "codigo": projeto["codigo"],
                                    "relatorios.numero": relatorio_numero
                                },
                                {
                                    "$set": {
                                        "relatorios.$.beneficiarios_quant":
                                            st.session_state.beneficiarios_quant
                                    }
                                }
                            )

                            st.success("Quantitativo de beneficiários salvo com sucesso.")
                            time.sleep(3)
                            st.rerun()











                # ======================================================
                # MODO VISUALIZAÇÃO
                # ======================================================

                else:

                    dados = st.session_state.beneficiarios_quant

                    # -------------------------------
                    # Totais por gênero
                    # -------------------------------
                    total_mulheres = sum(dados["mulheres"].values())
                    total_homens = sum(dados["homens"].values())
                    total_nb = sum(dados["nao_binarios"].values())

                    # -------------------------------
                    # Totais por faixa etária
                    # -------------------------------
                    total_jovens = (
                        dados["mulheres"]["jovens"]
                        + dados["homens"]["jovens"]
                        + dados["nao_binarios"]["jovens"]
                    )

                    total_adultos = (
                        dados["mulheres"]["adultas"]
                        + dados["homens"]["adultos"]
                        + dados["nao_binarios"]["adultos"]
                    )

                    total_idosos = (
                        dados["mulheres"]["idosas"]
                        + dados["homens"]["idosos"]
                        + dados["nao_binarios"]["idosos"]
                    )

                    total_geral = total_mulheres + total_homens + total_nb

                    st.write("")

                    # -------------------------------
                    # LAYOUT EM 4 COLUNAS
                    # -------------------------------
                    col_m, col_h, col_nb, col_totais = st.columns(4)

                    # -------- MULHERES --------
                    with col_m:
                        l, v = st.columns(2)
                        l.write("Mulheres jovens"); v.write(str(dados["mulheres"]["jovens"]))

                        l, v = st.columns(2)
                        l.write("Mulheres adultas"); v.write(str(dados["mulheres"]["adultas"]))

                        l, v = st.columns(2)
                        l.write("Mulheres idosas"); v.write(str(dados["mulheres"]["idosas"]))

                        l, v = st.columns(2)
                        l.markdown("**Total de mulheres**"); v.markdown(f"**{total_mulheres}**")

                    # -------- HOMENS --------
                    with col_h:
                        l, v = st.columns(2)
                        l.write("Homens jovens"); v.write(str(dados["homens"]["jovens"]))

                        l, v = st.columns(2)
                        l.write("Homens adultos"); v.write(str(dados["homens"]["adultos"]))

                        l, v = st.columns(2)
                        l.write("Homens idosos"); v.write(str(dados["homens"]["idosos"]))

                        l, v = st.columns(2)
                        l.markdown("**Total de homens**"); v.markdown(f"**{total_homens}**")

                    # -------- NÃO-BINÁRIOS --------
                    with col_nb:
                        l, v = st.columns(2)
                        l.write("Não-binários jovens"); v.write(str(dados["nao_binarios"]["jovens"]))

                        l, v = st.columns(2)
                        l.write("Não-binários adultos"); v.write(str(dados["nao_binarios"]["adultos"]))

                        l, v = st.columns(2)
                        l.write("Não-binários idosos"); v.write(str(dados["nao_binarios"]["idosos"]))

                        l, v = st.columns(2)
                        l.markdown("**Total de não-binários**"); v.markdown(f"**{total_nb}**")

                    # -------- TOTAIS GERAIS (NEGRITO) --------
                    with col_totais:
                        l, v = st.columns(2)
                        l.markdown("**Total de jovens**"); v.markdown(f"**{total_jovens}**")

                        l, v = st.columns(2)
                        l.markdown("**Total de adultos**"); v.markdown(f"**{total_adultos}**")

                        l, v = st.columns(2)
                        l.markdown("**Total de idosos**"); v.markdown(f"**{total_idosos}**")

                        l, v = st.columns(2)
                        l.markdown("**Total geral**"); v.markdown(f"**{total_geral}**")








                st.divider()

                # ============================================================================================================
                # PARTE 2 - TIPOS DE BENEFICIÁRIOS E BENEFICIOS 
                # ============================================================================================================

                st.write('')
                st.markdown("##### Tipos de Beneficiários e Benefícios")

                if usuario_beneficiario:

                    st.write("")
                    st.write(
                        "Registre aqui os tipos de **Beneficiários** e **Benefícios** do projeto para cada comunidade."
                    )

                st.write("")
                st.write("")


                projeto = col_projetos.find_one({"codigo": projeto["codigo"]})
                localidades = projeto.get("locais", {}).get("localidades", [])

                if not localidades:
                    st.info(
                        "Nenhuma comunidade cadastrada no projeto. "
                        "Adicione comunidades na página **Locais**."
                    )
                    st.stop()

                # =====================================================
                # LOOP DAS COMUNIDADES
                # =====================================================
                for localidade in localidades:

                    nome_localidade = localidade.get("nome_localidade")
                    beneficiarios_bd = localidade.get("beneficiarios", []) or []

                    # -------------------------------------------------
                    # ESTADO ORIGINAL DO BANCO
                    # -------------------------------------------------
                    estado_original = {
                        b["tipo_beneficiario"]: sorted(b.get("beneficios") or [])
                        for b in beneficiarios_bd
                        if b.get("tipo_beneficiario")
                    }

                    # -------------------------------------------------
                    # PÚBLICOS PARA RENDERIZAÇÃO
                    # -------------------------------------------------
                    publicos_renderizacao = list(opcoes_publicos[:-1])

                    for tipo in estado_original.keys():
                        if tipo not in publicos_renderizacao:
                            publicos_renderizacao.append(tipo)

                    publicos_renderizacao = sorted(publicos_renderizacao)

                    estado_atual = {}
                    houve_alteracao = False

                    col1, col2 = st.columns([1, 3])

                    # -------- COLUNA 1 --------

                    with col1:
                        st.markdown(f"**{nome_localidade}**")

                        municipio = localidade.get("municipio")

                        if municipio:
                            st.write(municipio)




                    # -------- COLUNA 2 --------
                    with col2:

                        st.write("**Tipos de Beneficiários e Benefícios:**")

                        # # =====================================================
                        # # MODO VISUALIZAÇÃO COM LISTA EM TÓPICOS - Para demostração de segunda opção !!!!!!!!!!!!!!!!!!!!!!!!!
                        # # =====================================================
                        # if modo_visualizacao_benef:

                        #     if not beneficiarios_bd:
                        #         st.write("Nenhum beneficiário cadastrado.")
                        #     else:
                        #         for b in beneficiarios_bd:

                        #             tipo = b.get("tipo_beneficiario")
                        #             beneficios = b.get("beneficios") or []

                        #             with st.container():
                        #                 st.write("")

                        #                 # Título: tipo de beneficiário
                        #                 st.markdown(f"**{tipo}**")

                        #                 # Lista de benefícios
                        #                 if beneficios:
                        #                     for beneficio in beneficios:
                        #                         st.markdown(f"- {beneficio}")
                        #                 else:
                        #                     st.markdown("_Nenhum benefício informado._")


                        # st.write('///////////////////////////')


                        # =====================================================
                        # MODO VISUALIZAÇÃO COM LISTA EM PILLS
                        # =====================================================
                        if modo_visualizacao_benef:

                            if not beneficiarios_bd:
                                st.write("Nenhum beneficiário cadastrado.")
                            else:
                                for b in beneficiarios_bd:

                                    tipo = b.get("tipo_beneficiario")
                                    beneficios = b.get("beneficios") or []

                                    with st.container():
                                        st.write(' ')
                                        if beneficios:
                                            st.pills(
                                                label=tipo,
                                                options=beneficios,
                                                width="content",
                                                key=f"pill_{projeto['codigo']}_{nome_localidade}_{tipo}"
                                            )
                                        else:
                                            st.pills(
                                                label=tipo,
                                                options=["Nenhum benefício informado"],
                                                width="content",
                                                key=f"pill_{projeto['codigo']}_{nome_localidade}_{tipo}"
                                            )


                        # =====================================================
                        # MODO EDIÇÃO
                        # =====================================================
                        if modo_edicao_benef:

                            # =============================================
                            # BENEFICIÁRIOS EXISTENTES
                            # =============================================
                            for publico in publicos_renderizacao:

                                with st.container(horizontal=True):

                                    chk_key = f"chk_{projeto['codigo']}_{nome_localidade}_{publico}"

                                    marcado_inicial = publico in estado_original

                                    marcado = st.checkbox(
                                        publico,
                                        value=marcado_inicial,
                                        key=chk_key,
                                        width=300
                                    )

                                    if marcado:

                                        beneficios_iniciais = estado_original.get(publico, [])

                                        beneficios = st.multiselect(
                                            f"Benefícios para {publico.lower()}",
                                            options=OPCOES_BENEFICIOS,
                                            default=beneficios_iniciais,
                                            key=f"ms_{projeto['codigo']}_{nome_localidade}_{publico}"
                                        )

                                        estado_atual[publico] = sorted(beneficios)

                                        if (
                                            publico not in estado_original
                                            or sorted(beneficios) != estado_original.get(publico, [])
                                        ):
                                            houve_alteracao = True

                                    else:
                                        if publico in estado_original:
                                            houve_alteracao = True

                            # =============================================
                            # CHECKBOX OUTROS
                            # =============================================
                            with st.container(horizontal=True):

                                chk_outros_key = f"chk_outros_{projeto['codigo']}_{nome_localidade}"

                                outros_marcado = st.checkbox(
                                    "Outros",
                                    value=False,
                                    key=chk_outros_key,
                                    width=300
                                )

                            # =============================================
                            # FORMULÁRIO OUTROS
                            # =============================================
                            if outros_marcado:

                                with st.container(horizontal=True):

                                    st.text_input(
                                        "Tipo de beneficiário",
                                        key=f"novo_tipo_{projeto['codigo']}_{nome_localidade}"
                                    )

                                    st.multiselect(
                                        "Benefícios",
                                        options=OPCOES_BENEFICIOS,
                                        key=f"novo_beneficios_{projeto['codigo']}_{nome_localidade}"
                                    )

                                novo_tipo = st.session_state.get(
                                    f"novo_tipo_{projeto['codigo']}_{nome_localidade}", ""
                                ).strip()

                                novos_beneficios = st.session_state.get(
                                    f"novo_beneficios_{projeto['codigo']}_{nome_localidade}", []
                                )

                                if novo_tipo and novos_beneficios:
                                    houve_alteracao = True

                    # =================================================
                    # BOTÃO SALVAR
                    # =================================================
                    if houve_alteracao:

                        st.write("")

                        erros = []

                        # with st.container(horizontal=True, horizontal_alignment="right"):
                        clicou_salvar = st.button(
                            f"Atualizar {nome_localidade}",
                            type="primary",
                            key=f"salvar_{projeto['codigo']}_{nome_localidade}",
                            icon=":material/save:"
                        )

                        if clicou_salvar:

                            beneficiarios_para_salvar = []

                            # -----------------------------------------
                            # BENEFICIÁRIOS EXISTENTES
                            # -----------------------------------------
                            for tipo, beneficios in estado_atual.items():
                                if not beneficios:
                                    erros.append(
                                        f"Selecione ao menos um benefício para **{tipo}**."
                                    )
                                else:
                                    beneficiarios_para_salvar.append({
                                        "tipo_beneficiario": tipo,
                                        "beneficios": beneficios
                                    })

                            # -----------------------------------------
                            # NOVO BENEFICIÁRIO (OUTROS)
                            # -----------------------------------------
                            if outros_marcado and novo_tipo:
                                beneficiarios_para_salvar.append({
                                    "tipo_beneficiario": novo_tipo,
                                    "beneficios": novos_beneficios
                                })

                            if erros:
                                for erro in erros:
                                    st.error(erro)
                                time.sleep(3)
                                st.rerun()

                            # -----------------------------------------
                            # SALVA NO BANCO
                            # -----------------------------------------
                            col_projetos.update_one(
                                {
                                    "codigo": projeto["codigo"],
                                    "locais.localidades.nome_localidade": nome_localidade
                                },
                                {
                                    "$set": {
                                        "locais.localidades.$.beneficiarios":
                                            beneficiarios_para_salvar
                                    }
                                }
                            )

                            st.success(
                                f"Beneficiários da comunidade "
                                f"**{nome_localidade}** salvos com sucesso."
                            )
                            time.sleep(3)
                            st.rerun()


                    st.divider()





            # ---------- PESQUISAS ----------
            if step == "Pesquisas":

                # ============================
                # CONTROLE DE USUÁRIO
                # ============================

                usuario_admin = tipo_usuario == "admin"
                usuario_equipe = tipo_usuario == "equipe"
                usuario_beneficiario = tipo_usuario == "beneficiario"
                

                pode_editar = usuario_admin or usuario_equipe or usuario_beneficiario
                pode_verificar = usuario_admin or usuario_equipe

                # ============================
                # BUSCA DADOS
                # ============================

                pesquisas = edital.get("pesquisas_relatorio", []) if edital else []

                if not pesquisas:
                    st.caption("Nenhuma pesquisa cadastrada.")
                    st.stop()

                st.write("")
                st.write("")
                st.markdown("##### Pesquisas / Ferramentas de Monitoramento")
                st.write("")

                pesquisas_projeto = projeto.get("pesquisas", [])
                status_map = {p["id_pesquisa"]: p for p in pesquisas_projeto}

                # ============================
                # RENDERIZAÇÃO DAS LINHAS
                # ============================

                for pesquisa in pesquisas:

                    status = status_map.get(pesquisa["id"], {})

                    # Valores atuais do banco
                    respondida_db = status.get("respondida", False)
                    verificada_db = status.get("verificada", False)
                    url_anexo_db = status.get("url_anexo")

                    # Chaves únicas
                    upload_key = f"upload_{relatorio_numero}_{pesquisa['id']}"
                    upload_salvo_key = f"upload_salvo_{relatorio_numero}_{pesquisa['id']}"

                    col1, col2, col3, col4, col5 = st.columns([4, 3, 1, 1, 1])

                    # -------- PESQUISA --------
                    with col1:
                        st.markdown(f"**{pesquisa['nome_pesquisa']}**")


                    # -------- ANEXO --------
                    arquivo = None

                    with col2:
                        # Caso a pesquisa exija upload
                        if pesquisa.get("upload_arquivo"):

                            # -----------------------------
                            # BENEFICIÁRIO → pode anexar
                            # -----------------------------
                            if (
                                tipo_usuario == "beneficiario"
                                and not verificada_db
                                and status_atual_db == "modo_edicao"
                            ):
                                arquivo = st.file_uploader(
                                    "Anexo",
                                    key=f"upload_{relatorio_numero}_{pesquisa['id']}"
                                )

                            # -----------------------------
                            # NÃO BENEFICIÁRIO
                            # Mostra aviso SOMENTE se não houver anexo salvo
                            # -----------------------------
                            elif tipo_usuario != "beneficiario" and not url_anexo_db:
                                st.write(":material/attach_file: Demanda anexo")

                        # -----------------------------
                        # Link do anexo (se existir)
                        # -----------------------------
                        if url_anexo_db:
                            st.markdown(f":material/attach_file: [Ver anexo]({url_anexo_db})")



                    # -------- RESPONDIDA --------
                    with col3:
                        respondida_ui = st.checkbox(
                            "Respondida",
                            value=respondida_db,
                            disabled=(
                                status_atual_db in ["em_analise", "aprovado"]
                                or not pode_editar
                                or (
                                    usuario_beneficiario and verificada_db
                                )
                            ),
                            key=f"resp_{relatorio_numero}_{pesquisa['id']}"
                        )

                    # -------- VERIFICADA --------
                    with col4:
                        verificada_ui = st.checkbox(
                            "Verificada",
                            value=verificada_db,
                            disabled=(
                                status_atual_db in ["em_analise", "aprovado"]
                                or not pode_verificar
                            ),
                            key=f"verif_{relatorio_numero}_{pesquisa['id']}"
                        )

                    # -------- DETECTA ALTERAÇÃO --------
                    linha_modificada = (
                        respondida_ui != respondida_db
                        or verificada_ui != verificada_db
                        or (
                            arquivo is not None
                            and not st.session_state.get(upload_salvo_key, False)
                        )
                    )

                    # -------- BOTÃO SALVAR --------
                    with col5:
                        if linha_modificada and pode_editar:

                            if st.button(
                                "Salvar",
                                type="primary",
                                key=f"salvar_{relatorio_numero}_{pesquisa['id']}",
                                icon=":material/save:",
                            ):


                                with st.spinner("Salvando..."):

                                    # Conecta ao Drive SOMENTE aqui
                                    servico = obter_servico_drive()

                                    # Pasta do projeto
                                    pasta_projeto = obter_pasta_projeto(
                                        servico,
                                        projeto["codigo"],
                                        projeto["sigla"]
                                    )

                                    # Pasta Pesquisas (direto no projeto)
                                    pasta_pesquisas = obter_pasta_pesquisas(
                                        servico,
                                        pasta_projeto,
                                        projeto["codigo"]
                                    )

                                    url_anexo_final = url_anexo_db  # valor já salvo no banco (se existir)

                                    # ------------------------------
                                    # UPLOAD (somente se houver novo arquivo)
                                    # ------------------------------
                                    if (
                                        arquivo is not None
                                        and not st.session_state.get(upload_salvo_key, False)
                                    ):
                                        id_drive = enviar_arquivo_drive(
                                            servico,
                                            pasta_pesquisas,
                                            arquivo
                                        )

                                        url_anexo_final = gerar_link_drive(id_drive)

                                        # Marca upload como concluído
                                        st.session_state[upload_salvo_key] = True

                                    # ------------------------------
                                    # MONTA O OBJETO DA PESQUISA
                                    # ------------------------------
                                    pesquisa_obj = {
                                        "id_pesquisa": pesquisa["id"],
                                        "respondida": respondida_ui,
                                        "verificada": verificada_ui
                                    }

                                    if url_anexo_final:
                                        pesquisa_obj["url_anexo"] = url_anexo_final

                                    # ------------------------------
                                    # VERIFICA SE JÁ EXISTE NO PROJETO
                                    # ------------------------------
                                    existe = col_projetos.count_documents(
                                        {
                                            "codigo": codigo_projeto_atual,
                                            "pesquisas.id_pesquisa": pesquisa["id"]
                                        }
                                    ) > 0

                                    if existe:
                                        col_projetos.update_one(
                                            {
                                                "codigo": codigo_projeto_atual,
                                                "pesquisas.id_pesquisa": pesquisa["id"]
                                            },
                                            {
                                                "$set": {
                                                    "pesquisas.$": pesquisa_obj
                                                }
                                            }
                                        )
                                    else:
                                        col_projetos.update_one(
                                            {"codigo": codigo_projeto_atual},
                                            {
                                                "$push": {
                                                    "pesquisas": pesquisa_obj
                                                }
                                            }
                                        )



                                # Limpa estados temporários
                                st.session_state.pop(upload_key, None)
                                st.session_state.pop(upload_salvo_key, None)

                                st.success(":material/check: Salvo!")
                                time.sleep(3)
                                st.rerun()

                    st.divider()




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

                        # Dicionário
                        st.session_state.respostas_formulario = (
                            relatorio.get("respostas_formulario", {}).copy()
                        )



                ###########################################################################
                # 3. RENDERIZAÇÃO DO FORMULÁRIO
                ###########################################################################

                st.write("")
                st.write("")


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




            # ---------- ENVIAR ----------


            if step == "Enviar":

                st.write('')
                st.write('')

                # --------------------------------------------------
                # CASO 1: RELATÓRIO JÁ ENVIADO (EM ANÁLISE)
                # --------------------------------------------------
                if status_atual_db == "em_analise":

                    # Recupera a data de envio salva no banco
                    data_envio = relatorio.get("data_envio")

                    # Formata a data para exibição (DD/MM/YYYY)
                    if data_envio:
                        data_formatada = datetime.datetime.strptime(
                            data_envio, "%Y-%m-%d"
                        ).strftime("%d/%m/%Y")
                    else:
                        data_formatada = "—"

                    st.markdown(
                        f"##### Relatório enviado em {data_formatada}.")

                    st.write("Aguardando análise.")
                # --------------------------------------------------
                # CASO 2: RELATÓRIO APROVADO
                # --------------------------------------------------
                elif status_atual_db == "aprovado":
                    st.markdown("##### Relatório aprovado.")

                # --------------------------------------------------
                # CASO 3: RELATÓRIO EM MODO EDIÇÃO E USUÁRIO PODE EDITAR
                # --------------------------------------------------
                elif pode_editar_relatorio:

                    st.markdown("### Enviar relatório")

                    st.write(
                        "Ao enviar o relatório, ele será encaminhado para análise "
                        "e não poderá mais ser editado enquanto estiver em análise."
                    )

                    st.divider()

                    enviar = st.button(
                        "Enviar relatório",
                        type="primary",
                        icon=":material/send:"
                    )

                    if enviar:

                        # Gera a data de envio no formato ISO (YYYY-MM-DD)
                        data_envio = datetime.datetime.now().strftime("%Y-%m-%d")

                        with st.spinner("Enviando relatório para análise..."):

                            # --------------------------------------------------
                            # 1. ATUALIZA STATUS E DATA DO RELATÓRIO
                            # --------------------------------------------------
                            col_projetos.update_one(
                                {
                                    "codigo": projeto_codigo,
                                    "relatorios.numero": relatorio_numero
                                },
                                {
                                    "$set": {
                                        "relatorios.$.status_relatorio": "em_analise",
                                        "relatorios.$.data_envio": data_envio
                                    }
                                }
                            )

                            # --------------------------------------------------
                            # 2. ATUALIZA STATUS DOS RELATOS ABERTOS
                            #    (somente os relatos deste relatório)
                            # --------------------------------------------------
                            projeto_atualizado = col_projetos.find_one(
                                {"codigo": projeto_codigo}
                            )

                            componentes = projeto_atualizado["plano_trabalho"]["componentes"]

                            houve_alteracao = False

                            for componente in componentes:
                                for entrega in componente["entregas"]:
                                    for atividade in entrega["atividades"]:
                                        for relato in atividade.get("relatos", []):

                                            # Apenas relatos do relatório atual
                                            # e que ainda estejam abertos
                                            if (
                                                relato.get("relatorio_numero") == relatorio_numero
                                                and relato.get("status_relato") == "aberto"
                                            ):
                                                relato["status_relato"] = "em_analise"
                                                houve_alteracao = True

                            # Salva no Mongo apenas se houve mudança
                            if houve_alteracao:
                                col_projetos.update_one(
                                    {"codigo": projeto_codigo},
                                    {
                                        "$set": {
                                            "plano_trabalho.componentes": componentes
                                        }
                                    }
                                )

                        st.success("Relatório enviado para análise.")

                        # Reseta para o rerun não se perder.
                        st.session_state.step_relatorio = "Atividades"

                        time.sleep(3)
                        st.rerun()

                # --------------------------------------------------
                # CASO 4: USUÁRIO NÃO PODE EDITAR
                # --------------------------------------------------
                else:
                    st.info("Este relatório não pode ser editado no momento.")






# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()