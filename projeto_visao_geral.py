import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao, sidebar_projeto, calcular_status_projetos, gerar_cronograma_financeiro
import pandas as pd
import streamlit_shadcn_ui as ui
import datetime
import time
import bson
import io


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
    content: "Arraste e solte os arquivos aqui";
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
# CONEXÃO COM O BANCO DE DADOS
###########################################################################################################

# Conexão com MongoDB
db = conectar_mongo_cepf_gestao()

# Coleções
col_pessoas = db["pessoas"]
col_projetos = db["projetos"]
col_editais = db["editais"]
col_direcoes_estrategicas = db["direcoes_estrategicas"]
col_publicos = db["publicos"]




###########################################################################################################
# CONEXÃO COM GOOGLE DRIVE
###########################################################################################################


# Escopo mínimo necessário para Drive
ESCOPO_DRIVE = ["https://www.googleapis.com/auth/drive"]

@st.cache_resource
def obter_servico_drive():
    """
    Retorna o cliente autenticado do Google Drive,
    usando as credenciais armazenadas em st.secrets.
    """
    credenciais = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=ESCOPO_DRIVE
    )
    return build("drive", "v3", credentials=credenciais)






###########################################################################################################
# FUNÇÕES
###########################################################################################################


def obter_ou_criar_pasta(servico, nome_pasta, id_pasta_pai):
    """
    Busca uma pasta com o nome especificado dentro da pasta pai no Google Drive.
    Se a pasta não existir, ela é criada.
    
    Retorna o ID da pasta encontrada ou criada.
    """

    # Monta a query de busca:
    # - nome exato da pasta
    # - dentro da pasta pai
    # - apenas pastas
    # - não deletadas
    consulta = (
        f"name='{nome_pasta}' and "
        f"'{id_pasta_pai}' in parents and "
        f"mimeType='application/vnd.google-apps.folder' and trashed=false"
    )

    # Executa a busca
    resultado = servico.files().list(
        q=consulta,
        fields="files(id)",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True
    ).execute()

    arquivos = resultado.get("files", [])

    # Se encontrou, reutiliza a pasta existente
    if arquivos:
        return arquivos[0]["id"]

    # Caso não exista, cria a pasta
    pasta = servico.files().create(
        body={
            "name": nome_pasta,
            "parents": [id_pasta_pai],
            "mimeType": "application/vnd.google-apps.folder"
        },
        fields="id",
        supportsAllDrives=True
    ).execute()

    return pasta["id"]



def obter_pasta_projeto(servico, codigo, sigla):
    """
    Retorna o ID da pasta do projeto no Google Drive.
    Cria se não existir.
    Usa cache baseado em código + sigla.
    """

    nome_pasta = f"{codigo} - {sigla}"
    chave_cache = f"pasta_projeto_{nome_pasta}"

    # Se já foi criada nesta sessão, reutiliza
    if chave_cache in st.session_state:
        return st.session_state[chave_cache]

    # Cria ou localiza a pasta
    pasta_id = obter_ou_criar_pasta(
        servico,
        nome_pasta,
        st.secrets["drive"]["pasta_drive_projetos"]
    )

    # Salva no cache
    st.session_state[chave_cache] = pasta_id

    return pasta_id






def obter_pasta_locais(servico, pasta_projeto_id):
    """
    Retorna o ID da subpasta 'Locais' dentro da pasta do projeto.

    Também usa cache no session_state para evitar múltiplas criações.
    """

    if "pasta_locais_id" in st.session_state:
        return st.session_state["pasta_locais_id"]

    pasta_id = obter_ou_criar_pasta(
        servico,
        "Locais",
        pasta_projeto_id
    )

    st.session_state["pasta_locais_id"] = pasta_id
    return pasta_id


def enviar_arquivo_drive(servico, id_pasta, arquivo):
    """
    Faz upload de um arquivo para o Google Drive dentro da pasta informada.

    Retorna o ID do arquivo criado.
    """

    # Converte o arquivo do Streamlit para bytes
    media = MediaIoBaseUpload(
        io.BytesIO(arquivo.read()),
        mimetype=arquivo.type,
        resumable=False
    )

    # Cria o arquivo no Drive
    arq = servico.files().create(
        body={
            "name": arquivo.name,
            "parents": [id_pasta]
        },
        media_body=media,
        fields="id",
        supportsAllDrives=True
    ).execute()

    return arq["id"]


def gerar_link_drive(id_arquivo):
    """
    Gera o link público padrão de visualização do arquivo no Google Drive.
    """
    return f"https://drive.google.com/file/d/{id_arquivo}/view"















###########################################################################################################
# CONTEXTO DO USUÁRIO
###########################################################################################################

# Verifica se o usuário logado é interno
usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]



###########################################################################################################
# CARREGAMENTO DOS DADOS
###########################################################################################################

# Projeto

# Código do projeto atual
codigo_projeto_atual = st.session_state.get("projeto_atual")

if not codigo_projeto_atual:
    st.error("Nenhum projeto selecionado.")
    st.stop()

df_projeto = pd.DataFrame(
    list(col_projetos.find({"codigo": codigo_projeto_atual}))
)

if df_projeto.empty:
    st.error("Projeto não encontrado no banco de dados.")
    st.stop()

# Facilita acesso aos dados
projeto = df_projeto.iloc[0].to_dict()


# Pessoas
df_pessoas = pd.DataFrame(list(col_pessoas.find()))

# Editais
df_editais = pd.DataFrame(list(col_editais.find()))

# Direções estratégicas
df_direcoes_estrategicas = pd.DataFrame(list(col_direcoes_estrategicas.find()))

# Públicos
df_publicos = pd.DataFrame(list(col_publicos.find()))

# Organizações
df_organizacoes = pd.DataFrame(list(db["organizacoes"].find()))


###########################################################################################################
# NORMALIZAÇÃO DE IDs
###########################################################################################################

def normalizar_id(df):
    if "_id" in df.columns:
        df["_id"] = df["_id"].astype(str)
    return df


df_projeto = normalizar_id(df_projeto)
df_editais = normalizar_id(df_editais)
df_direcoes_estrategicas = normalizar_id(df_direcoes_estrategicas)
df_publicos = normalizar_id(df_publicos)
df_organizacoes = normalizar_id(df_organizacoes)

###########################################################################################################
# CÁLCULO DE STATUS DO PROJETO
###########################################################################################################

df_projeto = calcular_status_projetos(df_projeto)


###########################################################################################################
# RELACIONAMENTO: PADRINHOS DO PROJETO
###########################################################################################################

# Filtra apenas usuários internos (admin e equipe)
df_pessoas_internos = df_pessoas[
    df_pessoas["tipo_usuario"].isin(["admin", "equipe"])
].copy()

# Seleciona apenas colunas necessárias
df_pessoas_proj = df_pessoas_internos[["nome_completo", "projetos"]].copy()

# Garante que "projetos" seja lista
df_pessoas_proj["projetos"] = df_pessoas_proj["projetos"].apply(
    lambda x: x if isinstance(x, list) else []
)

# Explode para uma linha por projeto
df_pessoas_proj = df_pessoas_proj.explode("projetos")

# Remove registros inválidos
df_pessoas_proj = df_pessoas_proj.dropna(subset=["projetos"])

# Renomeia colunas
df_pessoas_proj = df_pessoas_proj.rename(columns={
    "projetos": "codigo",
    "nome_completo": "padrinho"
})

# Agrupa padrinhos por projeto
df_padrinhos = (
    df_pessoas_proj
    .groupby("codigo")["padrinho"]
    .apply(lambda nomes: ", ".join(sorted(set(nomes))))
    .reset_index()
)

# Junta com o dataframe principal
df_projeto = df_projeto.merge(
    df_padrinhos,
    on="codigo",
    how="left"
)









###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################

# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')


# Código e Sigla do projeto
st.header(f"{df_projeto['sigla'].values[0]} - {df_projeto['codigo'].values[0]}")


# Toggle do modo de edição
with st.container(horizontal=True, horizontal_alignment="right"):
    if usuario_interno:
        editar_cadastro = st.toggle("Editar", key="editar_cadastro_projeto")
    else:
        editar_cadastro = False



# MODO DE VISUALIZAÇÃO
if not editar_cadastro:

    st.write(f"**Edital:** {df_projeto['edital'].values[0]}")
    st.write(f"**Organização:** {df_projeto['organizacao'].values[0]}")
    st.write(f"**Nome do projeto:** {df_projeto['nome_do_projeto'].values[0]}")
    st.write(f"**Objetivo geral:** {df_projeto['objetivo_geral'].values[0]}")
    st.write(f"**Duração:** {df_projeto['duracao'].values[0]} meses")

    cols = st.columns(3)
    cols[0].write(f"**Início:** {df_projeto['data_inicio_contrato'].values[0]}")
    cols[1].write(f"**Fim:** {df_projeto['data_fim_contrato'].values[0]}")

    # ---------- CONTRATOS ----------

    contratos = df_projeto["contratos"].values[0] if "contratos" in df_projeto.columns else None

    with cols[2]:


        if contratos:
            with st.popover("**Contrato**", type="tertiary"):
                
                for c in contratos:
                    st.markdown(
                        f"[**{c['descricao_contrato']}**]({c['url_contrato']})"
                    )
        else:
            st.markdown(
                "**Contrato:** <span style='color:#c46a00; font-style:italic;'>não cadastrado</span>",
                unsafe_allow_html=True
            )



    st.write(f"**Responsável:** {df_projeto['responsavel'].values[0]}")

    # Padrinho
    valor = df_projeto["padrinho"].values[0]
    if pd.isna(valor) or str(valor).strip() == "":
        st.markdown(
            "**Padrinho/Madrinha:** <span style='color:#c46a00; font-style:italic;'>não cadastrado</span>",
            unsafe_allow_html=True
        )
    else:
        st.write(f"**Padrinho/Madrinha:** {valor}")

    # st.write(f"**Padrinho/Madrinha:** {df_projeto['padrinho'].values[0]}")

    direcoes = df_projeto['direcoes_estrategicas'].values[0]
    if direcoes:

        with st.popover("**Direções estratégicas**", type="tertiary"):

            for d in direcoes:
                st.write(f"- {d}")

    publicos = df_projeto['publicos'].values[0]
    if publicos:
        st.write("**Beneficiários:**", " / ".join(publicos))



# MODO DE EDIÇÃO

else:
    st.write("**Editar informações cadastrais do projeto**")

    with st.form("form_editar_projeto", border=False):

        col1, col2, col3 = st.columns(3)

        # ---------- EDITAL ----------
        lista_editais = df_editais["codigo_edital"].tolist()

        # Garante que o valor atual exista na lista
        edital_atual = projeto.get("edital")
        if edital_atual in lista_editais:
            index_edital = lista_editais.index(edital_atual)
        else:
            index_edital = 0  

        edital = col1.selectbox(    # Coluna 1
            "Edital",
            options=lista_editais,
            index=index_edital
        )
        
        # ---------- CÓDIGO ----------
        codigo = col2.text_input("Código do Projeto", projeto["codigo"])      # Coluna 2    

        # ---------- SIGLA ----------
        sigla = col3.text_input("Sigla do Projeto", projeto["sigla"])      # Coluna 3



        # ---------- ORGANIZAÇÃO ----------
        lista_organizacoes = df_organizacoes["nome_organizacao"].tolist()

        # Garante que o valor atual exista na lista
        organizacao_atual = projeto.get("organizacao")
        if organizacao_atual in lista_organizacoes:
            index_organizacao = lista_organizacoes.index(organizacao_atual)
        else:
            index_organizacao = 0  

        organizacao = st.selectbox(    # Coluna 1
            "Organização",
            options=lista_organizacoes,
            index=index_organizacao
        )


        # ---------- NOME DO PROJETO ----------
        nome = st.text_input("Nome do Projeto", projeto["nome_do_projeto"])

        # ---------- OBJETIVO GERAL ----------
        objetivo = st.text_area(
            "Objetivo geral",
            projeto.get("objetivo_geral", "")
        )

        col1, col2, col3 = st.columns(3)

        # ---------- DURAÇÃO ----------

        duracao = col1.number_input(
            "Duração (meses)",
            min_value=1,
            value=int(projeto["duracao"])
        )

        # ---------- DATA DE INÍCIO DO CONTRATO ----------
        data_inicio = col2.date_input(
            "Data de início do contrato",
            value=pd.to_datetime(projeto["data_inicio_contrato"], dayfirst=True),
            format="DD/MM/YYYY"
        )

        # ---------- DATA DE FIM DO CONTRATO ----------
        data_fim = col3.date_input(
            "Data de fim do contrato",
            value=pd.to_datetime(projeto["data_fim_contrato"], dayfirst=True),
            format="DD/MM/YYYY"
        )



        # ---------- RESPONSÁVEL(IS) ----------

        # Filtra apenas usuários do tipo beneficiário
        df_pessoas_benef = df_pessoas[
            df_pessoas["tipo_usuario"] == "beneficiario"
        ].copy()

        # Lista de opções
        lista_beneficiarios = df_pessoas_benef["nome_completo"].dropna().tolist()

        # Valor atual salvo no projeto
        responsavel_atual = projeto.get("responsavel")

        # Normaliza o valor para lista válida
        if isinstance(responsavel_atual, list):
            # remove valores vazios
            responsavel_atual = [r for r in responsavel_atual if r]
        elif isinstance(responsavel_atual, str) and responsavel_atual.strip():
            responsavel_atual = [responsavel_atual]
        else:
            responsavel_atual = []  # <- deixa vazio se não houver valor válido

        # Campo de seleção
        responsavel = st.multiselect(
            "Responsável",
            options=lista_beneficiarios,
            default=responsavel_atual
        )

        # Converte lista de responsáveis em string separada por vírgula
        responsavel_str = ", ".join(responsavel) if responsavel else ""


        # ---------- PADRINHO / MADRINHA ----------

        # Lista de opções
        opcoes_padrinho_madrinha = sorted(df_pessoas_internos["nome_completo"].tolist())

        # Pessoas atualmente associadas a este projeto
        codigo_projeto = projeto["codigo"]

        padrinhos_atuais = df_pessoas_internos[
            df_pessoas_internos["projetos"].apply(
                lambda x: isinstance(x, list) and codigo_projeto in x
            )
        ]["nome_completo"].tolist()

        padrinho_madrinha = st.multiselect(
            "Padrinho / Madrinha",
            options=opcoes_padrinho_madrinha,
            default=padrinhos_atuais
        )



        # ---------- DIREÇÕES ESTRATÉGICAS ----------

        # Lista de opções disponíveis
        opcoes_direcoes = sorted(df_direcoes_estrategicas["tema"].dropna().tolist())

        # Valor salvo no banco
        direcoes_atual = projeto.get("direcoes_estrategicas")

        # Normaliza para lista válida
        if isinstance(direcoes_atual, list):
            direcoes_atual = [d for d in direcoes_atual if d]
        elif isinstance(direcoes_atual, str) and direcoes_atual.strip():
            direcoes_atual = [direcoes_atual]
        else:
            direcoes_atual = []  # vazio quando não houver dados

        # Campo de seleção
        direcoes = st.multiselect(
            "Direções estratégicas",
            options=opcoes_direcoes,
            default=direcoes_atual
        )

        # ---------- PÚBLICOS ----------

        # Lista de opções disponíveis
        opcoes_publicos = df_publicos["publico"].dropna().tolist()

        # Valor salvo no banco
        publicos_atual = projeto.get("publicos")

        # Normaliza para lista válida
        if isinstance(publicos_atual, list):
            publicos_atual = [p for p in publicos_atual if p]
        elif isinstance(publicos_atual, str) and publicos_atual.strip():
            publicos_atual = [publicos_atual]
        else:
            publicos_atual = []  # vazio quando não houver dados

        # Campo de seleção
        publicos = st.multiselect(
            "Públicos",
            options=opcoes_publicos,
            default=publicos_atual,
            key="multi_select_publicos"
        )


        # ---------- CONTRATO ----------
        
        st.divider()
        
        st.write('**Contratos e Emendas de contrato**')


        # ---------- DATA DE ASSINATURA DO CONTRATO ----------

        # Valor salvo no banco (pode não existir)
        data_assinatura_salva = projeto.get("contrato_data_assinatura")

        if data_assinatura_salva:
            # converte datetime/string para date
            data_assinatura_default = pd.to_datetime(data_assinatura_salva).date()
        else:
            data_assinatura_default = None

        data_assinatura_contrato = st.date_input(
            "Data de assinatura do contrato:",
            value=data_assinatura_default,
            format="DD/MM/YYYY",
            width=200
        )

        st.write('')
        
        contratos = projeto.get("contratos", [])

        if contratos:

            col1, col2 = st.columns([1, 5])

            col1.markdown("Contratos cadastrados:")

            for c in contratos:
                col2.markdown(f"[**{c['descricao_contrato']}**]({c['url_contrato']})")

                # col2.markdown(f"**{c['descricao_contrato']}**")
                # st.markdown(f"[Abrir contrato]({c['url_contrato']})")
        else:
            st.markdown(
            "<span style='color:#c46a00; font-style:italic; margin-left: 20px;'>Nenhum documento cadastrado</span>",
            unsafe_allow_html=True
        )

        st.write('')
        st.write("Adicionar documento:")

        descricao_contrato = st.text_input(
            "Descrição do documento",
            placeholder="Ex: Contrato principal, Aditivo 01..."
        )

        arquivo_contrato = st.file_uploader(
            "Selecione o arquivo",
            type=["pdf", "docx", "doc", "jpg", "png"],
            accept_multiple_files=False,
        )

        st.divider()

        # ---------- TOGGLE DE CANCELADO ----------

        # st.write('')
        # st.write('')

        # STATUS ATUAL DO PROJETO
        status_atual = projeto.get("status")  # pode ser None
        projeto_cancelado_atual = status_atual == "Cancelado"

        projeto_cancelado = st.toggle(
            "Projeto cancelado",
            value=projeto_cancelado_atual
        )

        # Define o novo status
        if projeto_cancelado:
            novo_status = "Cancelado"
        else:
            novo_status = None



        st.write("")

        salvar = st.form_submit_button("Salvar alterações", key="salvar_alteracoes_cadastrais", icon=":material/save:", type="primary", width=250)

        # ---------- SALVAR ----------
        if salvar:

            # --------------------------------------------------
            # VALIDAÇÕES ANTES DE SALVAR
            # --------------------------------------------------

            campos_obrigatorios = {
                "Edital": edital,
                "Código do Projeto": codigo,
                "Sigla do Projeto": sigla,
                "Organização": organizacao,
                "Nome do Projeto": nome,
                "Objetivo Geral": objetivo,
                "Duração do Projeto": duracao,
            }

            # Verifica campos vazios
            campos_faltando = [
                nome for nome, valor in campos_obrigatorios.items()
                if not valor
            ]

            if campos_faltando:
                st.error(
                    f":material/warning: Preencha os campos obrigatórios: {', '.join(campos_faltando)}"
                )

            else:
                # --------------------------------------------------
                # VALIDAÇÃO DE UNICIDADE (ignorando o próprio projeto)
                # --------------------------------------------------

                projeto_id = projeto["_id"]

                sigla_existente = col_projetos.find_one({
                    "sigla": sigla,
                    "_id": {"$ne": projeto_id}
                })

                codigo_existente = col_projetos.find_one({
                    "codigo": codigo,
                    "_id": {"$ne": projeto_id}
                })

                if sigla_existente:
                    st.warning(f":material/warning: A sigla **{sigla}** já está cadastrada em outro projeto.")
                
                elif codigo_existente:
                    st.warning(f":material/warning: O código **{codigo}** já está cadastrado em outro projeto.")

                else:
                    with st.spinner("Salvando alterações..."):
                        # --------------------------------------------------
                        # ATUALIZA O PROJETO
                        # --------------------------------------------------

                        # Converte para datetime (Mongo)
                        if data_assinatura_contrato:
                            data_assinatura_dt = datetime.datetime.combine(
                                data_assinatura_contrato, datetime.datetime.min.time()
                            )
                        else:
                            data_assinatura_dt = None



                        # Atualizações na coleção de Projetos
                        col_projetos.update_one(
                            {"_id": projeto_id},
                            {
                                "$set": {
                                    "edital": edital,
                                    "codigo": codigo,
                                    "sigla": sigla,
                                    "organizacao": organizacao,
                                    "nome_do_projeto": nome,
                                    "objetivo_geral": objetivo,
                                    "duracao": duracao,
                                    "data_inicio_contrato": data_inicio.strftime("%d/%m/%Y"),
                                    "data_fim_contrato": data_fim.strftime("%d/%m/%Y"),
                                    "responsavel": responsavel_str,
                                    "direcoes_estrategicas": direcoes or [],
                                    "publicos": publicos or [],
                                    "contrato_data_assinatura": data_assinatura_dt, 
                                }
                            }
                        )



                        # Atualiza status separadamente
                        if novo_status:
                            col_projetos.update_one(
                                {"_id": projeto_id},
                                {"$set": {"status": novo_status}}
                            )
                        else:
                            # Remove o campo se existir
                            col_projetos.update_one(
                                {"_id": projeto_id},
                                {"$unset": {"status": ""}}
                            )

                        # Atualizações na coleção de Pessoas
                        # ATUALIZA PADRINHOS DO PROJETO

                        # Pessoas que eram padrinhos antes
                        padrinhos_antes = set(padrinhos_atuais)

                        # Pessoas selecionadas agora
                        padrinhos_novos = set(padrinho_madrinha)

                        # Pessoas que precisam ser removidas
                        remover = padrinhos_antes - padrinhos_novos

                        # Pessoas que precisam ser adicionadas
                        adicionar = padrinhos_novos - padrinhos_antes

                        # Remove projeto das pessoas removidas
                        for nome in remover:
                            col_pessoas.update_one(
                                {"nome_completo": nome},
                                {"$pull": {"projetos": codigo}}
                            )

                        # Adiciona projeto às pessoas novas
                        for nome in adicionar:
                            col_pessoas.update_one(
                                {"nome_completo": nome},
                                {"$addToSet": {"projetos": codigo}}
                            )


                        # --------------------------------------------------
                        # SALVAR CONTRATO (SE INFORMADO)
                        # --------------------------------------------------
                        if descricao_contrato or arquivo_contrato:
                            if not descricao_contrato or not arquivo_contrato:
                                st.warning("Para adicionar um contrato, informe a descrição e selecione o arquivo.")
                            else:


                                # Conecta ao Drive
                                servico = obter_servico_drive()

                                # Pasta do projeto
                                pasta_projeto = obter_pasta_projeto(
                                    servico,
                                    projeto["codigo"],
                                    projeto["sigla"]
                                )

                                # Pasta "Contratos"
                                pasta_contratos = obter_ou_criar_pasta(
                                    servico,
                                    "Contratos",
                                    pasta_projeto
                                )

                                # Upload do arquivo
                                id_arquivo = enviar_arquivo_drive(
                                    servico,
                                    pasta_contratos,
                                    arquivo_contrato
                                )

                                # Gera link público
                                url_contrato = gerar_link_drive(id_arquivo)

                                # Salva no MongoDB
                                col_projetos.update_one(
                                    {"_id": projeto_id},
                                    {
                                        "$push": {
                                            "contratos": {
                                                "descricao_contrato": descricao_contrato,
                                                "url_contrato": url_contrato
                                            }
                                        }
                                    }
                                )





                        st.success(":material/check: Projeto atualizado com sucesso!")
                        time.sleep(3)
                        st.rerun()





st.divider()










# #############################################################################################
# STATUS DO PROJETO
# #############################################################################################

# ?????
# df_projeto = calcular_status_projetos(df_projeto)


status_projeto = df_projeto["status"].values[0]

cores_status = {
    "Em dia": "green",
    "Atrasado": "orange",
    "Concluído": "green",
    "Cancelado": "gray",
    "Sem cronograma": "orange"
}

st.markdown(
    f"#### O projeto está :{cores_status.get(status_projeto, 'gray')}[{status_projeto.lower()}]"
)

# #############################################################################################
# MENSAGEM DO STATUS
# #############################################################################################

# Se o projeto já finalizou
if status_projeto in ["Concluído", "Cancelado"]:
    if status_projeto == "Concluído":
        st.success("🎉 Parabéns! O projeto realizou todas as etapas e está concluído.")
    else:
        st.warning("Este projeto foi cancelado.")

else:
    # Dados já calculados no df_projeto
    proximo_evento = df_projeto["proximo_evento"].values[0]
    data_proximo_evento = df_projeto["data_proximo_evento"].values[0]
    dias_atraso = df_projeto["dias_atraso"].values[0]

    # Caso não exista cronograma
    if pd.isna(proximo_evento):
        st.caption("Este projeto ainda não possui cronograma de Parcelas e Relatórios.")

    else:

        # # ???
        # # DEBUG: MANIPULAÇÃO DA DATA DE HOJE
        # hoje = datetime.date(2026, 4, 30)

        hoje = datetime.date.today()

        # Texto da data
        if pd.notna(data_proximo_evento):
            if data_proximo_evento == hoje:
                texto_data = "previsto para hoje"
            else:
                texto_data = f"previsto para **{data_proximo_evento.strftime('%d/%m/%Y')}**"
        else:
            texto_data = "com data não informada."

        # Mensagem principal
        if str(proximo_evento).startswith("Parcela"):
            st.write(
                f"O próximo passo é o pagamento da **{proximo_evento.lower()}**, {texto_data}."
            )

        elif str(proximo_evento).startswith("Relatório"):
            st.write(
                f"O próximo passo é o envio do **{proximo_evento.lower()}**, {texto_data}."
            )

        else:
            st.info(
                f"Próximo evento: **{proximo_evento}**, {texto_data}."
            )

        # Atraso / antecedência
        if dias_atraso is not None:
            if dias_atraso > 0:
                st.write(f"O projeto acumula **{dias_atraso} dias** de atraso.")
            elif dias_atraso < 0:
                st.write(f"Faltam **{abs(dias_atraso)} dias**.")




st.write('')
st.write('')
st.write('')







# st.divider()

st.markdown('#### Anotações')


# ============================================================
# ANOTAÇÕES - DIÁLGO DE GERENCIAMENTO
# ============================================================


# Função do diálogo de gerenciar anotações  -------------------------------------
@st.dialog("Gerenciar anotações", width="medium")
def gerenciar_anotacoes():

    nova_tab, editar_tab = st.tabs(["Nova anotação", "Editar anotação"])

    # ========================================================
    # NOVA ANOTAÇÃO
    # ========================================================
    with nova_tab:

        tipo_anotacao = st.radio(
            "Tipo da anotação",
            options=["Interna", "Externa"],
            horizontal=True,
            key="tipo_anotacao_nova"
        )


        texto_anotacao = st.text_area(
            "Escreva aqui a anotação",
            height=150
        )

        st.write('')

        if st.button(
            "Salvar anotação",
            type="primary",
            icon=":material/save:",
            key="salvar_nova_anotacao"
        ):

            if not texto_anotacao.strip():
                st.warning("A anotação não pode estar vazia.")
                return

            anotacao = {
                "id": str(bson.ObjectId()),
                "data": datetime.datetime.now().strftime("%d/%m/%Y"),
                "autor": st.session_state.nome,
                "texto": texto_anotacao.strip(),
                "tipo": tipo_anotacao.lower()
            }

            resultado = col_projetos.update_one(
                {"codigo": st.session_state.projeto_atual},
                {"$push": {"anotacoes": anotacao}}
            )

            if resultado.modified_count == 1:
                st.success("Anotação salva com sucesso!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Erro ao salvar anotação.")

    # ========================================================
    # EDITAR ANOTAÇÃO
    # ========================================================
    with editar_tab:

        anotacoes_local = (
            df_projeto["anotacoes"].values[0]
            if "anotacoes" in df_projeto.columns
            else []
        )

        # Filtrar somente anotações do usuário logado
        
        anotacoes_usuario = [
            a for a in anotacoes_local
            if a.get("autor") == st.session_state.nome
            and (usuario_interno or a.get("tipo") != "interna")
        ]

        
       
        if not anotacoes_usuario:
            st.write("Não há anotações de sua autoria para editar.")
            return

        # Selectbox amigável
        mapa_anotacoes = {
            f"{a['data']} — {a['texto'][:60]}": a
            for a in anotacoes_usuario
        }

        anotacao_label = st.selectbox(
            "Selecione a anotação",
            list(mapa_anotacoes.keys())
        )

        anotacao_selecionada = mapa_anotacoes[anotacao_label]

        # Tipo da anotação (interna / externa)
        tipo_anotacao_edicao = st.radio(
            "Tipo da anotação",
            options=["Interna", "Externa"],
            index=0 if anotacao_selecionada.get("tipo", "externa") == "externa" else 1,
            horizontal=True,
            key="tipo_anotacao_edicao"
        )


        novo_texto = st.text_area(
            "Editar anotação",
            value=anotacao_selecionada["texto"],
            height=150
        )
        
        st.write('')
        if st.button(
            "Salvar alterações",
            type="primary",
            icon=":material/save:",
            key="salvar_editar_anotacao"
        ):

            if not novo_texto.strip():
                st.warning("A anotação não pode ficar vazia.")
                return

            resultado = col_projetos.update_one(
                {
                    "codigo": st.session_state.projeto_atual,
                    "anotacoes.id": anotacao_selecionada["id"],
                },
                {

                    "$set": {
                        "anotacoes.$.texto": novo_texto.strip(),
                        "anotacoes.$.tipo": tipo_anotacao_edicao.lower()
                    }

                }
            )

            if resultado.modified_count == 1:
                st.success("Anotação atualizada com sucesso!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Erro ao atualizar anotação.")


if usuario_interno:
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button(
            "Gerenciar anotações",
            icon=":material/edit:",
            type="secondary",
            width=200,
            key="gerenciar_anotacoes"
        ):
            gerenciar_anotacoes()



# ============================================================
# ANOTAÇÕES - LISTAGEM
# ============================================================



anotacoes = (
    df_projeto["anotacoes"].values[0]
    if "anotacoes" in df_projeto.columns
    else []
)

# Regra de visibilidade
if usuario_interno:
    anotacoes_visiveis = anotacoes
else:
    anotacoes_visiveis = [
        a for a in anotacoes
        if a.get("tipo") != "interna"
    ]


if not anotacoes_visiveis:
    st.caption("Não há anotações.")
else:
    df_anotacoes = pd.DataFrame(anotacoes_visiveis)
    df_anotacoes = df_anotacoes[["data", "texto", "autor", "tipo"]]

    # Renomeia colunas para exibição
    df_anotacoes = df_anotacoes.rename(columns={
        "data": "Data",
        "texto": "Anotação",
        "autor": "Autor(a)",
        "tipo": "Tipo"
    })

    with st.container():
        ui.table(data=df_anotacoes, key="tabela_anotacoes_fixa")




st.write('')
st.write('')
st.write('')












# Visitas 
st.markdown('#### Visitas')

# ============================================================
# VISITAS - DIÁLGO DE GERENCIAMENTO
# ============================================================

@st.dialog("Gerenciar visitas", width="medium")
def gerenciar_visitas():

    nova_tab, editar_tab = st.tabs(["Nova visita", "Editar visita"])

    # ========================================================
    # NOVA VISITA
    # ========================================================
    with nova_tab:

        data_visita = st.text_input(
            "Data da visita",
        )

        relato_visita = st.text_area(
            "Breve relato",
            height=150
        )

        st.write('')
        if st.button(
            "Salvar visita",
            type="primary",
            icon=":material/save:",
            key="salvar_nova_visita"
        ):

            if not data_visita.strip() or not relato_visita.strip():
                st.warning("Preencha a data da visita e o relato.")
                return

            visita = {
                "id": str(bson.ObjectId()),
                "data_visita": data_visita.strip(),
                "relato": relato_visita.strip(),
                "autor": st.session_state.nome,
            }

            resultado = col_projetos.update_one(
                {"codigo": st.session_state.projeto_atual},
                {"$push": {"visitas": visita}}
            )

            if resultado.modified_count == 1:
                st.success("Visita registrada com sucesso!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Erro ao salvar visita.")

    # ========================================================
    # EDITAR VISITA
    # ========================================================
    with editar_tab:

        visitas_local = (
            df_projeto["visitas"].values[0]
            if "visitas" in df_projeto.columns
            else []
        )

        visitas_usuario = [
            v for v in visitas_local
            if v.get("autor") == st.session_state.nome
        ]

        if not visitas_usuario:
            st.write("Não há visitas de sua autoria para editar.")
            return

        mapa_visitas = {
            f"{v['data_visita']} — {v['relato'][:60]}": v
            for v in visitas_usuario
        }

        visita_label = st.selectbox(
            "Selecione a visita",
            list(mapa_visitas.keys())
        )

        visita_selecionada = mapa_visitas[visita_label]

        nova_data = st.text_input(
            "Data da visita (DD/MM/AAAA)",
            value=visita_selecionada["data_visita"]
        )

        novo_relato = st.text_area(
            "Editar breve relato",
            value=visita_selecionada["relato"],
            height=150
        )
        
        st.write('')
        if st.button(
            "Salvar alterações",
            type="primary",
            icon=":material/save:",
            key="salvar_editar_visita"
        ):

            if not nova_data.strip() or not novo_relato.strip():
                st.warning("A data e o relato não podem ficar vazios.")
                return

            resultado = col_projetos.update_one(
                {
                    "codigo": st.session_state.projeto_atual,
                    "visitas.id": visita_selecionada["id"],
                },
                {
                    "$set": {
                        "visitas.$.data_visita": nova_data.strip(),
                        "visitas.$.relato": novo_relato.strip(),
                    }
                }
            )

            if resultado.modified_count == 1:
                st.success("Visita atualizada com sucesso!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Erro ao atualizar visita.")



# Botão para abrir o dialogo de gerenciar visitas (só pra usuários internos)

if usuario_interno:
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button(
            "Gerenciar visitas",
            icon=":material/edit:",
            type="secondary",
            width=200,
            key="gerenciar_visitas"
        ):
            gerenciar_visitas()





# ============================================================
# VISITAS — LISTAGEM
# ============================================================

visitas = (
    df_projeto["visitas"].values[0]
    if "visitas" in df_projeto.columns and df_projeto["visitas"].values[0]
    else []
)

if not visitas:
    st.caption("Não há visitas registradas.")
else:
    df_visitas = pd.DataFrame(visitas)
    df_visitas = df_visitas[["data_visita", "relato", "autor"]]
    with st.container():
        ui.table(data=df_visitas, key="tabela_visitas_fixa")




st.write('')
st.write('')
st.write('')




# ============================================================
# CONTATOS
# ============================================================

st.markdown("#### Contatos")

# ============================================================
# DIÁLOGO DE GERENCIAMENTO DE CONTATOS
# ============================================================

@st.dialog("Gerenciar contatos", width="medium")
def gerenciar_contatos():

    # Abas para criar e editar contatos
    nova_tab, editar_tab = st.tabs(["Novo contato", "Editar contato"])



    # ========================================================
    # NOVO CONTATO
    # ========================================================
    with nova_tab:

        # Campos do formulário
        nome = st.text_input("Nome")
        funcao = st.text_input("Função no projeto")
        telefone = st.text_input("Telefone")
        email = st.text_input("E-mail")

        assina_docs = st.checkbox(
            "Incluir na assinatura de contratos e recibos",
            value=False,
            key="novo_contato_assina_docs"
        )


        st.write('')
        # Botão de salvar
        if st.button(
            "Salvar contato",
            type="primary",
            icon=":material/save:",
            key="salvar_novo_contato"
        ):

            # Validação básica
            if not nome.strip() or not funcao.strip():
                st.warning("Nome e função são obrigatórios.")
                return

            # Estrutura do contato
            contato = {
                "nome": nome.strip(),
                "funcao": funcao.strip(),
                "telefone": telefone.strip(),
                "email": email.strip(),
                "assina_docs": assina_docs,  # 👈 NOVO
                "autor": st.session_state.nome,
            }

            # Insere o contato no projeto
            resultado = col_projetos.update_one(
                {"codigo": st.session_state.projeto_atual},
                {"$push": {"contatos": contato}}
            )

            if resultado.modified_count == 1:
                st.success("Contato cadastrado com sucesso!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Erro ao salvar contato.")







    # ========================================================
    # EDITAR CONTATO
    # ========================================================
    with editar_tab:

        # Recupera os contatos do projeto
        contatos_local = (
            df_projeto["contatos"].values[0]
            if "contatos" in df_projeto.columns
            else []
        )

        # Mostra apenas contatos criados pelo usuário
        contatos_usuario = [
            c for c in contatos_local
            if c.get("autor") == st.session_state.nome
        ]

        if not contatos_usuario:
            st.write("Não há contatos cadastrados por você.")
            return

        # Mapa amigável para seleção
        mapa_contatos = {
            f"{c['nome']} — {c['funcao']}": c
            for c in contatos_usuario
        }

        contato_label = st.selectbox(
            "Selecione o contato",
            list(mapa_contatos.keys())
        )

        contato_selecionado = mapa_contatos[contato_label]

        # Campos editáveis
        nome = st.text_input("Nome", value=contato_selecionado["nome"])
        funcao = st.text_input("Função no projeto", value=contato_selecionado["funcao"])
        telefone = st.text_input("Telefone", value=contato_selecionado.get("telefone", ""))
        email = st.text_input("E-mail", value=contato_selecionado.get("email", ""))

        # CHECKBOX PRÉ-CARREGADO DO BANCO
        assina_docs = st.checkbox(
            "Incluir na assinatura de contratos e recibos",
            value=contato_selecionado.get("assina_docs", False),
            key=f"editar_contato_assina_docs_{contato_selecionado['nome']}"
        )


        st.write('')
        # Botão de salvar alterações
        if st.button(
            "Salvar alterações",
            type="primary",
            icon=":material/save:",
            key="salvar_editar_contato"
        ):

            if not nome.strip() or not funcao.strip():
                st.warning("Nome e função são obrigatórios.")
                return

            # Atualiza o contato específico
            resultado = col_projetos.update_one(
                {
                    "codigo": st.session_state.projeto_atual,
                    "contatos.nome": contato_selecionado["nome"],
                    "contatos.funcao": contato_selecionado["funcao"],
                    "contatos.autor": st.session_state.nome,
                },
                {
                    "$set": {
                        "contatos.$.nome": nome.strip(),
                        "contatos.$.funcao": funcao.strip(),
                        "contatos.$.telefone": telefone.strip(),
                        "contatos.$.email": email.strip(),
                        "contatos.$.assina_docs": assina_docs,  # 👈 NOVO
                    }
                }
            )

            if resultado.modified_count == 1:
                st.success("Contato atualizado com sucesso!", icon=":material/check:")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Erro ao atualizar contato.")




with st.container(horizontal=True, horizontal_alignment="right"):
    if st.button(
        "Gerenciar contatos",
        icon=":material/edit:",
        type="secondary",
        width=200,
        key="gerenciar_contatos"
    ):
        gerenciar_contatos()








contatos = (
    df_projeto["contatos"].values[0]
    if "contatos" in df_projeto.columns and df_projeto["contatos"].values[0]
    else []
)

if not contatos:
    st.caption("Não há contatos cadastrados.")
else:
    df_contatos = pd.DataFrame(contatos)

    # Coluna de exibição: assina documentos
    df_contatos["Assina documentos"] = df_contatos.apply(
        lambda row: "Sim" if row.get("assina_docs", False) is True else "",
        axis=1
    )

    # Renomeia colunas para exibição
    df_contatos = df_contatos.rename(columns={
        "nome": "Nome",
        "funcao": "Função no projeto",
        "telefone": "Telefone",
        "email": "E-mail"
    })

    # Define ordem das colunas
    df_contatos = df_contatos[
        ["Nome", "Função no projeto", "Telefone", "E-mail", "Assina documentos"]
    ]

    with st.container():
        ui.table(data=df_contatos, key="tabela_contatos")







# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()

