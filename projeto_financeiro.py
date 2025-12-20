import streamlit as st
import pandas as pd
import time
from datetime import timedelta

import streamlit_shadcn_ui as ui

from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Define as coleções específicas que serão utilizadas a partir do banco
col_projetos = db["projetos"]


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


projeto = df_projeto.iloc[0]

# Capturando o financeiro no banco de dados
financeiro = projeto.get("financeiro", {})



###########################################################################################################
# FUNÇÕES
###########################################################################################################


def atualizar_datas_relatorios(col_projetos, codigo_projeto):
    projeto = col_projetos.find_one({"codigo": codigo_projeto})

    parcelas = projeto.get("financeiro", {}).get("parcelas", [])
    relatorios = projeto.get("relatorios", [])

    if not parcelas or not relatorios:
        return

    # Mapear parcelas por número
    mapa_parcelas = {
        p["numero"]: p for p in parcelas if p.get("numero") is not None
    }

    novos_relatorios = []

    for r in relatorios:
        numero = r.get("numero")

        if numero in mapa_parcelas:
            data_parcela = pd.to_datetime(
                mapa_parcelas[numero]["data_prevista"]
            )
            data_relatorio = (data_parcela + timedelta(days=15)).date().isoformat()
        else:
            data_relatorio = None

        novos_relatorios.append(
            {
                "numero": numero,
                "entregas": r.get("entregas", []),
                "data_prevista": data_relatorio
            }
        )

    col_projetos.update_one(
        {"codigo": codigo_projeto},
        {"$set": {"relatorios": novos_relatorios}}
    )



###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Financeiro")








# Abas para o "Cronograma de Desembolsos e Relatórios" e "Orçamento"
cron_desemb, orcamento = st.tabs(["Cronograma", "Orçamento"])



with cron_desemb:

    # Capturando os dados no bd
    valor_atual = financeiro.get("valor_total")




    # --------------------------------------------------
    # PERMISSÃO E MODO DE EDIÇÃO
    # --------------------------------------------------
    usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]

    with st.container(horizontal=True, horizontal_alignment="right"):
        if usuario_interno:
            modo_edicao = st.toggle("Modo de edição", key="editar_cronograma")
        else:
            modo_edicao = False



    # --------------------------------------------------
    # MODO VISUALIZAÇÃO
    # --------------------------------------------------
    if not modo_edicao:

        st.markdown('#### Cronograma de Parcelas e Relatórios')

        st.write("")
        st.write("")


        # -----------------------------
        # Construir cronograma
        # -----------------------------
        linhas_cronograma = []

        # ===== Parcelas =====
        parcelas = financeiro.get("parcelas", [])

        for p in parcelas:
            linhas_cronograma.append(
                {
                    "evento": f"Parcela {p.get('numero')}",
                    "entregas": [],
                    "valor": (
                        f"R$ {p['valor']:,.2f}".replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                        if p.get("valor") is not None else ""
                    ),
                    "percentual": (
                        f"{int(p['percentual'])} %"
                        if p.get("percentual") is not None else ""
                    ),
                    "data_prevista": (
                        pd.to_datetime(p.get("data_prevista")).strftime("%d/%m/%Y")
                        if p.get("data_prevista") else ""
                    ),
                    "data_realizada": (
                        pd.to_datetime(p.get("data_realizada")).strftime("%d/%m/%Y")
                        if p.get("data_realizada") else ""
                    ),
                }
            )

        # ===== Relatórios =====
        relatorios = projeto.get("relatorios", [])

        for r in relatorios:
            linhas_cronograma.append(
                {
                    "evento": f"Relatório {r.get('numero')}",
                    "entregas": r.get("entregas", []),
                    "valor": "",
                    "percentual": "",
                    "data_prevista": (
                        pd.to_datetime(r.get("data_prevista")).strftime("%d/%m/%Y")
                        if r.get("data_prevista") else ""
                    ),
                    "data_realizada": (
                        pd.to_datetime(r.get("data_realizada")).strftime("%d/%m/%Y")
                        if r.get("data_realizada") else ""
                    ),
                }
            )

        # Ordenar por data prevista
        linhas_cronograma = sorted(
            linhas_cronograma,
            key=lambda x: pd.to_datetime(
                x["data_prevista"], dayfirst=True, errors="coerce"
            )
        )

        # -----------------------------
        # Layout das colunas
        # -----------------------------
        layout_colunas = [2, 7, 2, 2, 2, 2]


        # -----------------------------
        # Cabeçalho
        # -----------------------------
        col_header = st.columns(layout_colunas)
        col_header[0].write("**Evento**")
        col_header[1].write("**Entregas**")
        col_header[2].write("**Valor**")
        col_header[3].write("**Percentual**")
        col_header[4].write("**Data prevista**")
        col_header[5].write("**Data realizada**")

        st.divider()

        # -----------------------------
        # Linhas
        # -----------------------------
        for row in linhas_cronograma:

            cols = st.columns(layout_colunas)

            # Evento
            cols[0].write(row["evento"])

            # Entregas (multilinha real)
            if row["entregas"]:
                for entrega in row["entregas"]:
                    cols[1].write(f"{entrega}")
            else:
                cols[1].write("")

            # Valor
            cols[2].write(row["valor"])

            # Percentual
            cols[3].write(row["percentual"])

            # Datas
            cols[4].write(row["data_prevista"])
            cols[5].write(row["data_realizada"])

            st.divider()





















        st.write('')
        st.write('')
        st.write('')

        st.markdown('#### OPÇÃO 2 de layout da tabela de cronograma')

        st.write("")

        # -----------------------------
        # Construir cronograma
        # -----------------------------
        linhas_cronograma = []

        # ===== Parcelas =====
        parcelas = financeiro.get("parcelas", [])

        for p in parcelas:
            numero = p.get("numero")
            percentual = p.get("percentual")
            valor = p.get("valor")
            data_prevista = p.get("data_prevista")
            data_realizada = p.get("data_realizada")

            linhas_cronograma.append(
                {
                    "evento": f"Parcela {numero}",
                    "Entregas": "",
                    "Valor R$": (
                        f"{valor:,.2f}".replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                        if valor is not None else ""
                    ),
                    "Percentual": (
                        f"{int(percentual)} %"
                        if percentual is not None else ""
                    ),
                    "Data prevista": pd.to_datetime(
                        data_prevista, errors="coerce"
                    ),
                    "Data realizada": (
                        pd.to_datetime(data_realizada).strftime("%d/%m/%Y")
                        if data_realizada else ""
                    ),
                }
            )

        # ===== Relatórios =====
        relatorios = projeto.get("relatorios", [])

        for r in relatorios:
            numero = r.get("numero")
            entregas = r.get("entregas", [])
            data_prevista = r.get("data_prevista")
            data_realizada = r.get("data_realizada")

            linhas_cronograma.append(
                {
                    "evento": f"Relatório {numero}",
                    "Entregas": "\n".join(entregas) if entregas else "",
                    # "Entregas": "<br>".join(entregas) if entregas else "",
                    "Valor R$": "",
                    "Percentual": "",
                    "Data prevista": pd.to_datetime(
                        data_prevista, errors="coerce"
                    ),
                    "Data realizada": (
                        pd.to_datetime(data_realizada).strftime("%d/%m/%Y")
                        if data_realizada else ""
                    ),
                }
            )

        # -----------------------------
        # DataFrame final
        # -----------------------------
        df_cronograma = pd.DataFrame(linhas_cronograma)

        if df_cronograma.empty:
            st.info("Não há dados financeiros para exibição.")
            st.stop()

        # Ordenar por data prevista
        df_cronograma = df_cronograma.sort_values(
            by="Data prevista",
            ascending=True
        )

        # Formatar data prevista para exibição
        df_cronograma["Data prevista"] = df_cronograma["Data prevista"].dt.strftime(
            "%d/%m/%Y"
        )

        # -----------------------------
        # Tabela
        # -----------------------------
        
        ui.table(df_cronograma)
        















    # --------------------------------------------------
    # MODO EDIÇÃO
    # --------------------------------------------------
    else:


        # Radio para escolher o que será editado
        opcao_editar_cron = st.radio(
            "O que deseja editar?",
            ["Valor total",
            "Parcelas", 
            "Relatórios"],
            horizontal=True
        )

        # st.divider()
        st.write('')
        st.write('')

        # -------------------------------------------------------
        # Editar o valor total do projeto


        if opcao_editar_cron == "Valor total":

            st.markdown("#### Valor total do projeto")

            with st.form("form_valor_total", border=False):

                valor_total = st.number_input(
                    "Valor total do projeto (R$)",
                    min_value=0.0,
                    step=1000.0,
                    format="%.2f",
                    value=float(valor_atual) if valor_atual is not None else 0.0,
                    width=300
                )

                st.write('')
                salvar = st.form_submit_button("Salvar", icon=":material/save:")

                if salvar:
                    col_projetos.update_one(
                        {"codigo": codigo_projeto_atual},
                        {
                            "$set": {
                                "financeiro.valor_total": float(valor_total)
                            }
                        }
                    )

                    st.success("Valor total do projeto salvo com sucesso!")
                    time.sleep(3)
                    st.rerun()



                    st.success("Valor total do projeto salvo com sucesso!")
                    time.sleep(3)
                    st.rerun()


        # -------------------------------------------------------
        # Editar Parcelas







        if opcao_editar_cron == "Parcelas":

            st.markdown("#### Parcelas")

            # -----------------------------------
            # Valor total do projeto
            # -----------------------------------
            valor_total = valor_atual if valor_atual is not None else 0.0

            # -----------------------------------
            # Dados atuais (fonte da verdade)
            # -----------------------------------
            parcelas = financeiro.get("parcelas", [])

            if parcelas:
                df_parcelas = pd.DataFrame(parcelas)

                df_parcelas["data_prevista"] = pd.to_datetime(
                    df_parcelas["data_prevista"],
                    errors="coerce"
                )

                if "numero" not in df_parcelas.columns:
                    df_parcelas["numero"] = None

            else:
                df_parcelas = pd.DataFrame(
                    columns=[
                        "numero",
                        "data_prevista",
                        "percentual",
                    ]
                )

            # -----------------------------------
            # Ordenar por data prevista
            # -----------------------------------
            if not df_parcelas.empty:
                df_parcelas = df_parcelas.sort_values(
                    by="data_prevista",
                    ascending=True
                ).reset_index(drop=True)

            # -----------------------------------
            # Calcular valor (fonte da verdade)
            # -----------------------------------
            df_parcelas["valor"] = (
                df_parcelas["percentual"].fillna(0) / 100 * valor_total
            )

            # -----------------------------------
            # Coluna de exibição (UI)
            # -----------------------------------
            df_parcelas["valor_fmt"] = df_parcelas["valor"].apply(
                lambda x: f"R$ {x:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

            # -----------------------------------
            # Editor (UI)
            # -----------------------------------
            df_editado = st.data_editor(
                df_parcelas[
                    [
                        "numero",
                        "percentual",
                        "valor_fmt",
                        "data_prevista",
                    ]
                ],
                num_rows="dynamic",
                width=800,
                column_config={
                    "numero": st.column_config.NumberColumn(
                        "Número",
                        min_value=1,
                        step=1
                    ),
                    "percentual": st.column_config.NumberColumn(
                        "Percentual (%)",
                        min_value=0.0,
                        max_value=100.0,
                        step=1.0,
                        format="%.0f%%"
                    ),
                    "valor_fmt": st.column_config.TextColumn(
                        "Valor (auto)",
                        disabled=True
                    ),
                    "data_prevista": st.column_config.DateColumn(
                        "Data prevista",
                        format="DD/MM/YYYY"
                    ),
                },
                key="editor_parcelas",
            )

            st.write("")

            # -----------------------------------
            # Sincronizar SOMENTE campos editáveis
            # -----------------------------------
            df_parcelas.loc[df_editado.index, "numero"] = df_editado["numero"]
            df_parcelas.loc[df_editado.index, "percentual"] = df_editado["percentual"]
            df_parcelas.loc[df_editado.index, "data_prevista"] = df_editado["data_prevista"]

            # Recalcular valor após edição
            df_parcelas["valor"] = (
                df_parcelas["percentual"].fillna(0) / 100 * valor_total
            )

            # -----------------------------------
            # Total das porcentagens
            # -----------------------------------
            soma_porcentagens = df_parcelas["percentual"].dropna().sum()
            st.write(f"**Total: {int(soma_porcentagens)}%**")

            # -----------------------------------
            # Salvar
            # -----------------------------------
            if st.button("Salvar parcelas", icon=":material/save:"):

                df_salvar = df_parcelas.dropna(
                    subset=["percentual", "data_prevista"],
                    how="any"
                ).copy()

                if df_salvar["percentual"].sum() != 100:
                    st.error(
                        "A soma das porcentagens deve ser 100%. Os dados não foram salvos.",
                        icon=":material/error:"
                    )
                    st.stop()

                df_salvar = df_salvar.sort_values(
                    by="data_prevista",
                    ascending=True
                ).reset_index(drop=True)

                parcelas_salvar = []

                for _, row in df_salvar.iterrows():

                    parcelas_salvar.append(
                        {
                            "numero": int(row["numero"]) if not pd.isna(row["numero"]) else None,
                            "percentual": float(row["percentual"]),
                            "valor": float(row["valor"]),
                            "data_prevista": (
                                pd.to_datetime(row["data_prevista"]).date().isoformat()
                            ),
                        }
                    )

                col_projetos.update_one(
                    {"codigo": codigo_projeto_atual},
                    {
                        "$set": {
                            "financeiro.parcelas": parcelas_salvar
                        }
                    }
                )

                # Atualizar as datas dos relatórios correspondentes na coleção de relatórios. Dataprevista do relatório = data_prevista da parcela + 15 dias
                atualizar_datas_relatorios(col_projetos, codigo_projeto_atual)


                st.success("Parcelas salvas com sucesso!")
                time.sleep(3)
                st.rerun()








        if opcao_editar_cron == "Relatórios":



            st.markdown("#### Relatórios")

            # --------------------------------------------------
            # Coletar TODAS as entregas do projeto
            # --------------------------------------------------
            entregas_projeto = []

            plano = projeto.get("plano_trabalho", {})
            for componente in plano.get("componentes", []):
                for entrega in componente.get("entregas", []):
                    if entrega.get("entrega"):
                        entregas_projeto.append(entrega["entrega"])

            entregas_projeto = sorted(set(entregas_projeto))

            # --------------------------------------------------
            # Parcelas (fonte da verdade)
            # --------------------------------------------------
            parcelas = financeiro.get("parcelas", [])

            # Ordenar parcelas por número
            parcelas = sorted(
                [p for p in parcelas if p.get("numero") is not None],
                key=lambda x: x["numero"]
            )

            # Se não houver parcelas suficientes, não há relatórios
            if len(parcelas) < 2:
                st.info("É necessário ter ao menos duas parcelas para gerar relatórios.")
                st.stop()

            # --------------------------------------------------
            # Montar DataFrame base dos relatórios
            # (parcelas - última)
            # --------------------------------------------------
            linhas_relatorios = []

            for parcela in parcelas[:-1]:  # ignora a última parcela
                numero = parcela["numero"]
                data_parcela = pd.to_datetime(parcela["data_prevista"], errors="coerce")

                data_relatorio = (
                    data_parcela + timedelta(days=15)
                    if not pd.isna(data_parcela)
                    else pd.NaT
                )

                linhas_relatorios.append(
                    {
                        "numero": numero,
                        "data_prevista": data_relatorio,
                        "entregas": [],
                    }
                )

            df_relatorios_base = pd.DataFrame(linhas_relatorios)

            # --------------------------------------------------
            # Mesclar com relatórios já existentes no banco
            # (preserva entregas já salvas)
            # --------------------------------------------------
            relatorios_existentes = projeto.get("relatorios", [])

            if relatorios_existentes:
                df_existente = pd.DataFrame(relatorios_existentes)

                for _, row in df_existente.iterrows():
                    numero = row.get("numero")

                    if numero in df_relatorios_base["numero"].values:
                        idx = df_relatorios_base.index[
                            df_relatorios_base["numero"] == numero
                        ][0]

                        df_relatorios_base.at[idx, "entregas"] = row.get("entregas", [])


            # Garantir que entregas seja sempre lista
            df_relatorios_base["entregas"] = df_relatorios_base["entregas"].apply(
                lambda x: x if isinstance(x, list) else []
            )

            # --------------------------------------------------
            # Editor (linhas fixas)
            # --------------------------------------------------
            df_editado = st.data_editor(
                df_relatorios_base[["numero", "entregas", "data_prevista"]],
                num_rows="fixed",
                use_container_width=True,
                column_config={
                    "numero": st.column_config.NumberColumn(
                        "Número (auto)",
                        disabled=True,
                        width=5
                    ),
                    "entregas": st.column_config.MultiselectColumn(
                        "Entregas",
                        options=[""] + entregas_projeto,
                        help="Selecione as entregas relacionadas a este relatório",
                        width=800
                    ),
                    "data_prevista": st.column_config.DateColumn(
                        "Data prevista (auto)",
                        format="DD/MM/YYYY",
                        disabled=True,
                        width=20
                    ),
                },
                key="editor_relatorios",
                hide_index=True
            )

            st.write("")

            # --------------------------------------------------
            # Salvar
            # --------------------------------------------------
            if st.button("Salvar relatórios", icon=":material/save:"):

                relatorios_salvar = []

                for _, row in df_editado.iterrows():

                    entregas = [e for e in row["entregas"] if e]

                    relatorios_salvar.append(
                        {
                            "numero": int(row["numero"]),
                            "entregas": entregas,
                            "data_prevista": (
                                None
                                if pd.isna(row["data_prevista"])
                                else row["data_prevista"].date().isoformat()
                            ),
                        }
                    )

                col_projetos.update_one(
                    {"codigo": codigo_projeto_atual},
                    {
                        "$set": {
                            "relatorios": relatorios_salvar
                        }
                    }
                )

                st.success("Relatórios salvos com sucesso!")
                time.sleep(3)
                st.rerun()





with orcamento:
    st.write('*Bloco do cronograma de parcelas, relatórios e status // Em construção*')