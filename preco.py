import streamlit as st
import pandas as pd
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Consulta de Campo - Preço Sugerido",
    layout="centered",
    page_icon="📱"
)

# --- 2. ESTILO VISUAL ---
st.markdown("""
<style>
.stApp { background-color: #F8F9FA; color: #2D3748; }
.produto-card {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E0;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    text-align: center;
    margin-top: 15px;
}
.caixa-preco-central {
    background: #E2E8F0;
    border: 2px solid #CBD5E0;
    padding: 20px;
    border-radius: 16px;
    margin-top: 20px;
    text-align: center;
}
.titulo-preco {
    color: #4A5568;
    font-size: 13px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.valor-preco {
    color: #000000;
    font-size: 46px;
    font-weight: 900;
    margin-top: 5px;
    line-height: 1.1;
}
</style>
""", unsafe_allow_html=True)

# --- 3. CARREGAR A BASE UNIFICADA ---
@st.cache_data
def carregar_dados():
    arquivo_base = "boneco_com_valor_h.xlsx"
    if not os.path.exists(arquivo_base):
        return None
    df = pd.read_excel(arquivo_base, sheet_name='Detalhado')
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

df_produtos = carregar_dados()

# --- 4. FUNÇÃO DE BUSCA DA IMAGEM ---
PASTA_FOTOS = "mockups_produtos"

def obter_caminho_imagem(codigo_minassal):
    extensoes = ['.png', '.jpg', '.jpeg', '.webp', '.PNG', '.JPG', '.JPEG']
    cod_limpo = str(codigo_minassal).strip().replace('.0', '')
    
    if os.path.exists(PASTA_FOTOS):
        for ext in extensoes:
            caminho_completo = os.path.join(PASTA_FOTOS, f"{cod_limpo}{ext}")
            if os.path.exists(caminho_completo):
                return caminho_completo
    return None

# --- 5. INTERFACE PRINCIPAL ---
st.markdown("<h2 style='text-align: center; color: #1A202C;'>📱 Consulta em Campo</h2>", unsafe_allow_html=True)

# Abas para alternar entre Digitação/EAN e Câmera de Foto
aba1, aba2 = st.tabs(["🔍 Digitar / EAN", "📸 Câmera (Tirar Foto)"])

codigo_busca = ""

with aba1:
    st.markdown("<p style='font-size: 13px; color: #718096;'>Digite o código Minassal, SKU ou EAN do produto:</p>", unsafe_allow_html=True)
    input_texto = st.text_input("Código ou EAN:", placeholder="Ex: 99176...", label_visibility="collapsed")
    if input_texto:
        codigo_busca = input_texto

with aba2:
    st.markdown("<p style='font-size: 13px; color: #718096;'>Se a embalagem estiver difícil de focar, tire uma foto para conferir o produto visualmente ou verifique o número impresso:</p>", unsafe_allow_html=True)
    foto_enviada = st.camera_input("Tirar foto do produto/etiqueta")
    if foto_enviada:
        st.success("📸 Foto capturada com sucesso! Use a aba de digitação se preferir buscar pelo código visualizado na embalagem.")

# --- 6. PROCESSAR A BUSCA E EXIBIR O PRODUTO ---
if codigo_busca:
    busca = str(codigo_busca).strip().replace('.0', '')
    
    if df_produtos is not None:
        df_match = df_produtos[
            (df_produtos['COD. EAN'].astype(str).str.strip() == busca) |
            (df_produtos['SKU'].astype(str).str.strip() == busca) |
            (df_produtos['CODIGO'].astype(str).str.strip() == busca)
        ]

        if not df_match.empty:
            row = df_match.iloc[0]
            
            nome_comercial = row.get('NOME COMERCIAL', row.get('DESCRICAO', 'Produto'))
            ean_val = str(row.get('COD. EAN', 'N/D')).replace('.0', '')
            cod_minassal = str(row.get('CODIGO', 'N/D')).replace('.0', '')
            familia_val = str(row.get('FAMILIA', 'Geral'))
            
            preco_mg = row.get('VALOR_RECOMENDADO_MG', 0.0)
            caminho_img = obter_caminho_imagem(cod_minassal)

            with st.container():
                st.markdown("<div class='produto-card'>", unsafe_allow_html=True)
                
                if caminho_img and os.path.exists(caminho_img):
                    st.image(caminho_img, use_container_width=True)
                else:
                    st.info("🖼️ Imagem não encontrada na pasta para este código.")
                
                st.markdown(f"<h3 style='text-align: center; color: #1A202C; margin-top: 10px;'>{nome_comercial}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; font-size: 13px; color: #718096;'><b>Família:</b> {familia_val} | <b>Cód:</b> {cod_minassal} | <b>EAN:</b> {ean_val}</p>", unsafe_allow_html=True)
                
                if pd.notna(preco_mg) and preco_mg > 0:
                    st.markdown(
                        f"""
                        <div class="caixa-preco-central">
                            <div class="titulo-preco">💰 Preço Sugerido de Ponta (MG)</div>
                            <div class="valor-preco">R$ {preco_mg:,.2f}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.warning("⚠️ Preço sugerido não disponível para este item.")
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error(f"❌ Nenhum produto encontrado com o código **{busca}**.")
