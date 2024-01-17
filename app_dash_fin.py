# Imports
import pandas            as pd
import streamlit         as st
import numpy             as np
#import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline as py

from datetime            import datetime
from PIL                 import Image
from io                  import BytesIO
from plotly.subplots import make_subplots
from plotly import tools

# Função para ler os dados
@st.cache_data
def load_data(file_data):
    try:
        dateparse = lambda x: datetime.strptime(x, '%d/%m/%Y')
        df = pd.read_csv(file_data, sep = ';', encoding = 'utf-8', 
                 parse_dates=['data', 'exercicio'],date_parser=dateparse, engine='openpyxl')  
        
        df['movimentacao'] = df['movimentacao'].apply(lambda x: float(x.replace(".","").replace(",",".")))
        df['saldo'] = df['saldo'].apply(lambda x: float(x.replace(".","").replace(",",".")))
        df_rend['movimentacao'] = df_rend['movimentacao'].apply(lambda x: float(x.replace(".","").replace(",",".")))
        df_rend['saldo'] = df_rend['saldo'].apply(lambda x: float(x.replace(".","").replace(",",".")))
        
        return df
    except:
        return pd.read_excel(file_data,
              sheet_name='fluxo_fin', header=1)
    

# Função para filtrar baseado na multiseleção de categorias
@st.cache_data
def multiselect_filter(relatorio, col, selecionados):
    if 'all' in selecionados:
        return relatorio
    else:
        return relatorio[relatorio[col].isin(selecionados)].reset_index(drop=True)
    


# Função principal da aplicação
def main():
    # Configuração inicial da página da aplicação
    st.set_page_config(page_title = 'Dash_fin', \
        layout="wide",
        initial_sidebar_state='expanded'
    )
    
    # Botão para carregar arquivo na aplicação
    st.sidebar.write("## Suba o arquivo")
    data_file_1 = st.sidebar.file_uploader("Suba Irene", type = ['csv','xlsx'])

    # Verifica se há conteúdo carregado na aplicação
    if (data_file_1 is not None):

        df_raw = load_data(data_file_1)
        df = df_raw.copy()
        df_rend = df_raw.copy()        
 
        with st.sidebar.form('my_form'):
            st.write("Inside the form")
            dia_final = df['exercicio'].max()
            data_inicial = df['exercicio'].min()
            st.write('Última data da base de dados: ', dia_final)

            df['mes'] = df.data.apply(lambda x: x.month)
            df['ano'] = df.data.apply(lambda x: x.year)
            df_rend['mes'] = df_rend.data.apply(lambda x: x.month)
            df_rend['ano'] = df_rend.data.apply(lambda x: x.year)

            lista_mes = df.mes.unique().tolist()
            lista_mes.append('all')
            mes_selecionado =  st.multiselect('Mês', lista_mes, [df['mes'].max()])

            lista_ano = df.ano.unique().tolist()
            lista_ano.append('all')
            ano_selecionado =  st.multiselect("Ano", lista_ano, df['ano'].max())

            # encadeamento de métodos para filtrar a seleção
            df = (df.pipe(multiselect_filter, 'mes', mes_selecionado)
                                .pipe(multiselect_filter, 'ano', ano_selecionado))

            # Every form must have a submit button.
            submit_button = st.form_submit_button(label='Aplicar')
        
        col1, col2 = st.columns(2)
        col1.write('# Dados:')
        col2.write('#### Maiores Gastos:')  
  
        saidas = df[df['tipo']=='Saída']
        entradas = df[df['tipo']=='Entrada']

        maiores_saidas = pd.pivot_table(saidas, index=['mes', 'ano'], columns=['segmento'], values='movimentacao')
        maiores_saidas_stack = maiores_saidas.fillna(0).stack().reset_index()   
        
        with col1:
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write('### Entradas: R${}'.format(round(df[df['tipo']=='Entrada'].movimentacao.sum(),2)))
            st.write('### Saídas: R${}'.format(round(df[df['tipo']=='Saída'].movimentacao.sum(),2)))
            saldo_mes = round(df[df['tipo']=='Entrada'].movimentacao.sum() - df[df['tipo']=='Saída'].movimentacao.sum(),2)
            st.write('### Saldo: R${}'.format(saldo_mes))
            st.write('### Total em caixa: R${}'.format(round(df.saldo.iloc[-1],2)))

        with col2:
            # Gráficos de pizza       
            mes = [df['mes'][0]]
            ano = [df['ano'][0]]

            gastos_mes = maiores_saidas_stack[(maiores_saidas_stack['mes'].isin(mes)) & (maiores_saidas_stack['ano'].isin(ano))]

            lista_gastos_mes = gastos_mes.groupby('segmento').sum().sort_values(0, ascending =  False).head(7)
            # lista_gastos_media = df_rend[df_rend['tipo']=='Saída'].groupby('segmento').mean().sort_values('movimentacao', ascending =  False).head(7)

            # trace1 = go.Pie(values=lista_gastos_media['movimentacao'], labels=lista_gastos_media.index,
            # domain=dict(x=[0, 0.5]),
            # hoverinfo="label+percent+name",
            # title = "Média dos maiores gastos")

            # trace2 = go.Pie(values=lista_gastos_mes[0], labels=lista_gastos_mes.index,
            # domain=dict(x=[0.5, 1]),
            # hoverinfo="label+percent+name",
            # title = "Maiores gastos atuais")

            # layout = go.Layout()
            # data = [trace1, trace2]
            # fig = go.Figure(data=data, layout=layout)
            # fig.update_traces(textposition='inside', textinfo='percent+label')
            
            fig = px.pie(lista_gastos_mes, values=lista_gastos_mes[0], names=lista_gastos_mes.index)
            fig.update_traces(textposition='inside', textinfo='percent+label')
           
            st.plotly_chart(fig, use_container_width=True)
            
        st.markdown("---")

        st.write('## Entradas x Saídas x Saldo')
        # Gráficos de Entradas x Saídas x Saldos

        saidas_rend = df_rend[df_rend['tipo']=='Saída']
        entradas_rend = df_rend[df_rend['tipo']=='Entrada']
	    
        entradas_mes = entradas_rend[['tipo', 'segmento', 'meio', 'movimentacao',
       				      'saldo', 'mes', 'ano']].groupby('mes').sum()
        saidas_mes = saidas_rend[['tipo', 'segmento', 'meio', 'movimentacao',
       				  'saldo', 'mes', 'ano']].groupby('mes').sum()

        saldos = pd.merge(entradas_mes, saidas_mes, on = 'mes', how='inner')
        saldos['variacao'] = saldos.movimentacao_x - saldos.movimentacao_y
        saldos.columns= ['entradas', 'saldo_ent', 'ano_ent', 'saidas', 'saldo_sai', 'ano_sai', 'variacao']

        fig = px.bar(saldos, x=saldos.index, y=['entradas', 'saidas'])
        fig.add_scatter(x=saldos.index, y=saldos['variacao'], mode='lines+text', text=round(saldos.variacao,2), name = 'Saldo')
        fig.update_layout(title='Entradas x Saídas',
        yaxis_title='R$',
        plot_bgcolor = 'white',
        font = {'family': 'Arial','size': 12,'color': 'black'},
        colorway=["green"])
        st.plotly_chart(fig, use_container_width=True) 
        
        st.markdown("---")

        st.write('## Rendimentos')
        # Gráficos de Rendimentos
        rendimentos = pd.pivot_table(df_rend[df_rend['meio']=='rendimento'],index='exercicio', columns='segmento', values='movimentacao')
        new_row = pd.DataFrame({'bb fundo m mercados': 6000, 'bb fundo rf tesouro': 7000, 'bb lca': 9000, 'bi arx vision': 4000,
                    'bi inter cons': 2000, 'bi inter corp': 3000, 'nu caixinha': 30000, 'rico alzr11': 400, 'rico bcff11': 7000,
                    'rico hglg11': 2000, 'rico trend di':2000}, index=[0])
        rendimentos = pd.concat([new_row,rendimentos.loc[:]]).reset_index(drop=True)

        for i in range(0,len(rendimentos.columns)):
	        rendimentos[rendimentos.columns[i]+'_cumsum'] = rendimentos[rendimentos.columns[i]].cumsum()
             
                
        rendimentos_acum = rendimentos[['bb fundo m mercados_cumsum', 'bb fundo rf tesouro_cumsum',
										'bb lca_cumsum', 'bi arx vision_cumsum', 'bi inter cons_cumsum',
										'bi inter corp_cumsum', 'nu caixinha_cumsum', 'rico alzr11_cumsum',
										'rico bcff11_cumsum', 'rico hglg11_cumsum', 'rico trend di_cumsum']] 
             
        fig = px.bar(rendimentos_acum, x=rendimentos_acum.index, y=rendimentos_acum.columns)
        fig.update_layout(title='Rendimentos',
        yaxis_title='R$',
        xaxis_title='Meses',
        plot_bgcolor = 'white',
        font = {'family': 'Arial','size': 12,'color': 'black'})
        st.plotly_chart(fig, use_container_width=True) 

        fig = px.line(rendimentos_acum, x=rendimentos_acum.index, y=rendimentos_acum.columns, 
	                    markers = True)

        fig.update_layout(title='Rendimentos',
        yaxis_title='R$',
        xaxis_title='Meses',
        plot_bgcolor = 'white',
        font = {'family': 'Arial','size': 12,'color': 'black'})
        st.plotly_chart(fig, use_container_width=True) 
    
    else:
        st.markdown('Insira o arquivo na aba a esquerda')


if __name__ == '__main__':
	main()
    









