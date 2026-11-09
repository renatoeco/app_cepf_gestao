
import streamlit as st
import pandas as pd

from funcoes_auxiliares import conectar_mongo_cepf_gestao


st.set_page_config(
    page_title="Migração de relacionamentos",
    page_icon=":material/database:"
)

st.title("Migração dos relacionamentos de projetos")

st.warning(
    "Esta operação prepara a migração dos relacionamentos "
    "da coleção pessoas. O campo projetos original será preservado."
)

# ==========================================================
# CONEXÃO
# ==========================================================

db = conectar_mongo_cepf_gestao()

col_projetos = db["projetos"]
col_pessoas = db["pessoas"]


# ==========================================================
# ANÁLISE DOS DADOS
# ==========================================================

def analisar_migracao():

    projetos = list(
        col_projetos.find(
            {},
            {
                "_id": 1,
                "codigo": 1
            }
        )
    )

    pessoas = list(
        col_pessoas.find(
            {},
            {
                "_id": 1,
                "nome_completo": 1,
                "projetos": 1,
                "projetos_ids": 1
            }
        )
    )

    # ------------------------------------------------------
    # MAPA CÓDIGO -> OBJECTID
    # ------------------------------------------------------

    mapa_projetos = {}
    codigos_duplicados = []

    for projeto in projetos:

        codigo = projeto.get("codigo")

        if not isinstance(codigo, str) or not codigo.strip():
            continue

        codigo = codigo.strip()

        if codigo in mapa_projetos:
            codigos_duplicados.append(codigo)
        else:
            mapa_projetos[codigo] = projeto["_id"]

    # ------------------------------------------------------
    # ANALISA AS ASSOCIAÇÕES DAS PESSOAS
    # ------------------------------------------------------

    plano_migracao = []
    projetos_nao_encontrados = []
    dados_invalidos = []
    pessoas_com_migracao_anterior = []

    for pessoa in pessoas:

        nome = pessoa.get("nome_completo", "Sem nome")

        # Evita sobrescrever uma migração anterior
        if "projetos_ids" in pessoa:
            pessoas_com_migracao_anterior.append(nome)
            continue

        projetos_pessoa = pessoa.get("projetos", [])

        if projetos_pessoa is None:
            projetos_pessoa = []

        if not isinstance(projetos_pessoa, list):
            dados_invalidos.append(
                f"{nome}: campo projetos não é uma lista"
            )
            continue

        ids_projetos = []

        for codigo in projetos_pessoa:

            if not isinstance(codigo, str):
                dados_invalidos.append(
                    f"{nome}: associação inválida ({codigo})"
                )
                continue

            codigo = codigo.strip()

            if not codigo:
                continue

            if codigo not in mapa_projetos:
                projetos_nao_encontrados.append(
                    f"{nome}: {codigo}"
                )
                continue

            id_projeto = mapa_projetos[codigo]

            if id_projeto not in ids_projetos:
                ids_projetos.append(id_projeto)

        plano_migracao.append({
            "_id": pessoa["_id"],
            "nome": nome,
            "projetos_ids": ids_projetos
        })

    problemas = (
        codigos_duplicados
        or projetos_nao_encontrados
        or dados_invalidos
        or pessoas_com_migracao_anterior
    )

    return {
        "projetos": projetos,
        "pessoas": pessoas,
        "plano": plano_migracao,
        "codigos_duplicados": codigos_duplicados,
        "projetos_nao_encontrados": projetos_nao_encontrados,
        "dados_invalidos": dados_invalidos,
        "pessoas_com_migracao_anterior": pessoas_com_migracao_anterior,
        "problemas": bool(problemas)
    }


# ==========================================================
# BOTÃO DE ANÁLISE
# ==========================================================

if st.button(
    "Analisar dados",
    type="primary",
    icon=":material/search:",
    width=250
):

    resultado = analisar_migracao()

    st.session_state["resultado_migracao"] = resultado


# ==========================================================
# RESULTADO DA ANÁLISE
# ==========================================================

resultado = st.session_state.get("resultado_migracao")

if resultado:

    st.divider()

    st.subheader("Resultado da análise")

    col1, col2 = st.columns(2)

    col1.metric(
        "Projetos encontrados",
        len(resultado["projetos"])
    )

    col2.metric(
        "Pessoas analisadas",
        len(resultado["pessoas"])
    )

    st.metric(
        "Pessoas no plano de migração",
        len(resultado["plano"])
    )

    # ------------------------------------------------------
    # INCONSISTÊNCIAS
    # ------------------------------------------------------

    if resultado["codigos_duplicados"]:

        st.error("Existem códigos de projetos duplicados.")

        st.write(
            sorted(set(resultado["codigos_duplicados"]))
        )

    if resultado["projetos_nao_encontrados"]:

        st.error("Existem projetos associados que não foram encontrados.")

        st.write(
            resultado["projetos_nao_encontrados"]
        )

    if resultado["dados_invalidos"]:

        st.error("Existem associações com dados inválidos.")

        st.write(
            resultado["dados_invalidos"]
        )

    if resultado["pessoas_com_migracao_anterior"]:

        st.warning(
            "Algumas pessoas já possuem o campo projetos_ids. "
            "A migração foi bloqueada para evitar sobrescrita."
        )

        st.write(
            resultado["pessoas_com_migracao_anterior"]
        )

    # ------------------------------------------------------
    # AUTORIZAÇÃO PARA MIGRAR
    # ------------------------------------------------------

    if resultado["problemas"]:

        st.error(
            "A migração não pode ser executada. "
            "Corrija as inconsistências antes de continuar."
        )

    else:

        st.success(
            "Análise concluída. Não foram encontradas inconsistências."
        )

        st.write(
            "Os relacionamentos estão prontos para serem convertidos "
            "em ObjectIds."
        )

        confirmar = st.checkbox(
            "Confirmo que fiz backup do banco de dados e quero executar a migração.",
            key="confirmar_migracao"
        )

        if st.button(
            "Executar migração",
            type="primary",
            icon=":material/database:",
            disabled=not confirmar
        ):

            atualizados = 0

            with st.spinner("Migrando relacionamentos..."):

                for pessoa in resultado["plano"]:

                    col_pessoas.update_one(
                        {
                            "_id": pessoa["_id"],
                            "projetos_ids": {"$exists": False}
                        },
                        {
                            "$set": {
                                "projetos_ids": pessoa["projetos_ids"]
                            }
                        }
                    )

                    atualizados += 1

            st.session_state.pop("resultado_migracao", None)
            st.session_state.pop("confirmar_migracao", None)

            st.success(
                f"Migração concluída. {atualizados} pessoas processadas."
            )

            st.rerun()


