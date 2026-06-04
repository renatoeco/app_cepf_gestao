import streamlit as st
import pandas as pd
import datetime
import time

from funcoes_auxiliares import (
    conectar_mongo_cepf_gestao,
    sidebar_projeto,
)


st.set_page_config(page_title="Salvaguardas", page_icon=":material/health_and_safety:")





###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Coleção de projetos
col_projetos = db["projetos"]


###########################################################################################################
# CARREGAMENTO DE DADOS
###########################################################################################################


# Capturando o código do projeto e os dados do projeto
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


# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()







###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')

# Título da página e identificação
col_titulo, col_identificacao = st.columns([3, 2])

with col_titulo:
    st.header("Salvaguardas")

with col_identificacao:
    st.markdown(
        f"<div style='text-align: right; margin-top: 30px;'>{df_projeto['codigo'].values[0]} - {df_projeto['sigla'].values[0]}</div>",
        unsafe_allow_html=True
    )


st.write('')
st.write('')




# ===============================================================================================
# PERMISSÃO - SALVAGUARDAS
# -----------------------------------------------------------------------------------------------
# Apenas admin/equipe podem editar. Usuários externos apenas visualizam.
# ===============================================================================================

usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]

# Usuários internos podem editar, externos apenas visualizar
modo_edicao = usuario_interno


st.subheader("Avaliação de risco")
st.write('')

# Recupera o documento do projeto como dicionário
projeto = df_projeto.iloc[0].to_dict()

# Recupera o objeto salvaguardas do documento do projeto
# Caso não exista, utiliza um dicionário vazio
salvaguardas_doc = projeto.get("salvaguardas", {})


# Extrai os subdocumentos de cada política
pol2 = salvaguardas_doc.get("pol_2_trabalho", {})
pol3 = salvaguardas_doc.get("pol_3_poluicao", {})
pol4 = salvaguardas_doc.get("pol_4_comunidade", {})
pol5 = salvaguardas_doc.get("pol_5_reassentamento", {})
pol6 = salvaguardas_doc.get("pol_6_biodiversidade", {})
pol7 = salvaguardas_doc.get("pol_7_indigenas", {})
pol8 = salvaguardas_doc.get("pol_8_patrimonio", {})
pol9 = salvaguardas_doc.get("pol_9_genero", {})


# Carrega valores existentes no session_state
# Isso faz com que os widgets apareçam já preenchidos ao abrir a página


if "salv_2_aplicavel" not in st.session_state:
    st.session_state["salv_2_aplicavel"] = pol2.get("aplicavel")

if "salv_2_detalhes" not in st.session_state:
    st.session_state["salv_2_detalhes"] = pol2.get("detalhes")

if "salv_2_categoria_risco" not in st.session_state:
    st.session_state["salv_2_categoria_risco"] = pol2.get("categoria")


if "salv_3_aplicavel" not in st.session_state:
    st.session_state["salv_3_aplicavel"] = pol3.get("aplicavel")

if "salv_3_pesticidas_detalhes" not in st.session_state:
    st.session_state["salv_3_pesticidas_detalhes"] = pol3.get("detalhes_pesticidas")

if "salv_3_poluicao_detalhes" not in st.session_state:
    st.session_state["salv_3_poluicao_detalhes"] = pol3.get("detalhes_poluicao")

if "salv_3_categoria_risco" not in st.session_state:
    st.session_state["salv_3_categoria_risco"] = pol3.get("categoria")


if "salv_4_aplicavel" not in st.session_state:
    st.session_state["salv_4_aplicavel"] = pol4.get("aplicavel")

if "salv_4_detalhes" not in st.session_state:
    st.session_state["salv_4_detalhes"] = pol4.get("detalhes")

if "salv_4_categoria_risco" not in st.session_state:
    st.session_state["salv_4_categoria_risco"] = pol4.get("categoria")


if "salv_5_aplicavel" not in st.session_state:
    st.session_state["salv_5_aplicavel"] = pol5.get("aplicavel")

if "salv_5_detalhes" not in st.session_state:
    st.session_state["salv_5_detalhes"] = pol5.get("detalhes")

if "salv_5_categoria_risco" not in st.session_state:
    st.session_state["salv_5_categoria_risco"] = pol5.get("categoria")


if "salv_6_aplicavel" not in st.session_state:
    st.session_state["salv_6_aplicavel"] = pol6.get("aplicavel")

if "salv_6_detalhes" not in st.session_state:
    st.session_state["salv_6_detalhes"] = pol6.get("detalhes")

if "salv_6_categoria_risco" not in st.session_state:
    st.session_state["salv_6_categoria_risco"] = pol6.get("categoria")


if "salv_7_aplicavel" not in st.session_state:
    st.session_state["salv_7_aplicavel"] = pol7.get("aplicavel")

if "salv_7_detalhes" not in st.session_state:
    st.session_state["salv_7_detalhes"] = pol7.get("detalhes")

if "salv_7_categoria_risco" not in st.session_state:
    st.session_state["salv_7_categoria_risco"] = pol7.get("categoria")


if "salv_8_aplicavel" not in st.session_state:
    st.session_state["salv_8_aplicavel"] = pol8.get("aplicavel")

if "salv_8_detalhes" not in st.session_state:
    st.session_state["salv_8_detalhes"] = pol8.get("detalhes")

if "salv_8_categoria_risco" not in st.session_state:
    st.session_state["salv_8_categoria_risco"] = pol8.get("categoria")


if "salv_9_detalhes" not in st.session_state:
    st.session_state["salv_9_detalhes"] = pol9.get("detalhes")

if "salv_9_categoria_risco" not in st.session_state:
    st.session_state["salv_9_categoria_risco"] = pol9.get("categoria")

if "salv_fortalecimento_capacidades" not in st.session_state:
    st.session_state["salv_fortalecimento_capacidades"] = salvaguardas_doc.get("fortalecimento_capacidades")



# COMEÇO DO FORMULÁRIO COM AS POLÍTICAS DE SALVAGUARDAS ###########################################################


# Duas colunas para o nome do avaliador e data da última atualização.
col1, col2 = st.columns(2)


# # Recupera o nome do usuário logado no session_state
# nome_usuario_atual = st.session_state.get("nome")


# Recupera o nome da pessoa que fez a última avaliação
nome_avaliador = salvaguardas_doc.get("nome_avaliador_risco")

st.write('')

# Mostra apenas se existir informação no banco
if nome_avaliador:
    col1.write(f"**Responsável pela última avaliação:** {nome_avaliador}")




# Recupera a data da última avaliação salva
data_aval_risco = salvaguardas_doc.get("data_aval_risco")

# Mostra a data apenas se existir no banco
if data_aval_risco:
    col2.write(f"**Data da última avaliação:** {data_aval_risco}")


st.write("")
st.write("")
st.write("")


# Define a largura padrão das colunas que será reutilizada na tabela de salvaguardas
largura_colunas = [2, 2, 3, 2, 3]

# Cria a primeira linha de colunas (cabeçalho)
cab1, cab2, cab3, cab4, cab5 = st.columns(largura_colunas)

# Cabeçalhos em negrito
cab1.markdown("**Política de Salvaguardas**")
cab2.markdown("**Aplicável?**")
cab3.markdown("**Avaliação de Risco**")
cab4.markdown("**Categoria de Risco**")
cab5.markdown("**Notas (os exemplos abaixo são indicativos e não prevêem todas as eventualidades)**")

st.divider()


# colunas das linhas de pergutnas e respostas
col1, col2, col3, col4, col5 = st.columns(largura_colunas, gap="medium")


# 1. Avaliação Ambiental e Social ------------------------------------------------------------------------------------------------

# Coluna 1 — nome da política
col1.write("**1. Avaliação Ambiental e Social**")

# Coluna 2 — política sempre aplicável
with col2:

    # Mostra o valor fixo para o usuário
    st.write("Sim")

    # Observação da política
    st.caption("Aplica-se a todos os projetos")

    # Define o valor no session_state para garantir que seja salvo
    st.session_state["salv_1_aplicavel"] = "Sim"

# Coluna 3 — avaliação de risco
col3.write("N/A")

# Coluna 4 — categoria de risco
col4.write("N/A")

# Coluna 5 — observação
col5.write("Não é necessário atribuir uma categoria de risco individual a esta política.")


st.divider()




# 2. Condições de Trabalho e Trabalhistas -------------------------------------------------------------

# colunas da segunda linha de perguntas e respostas
col1, col2, col3, col4, col5 = st.columns(largura_colunas, gap="medium")


# Coluna 1 — nome da política
col1.write("**2. Condições de Trabalho e Trabalhistas**")

# Coluna 2 — pergunta se a política é aplicável
with col2:
    st.radio(
        "Aplicável?",
        ["Sim", "Não"],
        key="salv_2_aplicavel",
        horizontal=True,
        disabled=not modo_edicao
    )

# Coluna 3 — pergunta de avaliação de risco e campo para detalhes
with col3:
    st.write("O projeto proposto apresenta riscos significativos em relação às condições de trabalho e trabalhistas?")
    st.text_area(
        "Detalhes:",
        key="salv_2_detalhes",
        height=120,
        disabled=not modo_edicao
    )

# Coluna 4 — categoria de risco
with col4:
    st.radio(
        "Categoria de risco",
        ["Categoria A", "Categoria B", "Categoria C"],
        key="salv_2_categoria_risco",
        disabled=not modo_edicao
    )

# Coluna 5 — observação explicativa
col5.write(
    "Projetos geralmente serão atribuídos à Categoria C para esta política, "
    "a menos que existam riscos elevados relacionados à saúde e segurança "
    "ocupacional, como mergulho ou trabalho como guardas ecológicos."
)

st.divider()




# 3. Eficiência de Recursos e Prevenção de Poluição --------------------------------------------------


# colunas da terceira linha de perguntas e respostas
col1, col2, col3, col4, col5 = st.columns(largura_colunas, gap="medium")


# Coluna 1 — nome da política
col1.write("**3. Eficiência de Recursos e Prevenção de Poluição**")

# Coluna 2 — pergunta se a política é aplicável
with col2:
    st.radio(
        "Aplicável?",
        ["Sim", "Não"],
        key="salv_3_aplicavel",
        horizontal=True,
        disabled=not modo_edicao
    )

# Coluna 3 — perguntas de avaliação de risco com campos de detalhe
with col3:

    st.write("O projeto proposto apresenta riscos significativos relacionados a pesticidas?")

    st.text_area(
        "Detalhes:",
        key="salv_3_pesticidas_detalhes",
        height=100,
        disabled=not modo_edicao
    )

    st.write("O projeto proposto apresenta riscos significativos relacionados ao uso insustentável de recursos e/ou formas de poluição que não sejam pesticidas?")

    st.text_area(
        "Detalhes:",
        key="salv_3_poluicao_detalhes",
        height=100,
        disabled=not modo_edicao
    )

# Coluna 4 — categoria de risco
with col4:
    st.radio(
        "Categoria de risco",
        ["Categoria A", "Categoria B", "Categoria C"],
        key="salv_3_categoria_risco",
        disabled=not modo_edicao
    )

# Coluna 5 — observações explicativas
with col5:
    st.write(
        "Projetos que envolvem a aquisição ou uso de pesticidas químicos serão atribuídos à Categoria B."
    )

    st.write(
        "Os projetos com potencial de exposição da comunidade a materiais e substâncias perigosos "
        "liberados por suas atividades serão classificados na Categoria A ou B."
    )

st.divider()





# 4. Saúde, Segurança e Proteção da Comunidade -------------------------------------------------------

# colunas da quarta linha de perguntas e respostas
col1, col2, col3, col4, col5 = st.columns(largura_colunas, gap="medium")



# Coluna 1 — nome da política
col1.write("**4. Saúde, Segurança e Proteção da Comunidade**")

# Coluna 2 — pergunta se a política é aplicável
with col2:
    st.radio(
        "Aplicável?",
        ["Sim", "Não"],
        key="salv_4_aplicavel",
        horizontal=True,
        disabled=not modo_edicao
    )

# Coluna 3 — pergunta de avaliação de risco com campo para detalhes
with col3:

    st.write(
        "O projeto proposto apresenta riscos significativos relacionados "
        "à saúde, segurança e proteção da comunidade?"
    )

    st.text_area(
        "Detalhes:",
        key="salv_4_detalhes",
        height=120,
        disabled=not modo_edicao
    )

# Coluna 4 — categoria de risco
with col4:
    st.radio(
        "Categoria de risco",
        ["Categoria A", "Categoria B", "Categoria C"],
        key="salv_4_categoria_risco",
        disabled=not modo_edicao
    )

# Coluna 5 — observações explicativas
with col5:

    st.markdown(
        "Projetos que financiam salários e/ou operações de guardas florestais, "
        "guardas ecológicos ou pessoal de segurança similar (armado ou desarmado) "
        "serão classificados como Categoria B<sup>1</sup>.",
        unsafe_allow_html=True
    )


    st.markdown(
        "Projetos que envolvem atividades de pesquisa<sup>2</sup> com seres humanos<sup>2</sup> "
        "serão classificados como Categoria B.",
        unsafe_allow_html=True
    )

st.write('')

# Nota de rodapé 1
st.caption(
    "<sup>1</sup> Esta disposição aplica-se independentemente de o pessoal de segurança ser empregado "
    "ou contratado pela entidade beneficiária, por uma agência governamental ou por um terceiro.",
    unsafe_allow_html=True
)

# Nota de rodapé 2
st.caption(
    "<sup>2</sup> Pesquisa com Seres Humanos refere-se a qualquer forma de investigação disciplinada "
    "que visa contribuir para um corpo de conhecimento ou teoria que envolva a obtenção de "
    "(a) dados de indivíduos vivos por meio de intervenção ou interação com o indivíduo ou "
    "(b) informações pessoais identificáveis. Projetos de demonstração de campo de conservação "
    "e/ou desenvolvimento geralmente não são considerados pesquisa, nem métodos participativos "
    "padrão usados para monitorar os impactos desses projetos no bem-estar humano "
    "(por exemplo, discussões em grupos focais).",
    unsafe_allow_html=True
)

st.divider()








# 5. Restrições de Uso da Terra e Reassentamento Involuntário ----------------------------------------

col1, col2, col3, col4, col5 = st.columns(largura_colunas, gap="medium")

col1.write("**5. Restrições de Uso da Terra e Reassentamento Involuntário**")

with col2:
    st.radio(
        "Aplicável?",
        ["Sim", "Não"],
        key="salv_5_aplicavel",
        horizontal=True,
        disabled=not modo_edicao
    )

with col3:
    st.write(
        "O projeto proposto apresenta riscos significativos relacionados a restrições "
        "de acesso associadas a impactos negativos nos meios de subsistência?"
    )

    st.text_area(
        "Detalhes:",
        key="salv_5_detalhes",
        height=120,
        disabled=not modo_edicao
    )

with col4:
    st.radio(
        "Categoria de risco",
        ["Categoria A", "Categoria B", "Categoria C"],
        key="salv_5_categoria_risco",
        disabled=not modo_edicao
    )

with col5:
    st.write(
        "Projetos que envolvem a criação ou expansão de áreas protegidas "
        "serão classificados como Categoria B."
    )

st.divider()


# 6. Conservação da Biodiversidade e Gestão Sustentável de Recursos Naturais Vivos -------------------

col1, col2, col3, col4, col5 = st.columns(largura_colunas, gap="medium")

col1.write("**6. Conservação da Biodiversidade e Gestão Sustentável de Recursos Naturais Vivos**")

with col2:
    st.radio(
        "Aplicável?",
        ["Sim", "Não"],
        key="salv_6_aplicavel",
        horizontal=True,
        disabled=not modo_edicao
    )

with col3:
    st.write(
        "O projeto proposto apresenta riscos significativos relacionados à "
        "degradação ou perda de habitat crítico ou outros habitats naturais?"
    )

    st.text_area(
        "Detalhes:",
        key="salv_6_detalhes",
        height=120,
        disabled=not modo_edicao
    )

with col4:
    st.radio(
        "Categoria de risco",
        ["Categoria A", "Categoria B", "Categoria C"],
        key="salv_6_categoria_risco",
        disabled=not modo_edicao
    )

with col5:
    
    st.markdown(
        "Projetos que envolvem impactos adversos em habitats críticos<sup>3</sup> "
        "serão classificados como Categoria A.",
        unsafe_allow_html=True
    )

    st.write(
        "Projetos que envolvem a aquisição de commodities de recursos naturais "
        "(por exemplo, madeira) que possam contribuir para a conversão ou "
        "degradação significativa de habitats naturais serão classificados como Categoria B."
    )

    st.write(
        "Projetos que envolvem a produção ou colheita de recursos naturais vivos "
        "de populações selvagens de espécies ameaçadas globalmente serão classificados como Categoria B."
    )

# Nota de rodapé 3
st.caption(
    "<sup>3</sup> Habitats críticos incluem, entre outros, áreas protegidas existentes "
    "e propostas, áreas reconhecidas como protegidas por comunidades locais tradicionais, "
    "bem como áreas identificadas como importantes para a conservação, como Áreas-Chave "
    "de Biodiversidade (KBAs), Sítios da Aliança para Extinção Zero (AZE), Áreas "
    "Importantes para Aves e Biodiversidade (IBAs), sítios Ramsar, etc.",
    unsafe_allow_html=True
)

st.divider()


# 7. Povos Indígenas ----------------------------------------------------------------------------------

col1, col2, col3, col4, col5 = st.columns(largura_colunas, gap="medium")

col1.write("**7. Povos Indígenas**")

with col2:
    st.radio(
        "Aplicável?",
        ["Sim", "Não"],
        key="salv_7_aplicavel",
        horizontal=True,
        disabled=not modo_edicao
    )

with col3:
    st.write(
        "O projeto proposto apresenta riscos significativos relacionados "
        "aos impactos sobre Povos Indígenas?"
    )

    st.text_area(
        "Detalhes:",
        key="salv_7_detalhes",
        height=120,
        disabled=not modo_edicao
    )

with col4:
    st.radio(
        "Categoria de risco",
        ["Categoria A", "Categoria B", "Categoria C"],
        key="salv_7_categoria_risco",
        disabled=not modo_edicao
    )

with col5:
    st.write(
        "Projetos que possam afetar Povos Indígenas em isolamento voluntário "
        "ou grupos remotos com contato externo limitado serão classificados como Categoria A."
    )

    st.write(
        "Projetos que envolvam o uso de ou restrições de acesso a recursos naturais "
        "que sejam centrais para a identidade, cultura e subsistência dos Povos Indígenas "
        "serão classificados como Categoria B."
    )

    st.write(
        "Projetos que envolvam o desenvolvimento comercial de terras e recursos naturais "
        "centrais para a identidade e subsistência dos Povos Indígenas ou o uso comercial "
        "de seu patrimônio cultural serão classificados como Categoria B."
    )


st.divider()


# 8. Patrimônio Cultural -------------------------------------------------------------------------------

col1, col2, col3, col4, col5 = st.columns(largura_colunas, gap="medium")

col1.write("**8. Patrimônio Cultural**")

with col2:
    st.radio(
        "Aplicável?",
        ["Sim", "Não"],
        key="salv_8_aplicavel",
        horizontal=True,
        disabled=not modo_edicao
    )

with col3:
    st.write(
        "O projeto proposto apresenta riscos significativos relacionados "
        "aos impactos sobre o patrimônio cultural tangível e/ou intangível?"
    )

    st.text_area(
        "Detalhes:",
        key="salv_8_detalhes",
        height=120,
        disabled=not modo_edicao
    )

with col4:
    st.radio(
        "Categoria de risco",
        ["Categoria A", "Categoria B", "Categoria C"],
        key="salv_8_categoria_risco",
        disabled=not modo_edicao
    )

with col5:
    st.write(
        "Projetos que introduzam restrições ao acesso das partes interessadas "
        "ao patrimônio cultural serão classificados como Categoria B."
    )

    st.write(
        "Projetos que envolvam o uso comercial de patrimônio cultural "
        "serão classificados como Categoria B."
    )

st.divider()


# 9. Igualdade de Gênero -------------------------------------------------------------------------------

col1, col2, col3, col4, col5 = st.columns(largura_colunas, gap="medium")

col1.write("**9. Igualdade de Gênero**")

# Coluna 2 — política sempre aplicável
with col2:

    st.write("Sim")
    st.caption("Aplica-se a todos os projetos")

    # Mantém o valor consistente para o salvamento
    st.session_state["salv_9_aplicavel"] = "Sim"



with col3:
    st.write(
        "O projeto proposto apresenta riscos significativos relacionados "
        "a impactos na promoção, proteção e respeito à igualdade de gênero?"
    )

    st.text_area(
        "Detalhes:",
        key="salv_9_detalhes",
        height=120,
        disabled=not modo_edicao
    )

with col4:
    st.radio(
        "Categoria de risco",
        ["Categoria A", "Categoria B", "Categoria C"],
        key="salv_9_categoria_risco",
        disabled=not modo_edicao
    )

with col5:
    st.write(
        "Projetos serão tipicamente atribuídos à Categoria C para esta política, "
        "a menos que existam riscos elevados de agravamento de desigualdades "
        "existentes relacionadas ao gênero."
    )

st.divider()


# 10. Engajamento de Partes Interessadas ---------------------------------------------------------------

col1, col2, col3, col4, col5 = st.columns(largura_colunas, gap="medium")

col1.write("**10. Engajamento de Partes Interessadas**")

with col2:
    st.write("Sim")
    st.caption("Aplica-se a todos os projetos")

    # Mantém o valor consistente para o salvamento
    st.session_state["salv_10_aplicavel"] = "Sim"

col3.write("N/A")
col4.write("N/A")

col5.write(
    "Não é necessário atribuir uma categoria de risco individual a esta política."
)

st.divider()









# CATEGORIA GERAL DE RISCO ---------------------------------------------------------------------------

col1, col2, col3, col4, col5 = st.columns(largura_colunas, gap="medium")

# Coluna 1
col1.write("**CATEGORIA GERAL DE RISCO**")

# Coluna 2
col2.write("N/A")

# Coluna 3
col3.write("N/A")


# Lê as categorias escolhidas nas perguntas 2 a 9

categorias_filtradas = []

for i in range(2, 10):  # perguntas 2 a 9

    aplicavel = st.session_state.get(f"salv_{i}_aplicavel")
    categoria = st.session_state.get(f"salv_{i}_categoria_risco")

    if aplicavel == "Sim" and categoria:
        categorias_filtradas.append(categoria)


# Inicializa a categoria geral
categoria_geral = ""

# Determina automaticamente a categoria geral
# prioridade: A > B > C

if "Categoria A" in categorias_filtradas:
    categoria_geral = "Categoria A"
elif "Categoria B" in categorias_filtradas:
    categoria_geral = "Categoria B"
elif "Categoria C" in categorias_filtradas:
    categoria_geral = "Categoria C"




col4.write("Resultado final:")

if categoria_geral:
    col4.write(f"**{categoria_geral}**")
else:
    col4.write("")


# Coluna 5
col5.write(
    "A categoria geral de risco para o projeto é equivalente à categoria mais alta "
    "atribuída às políticas individuais de salvaguarda."
)

st.divider()



# FORTALECIMENTO DE CAPACIDADE ---------------------------------------------------------------------------

largura_colunas = [2, 2, 3, 2, 3]

col1, col2 = st.columns([2, 11], gap="medium")


col1.write("**FORTALECIMENTO DE CAPACIDADE**")

col2.write("O solicitante necessita de fortalecimento de capacidade para gerenciar os riscos ambientais e sociais identificados aqui?")

col2.write("Se sim, descreva as atividades de fortalecimento de capacidade que precisam ser integradas ao desenho do projeto:")

col2.text_area(
    "Detalhes:",
    key="salv_fortalecimento_capacidades",
    height=120,
    disabled=not modo_edicao
)

st.divider()








st.write("")


# Botão somente para equipe e adimn

if st.session_state.get("tipo_usuario") in ["equipe", "admin"]:
    

    # Botão para salvar as respostas no banco
    if st.button("Salvar", icon=":material/save:", width=200, type="primary"):

        # Data da avaliação
        data_avaliacao = datetime.datetime.today().strftime("%d/%m/%Y")

        # Nome do avaliador
        avaliador_atual = st.session_state.get("nome", "Usuário")

        # Estrutura organizada das respostas de salvaguardas
        dados_salvaguardas = {

            "nome_avaliador_risco": avaliador_atual,
            "data_aval_risco": data_avaliacao,
            "categoria_geral_risco": categoria_geral,

            "pol_2_trabalho": {
                "aplicavel": st.session_state.get("salv_2_aplicavel"),
                "detalhes": st.session_state.get("salv_2_detalhes"),
                "categoria": st.session_state.get("salv_2_categoria_risco")
            },

            "pol_3_poluicao": {
                "aplicavel": st.session_state.get("salv_3_aplicavel"),
                "detalhes_pesticidas": st.session_state.get("salv_3_pesticidas_detalhes"),
                "detalhes_poluicao": st.session_state.get("salv_3_poluicao_detalhes"),
                "categoria": st.session_state.get("salv_3_categoria_risco")
            },

            "pol_4_comunidade": {
                "aplicavel": st.session_state.get("salv_4_aplicavel"),
                "detalhes": st.session_state.get("salv_4_detalhes"),
                "categoria": st.session_state.get("salv_4_categoria_risco")
            },

            "pol_5_reassentamento": {
                "aplicavel": st.session_state.get("salv_5_aplicavel"),
                "detalhes": st.session_state.get("salv_5_detalhes"),
                "categoria": st.session_state.get("salv_5_categoria_risco")
            },

            "pol_6_biodiversidade": {
                "aplicavel": st.session_state.get("salv_6_aplicavel"),
                "detalhes": st.session_state.get("salv_6_detalhes"),
                "categoria": st.session_state.get("salv_6_categoria_risco")
            },

            "pol_7_indigenas": {
                "aplicavel": st.session_state.get("salv_7_aplicavel"),
                "detalhes": st.session_state.get("salv_7_detalhes"),
                "categoria": st.session_state.get("salv_7_categoria_risco")
            },

            "pol_8_patrimonio": {
                "aplicavel": st.session_state.get("salv_8_aplicavel"),
                "detalhes": st.session_state.get("salv_8_detalhes"),
                "categoria": st.session_state.get("salv_8_categoria_risco")
            },

            "pol_9_genero": {
                "aplicavel": st.session_state.get("salv_9_aplicavel"),
                "detalhes": st.session_state.get("salv_9_detalhes"),
                "categoria": st.session_state.get("salv_9_categoria_risco")
            },

            "fortalecimento_capacidades": st.session_state.get("salv_fortalecimento_capacidades"),
        }

        # Atualiza o documento do projeto no MongoDB
        resultado = col_projetos.update_one(
            {"codigo": codigo_projeto_atual},
            {
                "$set": {
                    "salvaguardas": dados_salvaguardas
                }
            }
        )

        # Mostra mensagem de sucesso
        if resultado.modified_count >= 0:
            st.success("Respostas salvas com sucesso!", icon=":material/check:")
            time.sleep(3)
            st.rerun()






