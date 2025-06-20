import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import json

st.set_page_config(page_title="Monitor de Preços", layout="wide")
st.title("Monitor de Preços em Marketplaces")

# Sidebar: lista de produtos em JSON
produtos_input = st.sidebar.text_area(
    "Cole sua lista de produtos (JSON)", 
    value="""[
  {"marketplace": "Beleza na Web", "url": "https://www.belezanaweb.com.br/haya-lattafa-eau-de-parfum-perfume-feminino-100ml/ofertas-marketplace"},
  {"marketplace": "Riachuelo",     "url": "https://www.riachuelo.com.br/produto/lattafa-haya-eau-de-parfum-100ml-d7d65d0d35de4f91af3db1b07e1d18c1"}
]""",
    height=200
)
try:
    produtos = json.loads(produtos_input)
except json.JSONDecodeError:
    produtos = []
    st.sidebar.error("JSON inválido")

def checar_item(item):
    resp = requests.get(item["url"], headers={"User-Agent":"Mozilla/5.0"})
    html = resp.text
    disponivel, preco, vendedor = False, "—", item["marketplace"]

    if item["marketplace"] == "Beleza na Web":
        sellers = re.findall(r'Vendido por\s+([^<\n]+)', html)
        prices  = re.findall(r'R\$\s*[\d\.,]+', html)
        if prices:
            nums = [float(p.replace("R$","").replace(".","").replace(",", ".")) for p in prices]
            idx = nums.index(min(nums))
            disponivel, preco = True, prices[idx]
            if idx < len(sellers):
                vendedor = sellers[idx]

    elif item["marketplace"] == "Riachuelo":
        tag = BeautifulSoup(html, "html.parser").select_one("span.price-sales__value")
        if tag:
            disponivel, preco = True, tag.get_text(strip=True)

    return {
        "Timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Marketplace": item["marketplace"],
        "Disponível":  disponivel,
        "Preço":       preco,
        "Vendedor":    vendedor
    }

if st.sidebar.button("Rodar Monitoramento"):
    if not produtos:
        st.warning("Adicione pelo menos um produto em JSON na barra lateral.")
    else:
        resultados = [checar_item(p) for p in produtos]
        df = pd.DataFrame(resultados)
        st.dataframe(df, use_container_width=True)
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv_bytes, "monitoramento.csv", "text/csv")
