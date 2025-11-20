import pandas as pd
import streamlit as st
import plotly.express as px 
import requests

st.set_page_config(layout= 'wide')

st.title('Sales Dashboard :shopping_cart:')

def formata_numero(valor, prefixo =''):
    for unidade in ['', 'mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

url = 'https://labdados.com/produtos'

# Barra Lateral
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sul', 'Sudeste']

st.sidebar.title('Filtros')

regiao = st.sidebar.selectbox('Região', regioes)
if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao':regiao.lower(), 'ano':ano}
response = requests.get(url, params= query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]
## Métricas principais
## Tabelas
### Tabelas de receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending= False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending = False)

# receita_vendedor = dados.groupby('Vendedor')[['Preço']].sum().sort_values(by='Preço', ascending=False)

###Tabelas de quantidade de vendas
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)

### Tabelas de vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

### Gráficos
fig_estado = px.bar(receita_estados.head(5), 
                    x='Local da compra', 
                    y='Preço', 
                    title='Receita por Estado', 
                    text_auto='.2s')
fig_estado.update_layout(yaxis_title='Receita')

fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat = 'lat',
                                  lon = 'lon',
                                  scope = 'south america',
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name ='Local da compra', 
                                  hover_data={'lat':False, 'lon':False}, 
                                  title='Receita por Estado', 
                                  )


fig_receita_mensal = px.line(receita_mensal, 
                             x='Mes', 
                             y='Preço',
                             markers=True,
                             range_y=(0, receita_mensal['Preço'].max()),
                             color='Ano',
                             line_dash='Ano',
                             title='Receita Mensal')
fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_receita_categoria = px.bar(receita_categorias.head(),
                               text_auto= True,
                               title='Receita por Categoria')
fig_receita_categoria.update_layout(yaxis_title='Receita')  

# fig_receita_vendedor = px.bar(receita_vendedor.head(),
#                                text_auto= True,
#                                title='Receita por Vendedor')


## Visualização no Streamlit

aba1, aba2, aba3 = st.tabs(['Receitas', 'Quantidade de  Vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Total Receita', formata_numero(dados["Preço"].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_categoria, use_container_width=True)
    with coluna2:
            st.metric('Total de Produtos', formata_numero(dados.shape[0]))
            st.plotly_chart(fig_receita_mensal, use_container_width=True)
            st.plotly_chart(fig_estado, use_container_width=True)

with aba2: # Qtd Vendas
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Total Receita', formata_numero(dados["Preço"].sum(), 'R$'))

    with coluna2:
            st.metric('Total de Produtos', formata_numero(dados.shape[0]))
    st.dataframe(dados)
          
with aba3: # Vendedores

    qtd_vendedores = st.number_input('Número de Vendedores a exibir', min_value=2, max_value=10, value=5)
    
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Total Receita', formata_numero(dados["Preço"].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                        x= 'sum',
                                        y= vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                        text_auto= True,
                                        title=f'Receita dos Top {qtd_vendedores} Vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores)

    with coluna2:
        st.metric('Total de Produtos', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                        x= 'count',
                                        y= vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                        text_auto= True,
                                        title=f'Receita dos Top {qtd_vendedores} Vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores)

# st.dataframe(receita_vendedor.reset_index(), use_container_width=False)




# enable = st.checkbox('Camera')
# picture = st.camera_input("Take a picture", disabled=not enable)

# if picture:
#     st.image(picture)

