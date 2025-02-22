import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path
from tqdm import tqdm


data_direktori = Path('../data')
csv_files = list(data_direktori.glob('*.csv'))

list_data = [pd.read_csv(file) for file in tqdm(csv_files, desc="Membaca file CSV")]

if list_data:
    table = pd.concat(list_data, ignore_index=True)
else:
    st.error("Tidak ada data yang berhasil dibaca.")
    st.stop()

num_cols = table.select_dtypes(include=['number']).columns.to_list()
table[num_cols] = table[num_cols].fillna(table[num_cols].median())

cat_cols = table.select_dtypes(include=['object']).columns.to_list()
for col in cat_cols:
    table[col].fillna(table[col].mode()[0], inplace=True)


table = table.drop_duplicates()

def remove_outliers(df, column):
    Q1, Q3 = df[column].quantile([0.25, 0.75])
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

cols_to_check = ['price', 'freight_value', 'payment_value',
                 'product_description_lenght', 'product_weight_g',
                 'product_length_cm', 'product_height_cm', 'product_width_cm']
for col in cols_to_check:
    table = remove_outliers(table, col)

if 'order_purchase_timestamp' in table.columns:
    table['order_purchase_timestamp'] = pd.to_datetime(table['order_purchase_timestamp'])
    table['purchase_month'] = table['order_purchase_timestamp'].dt.to_period('M').astype(str)

st.title('Dashboard Penjualan Produk')
st.write("Dashboard ini menampilkan berbagai visualisasi terkait data penjualan produk berdasarkan kategori, lokasi, dan metode pembayaran.")

st.sidebar.header("Filter Data")
category_filter = st.sidebar.multiselect("Pilih Kategori Produk", table['product_category_name'].unique())
city_filter = st.sidebar.multiselect("Pilih Kota Pelanggan", table['customer_city'].unique())
payment_filter = st.sidebar.multiselect("Pilih Metode Pembayaran", table['payment_type'].unique())

filtered_table = table.copy()
if category_filter:
    filtered_table = filtered_table[filtered_table['product_category_name'].isin(category_filter)]
if city_filter:
    filtered_table = filtered_table[filtered_table['customer_city'].isin(city_filter)]
if payment_filter:
    filtered_table = filtered_table[filtered_table['payment_type'].isin(payment_filter)]

st.subheader("Jumlah Pembelian Produk Berdasarkan Kategori Tiap Bulan")
st.write("Grafik ini menunjukkan jumlah pembelian produk berdasarkan kategori setiap bulan. Dengan grafik ini, Anda dapat melihat tren penjualan berdasarkan kategori produk yang berbeda.")
monthly_category_counts = filtered_table.groupby(['purchase_month', 'product_category_name'])['order_item_id'].count().reset_index()
pivot_data = monthly_category_counts.pivot(index='purchase_month', columns='product_category_name', values='order_item_id').fillna(0)
fig, ax = plt.subplots(figsize=(14, 6))
colors = plt.cm.tab20(np.linspace(0, 1, len(pivot_data.columns)))

bottoms = np.zeros(len(pivot_data.index))
for i, column in enumerate(pivot_data.columns):
    ax.bar(pivot_data.index, pivot_data[column], bottom=bottoms, label=column, color=colors[i])
    bottoms += pivot_data[column]

ax.set_xlabel('Bulan Pembelian')
ax.set_ylabel('Jumlah Pembelian')
plt.xticks(rotation=45)
ax.legend(title='Kategori Produk', bbox_to_anchor=(1, 1), loc='upper left')
st.pyplot(fig)

st.subheader("Top 10 Kota dengan Jumlah Transaksi Terbanyak")
st.write("Grafik ini menunjukkan kota-kota dengan jumlah transaksi terbanyak. Kota-kota ini adalah pusat utama dari aktivitas pembelian dalam dataset.")
top_cities = filtered_table.groupby('customer_city')['order_id'].nunique().nlargest(10)
fig2, ax2 = plt.subplots(figsize=(10, 6))
sns.barplot(x=top_cities.values, y=top_cities.index, palette="rocket", ax=ax2)
ax2.set_xlabel("Jumlah Transaksi")
ax2.set_ylabel("Kota Pelanggan")
st.pyplot(fig2)

st.subheader("Distribusi Metode Pembayaran")
st.write("Grafik ini menunjukkan distribusi metode pembayaran yang digunakan oleh pelanggan. Informasi ini membantu dalam memahami preferensi pelanggan dalam melakukan transaksi.")
payment_counts = filtered_table['payment_type'].value_counts()
fig3, ax3 = plt.subplots(figsize=(10, 6))
sns.barplot(x=payment_counts.index, y=payment_counts.values, palette="viridis", ax=ax3)
ax3.set_xlabel("Metode Pembayaran")
ax3.set_ylabel("Jumlah Transaksi")
st.pyplot(fig3)
