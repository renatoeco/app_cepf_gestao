import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao # Funções personalizadas
import pandas as pd
import locale
import re
import time
import uuid
import datetime
import smtplib
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Importa coleções e cria dataframes
col_pessoas = db["pessoas"]
df_pessoas = pd.DataFrame(list(col_pessoas.find()))

col_projetos = db["projetos"]
df_projetos = pd.DataFrame(list(col_projetos.find()))


###########################################################################################################
# CONFIGURAÇÃO DE LOCALE
###########################################################################################################




###########################################################################################################
# FUNÇÕES
###########################################################################################################

def gerar_codigo_aleatorio():
    """Gera um código numérico aleatório de 6 dígitos como string."""
    return f"{random.randint(0, 999999):06d}"


def enviar_email_convite(nome_completo, email_destino, codigo):
    """
    Envia um e-mail de convite com código de 6 dígitos usando credenciais do st.secrets.
    Retorna True se enviado, False se falhou.
    """
    try:
        smtp_server = st.secrets["senhas"]["smtp_server"]
        port = st.secrets["senhas"]["port"]
        endereco_email = st.secrets["senhas"]["endereco_email"]
        senha_email = st.secrets["senhas"]["senha_email"]

        msg = MIMEMultipart()
        msg['From'] = endereco_email
        msg['To'] = email_destino
        msg['Subject'] = "Convite para a Plataforma CEPF"

        corpo_html = f"""
        <p>Olá {nome_completo},</p>
        <p>Você foi convidado para utilizar a <strong>Plataforma de Gestão de Projetos do CEPF</strong>.</p>
        <p>Para realizar seu cadastro, acesse o link abaixo e clique no botão <strong>"Primeiro acesso"</strong>:</p>
        <p><a href="https://cepf-ieb.streamlit.app/">Acesse aqui a Plataforma</a></p>
        <p>Insira o seu <strong>e-mail</strong> e o <strong>código</strong> que te enviamos abaixo:</p>
        <h2>{codigo}</h2>
        <p>Se tiver alguma dúvida, entre em contato com a equipe do CEPF.</p>
        """
        msg.attach(MIMEText(corpo_html, 'html'))

        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(endereco_email, senha_email)
        server.send_message(msg)
        server.quit()

        st.success(f":material/mail: E-mail de convite enviado para {email_destino}.")
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail para {email_destino}: {e}")
        return False




# def enviar_email_convite(nome_completo, email_destino, codigo):
#     """
#     Envia um e-mail de convite com código de 6 dígitos usando credenciais do st.secrets.
#     Retorna True se enviado, False se falhou.
#     """
#     try:
#         smtp_server = st.secrets["senhas"]["smtp_server"]
#         port = st.secrets["senhas"]["port"]
#         endereco_email = st.secrets["senhas"]["endereco_email"]
#         senha_email = st.secrets["senhas"]["senha_email"]

#         msg = MIMEMultipart()
#         msg['From'] = endereco_email
#         msg['To'] = email_destino
#         msg['Subject'] = "Convite para a Plataforma CEPF"

#         corpo_html = f"""
#         <p>Olá {nome_completo},</p>
#         <p>Você foi convidado para utilizar a <strong>Plataforma de Gestão de Projetos do CEPF</strong>.</p>
#         <p>Para realizar seu cadastro, acesse o link abaixo e clique no botão <strong>"Primeiro acesso"</strong>:</p>
#         <p><a href="https://cepf-ieb.streamlit.app/">Acesse aqui a Plataforma</a></p>
#         <p>Insira o seu e-mail e o código que te enviamos abaixo:</p>
#         <h2>{codigo}</h2>
#         <p>Se tiver alguma dúvida, entre em contato com a equipe do CEPF.</p>
#         """
#         msg.attach(MIMEText(corpo_html, 'html'))

#         server = smtplib.SMTP(smtp_server, port)
#         server.starttls()
#         server.login(endereco_email, senha_email)
#         server.send_message(msg)
#         server.quit()

#         return True
#     except Exception as e:
#         print(f"Erro ao enviar e-mail para {email_destino}: {e}")  # log no console
#         return False






def df_index1(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    df2.index = range(1, len(df2) + 1)
    return df2




# Regex para validar e-mail
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
def validar_email(email):
    if not email:
        return False
    return bool(re.match(EMAIL_REGEX, str(email).strip()))






###########################################################################################################
# TRATAMENTO DE DADOS   
###########################################################################################################

tipo_usuario = st.session_state.get("tipo_usuario", "")



projetos = df_projetos["sigla"].unique().tolist()

###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Convidar pessoa")


opcao_cadastro = st.radio("", ["Convite individual", "Convite em massa"], key="opcao_cadastro", horizontal=True)

st.write('')





# --------------------------
# FORMULÁRIO DE CADASTRO
# --------------------------
if opcao_cadastro == "Convite individual":

    # --- campos do formulário que vamos controlar ---
    CAMPOS_FORM_PESSOA = {
        "nome_completo_novo": "",
        "tipo_novo_usuario": "",
        "tipo_beneficiario": "",   # string; só usado quando beneficiário
        "e_mail": "",
        "telefone": "",
        "projetos_escolhidos": []  # multiselect espera lista
    }

    # --- limpeza no topo: se o flag estiver setado, reseta APENAS esses campos ---
    if st.session_state.get("limpar_form_pessoa", False):
        for k, default in CAMPOS_FORM_PESSOA.items():
            st.session_state[k] = default
        # remove o flag para não ficar em loop
        st.session_state.pop("limpar_form_pessoa", None)
        # re-renderiza com campos zerados (não necessário sempre, mas seguro)
        st.rerun()



    # --- Inputs com keys que coincidem com as chaves do session_state ---
    nome_completo_novo = st.text_input("Nome completo", key="nome_completo_novo")

    # depende do tipo de usuário logado (ex.: tipo_usuario vem do login)
    if tipo_usuario == "equipe":
        tipo_novo_usuario = st.selectbox(
            "Tipo de usuário", ["beneficiario", "visitante"], key="tipo_novo_usuario"
        )
    elif tipo_usuario == "admin":
        tipo_novo_usuario = st.selectbox(
            "Tipo de usuário", ["", "admin", "equipe", "beneficiario", "visitante"], key="tipo_novo_usuario"
        )
    else:
        # se quiser um fallback:
        tipo_novo_usuario = st.selectbox(
            "Tipo de usuário", ["", "beneficiario", "visitante"], key="tipo_novo_usuario"
        )

    # mostra apenas se selecionado beneficiário
    if st.session_state.get("tipo_novo_usuario") == "beneficiario":
        tipo_beneficiario = st.selectbox(
            "Tipo de beneficiário", ["", "técnico", "financeiro"], key="tipo_beneficiario"
        )
    else:
        # garante que o key exista (útil para limpeza/validação)
        if "tipo_beneficiario" not in st.session_state:
            st.session_state["tipo_beneficiario"] = ""

    e_mail = st.text_input("E-mail", key="e_mail")
    telefone = st.text_input("Telefone", key="telefone")

    # garante que a key exista com lista vazia caso ainda não exista
    if "projetos_escolhidos" not in st.session_state:
        st.session_state["projetos_escolhidos"] = []

    # Garante que a key exista com lista vazia caso ainda não exista
    if "projetos_escolhidos" not in st.session_state:
        st.session_state["projetos_escolhidos"] = []

    # Agora cria o multiselect sem passar default
    projetos_escolhidos = st.multiselect(
        "Projetos",
        projetos,
        key="projetos_escolhidos"
    )



    # projetos_escolhidos = st.multiselect(
    #     "Projetos",
    #     projetos,
    #     default=st.session_state["projetos_escolhidos"],  # pega o valor atual do session_state
    #     key="projetos_escolhidos"
    # )


    st.write("")
    submit_button = st.button("Salvar", icon=":material/save:", type="primary", width=150)



    if submit_button:
        # 1) Validações
        if not st.session_state["nome_completo_novo"] or not st.session_state["tipo_novo_usuario"] \
        or not st.session_state["e_mail"] or not st.session_state["telefone"]:
            st.error(":material/error: Todos os campos obrigatórios devem ser preenchidos.")
            st.stop()

        if st.session_state["tipo_novo_usuario"] == "beneficiario" and not st.session_state.get("tipo_beneficiario"):
            st.error(":material/error: O campo 'Tipo de beneficiário' é obrigatório para beneficiários.")
            st.stop()

        if not validar_email(st.session_state["e_mail"]):
            st.error(":material/error: E-mail inválido.")
            st.stop()

        if col_pessoas.find_one({"e_mail": st.session_state["e_mail"]}):
            st.error(f":material/error: O e-mail '{st.session_state['e_mail']}' já está cadastrado.")
            st.stop()

        # 2) Gera código de 6 dígitos
        codigo_6_digitos = gerar_codigo_aleatorio()

        # 3) Monta documento a inserir no MongoDB
        novo_doc = {
            "nome_completo": st.session_state["nome_completo_novo"],
            "tipo_usuario": st.session_state["tipo_novo_usuario"],
            "e_mail": st.session_state["e_mail"],
            "telefone": st.session_state["telefone"],
            "status": "convidado",
            "projetos": st.session_state.get("projetos_escolhidos", []),
            "data_convite": datetime.datetime.now().strftime("%d/%m/%Y"),
            "senha": None,
            "codigo_convite": codigo_6_digitos
        }

        if st.session_state["tipo_novo_usuario"] == "beneficiario":
            novo_doc["tipo_beneficiario"] = st.session_state.get("tipo_beneficiario")

        # 4) Inserir no banco
        col_pessoas.insert_one(novo_doc)

        with st.spinner("Cadastrando pessoa... aguarde..."):

            time.sleep(2)

            st.success(":material/check: Pessoa cadastrada com sucesso no banco de dados!")

            # 5) Envio do e-mail de convite
            enviado = enviar_email_convite(
                nome_completo=st.session_state["nome_completo_novo"],
                email_destino=st.session_state["e_mail"],
                codigo=codigo_6_digitos
            )



            # 6) Limpar campos do formulário e rerun
            st.session_state["limpar_form_pessoa"] = True
            time.sleep(6)
            st.rerun()









    # if submit_button:
    #     # validações
    #     if not st.session_state["nome_completo_novo"] or not st.session_state["tipo_novo_usuario"] \
    #     or not st.session_state["e_mail"] or not st.session_state["telefone"]:
    #         st.error(":material/error: Todos os campos obrigatórios devem ser preenchidos.")
    #         st.stop()

    #     if st.session_state["tipo_novo_usuario"] == "beneficiario" and not st.session_state.get("tipo_beneficiario"):
    #         st.error(":material/error: O campo 'Tipo de beneficiário' é obrigatório para beneficiários.")
    #         st.stop()

    #     if not validar_email(st.session_state["e_mail"]):
    #         st.error(":material/error: E-mail inválido.")
    #         st.stop()

    #     if col_pessoas.find_one({"e_mail": st.session_state["e_mail"]}):
    #         st.error(f":material/error: O e-mail '{st.session_state['e_mail']}' já está cadastrado.")
    #         st.stop()

    #     # Gera o código de 6 dígitos
    #     codigo_6_digitos = gerar_codigo_aleatorio()

    #     # monta documento a inserir
    #     novo_doc = {
    #         "nome_completo": st.session_state["nome_completo_novo"],
    #         "tipo_usuario": st.session_state["tipo_novo_usuario"],
    #         "e_mail": st.session_state["e_mail"],
    #         "telefone": st.session_state["telefone"],
    #         "status": "convidado",
    #         "projetos": st.session_state.get("projetos_escolhidos", []),
    #         "data_convite": datetime.datetime.now().strftime("%d/%m/%Y"),
    #         "senha": None,
    #         "codigo_convite": codigo_6_digitos
    #     }

    #     if st.session_state["tipo_novo_usuario"] == "beneficiario":
    #         novo_doc["tipo_beneficiario"] = st.session_state.get("tipo_beneficiario")

    #     # inserir no banco
    #     col_pessoas.insert_one(novo_doc)
    #     st.success(":material/check: Pessoa cadastrada com sucesso!")

    #     # Tenta enviar o e-mail de convite
    #     try:
    #         enviado = enviar_email_convite(
    #             nome_completo=st.session_state["nome_completo_novo"],
    #             email_destino=st.session_state["e_mail"],
    #             codigo=codigo_6_digitos
    #         )
    #         if enviado:
    #             st.success(":material/check: E-mail de convite enviado com sucesso!")
    #         else:
    #             st.warning(":material/warning: O e-mail de convite não pôde ser enviado.")
    #     except Exception as e:
    #         st.error(":material/error: Erro ao tentar enviar o e-mail de convite.")
    #         st.exception(e)

    #     # limpa campos do formulário
    #     time.sleep(2)
    #     st.session_state["limpar_form_pessoa"] = True
    #     st.rerun()






    # if submit_button:
    #     # validações
    #     if not st.session_state["nome_completo"] or not st.session_state["tipo_novo_usuario"] \
    #        or not st.session_state["e_mail"] or not st.session_state["telefone"]:
    #         st.error(":material/error: Todos os campos obrigatórios devem ser preenchidos.")
    #         st.stop()

    #     # se beneficiário, tipo_beneficiario obrigatório
    #     if st.session_state["tipo_novo_usuario"] == "beneficiario" and not st.session_state.get("tipo_beneficiario"):
    #         st.error(":material/error: O campo 'Tipo de beneficiário' é obrigatório para beneficiários.")
    #         st.stop()

    #     # valida email (usa sua função validar_email)
    #     if not validar_email(st.session_state["e_mail"]):
    #         st.error(":material/error: E-mail inválido.")
    #         st.stop()

    #     # duplicidade
    #     if col_pessoas.find_one({"e_mail": st.session_state["e_mail"]}):
    #         st.error(f":material/error: O e-mail '{st.session_state['e_mail']}' já está cadastrado.")
    #         st.stop()

    #     # monta documento a inserir
    #     novo_doc = {
    #         "nome_completo": st.session_state["nome_completo"],
    #         "tipo_usuario": st.session_state["tipo_novo_usuario"],
    #         "e_mail": st.session_state["e_mail"],
    #         "telefone": st.session_state["telefone"],
    #         "status": "convidado",
    #         "projetos": st.session_state.get("projetos_escolhidos", []),
    #         "data_convite": datetime.datetime.now().strftime("%d/%m/%Y"),
    #         "senha": None
    #     }

    #     if st.session_state["tipo_novo_usuario"] == "beneficiario":
    #         novo_doc["tipo_beneficiario"] = st.session_state.get("tipo_beneficiario")

    #     # inserir no banco
    #     col_pessoas.insert_one(novo_doc)
    #     st.success(":material/check: Pessoa cadastrada com sucesso!")

    #     # Enviar email de convite com código de 6 números
    #     codigo_6_digitos = gerar_codigo_aleatorio()

    #     enviar_email_convite(
    #         nome_completo=st.session_state["nome_completo"],
    #         email_destino=st.session_state["e_mail"],
    #         codigo=codigo_6_digitos
    #     )


    #     # marca para limpar apenas os campos do formulário e re-executa
    #     st.session_state["limpar_form_pessoa"] = True
    #     time.sleep(2)
    #     st.rerun()




# ----------------------------
#   CONVITE EM MASSA
# ----------------------------



elif opcao_cadastro == "Convite em massa":

    # Inicializa o 'key' do file_uploader se ele não existir
    if 'uploader_key' not in st.session_state:
        st.session_state['uploader_key'] = str(uuid.uuid4())

    st.write("Baixe aqui o modelo de tabela para convite em massa:")

    with open("modelos/modelo_convite_pessoas_em_massa.xlsx", "rb") as f:
        st.download_button(
            label=":material/download: Baixar modelo XLSX",
            data=f,
            file_name="modelo_convite_pessoas_em_massa.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.divider()

    # ------------------------------
    # Upload
    # ------------------------------
    arquivo = st.file_uploader(
        "Envie um arquivo XLSX preenchido para convidar múltiplas pessoas:",
        type=["xlsx"],
        key=st.session_state['uploader_key'],
        width=400
    )

    st.write("")

    if arquivo is not None:
        try:
            df_upload = pd.read_excel(arquivo)

            st.success("Arquivo carregado com sucesso!")

            # ==========================================================
            # Renomear colunas do modelo para padronizar
            # ==========================================================
            if "tipo_beneficiario (técnico ou financeiro)" in df_upload.columns:
                df_upload.rename(columns={"tipo_beneficiario (técnico ou financeiro)": "tipo_beneficiario"}, inplace=True)

            if "projetos (códigos separados por vírgula) (opcional)" in df_upload.columns:
                df_upload.rename(columns={"projetos (códigos separados por vírgula) (opcional)": "projetos"}, inplace=True)

            # ==========================================================
            # 0) Validar se o arquivo está vazio
            # ==========================================================
            if df_upload.empty or df_upload.dropna(how="all").empty:
                st.error(
                    ":material/error: O arquivo enviado está vazio!\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )
                st.stop()

            # Exibir com index iniciado em 1
            st.dataframe(df_index1(df_upload))
            st.write("")

            # ==========================================================
            # 1) Validar colunas obrigatórias
            # ==========================================================
            colunas_obrigatorias = ["nome_completo", "e_mail", "tipo_beneficiario"]
            faltando = [c for c in colunas_obrigatorias if c not in df_upload.columns]
            if faltando:
                st.error(
                    f":material/error: Faltam colunas obrigatórias no arquivo: {faltando}\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )
                st.stop()

            # Criar colunas opcionais se não existirem
            if "telefone (opcional)" not in df_upload.columns:
                df_upload["telefone (opcional)"] = ""
            if "projetos" not in df_upload.columns:
                df_upload["projetos"] = ""

            # ==========================================================
            # 2) Validar e-mails
            # ==========================================================
            df_upload["e_mail"] = df_upload["e_mail"].astype(str).str.strip()
            invalidos_email = df_upload[~df_upload["e_mail"].apply(validar_email)]
            if not invalidos_email.empty:
                st.error(
                    ":material/error: Existem e-mails inválidos!\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )
                st.dataframe(df_index1(invalidos_email))
                st.stop()

            # ==========================================================
            # 3) Validar tipo_beneficiario
            # ==========================================================
            valores_validos_benef = ["técnico", "financeiro"]
            df_upload["tipo_beneficiario"] = df_upload["tipo_beneficiario"].astype(str).str.strip()

            invalidos_benef = df_upload[~df_upload["tipo_beneficiario"].isin(valores_validos_benef)]
            if not invalidos_benef.empty:
                st.error(
                    ":material/error: Existem registros com 'tipo_beneficiario' inválido!\n"
                    "Os valores válidos são: técnico ou financeiro.\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )
                st.dataframe(df_index1(invalidos_benef))
                st.stop()

            erros_benef = df_upload[df_upload["tipo_beneficiario"] == ""]
            if not erros_benef.empty:
                st.error(
                    ":material/error: Todos os registros devem ter o campo 'tipo_beneficiario' preenchido.\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )
                st.dataframe(df_index1(erros_benef))
                st.stop()

            # ==========================================================
            # 4) Verificar duplicidade interna no arquivo
            # ==========================================================
            dup_email = df_upload[df_upload.duplicated("e_mail", keep=False)]
            if not dup_email.empty:
                st.error(
                    ":material/error: Existem e-mails duplicados dentro do próprio arquivo.\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )
                st.subheader("E-mails duplicados")
                st.dataframe(df_index1(dup_email))
                st.stop()

            # ==========================================================
            # 5) Verificar duplicidades no banco
            # ==========================================================
            existentes = pd.DataFrame(list(col_pessoas.find({}, {"e_mail": 1})))
            conflitos_email = []
            if not existentes.empty:
                for _, row in df_upload.iterrows():
                    if row["e_mail"] in existentes["e_mail"].values:
                        conflitos_email.append(row.to_dict())
            if conflitos_email:
                st.error(
                    ":material/error: Existem e-mails que já estão cadastrados no banco de dados!\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )
                st.write("**E-mails já existentes:**")
                st.dataframe(df_index1(pd.DataFrame(conflitos_email)))
                st.stop()


                # ==========================================================
                # 6) Validar projetos no banco
                # ==========================================================

                # Criar lista de códigos válidos a partir do banco
                codigos_validos = df_projetos["codigo"].astype(str).str.strip().unique()

                # Transformar a coluna projetos do upload em lista (aceitando vazio)
                df_upload["projetos"] = df_upload["projetos"].apply(
                    lambda x:
                        [] if pd.isna(x) or str(x).strip() == "" or str(x).strip().lower() == "nan"
                        else [p.strip() for p in str(x).split(",") if p.strip()]
                )

                # Verificar códigos inválidos
                invalidos_projetos = df_upload[df_upload["projetos"].apply(
                    lambda lst: any(codigo not in codigos_validos for codigo in lst)
                )]

                if not invalidos_projetos.empty:
                    st.error(
                        ":material/error: Existem projetos com códigos inválidos ou inexistentes no banco!\n\n"
                        "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                    )
                    st.dataframe(df_index1(invalidos_projetos))
                    st.stop()




            # ==========================================================
            # 7) Inserir no banco
            # ==========================================================
            if st.button(":material/save: Cadastrar pessoas", type="primary"):

                registros = []
                for _, row in df_upload.iterrows():
                    doc = {
                        "nome_completo": row["nome_completo"],
                        "tipo_usuario": "beneficiario",
                        "tipo_beneficiario": row["tipo_beneficiario"],
                        "e_mail": row["e_mail"],
                        "status": "ativo",
                        # "senha": None
                    }

                    # Adiciona telefone somente se houver valor
                    if pd.notna(row["telefone (opcional)"]) and str(row["telefone (opcional)"]).strip():
                        doc["telefone"] = str(row["telefone (opcional)"]).strip()


                    if row["projetos"]:
                        doc["projetos"] = row["projetos"]

                    registros.append(doc)

                resultado = col_pessoas.insert_many(registros)

                st.success(f":material/check: {len(resultado.inserted_ids)} pessoas cadastradas com sucesso!")

                # Resetar o uploader para limpar formulário
                st.session_state['uploader_key'] = str(uuid.uuid4())
                time.sleep(2)
                st.rerun()




        except Exception as e:
            st.error(
                ":material/error: Erro ao processar o arquivo.\n\n"
                "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
            )
            st.exception(e)





















# elif opcao_cadastro == "Cadastro em massa":

#     # Inicializa o 'key' do file_uploader se ele não existir
#     if 'uploader_key' not in st.session_state:
#         st.session_state['uploader_key'] = str(uuid.uuid4())

#     st.write("Baixe aqui o modelo de tabela para cadastro em massa:")

#     with open("modelos/modelo_cadastro_pessoas_em_massa.xlsx", "rb") as f:
#         st.download_button(
#             label=":material/download: Baixar modelo XLSX",
#             data=f,
#             file_name="modelo_cadastro_pessoas_em_massa.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         )

#     st.divider()

#     # ------------------------------
#     # Upload
#     # ------------------------------
#     arquivo = st.file_uploader(
#         "Envie um arquivo XLSX preenchido para cadastrar múltiplas pessoas:",
#         type=["xlsx"],
#         key=st.session_state['uploader_key']
#     )

#     st.write("")

#     if arquivo is not None:
#         try:
#             df_upload = pd.read_excel(arquivo)

#             st.success("Arquivo carregado com sucesso!")

#             # Renomear a coluna "tipo_beneficiario" "tipo_beneficiario (técnico ou financeiro)"
#             if "tipo_beneficiario (técnico ou financeiro)" in df_upload.columns:
#                 df_upload.rename(columns={"tipo_beneficiario (técnico ou financeiro)": "tipo_beneficiario"}, inplace=True)

#             # Renomear a coluna "projetos (códigos separados por vírgula) (opcional)"
#             if "projetos (códigos separados por vírgula) (opcional)" in df_upload.columns:   
#                 df_upload.rename(columns={"projetos (códigos separados por vírgula) (opcional)": "projetos"}, inplace=True)


#             # ==========================================================
#             # 0) Validar se o arquivo está vazio
#             # ==========================================================
#             if df_upload.empty or df_upload.dropna(how="all").empty:
#                 st.error(
#                     ":material/error: O arquivo enviado está vazio!\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.stop()

#             # Exibir com index iniciado em 1
#             st.dataframe(df_index1(df_upload))
#             st.write("")

#             # ==========================================================
#             # 1) Validar colunas obrigatórias
#             # ==========================================================
#             colunas_obrigatorias = ["nome_completo", "e_mail", "tipo_beneficiario"]
#             faltando = [c for c in colunas_obrigatorias if c not in df_upload.columns]

#             if faltando:
#                 st.error(
#                     f":material/error: Faltam colunas obrigatórias no arquivo: {faltando}\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.stop()

#             # Criar colunas opcionais se não existirem
#             if "telefone (opcional)" not in df_upload.columns:
#                 df_upload["telefone (opcional)"] = ""

#             if "projetos (códigos separados por vírgula) (opcional)" not in df_upload.columns:
#                 df_upload["projetos (códigos separados por vírgula) (opcional)"] = ""

#             # ==========================================================
#             # 2) Validar e-mails
#             # ==========================================================
#             df_upload["e_mail"] = df_upload["e_mail"].astype(str).str.strip()
#             invalidos = df_upload[~df_upload["e_mail"].apply(validar_email)]
#             if not invalidos.empty:
#                 st.error(
#                     ":material/error: Existem e-mails inválidos!\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.dataframe(df_index1(invalidos))
#                 st.stop()

#             # ==========================================================
#             # 3) Verificar se tipo_beneficiario está preenchido e valores válidos de tipo_beneficiario
#             # ==========================================================

#             valores_validos_benef = ["técnico", "financeiro"]
#             invalidos_benef = df_upload[~df_upload["tipo_beneficiario"].astype(str).str.strip().isin(valores_validos_benef)]

#             if not invalidos_benef.empty:
#                 st.error(
#                     ":material/error: Existem registros com 'tipo_beneficiario' inválido!\n"
#                     "Os valores válidos são: técnico ou financeiro.\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.dataframe(df_index1(invalidos_benef))
#                 st.stop()

#             erros_benef = df_upload[df_upload["tipo_beneficiario"].astype(str).str.strip() == ""]
#             if not erros_benef.empty:
#                 st.error(
#                     ":material/error: Todos os registros devem ter o campo 'tipo_beneficiario' preenchido.\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.dataframe(df_index1(erros_benef))
#                 st.stop()

#             # ==========================================================
#             # 4) Verificar duplicidade interna no arquivo
#             # ==========================================================
#             dup_email = df_upload[df_upload.duplicated("e_mail", keep=False)]
#             if not dup_email.empty:
#                 st.error(
#                     ":material/error: Existem e-mails duplicados dentro do próprio arquivo.\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.subheader("E-mails duplicados")
#                 st.dataframe(df_index1(dup_email))
#                 st.stop()

#             # ==========================================================
#             # 5) Verificar duplicidades no banco
#             # ==========================================================

#             existentes = pd.DataFrame(list(col_pessoas.find({}, {"e_mail": 1})))
#             conflitos_email = []

#             if not existentes.empty:
#                 for _, row in df_upload.iterrows():
#                     if row["e_mail"] in existentes["e_mail"].values:
#                         conflitos_email.append(row.to_dict())

#             if conflitos_email:
#                 st.error(
#                     ":material/error: Existem e-mails que já estão cadastrados no banco de dados!\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.write("**E-mails já existentes:**")
#                 st.dataframe(df_index1(pd.DataFrame(conflitos_email)))
#                 st.stop()

#             # ==========================================================
#             # 6) Inserir no banco
#             # ==========================================================
#             if st.button(":material/save: Cadastrar pessoas", type="primary"):

#                 registros = []
#                 for _, row in df_upload.iterrows():

#                     doc = {
#                         "nome_completo": row["nome_completo"],
#                         "tipo_usuario": "beneficiario",  # Sempre beneficiário
#                         "tipo_beneficiario": row["tipo_beneficiario"],
#                         "e_mail": row["e_mail"],
#                         "telefone": row["telefone (opcional)"] if row["telefone (opcional)"] else None,
#                         "status": "ativo",
#                         "senha": None,
#                         "projetos": [p.strip() for p in str(row["projetos"]).split(",") if p.strip()]
#                     }

#                     registros.append(doc)

#                 resultado = col_pessoas.insert_many(registros)

#                 st.success(f":material/check: {len(resultado.inserted_ids)} pessoas cadastradas com sucesso!")

#                 # Resetar o uploader para limpar formulário
#                 st.session_state['uploader_key'] = str(uuid.uuid4())

#                 time.sleep(2)
#                 st.rerun()

#         except Exception as e:
#             st.error(
#                 ":material/error: Erro ao processar o arquivo.\n\n"
#                 "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#             )
#             st.exception(e)



















# elif opcao_cadastro == "Cadastro em massa":

#     # Inicializa o 'key' do file_uploader se ele não existir
#     if 'uploader_key' not in st.session_state:
#         st.session_state['uploader_key'] = str(uuid.uuid4())

#     st.write("Baixe aqui o modelo de tabela para cadastro em massa:")

#     with open("modelos/modelo_cadastro_pessoas_em_massa.xlsx", "rb") as f:
#         st.download_button(
#             label=":material/download: Baixar modelo XLSX",
#             data=f,
#             file_name="modelo_cadastro_pessoas_em_massa.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         )

#     st.divider()

#     # ------------------------------
#     # Upload
#     # ------------------------------
#     arquivo = st.file_uploader(
#         "Envie um arquivo XLSX preenchido para cadastrar múltiplas pessoas:",
#         type=["xlsx"],
#         key=st.session_state['uploader_key']
#     )

#     st.write("")

#     if arquivo is not None:
#         try:
#             df_upload = pd.read_excel(arquivo)

#             st.success("Arquivo carregado com sucesso!")

#             # ==========================================================
#             # 0) Validar se o arquivo está vazio
#             # ==========================================================
#             if df_upload.empty or df_upload.dropna(how="all").empty:
#                 st.error(
#                     ":material/error: O arquivo enviado está vazio!\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.stop()

#             # Exibir com index iniciado em 1
#             st.dataframe(df_index1(df_upload))
#             st.write("")

#             # ==========================================================
#             # 1) Validar colunas obrigatórias
#             # ==========================================================
#             colunas_obrigatorias = ["nome_completo", "tipo_usuario", "e_mail"]
#             faltando = [c for c in colunas_obrigatorias if c not in df_upload.columns]

#             if faltando:
#                 st.error(
#                     f":material/error: Faltam colunas obrigatórias no arquivo: {faltando}\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.stop()

#             # Criar colunas opcionais se não existirem
#             if "tipo_beneficiario" not in df_upload.columns:
#                 df_upload["tipo_beneficiario"] = ""

#             if "telefone (opcional)" not in df_upload.columns:
#                 df_upload["telefone (opcional)"] = ""

#             if "projetos (siglas separadas por vírgula) (opcional)" not in df_upload.columns:
#                 df_upload["projetos (siglas separadas por vírgula) (opcional)"] = ""

#             # ==========================================================
#             # 2) Validar e-mails
#             # ==========================================================
#             df_upload["e_mail"] = df_upload["e_mail"].astype(str).str.strip()
#             invalidos = df_upload[~df_upload["e_mail"].apply(validar_email)]
#             if not invalidos.empty:
#                 st.error(
#                     ":material/error: Existem e-mails inválidos!\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.dataframe(df_index1(invalidos))
#                 st.stop()

#             # ==========================================================
#             # 3) Validar beneficiários
#             # ==========================================================
#             erros_benef = df_upload[
#                 (df_upload["tipo_usuario"] == "beneficiario")
#                 & (df_upload["tipo_beneficiario"].astype(str).str.strip() == "")
#             ]
#             if not erros_benef.empty:
#                 st.error(
#                     ":material/error: Existem beneficiários sem o campo 'tipo_beneficiario'.\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.dataframe(df_index1(erros_benef))
#                 st.stop()

#             # ==========================================================
#             # 4) Verificar duplicidade interna no arquivo
#             # ==========================================================
#             dup_email = df_upload[df_upload.duplicated("e_mail", keep=False)]
#             if not dup_email.empty:
#                 st.error(
#                     ":material/error: Existem e-mails duplicados dentro do próprio arquivo.\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.write("**E-mails duplicados**")
#                 st.dataframe(df_index1(dup_email))
#                 st.stop()

#             # ==========================================================
#             # 5) Verificar duplicidades no banco
#             # ==========================================================
#             # db = conectar_mongo_cepf_gestao()
#             # col_pessoas = db["pessoas"]

#             existentes = pd.DataFrame(list(col_pessoas.find({}, {"e_mail": 1})))
#             conflitos_email = []

#             if not existentes.empty:
#                 for _, row in df_upload.iterrows():
#                     if row["e_mail"] in existentes["e_mail"].values:
#                         conflitos_email.append(row.to_dict())

#             if conflitos_email:
#                 st.error(
#                     ":material/error: Existem e-mails que já estão cadastrados no banco de dados!\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.write("**E-mails já existentes:**")
#                 st.dataframe(df_index1(pd.DataFrame(conflitos_email)))
#                 st.stop()

#             # ==========================================================
#             # 6) Inserir no banco
#             # ==========================================================
#             if st.button(":material/save: Cadastrar pessoas", type="primary"):

#                 registros = []
#                 for _, row in df_upload.iterrows():

#                     doc = {
#                         "nome_completo": row["nome_completo"],
#                         "tipo_usuario": row["tipo_usuario"],
#                         "e_mail": row["e_mail"],
#                         "telefone": row["telefone (opcional)"] if row["telefone (opcional)"] else None,
#                         "status": "ativo",
#                         "senha": None,
#                         "projetos": [p.strip() for p in str(row["projetos (siglas separadas por vírgula) (opcional)"]).split(",") if p.strip()]
#                     }

#                     if row["tipo_usuario"] == "beneficiario":
#                         doc["tipo_beneficiario"] = row["tipo_beneficiario"]

#                     registros.append(doc)

#                 resultado = col_pessoas.insert_many(registros)

#                 st.success(f":material/check: {len(resultado.inserted_ids)} pessoas cadastradas com sucesso!")

#                 # Resetar o uploader
#                 st.session_state['uploader_key'] = str(uuid.uuid4())

#                 time.sleep(2)
#                 st.rerun()

#         except Exception as e:
#             st.error(
#                 ":material/error: Erro ao processar o arquivo.\n\n"
#                 "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#             )
#             st.exception(e)





















# elif opcao_cadastro == "Cadastro em massa":

#     # Inicializa o 'key' do file_uploader se ele não existir
#     if 'uploader_key' not in st.session_state:
#         st.session_state['uploader_key'] = str(uuid.uuid4())

#     st.write("Baixe aqui o modelo de tabela para cadastro em massa:")

#     with open("modelos/modelo_cadastro_pessoas_em_massa.xlsx", "rb") as f:
#         st.download_button(
#             label=":material/download: Baixar modelo XLSX",
#             data=f,
#             file_name="modelo_cadastro_pessoas_em_massa.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         )

#     st.divider()

#     # ------------------------------
#     # Upload
#     # ------------------------------

#     arquivo = st.file_uploader(
#         "Envie um arquivo XLSX preenchido para cadastrar múltiplas pessoas:",
#         type=["xlsx"],
#         key=st.session_state['uploader_key']
#     )

#     st.write("")

#     if arquivo is not None:

#         try:

#             df_upload = pd.read_excel(arquivo)

#             st.success("Arquivo carregado com sucesso!")

#             # ==========================================================
#             # 0) Validar se o arquivo está vazio
#             # ==========================================================
#             if df_upload.empty or df_upload.dropna(how="all").empty:
#                 st.error(
#                     ":material/error: O arquivo enviado está vazio!\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.stop()

#             # Exibir com index iniciado em 1
#             st.dataframe(df_index1(df_upload))
#             st.write("")

#             # ==========================================================
#             # 1) Validar colunas obrigatórias
#             # ==========================================================
#             colunas_obrigatorias = [
#                 "nome_completo",
#                 "tipo_usuario",
#                 "e_mail",
#                 "telefone"
#             ]

#             faltando = [c for c in colunas_obrigatorias if c not in df_upload.columns]

#             if faltando:
#                 st.error(
#                     f":material/error: Faltam colunas obrigatórias no arquivo: {faltando}\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.stop()

#             # Criar colunas opcionais se não existirem
#             if "tipo_beneficiario" not in df_upload.columns:
#                 df_upload["tipo_beneficiario"] = ""

#             if "projetos" not in df_upload.columns:
#                 df_upload["projetos"] = ""

#             # ==========================================================
#             # 2) Validar e-mails
#             # ==========================================================
#             df_upload["e_mail"] = df_upload["e_mail"].astype(str).str.strip()

#             invalidos = df_upload[~df_upload["e_mail"].apply(validar_email)]
#             if not invalidos.empty:
#                 st.error(
#                     ":material/error: Existem e-mails inválidos!\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.dataframe(df_index1(invalidos))
#                 st.stop()

#             # ==========================================================
#             # 3) Validar beneficiários
#             # ==========================================================
#             erros_benef = df_upload[
#                 (df_upload["tipo_usuario"] == "beneficiario")
#                 & (df_upload["tipo_beneficiario"].astype(str).str.strip() == "")
#             ]

#             if not erros_benef.empty:
#                 st.error(
#                     ":material/error: Existem beneficiários sem o campo 'tipo_beneficiario'.\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.dataframe(df_index1(erros_benef))
#                 st.stop()

#             # ==========================================================
#             # 4) Verificar duplicidade interna no arquivo
#             # ==========================================================
#             dup_email = df_upload[df_upload.duplicated("e_mail", keep=False)]

#             if not dup_email.empty:
#                 st.error(
#                     ":material/error: Existem e-mails duplicados dentro do próprio arquivo.\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.subheader("E-mails duplicados")
#                 st.dataframe(df_index1(dup_email))
#                 st.stop()

#             # ==========================================================
#             # 5) Verificar duplicidades no banco
#             # ==========================================================
#             db = conectar_mongo_cepf_gestao()
#             col_pessoas = db["pessoas"]

#             existentes = pd.DataFrame(list(col_pessoas.find({}, {"e_mail": 1})))

#             conflitos_email = []

#             if not existentes.empty:
#                 for _, row in df_upload.iterrows():
#                     if row["e_mail"] in existentes["e_mail"].values:
#                         conflitos_email.append(row.to_dict())

#             if conflitos_email:
#                 st.error(
#                     ":material/error: Existem e-mails que já estão cadastrados no banco de dados!\n\n"
#                     "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#                 )
#                 st.write("**E-mails já existentes:**")
#                 st.dataframe(df_index1(pd.DataFrame(conflitos_email)))
#                 st.stop()

#             # ==========================================================
#             # 6) Inserir no banco
#             # ==========================================================
#             if st.button(":material/save: Cadastrar pessoas", type="primary"):

#                 registros = []
#                 for _, row in df_upload.iterrows():

#                     doc = {
#                         "nome_completo": row["nome_completo"],
#                         "tipo_usuario": row["tipo_usuario"],
#                         "e_mail": row["e_mail"],
#                         "telefone": row["telefone"],
#                         "status": "ativo",
#                         "senha": None,
#                         "projetos": [p.strip() for p in str(row["projetos"]).split(",") if p.strip()]
#                     }

#                     if row["tipo_usuario"] == "beneficiario":
#                         doc["tipo_beneficiario"] = row["tipo_beneficiario"]

#                     registros.append(doc)

#                 resultado = col_pessoas.insert_many(registros)

#                 st.success(f":material/check: {len(resultado.inserted_ids)} pessoas cadastradas com sucesso!")

#                 # Resetar o uploader
#                 st.session_state['uploader_key'] = str(uuid.uuid4())

#                 time.sleep(2)
#                 st.rerun()

#         except Exception as e:
#             st.error(
#                 ":material/error: Erro ao processar o arquivo.\n\n"
#                 "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
#             )
#             st.exception(e)


