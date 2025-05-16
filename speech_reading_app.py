#streamlit run speech_reading_app.py   /bunu cmd'de de H: yap bunu yaz enter yap

import streamlit as st
import docx
import re
import random

def get_text_from_docx(uploaded_file, topic_no):
    if uploaded_file is not None:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        doc = docx.Document(tmp_file_path)
        paragraphs = [p for p in doc.paragraphs if p.text.strip()]
        topics = []
        current_topic = ""
        current_number = None
        for p in paragraphs:
            match = re.match(r'^Konu\s*[:\s]*(\d+)', p.text, re.IGNORECASE)
            if match:
                if current_topic and current_number is not None:
                    topics.append({"number": current_number, "text": current_topic})
                current_number = int(match.group(1))
                current_topic = ""
            else:
                if current_number is not None:
                    current_topic += p.text + "\n"
        if current_topic and current_number is not None:
            topics.append({"number": current_number, "text": current_topic})
        for topic in topics:
            if topic["number"] == topic_no:
                import os
                os.unlink(tmp_file_path)
                return topic["text"]
        import os
        os.unlink(tmp_file_path)
        return None
    return None

def main():
    st.title("Sesle Okuma Çalışması")
    st.write("Rastgele sayı:", random.randint(1, 158))
    st.write("Veritabanında 158 okuma parçası bulunmaktadır.")
    topic_no = st.number_input("Okuma parçasının numarasını giriniz (1-158):", min_value=1, max_value=158, step=1)
    
    st.markdown("""
    <style>
    [data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }
    [data-testid="stFileUploader"] button {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type="docx", label_visibility="collapsed")
    
    if st.button("Metni Yükle") and uploaded_file and topic_no:
        text = get_text_from_docx(uploaded_file, topic_no)
        if text:
            st.success("METİN BAŞARIYLA YÜKLENDİ!")
            st.write(text)
        else:
            st.error("Belirtilen konu numarasına ait metin bulunamadı. Lütfen 1-158 arasında bir numara giriniz.")

if __name__ == "__main__":
    main()