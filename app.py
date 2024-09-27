import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
from PIL import Image
import hmac
import pymysql

st.set_page_config(
    layout="wide",
    page_title="Dash VOP",
)
db_name = 'vop'

months = {
    '01': 'Janeiro',
    '02': 'Fevereiro',
    '03': 'Março',
    '04': 'Abril',
    '05': 'Maio',
    '06': 'Junho',
    '07': 'Julho',
    '08': 'Agosto',
    '09': 'Setembro',
    '10': 'Outubro',
    '11': 'Novembro',
    '12': 'Dezembro',
}

def get_funis(db_name):
    db_host = 'bubup.cngui0qechn6.sa-east-1.rds.amazonaws.com'
    db_port = 3306
    db_user = 'admin'
    db_password = 'Bubup.db'
    
    conn = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cur1 = conn.cursor()
    query1 = f"SELECT * FROM RD_funil_etapas;"
    cur1.execute(query1)
    colunas1 = [i[0] for i in cur1.description]
    df = pd.DataFrame(cur1.fetchall(), columns=colunas1)
    cur1.close()
    return df
    


############# CSS #############
st.markdown(
    """
    <style>
    /* Cor de fundo da sidebar */
    [data-testid="stSidebar"] {
        background-color: grey;  /* Cor de fundo da sidebar */
    }
    [data-testid="stSidebar"] label {
    color: white !important;  /* Cor do texto como branco */
    }
    </style>
    """,
    unsafe_allow_html=True
)
###############################
def get_fullDeals(db_name):
    db_host = 'bubup.cngui0qechn6.sa-east-1.rds.amazonaws.com'
    db_port = 3306
    db_user = 'admin'
    db_password = 'Bubup.db'
    
    conn = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cur1 = conn.cursor()
    query1 = f"SELECT * FROM RD_deals;"
    cur1.execute(query1)
    colunas1 = [i[0] for i in cur1.description]
    df_deals = pd.DataFrame(cur1.fetchall(), columns=colunas1)
    cur1.close()
    
    cur2 = conn.cursor()
    query2 = f"SELECT * FROM RD_deal_lost_reason;"
    cur2.execute(query2)
    colunas2 = [i[0] for i in cur2.description]
    df_lost_deals = pd.DataFrame(cur2.fetchall(), columns=colunas2)
    cur2.close()
    
    df_lost_deals['_id'] = df_lost_deals['_id'].astype(str)
    df_deals['Motivo de Perda'] = df_deals['Motivo de Perda'].astype(str)
    df_deals = pd.merge(df_deals, df_lost_deals, left_on='Motivo de Perda', right_on='_id', how='left')
    df_deals['Motivo de Perda'] = df_deals['name']
    df_deals['Data de criação'] = pd.to_datetime(df_deals['Data de criação'], format='%Y-%m-%d', errors='coerce')
    df_deals['Data de fechamento'] = pd.to_datetime(df_deals['Data de fechamento'], format='%Y-%m-%d', errors='coerce')
    df_deals.loc[:, 'Data de fechamento'] = df_deals['Data de fechamento'].fillna(df_deals['Data de criação'])
    if df_deals['Valor Único'].dtype == 'O':
        df_deals['Valor Único'] = df_deals['Valor Único'].str.replace(',', '').astype(float)  # Convertendo 'Valor Único' para float

    return df_deals

#################### FUNÇÕES ####################
@st.cache_data
def load_data():
    df = get_fullDeals(db_name)
    return df

@st.cache_data
def load_metas():
    df_metas = pd.read_csv("metas.csv")
    return df_metas

@st.cache_data
def load_funis():
    df_funis = get_funis(db_name)
    return df_funis

funis = load_funis().groupby('Funil')['Etapa'].apply(list).to_dict()

def check_password():
    """Returns `True` if the user had the correct password."""
    if not 'senha' in st.session_state:
        st.session_state.senha = st.secrets["passwords"]["password"]

    def password_entered():
        """Checks whether a password entered por the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.session_state.senha):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input por password.
    st.text_input(
        "Senha de acesso:", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Senha incorreta.")
    return False

if not check_password():
    st.stop()
    
def get_vendas_realizadas_por_vendedor(df):
    df_vendidas = df[df['Estado'] == 'Vendida']
    if 'Produtos' in df_vendidas.columns:
        df_vendidas = df_vendidas.groupby('Responsável')['Valor Único'].sum().reset_index(name='Valor Total')
        df_vendidas.rename(columns={'Produtos': 'Produto'}, inplace=True)
    else:
        df_vendidas = pd.DataFrame(columns=['Produto', 'Valor Total'])
    return df_vendidas

def get_receita_total(df):
    df_vendidas = df[df['Estado'] == 'Vendida']
    if 'Produtos' in df_vendidas.columns:
        df_vendidas = df_vendidas.groupby('Produtos')['Valor Único'].sum().reset_index(name='Valor Total')
        df_vendidas.rename(columns={'Produtos': 'Produto'}, inplace=True)
    else:
        df_vendidas = pd.DataFrame(columns=['Produto', 'Valor Total'])
    return df_vendidas

def get_vendas_realizadas(df):
    df_vendidas = df[df['Estado'] == 'Vendida']
    if 'Produtos' in df_vendidas.columns:
        df_vendidas = df_vendidas.groupby('Produtos').size().reset_index(name='Quantidade')
        df_vendidas.rename(columns={'Produtos': 'Produto'}, inplace=True)
    else:
        df_vendidas = pd.DataFrame(columns=['Produto', 'Quantidade'])
    return df_vendidas

def get_ticket_medio_por_vendedor(df):
    df_vendidas = df[df['Estado'] == 'Vendida']
    if 'Responsável' in df_vendidas.columns:
        df_vendidas = df_vendidas.groupby('Responsável')['Valor Único'].mean().reset_index(name='Ticket Médio')
        df_vendidas.rename(columns={'Responsável': 'Responsável'}, inplace=True)
    else:
        df_vendidas = pd.DataFrame(columns=['Responsável', 'Ticket Médio'])
    return df_vendidas

def get_conversao_por_vendedor(df):
    total_por_responsavel = df.groupby('Responsável').size()
    vendidas_por_responsavel = df[df['Estado'] == 'Vendida'].groupby('Responsável').size()
    taxa_conversao_responsavel_e_venda = (vendidas_por_responsavel / total_por_responsavel).fillna(0) * 100
    taxa_conversao_responsavel_e_venda = taxa_conversao_responsavel_e_venda.rename('Taxa de Conversão (%)')
    taxa_conversao_responsavel_e_venda = (taxa_conversao_responsavel_e_venda / 100).round(4)
    return taxa_conversao_responsavel_e_venda, vendidas_por_responsavel
################################################

df = load_data()
df_metas = load_metas()
df_total = load_data()
st.session_state["negocios"] = df
# st.sidebar.image("logo.png", width=100)
st.header("Dashboard - VOP")
st.divider()
st.sidebar.image("logo2.png", width=250)

################ FILTROS ####################
# DATA
data_inicial = st.sidebar.date_input('Data Inicial', date.today().replace(day=1))
data_final = st.sidebar.date_input('Data Final', date.today())
data_inicial = pd.to_datetime(data_inicial)
data_final = pd.to_datetime(data_final)
flag_data_final_maior_que_inicial = False

if data_final < data_inicial:
    st.sidebar.warning('A data final não pode ser anterior à data inicial.')
    flag_data_final_maior_que_inicial = True
else:
    df = df[(df['Data de fechamento'] >= data_inicial) & (df['Data de fechamento'] <= data_final)]

df_filtro_data = df.copy()   # Cópia do dataframe original para primeiro gráfico
# FUNIL
todos_funis = ['Todos'] + df['Funil de vendas'].unique().tolist()
funil_selecionado = st.sidebar.selectbox('Funil', todos_funis)
if funil_selecionado != 'Todos':
    df = df[df['Funil de vendas'] == funil_selecionado]

# PERFORMANCE
performance_etapa = df.groupby(['Responsável', 'Etapa']).size().unstack(fill_value=0)
performance_estado = df.groupby(['Responsável', 'Estado']).size().unstack(fill_value=0)
performance_vendedores = performance_etapa.join(performance_estado, lsuffix='_Etapa', rsuffix='_Estado')

# Organize de dataframe based on funil selected

if funil_selecionado != 'Todos':
    valores_funil = [valor for valor in funis[funil_selecionado] if valor in performance_etapa.columns]
    performance_etapa = performance_etapa[valores_funil]

# FILTRO DE RESPONSÁVEL
if not performance_etapa.empty and not performance_estado.empty:
    todos_responsaveis = ['Todos'] + df['Responsável'].unique().tolist()
    responsavel_conversao = st.sidebar.selectbox('Responsável', todos_responsaveis)
    if responsavel_conversao != 'Todos':
        df = df[df['Responsável'] == responsavel_conversao]
################################################


########### CÁLCULO DE TOTAIS ###############
total_por_responsavel = df.groupby('Responsável').size()
fechados_por_responsavel = df[df['Estado'] == 'Vendida'].groupby('Responsável').size()
for responsavel in total_por_responsavel.index:
    if responsavel not in fechados_por_responsavel.index:
        fechados_por_responsavel[responsavel] = 0

vendidas_por_responsavel = df[df['Etapa'] == 'Ganho'].groupby('Responsável').size()
taxa_conversao_etapa = (vendidas_por_responsavel / total_por_responsavel).fillna(0) * 100
vendidos_total = df[df['Estado'] == 'Vendida'].shape[0]
if df.shape[0] > 0:
    taxa_conversao_total = (vendidos_total / df.shape[0]) * 100
else:
    taxa_conversao_total = 0
################################################

df_realizado_total = get_receita_total(df_filtro_data)
df_receita = get_receita_total(df)
df_mes_atual = df_total[(df_total['Data de fechamento'].dt.month == data_inicial.month) & (df_total['Data de fechamento'].dt.year == data_inicial.year)]
df_realizado_por_vendedor = get_vendas_realizadas_por_vendedor(df_mes_atual)

############### FUNÇÕES PARA GRÁFICOS ###############
def get_fig_metas1(df_realizado=df_receita):
    if not df_realizado.empty and data_inicial.month == data_final.month:
        # Ordenar por 'Valor Total' para exibição
        df_realizado = df_realizado.sort_values('Valor Total', ascending=False)
        
        bar_width = 0.15
        
        # Criar o gráfico
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_realizado["Produto"],
            y=df_realizado["Valor Total"],
            name='Valor Total Vendido',
            marker_color='#4A0A86',  # Amarelo claro
            text='R$ ' + df_realizado['Valor Total'].round(2).astype(str),  # Exibir o valor total
            textposition='outside',
            width=[bar_width] * len(df_realizado)

        ))

        # Atualizar o layout
        fig.update_layout(
            barmode='group',
            title=f'Vendas Realizadas - por produto',
            xaxis_title='Produto',
            yaxis_title='Valor Total Vendido (R$)',
            title_font_size=20,
            title_x=0,
            yaxis=dict(
                range=[0, max(df_realizado['Valor Total'].max(), 10) * 1.1]  # Ajustar o intervalo do eixo Y
            ),
        )
        fig.update_traces(
            marker_line_color='white', 
            marker_line_width=2,
        )
    else:
        st.warning('Não há dados para exibir no mês selecionado.')
        fig = go.Figure()

    return fig

def get_fig_metas2():
    if data_inicial.month != data_final.month:
        fig = go.Figure()
        st.warning('Por favor, selecione o mesmo mês para comparação.')
        return fig

    df_realizado = get_vendas_realizadas(df_mes_atual)
    meta_empresa = df_metas.loc[(df_metas['Mes'] == months[str(data_inicial.month).zfill(2)]) & (df_metas['Responsável'] == 'Empresa')]['Meta'].values[0]
    realizado_percentual = round(float((df_realizado["Quantidade"].sum() / meta_empresa) * 100), 2)
    restante_percentual = 100 - realizado_percentual
    
    if realizado_percentual > 100:
        realizado_percentual = 100
        restante_percentual = 0

    fig = go.Figure()

    if data_inicial.month == data_final.month and not df_metas.empty:
        fig.add_trace(go.Pie(
            labels=['Realizado', 'Restante'],
            values=[realizado_percentual, restante_percentual],
            marker=dict(colors=[f'#4A0A86', 'lightgrey']),
            textinfo='label+percent',  # Mostra o rótulo e o percentual
            hole=.4,  # Isso cria um gráfico de pizza "anular" (com um buraco no meio)
        ))

        # Atualizando layout
        fig.update_layout(
            title=f'Metas X Realizados - Total',
            title_font_size=20,
            title_x=0,
            showlegend=True,  # Mostra a legenda
        )

    return fig

# def get_fig_metas3(df_realizado=df_realizado_por_vendedor, df_metas=df_metas):
    fig = go.Figure()
    bar_width = 0.15
    show_fig = False

    # Verificar se as datas inicial e final estão no mesmo mês
    if data_inicial.month == data_final.month:
        mes = months[str(data_inicial.month).zfill(2)]
        if mes not in df_metas['Mes'].values:
            st.warning('O mês selecionado não possui metas cadastradas.')
            return show_fig, fig

        # Filtrar as metas do mês selecionado, excluindo a linha da "Empresa"
        df_metas_mes = df_metas.loc[(df_metas['Mes'] == mes) & (df_metas['Responsável'] != 'Empresa')]

        # Verificar se existem metas cadastradas para os responsáveis no mês selecionado
        if not df_metas_mes.empty:
            # Garantir que todos os responsáveis com metas apareçam no gráfico, mesmo sem vendas
            df_realizado_completo = df_metas_mes[['Responsável']].merge(df_realizado, on='Responsável', how='left')
            df_realizado_completo['Valor Total'] = df_realizado_completo['Valor Total'].fillna(0)

            # Iterar sobre cada vendedor para calcular o percentual realizado da meta
            for _, row in df_realizado_completo.iterrows():
                responsavel = row['Responsável']
                valor_realizado = row['Valor Total']
                
                if responsavel not in df_metas_mes['Responsável'].values:
                    continue

                # Verificar se há uma meta para o responsável no mês
                meta_responsavel = df_metas_mes.loc[df_metas_mes['Responsável'] == responsavel]['Meta'].values
                if meta_responsavel.size > 0:
                    meta_responsavel = meta_responsavel[0]
                    
                    if meta_responsavel == 0:
                        realizado_percentual = 0.
                    else:
                        realizado_percentual = round(float((valor_realizado / meta_responsavel) * 100), 2)
                else:
                    realizado_percentual = 0.0

                # Adicionar a barra ao gráfico
                fig.add_trace(go.Bar(
                    x=[responsavel],
                    y=[realizado_percentual],
                    name=responsavel,
                    marker_color=f'#4A0A86',
                    text=f'{realizado_percentual}%',
                    textposition='outside',
                    width=[bar_width] * len(df_realizado_completo)
                ))

            # Atualizar o layout
            fig.update_layout(
                title=f'Percentual da Meta Alcançada por Vendedor - {mes}',
                title_font_size=20,
                title_x=0,
                yaxis=dict(title='Percentual (%)', range=[0, 100]),
                xaxis=dict(title='Responsável'),
                showlegend=False
            )
            show_fig = True
        else:
            st.warning('O mês selecionado não possui metas cadastradas.')
            fig = go.Figure()
    else:
        st.warning('Por favor, selecione datas dentro do mesmo mês.')
        fig = go.Figure()

    return show_fig, fig

def get_fig_receitas():
    receita_meses = {}
    
    for meses_atras in range(6, -1, -1):
        if data_inicial.month - meses_atras <= 0:
            receita_meses[months[str(data_inicial.month - meses_atras + 12).zfill(2)]] = get_receita_total(df_total[(df_total['Data de fechamento'].dt.month == data_inicial.month - meses_atras + 12) & (df_total['Data de fechamento'].dt.year == data_inicial.year - 1)])
        else:
            receita_meses[months[str(data_inicial.month - meses_atras).zfill(2)]] = get_receita_total(df_total[(df_total['Data de fechamento'].dt.month == data_inicial.month - meses_atras) & (df_total['Data de fechamento'].dt.year == data_inicial.year)])
        
        fig = go.Figure()
        fig.add_trace(go.Line(
            x=[months for months in receita_meses.keys()],
            y=[df_receita["Valor Total"].sum() for df_receita in receita_meses.values()],
            mode='lines+markers+text',
            marker=dict(color='#4A0A86'),
            name='Receita Total',
            text = [f'R$ {df_receita["Valor Total"].sum():,.2f}' if mes == months[str(data_inicial.month).zfill(2)] else '' for mes, df_receita in receita_meses.items()],
            textposition='top center',
            textfont=dict(
            family="sans serif",
            size=14,
            color="black"
        )
        ))
        fig.update_layout(
            title='Receita Total - Últimos 6 meses',
            xaxis_title='Mês',
            yaxis_title='Valor Total (R$)',
            title_font_size=20,
            title_x=0,
            showlegend=False,
            yaxis=dict(
                    range=[0, max([df_receita["Valor Total"].sum() for df_receita in receita_meses.values()]) * 1.1]  # Adjust the y-axis range
                ),
            xaxis=dict(
                    range=[-0.5, 7]  # Adjust the x-axis range
            )
        )
        
        fig.update_traces(
                marker_line_color='black', 
                marker_line_width=1,
            )
    return fig

def plot_vendedores_scatter_heatmap(df):
    # Calcula a taxa de conversão por vendedor
    taxa_conversao_responsavel = get_conversao_por_vendedor(df)[0]
    qtde_vendida = get_conversao_por_vendedor(df)[1]
    
    # Calcula o ticket médio por vendedor
    df_ticket_medio_por_vendedor = get_ticket_medio_por_vendedor(df)
    
    
    if taxa_conversao_responsavel.empty or df_ticket_medio_por_vendedor.empty:
        st.warning('Não há dados para exibir.')
        fig = go.Figure()
        return fig
    
    # Junta os dois DataFrames pelo nome do vendedor
    df_combined = pd.merge(
        taxa_conversao_responsavel.reset_index(), 
        df_ticket_medio_por_vendedor, 
        on='Responsável'
    )
    
        
    # Renomeia as colunas para facilitar o entendimento
    df_combined.columns = ['Responsável', 'Taxa de Conversão', 'Ticket Médio']
    df_combined['QTDE'] = qtde_vendida.values
    
    # Calcula o Indicador
    df_combined['Indicador'] = df_combined['Taxa de Conversão'] * df_combined['Ticket Médio'] * df_combined['QTDE']
    
    # Gera o scatter plot com marcadores quadrados grandes
    scatter_fig = px.scatter(
        df_combined,
        x='Taxa de Conversão',
        y='Ticket Médio',
        text='Responsável',
        size='Indicador',  # Tamanho do quadrado baseado no Indicador
        color='Indicador',  # Cor baseada no Indicador
        color_continuous_scale='Viridis',  # Esquema de cores
        labels={
            'Taxa de Conversão': 'Taxa de Conversão (%)',
            'Ticket Médio': 'Ticket Médio (R$)',
            'Indicador': 'Indicador (Taxa de Conversão * Ticket Médio * QTDE Vendas)',
        },
        title='Mapa dos Vendedores - Taxa de Conversão x Ticket Médio',
    ).update_traces(
        marker=dict(sizemode='area'),
        textposition='top center',
        textfont=dict(
            size=14,
            color="black"
        ),
        
        
    ).update_layout(
        xaxis_nticks=10,
        yaxis_nticks=10,
        # height=600,
        # width=800,
        coloraxis_showscale=False,
        xaxis=dict(
            range=[-0.001, max(df_combined['Taxa de Conversão']) * 1.2],
            tickformat=".0%"
        ),
        yaxis=dict(
            range=[-0.001, max(df_combined['Ticket Médio']) * 1.2],
        ),
        title={
            'font': {
                'size': 20  # Altere o valor para o tamanho desejado
            }
        }
    )    
    return scatter_fig
################################################

if not flag_data_final_maior_que_inicial:
    ############# Gráficos ##############
    ########### BOTÃO PARA RECARREGAR OS DADOS ########
    st.sidebar.markdown("")
    if st.sidebar.button('Recarregar Planilha'):
        st.cache_data.clear()  # Reseta o cache
    col11, col22 = st.columns([2, 1])

    with col11:
        st.plotly_chart(get_fig_metas2(), use_container_width=True)
    with col22:
        st.plotly_chart(get_fig_receitas(), use_container_width=True)
    st.divider()

    col1, col2 = st.columns(2, gap='large')
    with col1:
        st.subheader('TAXA DE CONVERSÃO POR VENDEDOR')
        if performance_estado.empty or performance_etapa.empty:
            st.warning('Não há dados para exibir.')
        
        col1c, col1d = st.columns(2)
        with col1c:
            if not performance_estado.empty:
                if responsavel_conversao == 'Todos':
                    st.metric('Vendas realizadas', df[df['Estado'] == 'Vendida'].shape[0])
                else:
                    st.metric('Vendas realizadas', fechados_por_responsavel[responsavel_conversao])
                
        with col1d:
            if not performance_etapa.empty:
                if responsavel_conversao == 'Todos':
                    st.metric('Taxa de Conversão Total (Ganho/Total) (%)', f'{round(taxa_conversao_total, 2)}%')
                else:
                    st.metric(f'Taxa de Conversão {responsavel_conversao.split(' ')[0]} (Ganho/Total) (%)', f'{round(taxa_conversao_etapa[responsavel_conversao], 2)}%')
            
        if not performance_etapa.empty:
            etapas_presentes = [etapa for etapa in performance_etapa.columns]
            
            if funil_selecionado == 'Todos':
                st.warning(f'Por favor, selecione um funil para exibir a performance.')
            else:
                order_funil = [etapa for etapa in funis[funil_selecionado] if funil_selecionado != 'Todos' and etapa in etapas_presentes]
                if responsavel_conversao == 'Todos':
                    df_etapas = performance_etapa[order_funil].transpose()
                    df_etapas = df_etapas.loc[order_funil]
                    st.dataframe(df_etapas, use_container_width=True)

                else:
                    df_etapas = performance_etapa.loc[responsavel_conversao]
                    st.dataframe(df_etapas, use_container_width=True)
        
        st.divider()
        st.plotly_chart(plot_vendedores_scatter_heatmap(df), use_container_width=True)

    with col2:
        st.subheader('VENDAS POR VENDEDORES')
        if not df[df['Estado'] == 'Vendida'].empty:
            df_vendedores_vendidas = df[df['Estado'] == 'Vendida'].groupby('Responsável').size().to_frame('Vendas Realizadas').sort_values('Vendas Realizadas', ascending=False)
            st.dataframe(df_vendedores_vendidas, use_container_width=True)
        else:
            st.warning('Não há dados para exibir.')
        
        st.divider()
        
        st.subheader('VENDAS PERDIDAS')
        
        if performance_estado.empty:
            st.warning('Não há dados para exibir.')
            
        if not performance_estado.empty:
            if responsavel_conversao == 'Todos':
                df_perdidas = df[df['Estado'] == 'Perdida']
            else:
                df_perdidas = df[(df['Responsável'] == responsavel_conversao) & (df['Estado'] == 'Perdida')]
            if not df_perdidas.empty:
                col2a, col2b = st.columns([1, 1.5])
                with col2a:
                    st.subheader('Total de vendas perdidas')
                    st.metric('Vendas perdidas', df_perdidas.shape[0], label_visibility='collapsed')      
                with col2b:
                    st.subheader('Top 3 Motivos de Perda')
                    df_perda = df_perdidas['Motivo de Perda'].value_counts().head(3)
                    df_perda.name = 'Quantidade'
                    st.dataframe(df_perda, use_container_width=True)
            else:
                st.warning('Não há dados para exibir.')
                                        
    st.divider()
    cola, colb, colc = st.columns([1, 1.5, 1])
    with cola:
        col1aa, col1ab = st.columns(2)
        with col1aa:
            # Criar um dropdown para selecionar o número de produtos a exibir
            tops = st.selectbox('Top Produtos', [5, 10, 15, 20, 50], index=0)
    with colb:
        st.subheader('PERFORMANCE DE PRODUTOS')
    st.plotly_chart(get_fig_metas1(df_realizado_total.sort_values('Valor Total', ascending=False).head(tops)), use_container_width=True)