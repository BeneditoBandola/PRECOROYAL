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

# --- 2. ESTILO VISUAL, CORES E PADRONIZAÇÃO DE IMAGENS ---
st.markdown("""
<style>
.stApp { 
    background-color: #F1F5F9; 
    color: #1E293B; 
}
.produto-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-top: 4px solid #E2001A;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
    text-align: center;
    margin-top: 15px;
    margin-bottom: 22px;
}
/* Centraliza a imagem e força altura uniforme */
div[data-testid="stImage"] {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 10px;
}
div[data-testid="stImage"] img {
    max-height: 220px !important;
    max-width: 100% !important;
    object-fit: contain !important;
}
.caixa-preco-central {
    background: #F8FAFC;
    border: 1.5px solid #CBD5E1;
    border-top: 3px solid #E2001A;
    padding: 14px;
    border-radius: 12px;
    margin-top: 14px;
    text-align: center;
}
.titulo-preco {
    color: #475569;
    font-size: 11.5px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.valor-preco {
    color: #047857;
    font-size: 38px;
    font-weight: 900;
    margin-top: 2px;
    line-height: 1.1;
    font-family: monospace, sans-serif;
}
.badge-familia {
    display: inline-block;
    background-color: #E2E8F0;
    color: #334155;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11.5px;
    font-weight: 700;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# --- 3. CARREGAR A BASE UNIFICADA ---
def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

def limpar_campo_codigo(val):
    if pd.isna(val):
        return ""
    txt = str(val).strip()
    if txt.endswith('.0'):
        txt = txt[:-2]
    return txt

@st.cache_data
def carregar_dados():
    arquivo_base = "boneco_com_valor_h.xlsx"
    if not os.path.exists(arquivo_base):
        return None
    try:
        df = pd.read_excel(arquivo_base, sheet_name='Detalhado')
    except Exception:
        try:
            df = pd.read_excel(arquivo_base)
        except Exception as e:
            st.error(f"Erro ao abrir a planilha: {e}")
            return None

    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Padroniza os campos para evitar erros com .0
    for col in ['CODIGO', 'COD. EAN', 'SKU']:
        if col in df.columns:
            df[f"{col}_LIMPO"] = df[col].apply(limpar_campo_codigo)
        else:
            df[f"{col}_LIMPO"] = ""

    # Constrói o índice de busca textual rápida
    df['BUSCA_COMPLETA'] = df.apply(
        lambda r: normalizar_texto(
            f"{r.get('DESCRICAO', '')} {r.get('NOME COMERCIAL', '')} {r.get('FAMILIA', '')} "
            f"{r.get('CODIGO_LIMPO', '')} {r.get('COD. EAN_LIMPO', '')} {r.get('SKU_LIMPO', '')}"
        ),
        axis=1
    )
    return df

df_produtos = carregar_dados()

# --- 4. FUNÇÃO DE BUSCA DA IMAGEM ---
PASTA_FOTOS = "mockups_produtos"

def obter_caminho_imagem(codigo_identificador):
    extensoes = ['.png', '.jpg', '.jpeg', '.webp', '.PNG', '.JPG', '.JPEG']
    cod_limpo = str(codigo_identificador).strip().replace('.0', '')
    
    if os.path.exists(PASTA_FOTOS) and cod_limpo:
        for ext in extensoes:
            caminho_completo = os.path.join(PASTA_FOTOS, f"{cod_limpo}{ext}")
            if os.path.exists(caminho_completo):
                return caminho_completo
    return None

# --- 5. INTERFACE PRINCIPAL ---
st.markdown("<h2 style='text-align: center; color: #0F172A; margin-bottom: 2px;'>📱 Consulta em Campo</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 13px; color: #64748B;'>Digite os <b>dígitos finais do código</b> ou o <b>nome / peso</b> do produto:</p>", unsafe_allow_html=True)

codigo_busca = st.text_input("🔍 Buscar Produto:", placeholder="Ex: 214731, shih tzu 2.5, gastro feline, kitten...", label_visibility="collapsed")

# --- 6. PROCESSAR A BUSCA INTELIGENTE HÍBRIDA ---
if df_produtos is None:
    st.error("⚠️ Planilha `boneco_com_valor_h.xlsx` não encontrada no diretório raiz.")
elif codigo_busca:
    busca_raw = str(codigo_busca).strip()
    busca_limpa = busca_raw.replace('.0', '').strip()
    
    # 1. Busca por código (final do código ou correspondência exata)
    if busca_limpa.isdigit():
        df_match = df_produtos[
            (df_produtos['COD. EAN_LIMPO'].str.endswith(busca_limpa)) |
            (df_produtos['SKU_LIMPO'].str.endswith(busca_limpa)) |
            (df_produtos['CODIGO_LIMPO'].str.endswith(busca_limpa)) |
            (df_produtos['COD. EAN_LIMPO'] == busca_limpa) |
            (df_produtos['SKU_LIMPO'] == busca_limpa) |
            (df_produtos['CODIGO_LIMPO'] == busca_limpa)
        ]
    else:
        # 2. Busca textual multi-termos
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

    # 3. Exibição dos resultados
    if not df_match.empty:
        if len(df_match) > 1:
            st.info(f"ℹ️ Encontrados **{len(df_match)} produtos** correspondentes:")
            
        for index, row in df_match.iterrows():
            nome_comercial = row.get('NOME COMERCIAL', row.get('DESCRICAO', 'Produto'))
            ean_val = row.get('COD. EAN_LIMPO', 'N/D')
            cod_minassal = row.get('CODIGO_LIMPO', 'N/D')
            sku_val = row.get('SKU_LIMPO', 'N/D')
            familia_val = str(row.get('FAMILIA', 'Geral'))
            
            # Tratamento numérico do preço
            preco_raw = row.get('VALOR_RECOMENDADO_MG', 0.0)
            try:
                if isinstance(preco_raw, str):
                    preco_raw = preco_raw.replace('R$', '').replace('.', '').replace(',', '.').strip()
                preco_mg = float(preco_raw)
            except Exception:
                preco_mg = 0.0
            
            caminho_img = obter_caminho_imagem(cod_minassal) or obter_caminho_imagem(sku_val)

            with st.container():
                st.markdown("<div class='produto-card'>", unsafe_allow_html=True)
                
                # Exibição direta e limpa da imagem sem tags duplicadas
                if caminho_img and os.path.exists(caminho_img):
                    st.image(caminho_img, width=180)
                else:
                    st.markdown("<div style='height: 120px; display: flex; align-items: center; justify-content: center; background-color: #FAFAFA; border-radius: 10px; margin-bottom: 12px;'><p style='color: #94A3B8; font-size: 13px; margin: 0;'>🖼️ Imagem não disponível</p></div>", unsafe_allow_html=True)
                
                st.markdown(f"<span class='badge-familia'>{familia_val}</span>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align: center; color: #0F172A; margin-top: 4px; margin-bottom: 6px; font-size: 18px;'>{nome_comercial}</h3>", unsafe_allow_html=True)
                
                # Exibição dos códigos de identificação
                detalhes_str = f"<b>Cód:</b> {cod_minassal}"
                if sku_val and sku_val != "N/D":
                    detalhes_str += f" | <b>SKU:</b> {sku_val}"
                if ean_val and ean_val != "N/D":
                    detalhes_str += f" | <b>EAN:</b> {ean_val}"
                    
                st.markdown(f"<p style='text-align: center; font-size: 12.5px; color: #64748B;'>{detalhes_str}</p>", unsafe_allow_html=True)
                
                if preco_mg > 0:
                    preco_formatado = f"R$ {preco_mg:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    st.markdown(f"""
                        <div class="caixa-preco-central">
                            <div class="titulo-preco">💰 Preço Sugerido de Ponta (MG)</div>
                            <div class="valor-preco">{preco_formatado}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Preço sugerido não cadastrado para este item.")
                    
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.error(f"❌ Nenhum produto encontrado para: **{codigo_busca}**.")
