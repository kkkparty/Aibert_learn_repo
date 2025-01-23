from fpdf import FPDF

def create_test_pdf(filename="test_paper.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # 添加标题
    pdf.cell(200, 10, txt="Deep Learning Approaches for Natural Language Processing", ln=True, align='C')

    # 添加摘要
    pdf.cell(200, 10, txt="Abstract", ln=True)
    pdf.multi_cell(0, 10, txt="This paper presents a comprehensive survey of deep learning methods in Natural Language Processing (NLP). We examine various architectures including RNNs, LSTMs, and Transformer models.")

    # 添加引言
    pdf.cell(200, 10, txt="1. Introduction", ln=True)
    pdf.multi_cell(0, 10, txt="Natural Language Processing has witnessed significant advances with the advent of deep learning techniques. These approaches have revolutionized how we handle tasks such as machine translation and text classification.")

    pdf.output(filename)

if __name__ == "__main__":
    create_test_pdf()