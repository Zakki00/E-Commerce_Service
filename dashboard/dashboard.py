import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from tqdm import tqdm

# Membaca dan menggabungkan data
st.title("Dashboard Analisis Data Produk")

data_direktori = Path('data')
csv_files = list(data_direktori.glob('*.csv'))

if not data_direktori.exists() or not csv_files:
    st.error("Tidak ditemukan file CSV dalam direktori data.")
else:
    list_data = []
    for file in tqdm(csv_files, desc="Membaca file CSV"):
        try:
            df = pd.read_csv(file)
            list_data.append(df)
        except Exception as e:
            continue

    if list_data:
        table = list_data[0]
        for df in list_data[1:]:
            common_columns = list(set(table.columns) & set(df.columns))
            if common_columns:
                table = table.merge(df, on=common_columns, how='outer')

        # Mengatasi nilai yang hilang
        number_value = table.select_dtypes(include=['integer', 'float']).columns.to_list()
        table[number_value] = table[number_value].fillna(table[number_value].median())
        categories = table.select_dtypes(include=['object']).columns.tolist()
        for column in categories:
            value = table[column].value_counts().index[0]
            table[column] = table[column].fillna(value)

        # Menghapus duplikasi
        table = table.drop_duplicates()

        # Menghapus outliers
        def remove_outliers(df, column):
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
        
        cols_to_check = ['price', 'freight_value', 'payment_value', 'product_description_lenght',
                         'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm']
        for col in cols_to_check:
            table = remove_outliers(table, col)

        # Filter pada dashboard
        st.sidebar.header("Filter Data")
        price_range = st.sidebar.slider("Rentang Harga", float(table['price'].min()), float(table['price'].max()), 
                                        (float(table['price'].min()), float(table['price'].max())))
        category_filter = st.sidebar.multiselect("Kategori Produk", table['product_category_name_english'].unique())
        
        filtered_table = table[(table['price'] >= price_range[0]) & (table['price'] <= price_range[1])]
        if category_filter:
            filtered_table = filtered_table[filtered_table['product_category_name_english'].isin(category_filter)]
        
        # Konten 1: Distribusi Harga Produk
        st.subheader("Distribusi Harga Produk")
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.histplot(filtered_table['price'].dropna(), bins=50, kde=True, ax=ax)
        ax.set_xlabel("Harga Produk")
        ax.set_ylabel("Frekuensi")
        ax.set_title("Distribusi Harga Produk")
        st.pyplot(fig)

        # Konten 2: Kategori Produk Terpopuler
        st.subheader("10 Kategori Produk Paling Populer")
        df_product = filtered_table["product_category_name_english"].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.barplot(x=df_product.values, y=df_product.index, palette="viridis", ax=ax)
        ax.set_xlabel("Jumlah Produk")
        ax.set_ylabel("Kategori Produk")
        ax.set_title("10 Kategori Produk Paling Populer")
        st.pyplot(fig)

        # Konten 3: Tren Jumlah Pesanan per Bulan
        st.subheader("Tren Jumlah Pesanan per Bulan")
        table["order_purchase_timestamp"] = pd.to_datetime(table["order_purchase_timestamp"])
        table['order_month'] = table['order_purchase_timestamp'].dt.to_period('M')
        order_trend = table['order_month'].value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(x=order_trend.index.astype(str), y=order_trend.values, marker="o", ax=ax)
        ax.set_xlabel("Bulan")
        ax.set_ylabel("Jumlah Pesanan")
        ax.set_title("Tren Jumlah Pesanan per Bulan")
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Konten 4: Distribusi Skor Ulasan Produk
        st.subheader("Distribusi Skor Ulasan Produk")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.countplot(x=filtered_table["review_score"].dropna(), palette="coolwarm", ax=ax)
        ax.set_xlabel("Skor Ulasan")
        ax.set_ylabel("Jumlah")
        ax.set_title("Distribusi Skor Ulasan Produk")
        st.pyplot(fig)

        # Konten 5: Kota dengan Penjual Terbanyak
        st.subheader("10 Kota dengan Penjual Terbanyak")
        seller_city_count = filtered_table["seller_city"].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x=seller_city_count.values, y=seller_city_count.index, palette="plasma", ax=ax)
        ax.set_xlabel("Jumlah Penjual")
        ax.set_ylabel("Kota")
        ax.set_title("10 Kota dengan Penjual Terbanyak")
        st.pyplot(fig)

        st.write("Sumber Data: CSV dalam direktori data/")
