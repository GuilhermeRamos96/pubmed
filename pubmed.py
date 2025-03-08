import streamlit as st
import pandas as pd
from Bio import Entrez, Medline
from fpdf import FPDF

# Configurar e-mail para acessar o PubMed
Entrez.email = "seuemail@exemplo.com"

def buscar_pubmed(termo, revista, ano_inicio, ano_fim, num_artigos, delineamento):
    search_term = f"({termo}) AND ({ano_inicio}[PDAT] : {ano_fim}[PDAT])"
    if revista:
        search_term += f" AND {revista}[journal]"
    if delineamento:
        search_term += f" AND {delineamento}[PT]"
    
    try:
        handle = Entrez.esearch(db="pubmed", term=search_term, retmax=num_artigos)
        record = Entrez.read(handle)
        handle.close()

        id_list = record["IdList"]
        if not id_list:
            return []

        fetch_handle = Entrez.efetch(db="pubmed", id=",".join(id_list), rettype="medline", retmode="text")
        articles = Medline.parse(fetch_handle)
        artigos = list(articles)
        fetch_handle.close()

        artigos.sort(key=lambda x: x.get("DP", "0000"), reverse=True)
        return artigos
    except Exception as e:
        st.error(f"Erro ao buscar artigos: {str(e)}")
        return []

def criar_pdf(dados, termo, revista, ano_inicio, ano_fim, delineamento):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(200, 10, "Resultados da Pesquisa PubMed", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)

    def safe_text(text):
        return text.encode("latin-1", "replace").decode("latin-1")

    pdf.multi_cell(0, 8, safe_text(f"Palavras-chave: {termo}"))
    pdf.multi_cell(0, 8, safe_text(f"Período: {ano_inicio} - {ano_fim}"))
    pdf.multi_cell(0, 8, safe_text(f"Revista: {revista if revista else 'Não especificada'}"))
    pdf.multi_cell(0, 8, safe_text(f"Delineamento: {delineamento if delineamento else 'Não especificado'}"))
    pdf.ln(10)
    
    for artigo in dados:
        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 10, safe_text(f"Título: {artigo[0]}"))
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, safe_text(f"Autores: {artigo[1]}"))
        pdf.multi_cell(0, 8, safe_text(f"Ano: {artigo[2]}"))
        pdf.multi_cell(0, 8, safe_text(f"Delineamento: {artigo[3]}"))
        pdf.multi_cell(0, 8, safe_text(f"Revista: {artigo[4]}"))
        pdf.set_font("Arial", "I", 11)
        pdf.multi_cell(0, 8, safe_text(f"Resumo: {artigo[5]}"))
        pdf.set_font("Arial", "U", 11)
        pdf.multi_cell(0, 8, safe_text(f"Link: {artigo[6]}"))
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
    
    return pdf

st.set_page_config(page_title="Encontre seu Artigo", layout="wide")
st.title("📚 Encontre seu Artigo")

if "dados" not in st.session_state:
    st.session_state.dados = []

col1, col2, col3 = st.columns(3)
with col1:
    termo = st.text_input("🔍 Termo de Pesquisa", placeholder="Ex: Ameloblastoma AND Treatment")
    revista = st.text_input("📰 Nome da Revista (opcional)", placeholder="Ex: Int J Oral Maxillofac Surg")
with col2:
    ano_inicio = st.text_input("📅 Ano Inicial", placeholder="Ex: 1900")
    ano_fim = st.text_input("📅 Ano Final", placeholder="Ex: 2025")
with col3:
    num_artigos = st.selectbox("🔢 Número de Artigos", ["5", "10", "20", "50", "100", "Todos"], index=0)
    delineamento = st.text_input("🏰 Delineamento (opcional)", placeholder="Ex: Clinical Trial, Systematic Review")

if st.button("🔎 Buscar Artigos"):
    if not termo or not ano_inicio or not ano_fim:
        st.warning("⚠️ Preencha os campos obrigatórios (Termo, Ano Inicial e Ano Final).")
    else:
        num_artigos = 10000 if num_artigos == "Todos" else int(num_artigos)
        st.session_state.dados = buscar_pubmed(termo, revista, ano_inicio, ano_fim, num_artigos, delineamento)

if st.session_state.dados:
    dados = [[artigo.get("TI", "Título não disponível"), ", ".join(artigo.get("AU", ["Autores não disponíveis"])), artigo.get("DP", "Data não disponível").split(" ")[0], ", ".join(artigo.get("PT", ["Tipo não disponível"])), artigo.get("TA", "Revista não disponível"), artigo.get("AB", "Resumo não disponível"), f"https://pubmed.ncbi.nlm.nih.gov/{artigo.get('PMID', '0')}/"] for artigo in st.session_state.dados]
    df = pd.DataFrame(dados, columns=["Título", "Autores", "Ano", "Delineamento", "Revista", "Resumo", "Link"])
    st.markdown("### 📄 Resultados da Pesquisa")
    st.dataframe(df, height=600, use_container_width=True)
    csv_data = df.to_csv(index=False, sep=";", encoding="utf-8", quotechar='"')
    st.download_button("📥 Baixar CSV", data=csv_data.encode("utf-8"), file_name="resultados_pubmed.csv", mime="text/csv")
    pdf = criar_pdf(dados, termo, revista, ano_inicio, ano_fim, delineamento)
    pdf_file = "resultados_pubmed.pdf"
    pdf.output(pdf_file)
    with open(pdf_file, "rb") as f:
        st.download_button("📥 Baixar PDF", data=f, file_name="resultados_pubmed.pdf", mime="application/pdf")

st.markdown("---")
st.markdown("📌 Desenvolvido por **[Guilherme]** - Pesquisa baseada na PubMed via Biopython.")

