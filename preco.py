import streamlit as st
import pandas as pd
import unicodedata
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
    margin-bottom: 20px;
}
.caixa-preco-central {
    background: #E2E8F0;
    border: 2px solid #CBD5E0;
    padding: 16px;
    border-radius: 16px;
    margin-top: 15px;
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
    color: #047857;
    font-size: 42px;
    font-weight: 900;
    margin-top: 5px;
    line-height: 1.1;
}
</style>
""", unsafe_allow_html=True)

# --- 3. CARREGAR A BASE UNIFICADA ---
def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

@st.cache_data
def carregar_dados():
    arquivo_base = "boneco_com_valor_h.xlsx"
    if not os.path.exists(arquivo_base):
        return None
    df = pd.read_excel(arquivo_base, sheet_name='Detalhado')
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Campo unificado para busca em texto ultra rápida
    df['BUSCA_COMPLETA'] = df.apply(
        lambda r: normalizar_texto(
            f"{r.get('DESCRICAO', '')} {r.get('NOME COMERCIAL', '')} {r.get('FAMILIA', '')} "
            f"{r.get('CODIGO', '')} {r.get('COD. EAN', '')} {r.get('SKU', '')}"
        ),
        axis=1
    )
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
st.markdown("<p style='text-align: center; font-size: 13px; color: #718096;'>Digite os <b>dígitos finais do código</b> ou o <b>nome / peso</b> do produto:</p>", unsafe_allow_html=True)

codigo_busca = st.text_input("🔍 Buscar Produto:", placeholder="Ex: 214731, shih tzu 2.5, gastro feline, kitten...")

# --- 6. PROCESSAR A BUSCA INTELIGENTE HÍBRIDA ---
if codigo_busca and df_produtos is not None:
    busca_raw = str(codigo_busca).strip()
    busca_limpa = busca_raw.replace('.0', '').strip()
    
    # Se for estritamente numérico, prioriza terminação de código (EAN, SKU, Código Minassal)
    if busca_limpa.isdigit():
        df_match = df_produtos[
            (df_produtos['COD. EAN'].astype(str).str.strip().str.endswith(busca_limpa)) |
            (df_produtos['SKU'].astype(str).str.strip().str.endswith(busca_limpa)) |
            (df_produtos['CODIGO'].astype(str).str.strip().str.endswith(busca_limpa)) |
            (df_produtos['COD. EAN'].astype(str).str.strip() == busca_limpa) |
            (df_produtos['SKU'].astype(str).str.strip() == busca_limpa) |
            (df_produtos['CODIGO'].astype(str).str.strip() == busca_limpa)
        ]
    else:
        # Busca textual multi-termos (todas as palavras digitadas precisam estar no produto)
        tokens = [normalizar_texto(t) for t in busca_raw.split() if t.strip()]
        
        def match_tokens(texto_registro):
            texto_reg_pontos = texto_registro.replace(',', '.')
            for tok in tokens:
                tok_com_virgula = tok.replace('.', ',')
                tok_com_ponto = tok.replace(',', '.')
                if (tok not in texto_registro and 
                    tok_com_virgula not in texto_registro and 
                    tok_com_ponto not in texto_reg_pontos):
                    return False
            return True

        df_match = df_produtos[df_produtos['BUSCA_COMPLETA'].apply(match_tokens)]

    # Exibição dos resultados
    if not df_match.empty:
        if len(df_match) > 1:
            st.info(f"ℹ️ Encontramos **{len(df_match)} produtos**. Veja as opções abaixo:")
            
        for index, row in df_match.iterrows():
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
                    st.info("🖼️ Imagem não disponível.")
                
                st.markdown(f"<h3 style='text-align: center; color: #1A202C; margin-top: 10px;'>{nome_comercial}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; font-size: 13px; color: #718096;'><b>Família:</b> {familia_val} | <b>Cód:</b> {cod_minassal} | <b>EAN:</b> {ean_val}</p>", unsafe_allow_html=True)
                
                if pd.notna(preco_mg) and preco_mg > 0:
                    preco_formatado = f"R$ {preco_mg:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    st.markdown(f"""
                        <div class="caixa-preco-central">
                            <div class="titulo-preco">💰 Preço Sugerido de Ponta (MG)</div>
                            <div class="valor-preco">{preco_formatado}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Preço não disponível.")
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.error(f"❌ Nenhum produto encontrado para: **{codigo_busca}**.")
