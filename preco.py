import streamlit as st
import pandas as pd
import os
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO DA PÁGINA (Layout Mobile Centralizado) ---
st.set_page_config(
    page_title="Consulta de Campo - Preço Sugerido",
    layout="centered",
    page_icon="📱"
)

# --- 2. ESTILO VISUAL ---
st.markdown("""
<style>
.stApp { background-color: #F8F9FA; color: #2D3748; }
[data-testid="stSidebar"] { border-right: 1px solid #E2E8F0; background-color: #FFFFFF; }
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
st.markdown("<p style='text-align: center; font-size: 14px; color: #718096;'>Aponte a câmera para o código de barras ou digite o código abaixo.</p>", unsafe_allow_html=True)

# Componente HTML5 nativo para leitura de código de barras via Câmera do Celular
barcode_component = components.html(
    """
    <div style="text-align: center; font-family: sans-serif;">
        <button id="start-scan" style="background-color: #319795; color: white; border: none; padding: 12px 20px; font-size: 16px; font-weight: bold; border-radius: 12px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            📷 Abrir Câmera para Escanear
        </button>
        <div id="reader" style="width: 100%; max-width: 400px; margin: 15px auto;"></div>
    </div>
    
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
        const button = document.getElementById('start-scan');
        let html5QrCode;
        
        button.onclick = function() {
            button.style.display = 'none';
            html5QrCode = new Html5Qrcode("reader");
            const config = { fps: 10, qrbox: { width: 250, height: 150 } };
            
            html5QrCode.start({ facingMode: "environment" }, config, (decodedText) => {
                // Quando ler o código de barras com sucesso, envia para o Streamlit via URL parameter
                html5QrCode.stop().then(() => {
                    const url = new URL(window.parent.location.href);
                    url.searchParams.set('barcode', decodedText);
                    window.parent.location.href = url.href;
                }).catch((err) => {
                    console.error("Erro ao parar a câmera", err);
                });
            }, (errorMessage) => {
                // Erros de leitura quadro a quadro são ignorados para fluidez
            }).catch((err) => {
                alert("Erro ao acessar a câmera. Verifique as permissões do navegador.");
                button.style.display = 'block';
            });
        };
    </script>
    """,
    height=120
)

# Captura o código vindo da câmera ou da digitação manual
params = st.query_params
codigo_camera = params.get("barcode", "")

# Input manual / Pistola Bluetooth (também recebe o código da câmera automaticamente)
codigo_input = st.text_input("🔍 Código do Produto / EAN / SKU:", value=codigo_camera, placeholder="Digite, escaneie ou use a câmera...")

if codigo_input:
    busca = str(codigo_input).strip().replace('.0', '')
    
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
                
                # Imagem grande centralizada
                if caminho_img and os.path.exists(caminho_img):
                    st.image(caminho_img, use_container_width=True)
                else:
                    st.info("🖼️ Imagem não encontrada na pasta para este código.")
                
                # Nome do Produto em destaque centralizado
                st.markdown(f"<h3 style='text-align: center; color: #1A202C; margin-top: 10px;'>{nome_comercial}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; font-size: 13px; color: #718096;'><b>Família:</b> {familia_val} | <b>Cód:</b> {cod_minassal} | <b>EAN:</b> {ean_val}</p>", unsafe_allow_html=True)
                
                # Bloco de Preço Gigante, Preto e Centralizado
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