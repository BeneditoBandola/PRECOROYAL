import os
import unicodedata
import pandas as pd
import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Consulta de Campo - Preço Sugerido",
    layout="centered",
    page_icon="📱",
)

# --- 2. CAPTURAR O ESTADO SELECIONADO ANTES DO CSS ---
st.markdown(
    "<h2 style='text-align: center; color: #0F172A; margin-bottom: 2px;'>📱"
    " Consulta em Campo</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; font-size: 13px; color: #64748B;"
    " margin-bottom: 10px;'>Selecione o estado de consulta e digite os"
    " <b>dígitos finais do código</b> ou o <b>nome / peso</b> do produto:</p>",
    unsafe_allow_html=True,
)

# Seletor de Estado em destaque no topo
estado_selecionado = st.radio(
    "Estado de Consulta",
    options=["MG", "SP", "MS"],
    horizontal=True,
    label_visibility="collapsed",
)

# --- 3. CONFIGURAÇÃO DE CORES DINÂMICAS POR ESTADO ---
if estado_selecionado == "SP":
  bg_color = "#EFF6FF"  # Azul claro / pastel para São Paulo
  accent_color = "#2563EB"  # Azul forte para destaque
elif estado_selecionado == "MS":
  bg_color = "#F0FDF4"  # Verde claro / pastel para Mato Grosso do Sul
  accent_color = "#16A34A"  # Verde forte para destaque
else:
  bg_color = "#F1F5F9"  # Cinza-azulado padrão para Minas Gerais
  accent_color = "#E2001A"  # Vermelho Royal Canin padrão

# --- 4. ESTILO VISUAL DINÂMICO ---
st.markdown(
    f"""
<style>
.stApp {{ 
    background-color: {bg_color}; 
    color: #1E293B; 
    transition: background-color 0.3s ease;
}}
/* Garante alta visibilidade e leitura perfeita nos botões de rádio dos estados */
div[data-testid="stRadio"] label {{
    background-color: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    padding: 6px 18px !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
    color: #0F172A !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}
div[data-testid="stRadio"] div[role="radiogroup"] {{
    gap: 12px;
    justify-content: center;
}}
.caixa-estado-topo {{
    background-color: #FFFFFF;
    border: 2px solid {accent_color};
    border-radius: 12px;
    padding: 8px;
    text-align: center;
    font-weight: 800;
    color: {accent_color};
    margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}}
.caixa-produto-info {{
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-top: 4px solid {accent_color};
    border-radius: 16px;
    padding: 24px 20px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
    text-align: center;
    margin-top: 15px;
    margin-bottom: 25px;
}}
.caixa-preco-central {{
    background: #F8FAFC;
    border: 1.5px solid #CBD5E1;
    border-top: 3.5px solid {accent_color};
    padding: 16px;
    border-radius: 12px;
    margin-top: 16px;
    text-align: center;
}}
.titulo-preco {{
    color: #475569;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}
.valor-preco {{
    color: {accent_color};
    font-size: 40px;
    font-weight: 900;
    margin-top: 2px;
    line-height: 1.1;
    font-family: monospace, sans-serif;
}}
.badge-familia {{
    display: inline-block;
    background-color: #E2E8F0;
    color: #334155;
    padding: 4px 12px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 8px;
}}
div[data-testid="stImage"] {{
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 15px;
}}
div[data-testid="stImage"] img {{
    max-height: 280px !important;
    object-fit: contain !important;
}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="caixa-estado-topo">🌍 TABELA ATIVA: ESTADO DE {estado_selecionado}</div>',
    unsafe_allow_html=True,
)


# --- 5. CARREGAR A BASE UNIFICADA ---
def normalizar_texto(texto):
  if pd.isna(texto):
    return ""
  nfkd = unicodedata.normalize("NFKD", str(texto))
  return "".join(
      [c for c in nfkd if not unicodedata.combining(c)]
  ).lower().strip()


def limpar_campo_codigo(val):
  if pd.isna(val):
    return ""
  txt = str(val).strip()
  if txt.endswith(".0"):
    txt = txt[:-2]
  return txt


@st.cache_data
def carregar_dados():
  arquivo_base = "boneco_com_valor_h.xlsx"
  if not os.path.exists(arquivo_base):
    return None
  try:
    df = pd.read_excel(arquivo_base, sheet_name="Detalhado")
  except Exception:
    try:
      df = pd.read_excel(arquivo_base)
    except Exception as e:
      st.error(f"Erro ao abrir a planilha: {e}")
      return None

  df.columns = [str(c).strip().upper() for c in df.columns]

  for col in ["CODIGO", "COD. EAN", "SKU"]:
    if col in df.columns:
      df[f"{col}_LIMPO"] = df[col].apply(limpar_campo_codigo)
    else:
      df[f"{col}_LIMPO"] = ""

  df["BUSCA_COMPLETA"] = df.apply(
      lambda r: normalizar_texto(
          f"{r.get('DESCRICAO', '')} {r.get('NOME COMERCIAL', '')}"
          f" {r.get('FAMILIA', '')} {r.get('CODIGO_LIMPO', '')}"
          f" {r.get('COD. EAN_LIMPO', '')} {r.get('SKU_LIMPO', '')}"
      ),
      axis=1,
  )
  return df


df_produtos = carregar_dados()

# --- 6. FUNÇÃO DE BUSCA DA IMAGEM ---
PASTA_FOTOS = "mockups_produtos"


def obter_caminho_imagem(codigo_identificador):
  extensoes = [".png", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG"]
  cod_limpo = str(codigo_identificador).strip().replace(".0", "")

  if os.path.exists(PASTA_FOTOS) and cod_limpo:
    for ext in extensoes:
      caminho_completo = os.path.join(PASTA_FOTOS, f"{cod_limpo}{ext}")
      if os.path.exists(caminho_completo):
        return caminho_completo
  return None


# --- 7. CAMPO DE BUSCA ---
codigo_busca = st.text_input(
    "🔍 Buscar Produto:",
    placeholder="Ex: 214731, shih tzu 2.5, gastro feline, kitten...",
    label_visibility="collapsed",
)

# Mapear coluna de preço conforme o estado escolhido
coluna_preco_map = {
    "MG": "VALOR_RECOMENDADO_MG",
    "SP": "VALOR_RECOMENDADO_SP",
    "MS": "VALOR_RECOMENDADO_MS",
}
coluna_ativa = coluna_preco_map[estado_selecionado]

# --- 8. PROCESSAR A BUSCA INTELIGENTE HÍBRIDA ---
if df_produtos is None:
  st.error("⚠️ Planilha `boneco_com_valor_h.xlsx` não encontrada no diretório raiz.")
elif codigo_busca:
  busca_raw = str(codigo_busca).strip()
  busca_limpa = busca_raw.replace(".0", "").strip()

  if busca_limpa.isdigit():
    df_match = df_produtos[
        (df_produtos["COD. EAN_LIMPO"].str.endswith(busca_limpa))
        | (df_produtos["SKU_LIMPO"].str.endswith(busca_limpa))
        | (df_produtos["CODIGO_LIMPO"].str.endswith(busca_limpa))
        | (df_produtos["COD. EAN_LIMPO"] == busca_limpa)
        | (df_produtos["SKU_LIMPO"] == busca_limpa)
        | (df_produtos["CODIGO_LIMPO"] == busca_limpa)
    ]
  else:
    tokens = [normalizar_texto(t) for t in busca_raw.split() if t.strip()]

    def match_tokens(texto_registro):
      texto_reg_pontos = texto_registro.replace(",", ".")
      for tok in tokens:
        tok_com_virgula = tok.replace(".", ",")
        tok_com_ponto = tok.replace(",", ".")
        if (
            tok not in texto_registro
            and tok_com_virgula not in texto_registro
            and tok_com_ponto not in texto_reg_pontos
        ):
          return False
      return True

    df_match = df_produtos[df_produtos["BUSCA_COMPLETA"].apply(match_tokens)]

  if not df_match.empty:
    if len(df_match) > 1:
      st.info(f"ℹ️ Encontrados **{len(df_match)} produtos** correspondentes:")

    for index, row in df_match.iterrows():
      nome_comercial = row.get(
          "NOME COMERCIAL", row.get("DESCRICAO", "Produto")
      )
      ean_val = row.get("COD. EAN_LIMPO", "N/D")
      cod_minassal = row.get("CODIGO_LIMPO", "N/D")
      sku_val = row.get("SKU_LIMPO", "N/D")
      familia_val = str(row.get("FAMILIA", "Geral"))

      preco_raw = row.get(coluna_ativa, 0.0)
      try:
        if isinstance(preco_raw, str):
          preco_raw = (
              preco_raw.replace("R$", "")
              .replace(".", "")
              .replace(",", ".")
              .strip()
          )
        preco_estado = float(preco_raw)
      except Exception:
        preco_estado = 0.0

      caminho_img = obter_caminho_imagem(cod_minassal) or obter_caminho_imagem(
          sku_val
      )

      # Centralização da imagem em tamanho grande
      col_esq, col_centro, col_dir = st.columns([1, 2.8, 1])
      with col_centro:
        if caminho_img and os.path.exists(caminho_img):
          st.image(caminho_img, use_container_width=True)
        else:
          st.markdown(
              "<p style='text-align: center; color: #94A3B8; font-size: 13px;"
              " margin: 20px 0;'>🖼️ Imagem não disponível</p>",
              unsafe_allow_html=True,
          )

      # Formatação dos identificadores
      detalhes_str = f"<b>Cód:</b> {cod_minassal}"
      if sku_val and sku_val != "N/D":
        detalhes_str += f" | <b>SKU:</b> {sku_val}"
      if ean_val and ean_val != "N/D":
        detalhes_str += f" | <b>EAN:</b> {ean_val}"

      # Bloco de preço formatado
      if preco_estado > 0:
        preco_formatado = (
            f"R$ {preco_estado:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        bloco_preco = (
            f'<div class="caixa-preco-central"><div'
            f' class="titulo-preco">💰 Preço Sugerido de Ponta ({estado_selecionado})</div><div'
            f' class="valor-preco">{preco_formatado}</div></div>'
        )
      else:
        bloco_preco = (
            f'<div style="margin-top: 12px;"><span style="color: #D97706;'
            f' font-size: 13px; font-weight: 700;">⚠️ Preço sugerido para'
            f" {estado_selecionado} não cadastrado</span></div>"
        )

      # Renderização do Card Unificado
      html_card = (
          f'<div class="caixa-produto-info"><span'
          f' class="badge-familia">{familia_val}</span><h3 style="color:'
          f' #0F172A; margin-top: 4px; margin-bottom: 6px; font-size:'
          f' 19px;">{nome_comercial}</h3><p style="font-size: 12.5px; color:'
          f' #64748B; margin-bottom: 0;">{detalhes_str}</p>{bloco_preco}</div>'
      )

      st.markdown(html_card, unsafe_allow_html=True)
  else:
    st.error(f"❌ Nenhum produto encontrado para: **{codigo_busca}**.")

# Assinatura de autoria na tela do programa (interface do Streamlit)
st.markdown("<br><hr><p style='text-align: center; color: #555555; font-size: 11px;'>Desenvolvido por Benedito Bandola</p>", unsafe_allow_html=True)
