import streamlit as st  
# from pymongo import MongoClient  
import time 
import random  
import smtplib  
from email.mime.text import MIMEText  
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import bcrypt
import textwrap


# Configurar o streamlit para tela wide
st.set_page_config(layout="wide")


##############################################################################################################
# CONEXÃO COM O BANCO DE DADOS (MONGODB)
###############################################################################################################


# Conecta ao banco de dados MongoDB usando função importada (com cache para otimizar desempenho)
db = conectar_mongo_cepf_gestao()

# Define a coleção a ser utilizada
col_pessoas = db["pessoas"]





##############################################################################################################
# FUNÇÕES AUXILIARES
##############################################################################################################


def encontrar_usuario_por_email(pessoas, email_busca):
    usuario = pessoas.find_one({"e_mail": email_busca})
    if usuario:
        return usuario.get("nome_completo"), usuario  # Retorna o nome e os dados do usuário
    return None, None  # Caso não encontre


# Função para enviar um e_mail com código de verificação
def enviar_email(destinatario, codigo):
    # Dados de autenticação, retirados do arquivo secrets.toml
    remetente = st.secrets["senhas"]["endereco_email"]
    senha = st.secrets["senhas"]["senha_email"]

    # Conteúdo do e_mail
    assunto = f"Código de Verificação - CEPF Gestão: {codigo}"
    corpo = f"""
    <html>
        <body>
            <p style='font-size: 1.5em;'>
                Seu código para redefinição é: <strong>{codigo}</strong>
            </p>
        </body>
    </html>
    """

    # Cria o e_mail formatado com HTML
    msg = MIMEText(corpo, "html", "utf-8")
    msg["Subject"] = assunto
    msg["From"] = remetente
    msg["To"] = destinatario

    # Tenta enviar o e_mail via SMTP seguro (SSL)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(remetente, senha)
            server.sendmail(remetente, destinatario, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False


##############################################################################################################
# CAIXA DE DIÁLOGO PARA RECUPERAÇÃO DE SENHA
##############################################################################################################


@st.dialog("Recuperação de Senha")
def recuperar_senha_dialog():
    st.session_state.setdefault("codigo_enviado", False)
    st.session_state.setdefault("codigo_verificacao", "")
    st.session_state.setdefault("email_verificado", "")
    st.session_state.setdefault("codigo_validado", False)

    conteudo_dialogo = st.empty()

    # Etapa 1: Entrada do e-mail
    if not st.session_state.codigo_enviado:
        with conteudo_dialogo.form(key="recover_password_form", border=False):
            # Preenche automaticamente com email da sessão (se houver)
            email_default = st.session_state.get("email_para_recuperar", "")
            email = st.text_input("Digite seu e-mail:", value=email_default)

            if st.form_submit_button("Enviar código de verificação", icon=":material/mail:"):
                if email:
                    nome, verificar_colaboradores = encontrar_usuario_por_email(col_pessoas, email)
                    if verificar_colaboradores:

                        if verificar_colaboradores.get("status", "").lower() != "ativo":
                            st.error("Usuário inativo. Entre em contato com o administrador do sistema.")
                            return
                        
                        codigo = str(random.randint(100, 999))  # Gera um código aleatório
                        with st.spinner(f"Enviando código para {email}..."):
                            if enviar_email(email, codigo):  # Envia o código por e-mail
                                st.session_state.codigo_verificacao = codigo
                                st.session_state.codigo_enviado = True
                                st.session_state.email_verificado = email
                                st.success(f"Código enviado para {email}.")
                            else:
                                st.error("Erro ao enviar o e-mail. Tente novamente.")
                    else:
                        st.error("E-mail não encontrado. Tente novamente.")
                else:
                    st.error("Por favor, insira um e-mail.")

    # --- Etapa 2: Verificação do código recebido ---
    if st.session_state.codigo_enviado and not st.session_state.codigo_validado:
        with conteudo_dialogo.form(key="codigo_verificacao_form", border=False):
            st.subheader("Código de verificação")
            email_mask = st.session_state.email_verificado.replace("@", "​@")  # Máscara leve no e-mail
            st.write(f"Um código foi enviado para: **{email_mask}**")

            codigo_input = st.text_input("Informe o código recebido por e-mail", placeholder="000")
            if st.form_submit_button("Verificar"):
                if codigo_input == st.session_state.codigo_verificacao:
                    sucesso = st.success("Código verificado com sucesso!")
                    time.sleep(2)
                    sucesso.empty()
                    st.session_state.codigo_validado = True
                else:
                    st.error("Código inválido. Tente novamente.")

    # --- Etapa 3: Definição da nova senha ---

    if st.session_state.codigo_validado:
        with conteudo_dialogo.form("nova_senha_form", border=True):
            st.markdown("### Defina sua nova senha")
            nova_senha = st.text_input("Nova senha", type="password")
            confirmar_senha = st.text_input("Confirme a senha", type="password")
            enviar_nova_senha = st.form_submit_button("Salvar")


            if enviar_nova_senha:
                if nova_senha == confirmar_senha and nova_senha.strip():
                    email = st.session_state.email_verificado

                    usuario = col_pessoas.find_one({"e_mail": email})

                    if usuario:
                        try:
                            # Gera hash seguro da senha
                            hash_senha = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt())

                            # Atualiza no banco o hash, não a senha em texto puro
                            result = col_pessoas.update_one(
                                {"e_mail": email},
                                {"$set": {"senha": hash_senha}}
                            )

                            if result.matched_count > 0:
                                st.success("Senha redefinida com sucesso!")

                                # Limpa variáveis de sessão
                                for key in ["codigo_enviado", "codigo_verificacao", "email_verificado", "codigo_validado"]:
                                    st.session_state.pop(key, None)

                                # Inicializa tipo de usuário
                                tipo_usuario = [x.strip() for x in usuario.get("tipo de usuário", "").split(",")]
                                st.session_state["tipo_usuario"] = tipo_usuario

                                # Marca usuário como logado e reinicia
                                st.session_state.logged_in = True
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Erro ao redefinir a senha. Tente novamente.")
                        except Exception as e:
                            st.error(f"Erro ao atualizar a senha: {e}")
                    else:
                        st.error("Nenhum usuário encontrado com esse e-mail.")
                else:
                    st.error("As senhas não coincidem ou estão vazias.")






##############################################################################################################
# TELA DE LOGIN
##############################################################################################################

def login():

    # st.image("images/logo_ISPN_horizontal_ass.png", width=300)
    
    # Exibe o logo
    container_logo = st.container(horizontal=True, horizontal_alignment="center")
    container_logo.image("images/ieb_logo.svg", width=300)

    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')

    # CSS para centralizar e estilizar
    st.markdown(
        """
        <h2 style='text-align: center; color: slategray;'>
            Plataforma de Gestão de Projetos do CEPF Brasil
        </h2>
        """,
        unsafe_allow_html=True
    )

    # Pula 7 linhas
    for _ in range(7):
        st.write('')


    with st.container(horizontal=True, gap="large"):

        # Coluna da esquerda
        with st.container():

            cols = st.columns([1, 3])

            cols[1].image("images/cepf_logo.png", width=400)
            cols[1].write('')
            cols[1].write('')

            st.write('')
            st.write('')
            st.write('')
            st.write('')

        # Coluna da direita
        with st.container():
 
            with st.form("login_form", border=False):
                # Campo de e-mail
                email_input = st.text_input("E-mail", width=300)

                # Campo de senha
                password = st.text_input("Senha", type="password", width=300)

                if st.form_submit_button("Entrar", type="primary"):
                    # Busca apenas pelo e-mail
                    usuario_encontrado = col_pessoas.find_one({
                        "e_mail": {"$regex": f"^{email_input.strip()}$", "$options": "i"}
                    })

                    # Salva o email para possível recuperação de senha
                    st.session_state["email_para_recuperar"] = email_input.strip()

                    if usuario_encontrado:
                        senha_hash = usuario_encontrado.get("senha")

                        # Forma segura: só aceita hashes válidos (bytes)
                        if isinstance(senha_hash, bytes) and bcrypt.checkpw(password.encode("utf-8"), senha_hash):
                            if usuario_encontrado.get("status", "").lower() != "ativo":
                                with st.container(width=300):
                                    st.error("Usuário inativo. Entre em contato com o a equipe do CEPF.")
    
                                st.stop()

                            # tipo_usuario = usuario_encontrado.get("tipo_usuario", [])
                            tipo_usuario = usuario_encontrado.get("tipo_usuario", "")


                            # Autentica
                            st.session_state["logged_in"] = True
                            st.session_state["tipo_usuario"] = tipo_usuario
                            st.session_state["nome"] = usuario_encontrado.get("nome_completo")
                            # st.session_state["cpf"] = usuario_encontrado.get("CPF")
                            st.session_state["id_usuario"] = usuario_encontrado.get("_id")
                            st.session_state["projetos"] = usuario_encontrado.get("projetos", [])
                            st.rerun()
                        else:
                            # Senha inválida ou não hashada corretamente
                            st.error("E-mail ou senha inválidos!", width=300)
                    else:
                        st.error("E-mail ou senha inválidos!", width=300)

            st.write('')
            st.write('')
            st.write('')

            # Botão para recuperar senha
            st.button(
                "Esqueci a senha", 
                key="forgot_password", 
                type="tertiary", 
                on_click=recuperar_senha_dialog
            )



##############################################################################################################
# EXECUÇÃO PRINCIPAL: VERIFICA LOGIN E NAVEGA ENTRE PÁGINAS
##############################################################################################################

# Verifica se está logado

# Não logado:
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login()  # Mostra tela de login


# Logado:
else:

    # Define as páginas disponíveis para cada tipo de usuário
    pags_por_tipo = {
        "home_admin": [
            st.Page("home_interna.py", title="Projetos", icon=":material/assignment:"),
            st.Page("novo_projeto.py", title="Novo projeto", icon=":material/add_circle:"),
            st.Page("novo_edital.py", title="Novo edital", icon=":material/campaign:"),
            st.Page("mapa.py", title="Mapa", icon=":material/map:"),
            st.Page("pessoas.py", title="Pessoas", icon=":material/group:"),
            st.Page("administracao.py", title="Administração", icon=":material/admin_panel_settings:")
        ],
        "home_monitor": [
            st.Page("home_interna.py", title="Projetos", icon=":material/assignment:"),
            st.Page("novo_projeto.py", title="Novo projeto", icon=":material/add_circle:"),
            st.Page("novo_edital.py", title="Novo edital", icon=":material/campaign:"),
            st.Page("mapa.py", title="Mapa", icon=":material/map:"),
            st.Page("pessoas.py", title="Pessoas", icon=":material/group:"),
        ],
        "ver_projeto": [
            st.Page("projeto_visao_geral.py", title="Visão geral", icon=":material/assignment:"),
            st.Page("projeto_atividades.py", title="Atividades", icon=":material/add_circle:"),
            st.Page("projeto_financeiro.py", title="Financeiro", icon=":material/campaign:"),
            st.Page("projeto_locais.py", title="Locais", icon=":material/map:"),
            st.Page("projeto_relatorios.py", title="Relatórios", icon=":material/group:"),
        ],
        "beneficiario": [
            st.Page("home_interna.py", title="Projetos", icon=":material/assignment:"),
            st.Page("novo_projeto.py", title="Novo projeto", icon=":material/add_circle:"),
            st.Page("novo_edital.py", title="Novo edital", icon=":material/campaign:"),
            st.Page("mapa.py", title="Mapa", icon=":material/map:"),
            st.Page("pessoas.py", title="Pessoas", icon=":material/group:"),
        ],
        "visitante": [
            st.Page("home_interna.py", title="Projetos", icon=":material/assignment:"),
            st.Page("mapa.py", title="Mapa", icon=":material/map:"),
        ]
    }


    # Inicializa a página atual se não existir
    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = None

    # Inicializa a projeto atual se não existir
    if "projeto_atual" not in st.session_state:
        st.session_state.projeto_atual = None

# ????????????????
    # st.write(st.session_state)

    # Garante que tipo_usuario existe
    # tipo_usuario = set(st.session_state.get("tipo_usuario", []))
    tipo_usuario = st.session_state.get("tipo_usuario", "")


    if tipo_usuario == "admin":
        
        # Página inicial do admin 

        # Primeira execução: 
        # se pagina_atual == None, a pagina atual será home_admin
        if st.session_state.pagina_atual is None:
            st.session_state.pagina_atual = "home_admin"

        # Demais execuções
        # Home do admin
        if st.session_state.pagina_atual == "home_admin":
            pages = pags_por_tipo["home_admin"]

        # Admin visita projetos
        elif st.session_state.pagina_atual == "ver_projeto":
            pages = pags_por_tipo["ver_projeto"]


    # Cria e executa a navegação
    pg = st.navigation(pages)
    pg.run()

