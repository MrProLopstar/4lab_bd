import os
import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt

engine = create_engine('postgresql://postgres@localhost:5432/mydatabase')
conn = engine.connect()

st.title('Отчёты — визуализация')

diag_path = 'er_diagram.png'
if os.path.exists(diag_path):
    st.image(diag_path, use_container_width=True)
else:
    st.warning('ER-диаграмма не найдена, пропускаем изображение.')

@st.cache_data
def query_df(sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, conn)

st.sidebar.header('Выбор задания')
option = st.sidebar.selectbox('', [
    'Доля типов работ',
    'Итоги по мастерам',
    'Топ-10 клиентов 20–45 лет',
    'Работы клиентов с начала года',
    'Клиенты с общими затратами > среднего',
    'Все клиенты',
    'Все мастера',
    'Все заказы',
])

if option == 'Доля типов работ':
    sql = """
        SELECT work_type,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percent_share
        FROM serviceorders
        GROUP BY work_type;
    """
    df = query_df(sql)
    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots()
    ax.pie(df['percent_share'], labels=df['work_type'], autopct='%1.1f%%')
    ax.set_title('Доля типов работ, %')
    st.pyplot(fig)

elif option == 'Итоги по мастерам':
    sql = """
        SELECT m.full_name AS master,
               COUNT(s.order_id) AS total_orders,
               SUM(s.cost)       AS total_cost
        FROM serviceorders s
        JOIN masters m ON s.master_id = m.master_id
        GROUP BY m.full_name
        ORDER BY total_cost DESC;
    """
    df = query_df(sql)
    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots()
    ax.bar(df['master'], df['total_cost'])
    ax.set_ylabel('Суммарная стоимость')
    ax.set_xticklabels(df['master'], rotation=45, ha='right')
    st.pyplot(fig)

elif option == 'Топ-10 клиентов 20–45 лет':
    sql = """
        SELECT c.full_name,
               COUNT(s.order_id) AS total_orders,
               SUM(s.cost)       AS total_cost
        FROM clients c
        JOIN serviceorders s ON c.client_id = s.client_id
        WHERE AGE(current_date, c.birth_date)
              BETWEEN INTERVAL '20 years' AND INTERVAL '45 years'
        GROUP BY c.client_id, c.full_name
        ORDER BY total_orders DESC
        LIMIT 10;
    """
    df = query_df(sql)
    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots()
    ax.bar(df['full_name'], df['total_orders'])
    ax.set_ylabel('Количество заказов')
    ax.set_xticklabels(df['full_name'], rotation=45, ha='right')
    st.pyplot(fig)

elif option == 'Работы клиентов с начала года':
    sql = """
        SELECT c.full_name,
               COUNT(DISTINCT s.work_type) AS unique_work_types
        FROM clients c
        JOIN serviceorders s ON c.client_id = s.client_id
        WHERE s.order_received >= DATE_TRUNC('year', CURRENT_DATE)
        GROUP BY c.client_id, c.full_name
        ORDER BY unique_work_types DESC;
    """
    df = query_df(sql)
    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots()
    ax.bar(df['full_name'], df['unique_work_types'])
    ax.set_ylabel('Различных типов работ')
    ax.set_xticklabels(df['full_name'], rotation=45, ha='right')
    st.pyplot(fig)

elif option == 'Клиенты с общими затратами > среднего':
    sql = """
        SELECT c.full_name,
               SUM(s.cost) AS total_cost
        FROM clients c
        JOIN serviceorders s ON c.client_id = s.client_id
        GROUP BY c.client_id, c.full_name
        HAVING SUM(s.cost) > (
            SELECT AVG(cost) FROM serviceorders
        );
    """
    df = query_df(sql)
    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots()
    ax.bar(df['full_name'], df['total_cost'])
    ax.set_ylabel('Суммарные затраты')
    ax.set_xticklabels(df['full_name'], rotation=45, ha='right')
    st.pyplot(fig)

elif option == 'Все клиенты':
    df = query_df("SELECT * FROM clients;")
    st.dataframe(df, use_container_width=True)

elif option == 'Все мастера':
    df = query_df("SELECT * FROM masters;")
    st.dataframe(df, use_container_width=True)

elif option == 'Все заказы':
    df = query_df("SELECT * FROM serviceorders;")
    st.dataframe(df, use_container_width=True)
