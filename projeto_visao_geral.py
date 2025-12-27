import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao, sidebar_projeto, calcular_status_projetos, gerar_cronograma_financeiro
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

# Pessoas
col_pessoas = db["pessoas"]
df_pessoas = pd.DataFrame(list(col_pessoas.find()))


# Projetos
col_projetos = db["projetos"]


###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# TRATAMENTO DE DADOS
###########################################################################################################

# Verifica se o usuário logado é interno (bool)
usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]


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


# Inclulir o status no dataframe de projetos
df_projeto = calcular_status_projetos(df_projeto)


# Incluir padrinho no dataframe de projetos
# Fazendo um dataframe auxiliar de relacionamento
# Seleciona apenas colunas necessárias
df_pessoas_proj = df_pessoas[["nome_completo", "projetos"]].copy()

# Garante que "projetos" seja sempre lista
df_pessoas_proj["projetos"] = df_pessoas_proj["projetos"].apply(
    lambda x: x if isinstance(x, list) else []
)

# Explode: uma linha por projeto
df_pessoas_proj = df_pessoas_proj.explode("projetos")

# Remove linhas sem código de projeto
df_pessoas_proj = df_pessoas_proj.dropna(subset=["projetos"])

# Renomeia para facilitar o merge
df_pessoas_proj = df_pessoas_proj.rename(columns={
    "projetos": "codigo",
    "nome_completo": "padrinho"
})

# Agrupar (caso haja mais de um padrinho por projeto)
df_padrinhos = (
    df_pessoas_proj
    .groupby("codigo")["padrinho"]
    .apply(lambda nomes: ", ".join(sorted(set(nomes))))
    .reset_index()
)

# Fazer o merge
df_projeto = df_projeto.merge(
    df_padrinhos,
    on="codigo",
    how="left"
)











###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################

# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# ??????
st.sidebar.write(df_projeto.columns)



# Toggle do modo de edição



modo_edicao = st.toggle("Editar", value=False)



# MODO DE VISUALIZAÇÃO

if not modo_edicao:

    st.header(f"{df_projeto['sigla'].values[0]} - {df_projeto['codigo'].values[0]}")

    st.write(f"Edital: {df_projeto['edital'].values[0]}")
    st.write(f"Organização: {df_projeto['organizacao'].values[0]}")
    st.write(f"Nome do projeto: {df_projeto['nome_do_projeto'].values[0]}")
    st.write(f"Objetivo geral: {df_projeto['objetivo_geral'].values[0]}")
    st.write(f"Duração: {df_projeto['duracao'].values[0]} meses")

    cols = st.columns(3)
    cols[0].write(f"Início: {df_projeto['data_inicio_contrato'].values[0]}")
    cols[1].write(f"Fim: {df_projeto['data_fim_contrato'].values[0]}")
    cols[2].write("Contrato: em breve")

    st.write(f"Responsável: {df_projeto['responsavel'].values[0]}")
    st.write(f"Padrinho/Madrinha: {df_projeto['padrinho'].values[0]}")

    direcoes = df_projeto['direcoes_estrategicas'].values[0]
    if direcoes:
        st.write("Direções estratégicas:")
        for d in direcoes:
            st.write(f"- {d}")

    publicos = df_projeto['publicos'].values[0]
    if publicos:
        st.write("Público:", " / ".join(publicos))



# MODO DE EDIÇÃO

else:
    st.write("**Editar informações cadastrais do projeto**")

    projeto = df_projeto.iloc[0]

    with st.form("form_editar_projeto"):

        # ---------- CAMPOS ----------
        edital = st.text_input("Edital", projeto["edital"])
        codigo = st.text_input("Código do Projeto", projeto["codigo"])
        sigla = st.text_input("Sigla do Projeto", projeto["sigla"])
        nome = st.text_input("Nome do Projeto", projeto["nome_do_projeto"])

        duracao = st.number_input(
            "Duração (meses)",
            min_value=1,
            value=int(projeto["duracao"])
        )

        data_inicio = st.date_input(
            "Data de início",
            pd.to_datetime(projeto["data_inicio_contrato"], dayfirst=True)
        )

        data_fim = st.date_input(
            "Data de fim",
            pd.to_datetime(projeto["data_fim_contrato"], dayfirst=True)
        )

        responsavel = st.text_input(
            "Responsável",
            projeto.get("responsavel", "")
        )

        objetivo = st.text_area(
            "Objetivo geral",
            projeto.get("objetivo_geral", "")
        )

        direcoes = st.multiselect(
            "Direções estratégicas",
            options=df_direcoes["tema"].tolist(),
            default=projeto.get("direcoes_estrategicas", [])
        )

        publicos = st.multiselect(
            "Públicos",
            options=df_publicos["publico"].tolist(),
            default=projeto.get("publicos", [])
        )

        salvar = st.form_submit_button("💾 Salvar alterações")

        # ---------- SALVAR ----------
        if salvar:
            col_projetos.update_one(
                {"_id": projeto["_id"]},
                {
                    "$set": {
                        "edital": edital,
                        "codigo": codigo,
                        "sigla": sigla,
                        "nome_do_projeto": nome,
                        "objetivo_geral": objetivo,
                        "duracao": duracao,
                        "data_inicio_contrato": data_inicio.strftime("%d/%m/%Y"),
                        "data_fim_contrato": data_fim.strftime("%d/%m/%Y"),
                        "responsavel": responsavel,
                        "direcoes_estrategicas": direcoes,
                        "publicos": publicos,
                    }
                }
            )

            st.success("✅ Projeto atualizado com sucesso!")
            st.rerun()







# # Código e sigla do projeto 
# st.header(f"{df_projeto['sigla'].values[0]} - {df_projeto['codigo'].values[0]}")

# # Edital
# st.write(f"Edital: {df_projeto['edital'].values[0]}")

# # Organização
# st.write(f"Organização: {df_projeto['organizacao'].values[0]}")

# # Nome do projeto
# st.write(f"Nome: {df_projeto['nome_do_projeto'].values[0]}")

# # Objetivo geral
# st.write(f"Objetivo geral: {df_projeto['objetivo_geral'].values[0]}")

# # Duração do projeto
# st.write(f"Duração: {df_projeto['duracao'].values[0]} meses")

# cols = st.columns(3)

# # Data de início do contrato
# cols[0].write(f"Data de início do contrato: {df_projeto['data_inicio_contrato'].values[0]}")

# # Data de fim do contrato
# cols[1].write(f"Data de fim do contrato: {df_projeto['data_fim_contrato'].values[0]}")

# # Link para o contrato
# cols[2].write(f"Link para o contrato: *em breve*")

# # Responsável (coordenador)
# st.write(f"Responsável: {df_projeto['responsavel'].values[0]}")

# # Padrinho
# st.write(f"Padrinho/Madrinha: {df_projeto['padrinho'].values[0]}")

# # Direções estratégicas (lista)
# st.write("Direções estratégicas:")
# direcoes = df_projeto['direcoes_estrategicas'].values[0]
# if direcoes:
#     for direcao in direcoes:
#         st.write(f"- {direcao}")

# # Público (lista)
# publicos = df_projeto['publicos'].values[0]
# if publicos:
#     publicos_formatado = " / ".join(publicos)
#     st.write(f"Público: {publicos_formatado}")



















st.divider()



# #############################################################################################
# BLOCO DE STATUS
# #############################################################################################


# STATUS
status_projeto = df_projeto["status"].values[0]

if status_projeto == "Em dia":
    st.markdown(f"#### O projeto está :green[{status_projeto.lower()}]")
elif status_projeto == "Atrasado":
    st.markdown(f"#### O projeto está :orange[{status_projeto.lower()}]")
elif status_projeto == "Concluído":
    st.markdown(f"#### O projeto está :green[{status_projeto.lower()}]")
elif status_projeto == "Cancelado":
    st.markdown(f"#### O projeto está :red[{status_projeto.lower()}]")


# MENSAGEM DO STATUS

projeto = df_projeto.iloc[0].to_dict()
parcelas = projeto.get("financeiro", {}).get("parcelas", [])
relatorios = projeto.get("relatorios", [])

df_cronograma = gerar_cronograma_financeiro(parcelas, relatorios)

# reset index
df_cronograma = df_cronograma.reset_index(drop=True)

# Garante que o DataFrame não está vazio
if df_projeto.empty:
    st.caption("Não há dados no cronograma.")

else:
    hoje = datetime.date.today()

    proximo_evento = df_projeto.iloc[0]["proximo_evento"]
    data_proximo_evento = df_projeto.iloc[0]["data_proximo_evento"]
    dias_atraso = df_projeto.iloc[0]["dias_atraso"]

    # Projeto concluído
    if proximo_evento is None:
        st.success("🎉 Parabéns! O projeto realizou todas as etapas e está concluído.")

    else:
        # Texto da data
        if pd.notna(data_proximo_evento):
            if data_proximo_evento == hoje:
                texto_data = "previsto para hoje"
            else:
                texto_data = f"previsto para **{data_proximo_evento.strftime('%d/%m/%Y')}**"
        else:
            texto_data = "com data não informada"

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

        # Exibe atraso / antecedência
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

        texto_anotacao = st.text_area(
            "Escreva aqui a anotação",
            height=150
        )

        if st.button(
            "Salvar anotação",
            type="primary",
            icon=":material/save:"
        ):

            if not texto_anotacao.strip():
                st.warning("A anotação não pode estar vazia.")
                return

            anotacao = {
                "id": str(bson.ObjectId()),
                "data": datetime.datetime.now().strftime("%d/%m/%Y"),
                "autor": st.session_state.nome,
                "texto": texto_anotacao.strip(),
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

        novo_texto = st.text_area(
            "Editar anotação",
            value=anotacao_selecionada["texto"],
            height=150
        )

        if st.button(
            "Salvar alterações",
            type="primary",
            icon=":material/save:"
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
                        "anotacoes.$.texto": novo_texto.strip()
                    }
                }
            )

            if resultado.modified_count == 1:
                st.success("Anotação atualizada com sucesso!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Erro ao atualizar anotação.")



with st.container(horizontal=True, horizontal_alignment="right"):
    if st.button(
        "Gerenciar anotações",
        icon=":material/edit:",
        type="secondary",
        width=200
    ):
        gerenciar_anotacoes()



# ============================================================
# ANOTAÇÕES - LISTAGEM
# ============================================================


anotacoes = (
    df_projeto["anotacoes"].values[0]
    if "anotacoes" in df_projeto.columns and df_projeto["anotacoes"].values[0]
    else []
)

if not anotacoes:
    st.write("Não há anotações")
else:
    df_anotacoes = pd.DataFrame(anotacoes)
    df_anotacoes = df_anotacoes[["data", "texto", "autor"]]
    ui.table(data=df_anotacoes)


st.write('')
st.write('')
st.write('')



# st.divider()

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

        if st.button(
            "Salvar visita",
            type="primary",
            icon=":material/save:"
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

        if st.button(
            "Salvar alterações",
            type="primary",
            icon=":material/save:"
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
            width=200
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
    st.write("Não há visitas registradas")
else:
    df_visitas = pd.DataFrame(visitas)
    df_visitas = df_visitas[["data_visita", "relato", "autor"]]
    ui.table(data=df_visitas)










# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()

