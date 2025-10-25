import streamlit as st  
# from pymongo import MongoClient  
import time 
import random  
import smtplib  
from email.mime.text import MIMEText  
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import bcrypt


# Configurar o streamlit para tela wide
st.set_page_config(layout="wide")


##############################################################################################################
# CONEXÃO COM O BANCO DE DADOS (MONGODB)
###############################################################################################################


# Conecta ao banco de dados MongoDB usando função importada (com cache para otimizar desempenho)
db = conectar_mongo_cepf_gestao()

# Define a coleção a ser utilizada
colaboradores = db["pessoas"]


##############################################################################################################
# FUNÇÕES AUXILIARES
##############################################################################################################


def encontrar_usuario_por_email(colaboradores, email_busca):
    usuario = colaboradores.find_one({"e_mail": email_busca})
    if usuario:
        return usuario.get("nome_completo"), usuario  # Retorna o nome e os dados do usuário
    return None, None  # Caso não encontre


# Função para enviar um e_mail com código de verificação
def enviar_email(destinatario, codigo):
    # Dados de autenticação, retirados do arquivo secrets.toml
    remetente = st.secrets["senhas"]["endereco_email"]
    senha = st.secrets["senhas"]["senha_email"]

    # Conteúdo do e_mail
    assunto = f"Código de Verificação - Colab ISPN: {codigo}"
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
                    nome, verificar_colaboradores = encontrar_usuario_por_email(colaboradores, email)
                    if verificar_colaboradores:

                        if verificar_colaboradores.get("status", "").lower() != "ativo":
                            st.error("Usuário inativo. Entre em contato com o renato@ispn.org.br.")
                            return
                        
                        codigo = str(random.randint(100, 999))  # Gera um código aleatório
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

                    usuario = colaboradores.find_one({"e_mail": email})

                    if usuario:
                        try:
                            # Gera hash seguro da senha
                            hash_senha = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt())

                            # Atualiza no banco o hash, não a senha em texto puro
                            result = colaboradores.update_one(
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
    container_logo.image("images/logo_ISPN_horizontal_ass.png", width=300)



    # Pula 10 linhas
    for _ in range(9):
        st.write('')


    with st.container(horizontal=True, gap="large"):

        # Coluna da esquerda
        with st.container():
            
            st.write('')
            st.write('')
            st.write('')

            cols = st.columns([1, 3])

            # Exibe o logo - TESTE DE LOGOS

            # cols[1].write("Teste de logos. Quero opiniões!")

            cols[1].image("images/colab_rounded_THIN.png", width=400)
            cols[1].write('')
            cols[1].write('')

            # cols[1].image("images/colab_fauna_THIN.png", width=400)
            # cols[1].write('')
            # cols[1].write('')
            
            # cols[1].image("images/COLAB_caderno_THIN.png", width=400)
            # cols[1].write('')
            # cols[1].write('')
            
            # cols[1].image("images/colab_onca_THIN.png", width=400)
            # cols[1].write('')
            # cols[1].write('')
                        
            # cols[1].image("images/colab_onca_round_THIN.png", width=400)
            # cols[1].write('')
            # cols[1].write('')
            
            # cols[1].image("images/colab_onca_round_caderno_THIN.png", width=400)
            # cols[1].write('')
            # cols[1].write('')

            # cols[1].image("images/colab_onca_office_THIN.png", width=400)
            # cols[1].write('')
            # cols[1].write('')

            # cols[1].image("images/colab_26_1_CUT.png", width=400)
            # cols[1].write('')
            # cols[1].write('')

            # cols[1].image("images/colab_26_2_CUT.png", width=400)
            # cols[1].write('')
            # cols[1].write('')
            
            # cols[1].image("images/colab_26_4_CUT.png", width=400)
            # cols[1].write('')
            # cols[1].write('')
            
            # cols[1].image("images/colab_26_5_CUT.png", width=400)
            # cols[1].write('')
            # cols[1].write('')
            
            # cols[1].image("images/colab_26_6_cut.png", width=400)
            # cols[1].write('')
            # cols[1].write('')

            st.write('')
            st.write('')
            st.write('')
            st.write('')

        # Coluna da direita
 
        with st.container():

            st.write('')
            st.write('')
            st.write('')

            with st.form("login_form", border=False):
                # Campo de e-mail
                email_input = st.text_input("E-mail", width=300)

                # Campo de senha
                password = st.text_input("Senha", type="password", width=300)

                if st.form_submit_button("Entrar", type="primary"):
                    # Busca apenas pelo e-mail
                    usuario_encontrado = colaboradores.find_one({
                        "e_mail": {"$regex": f"^{email_input.strip()}$", "$options": "i"}
                    })

                    # Salva o email para possível recuperação de senha
                    st.session_state["email_para_recuperar"] = email_input.strip()

                    if usuario_encontrado:
                        senha_hash = usuario_encontrado.get("senha")

                        # Forma segura: só aceita hashes válidos (bytes)
                        if isinstance(senha_hash, bytes) and bcrypt.checkpw(password.encode("utf-8"), senha_hash):
                            if usuario_encontrado.get("status", "").lower() != "ativo":
                                st.error("Usuário inativo. Entre em contato com o renato@ispn.org.br.")
                                st.stop()

                            tipo_usuario = [x.strip() for x in usuario_encontrado.get("tipo de usuário", "").split(",")]

                            # Autentica
                            st.session_state["logged_in"] = True
                            st.session_state["tipo_usuario"] = tipo_usuario
                            st.session_state["nome"] = usuario_encontrado.get("nome_completo")
                            st.session_state["cpf"] = usuario_encontrado.get("CPF")
                            st.session_state["id_usuario"] = usuario_encontrado.get("_id")
                            st.rerun()
                        else:
                            # Senha inválida ou não hashada corretamente
                            st.error("E-mail ou senha inválidos!", width=300)
                    else:
                        st.error("E-mail ou senha inválidos!", width=300)

            # Botão para recuperar senha
            st.write('')
            st.write('')


            st.write('')
            st.button(
                "Esqueci a senha", 
                key="forgot_password", 
                type="secondary", 
                on_click=recuperar_senha_dialog
            )

            # Informação adicional
            st.markdown(
                "<div style='color: #007ad3;'><br>É o seu primeiro acesso?<br>Clique em \"Esqueci a senha\".</div>",
                unsafe_allow_html=True
            )


##############################################################################################################
# EXECUÇÃO PRINCIPAL: VERIFICA LOGIN E NAVEGA ENTRE PÁGINAS
##############################################################################################################


# Se o usuário ainda não estiver logado
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login()  # Mostra tela de login

else:

    # pg = st.navigation([
    #     st.Page("Institucional.py", title="Institucional", icon=":material/account_balance:"),
    #     # st.Page("Estratégia.py", title="Estratégia", icon=":material/tactic:"),
    #     st.Page("Indicadores.py", title="Indicadores", icon=":material/monitoring:"),
    #     # st.Page("Programas e Áreas.py", title="Programas e Áreas", icon=":material/team_dashboard:"),
    #     # st.Page("Pessoas.py", title="Pessoas", icon=":material/groups:"),
    #     # st.Page("Doadores.py", title="Doadores", icon=":material/all_inclusive:"),
    #     # st.Page("Projetos.py", title="Projetos", icon=":material/book:"),
    #     st.Page("Fundo Ecos.py", title="Fundo Ecos", icon=":material/owl:"),
    #     # st.Page("Redes e Articulações.py", title="Redes e Articulações", icon=":material/network_node:"),
    #     # st.Page("Monitor de PLs.py", title="Monitor de PLs", icon=":material/balance:"),
    #     # st.Page("Clipping de Notícias.py", title="Clipping de Notícias", icon=":material/attach_file:"),
    #     # st.Page("Viagens.py", title="Viagens", icon=":material/travel:"),
    #     # st.Page("Férias e recessos.py", title="Férias e Recessos", icon=":material/beach_access:"),
    #     # st.Page("Manuais.py", title="Manuais", icon=":material/menu_book:"),
    # ])
    # pg.run()

    pg = st.navigation([
        st.Page("Institucional.py", title="Institucional", icon=":material/account_balance:"),
        # st.Page("Estratégia.py", title="Estratégia", icon=":material/tactic:"),
        st.Page("Indicadores.py", title="Indicadores", icon=":material/monitoring:"),
        # st.Page("Programas e Áreas.py", title="Programas e Áreas", icon=":material/team_dashboard:"),
        # st.Page("Pessoas.py", title="Pessoas", icon=":material/groups:"),
        # st.Page("Doadores.py", title="Doadores", icon=":material/all_inclusive:"),
        st.Page("Projetos.py", title="Projetos", icon=":material/book:"),
        st.Page("Fundo Ecos.py", title="Fundo Ecos", icon=":material/owl:"),
        # st.Page("Redes e Articulações.py", title="Redes e Articulações", icon=":material/network_node:"),
        # st.Page("Monitor de PLs.py", title="Monitor de PLs", icon=":material/balance:"),
        # st.Page("Clipping de Notícias.py", title="Clipping de Notícias", icon=":material/attach_file:"),
        # st.Page("Viagens.py", title="Viagens", icon=":material/travel:"),
        st.Page("Férias e recessos.py", title="Férias e Recessos", icon=":material/beach_access:"),
        # st.Page("Manuais.py", title="Manuais", icon=":material/menu_book:"),
    ])
    pg.run()



