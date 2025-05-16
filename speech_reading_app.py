#streamlit run speech_reading_app.py   /bunu cmd'de de H: yap bunu yaz enter yap

import streamlit as st
import docx
import re
import random

def get_text_from_docx(uploaded_file, topic_no):
    if uploaded_file is not None:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            try:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            except Exception as e:
                st.error(f"Dosya yazma hatası: {str(e)}")
                return None
        try:
            doc = docx.Document(tmp_file_path)
            paragraphs = [p for p in doc.paragraphs if p.text.strip()]
            topics = []
            current_topic = []
            current_number = None
            for p in paragraphs:
                match = re.match(r'^Konu\s*[:\s]*(\d+)', p.text, re.IGNORECASE)
                if match:
                    if current_topic and current_number is not None:
                        topics.append({"number": current_number, "text": current_topic})
                    current_number = int(match.group(1))
                    current_topic = []
                else:
                    if current_number is not None:
                        current_topic.append(p.text)
            if current_topic and current_number is not None:
                topics.append({"number": current_number, "text": current_topic})
            # Hata ayıklama: topics listesini kontrol et
            st.write("Oluşturulan topics listesi:", [{"number": t["number"], "text": t["text"][:50] + "..." if t["text"] else "Boş"} for t in topics])
            for topic in topics:
                if topic["number"] == topic_no:
                    return topic["text"]
            st.error(f"Konu {topic_no} bulunamadı!")
            return None
        except Exception as e:
            st.error(f"Metin işleme hatası: {str(e)}")
            return None
        finally:
            import os
            os.unlink(tmp_file_path)
    st.error("Dosya yüklenmedi!")
    return None

def main():
    st.title("Sesle Okuma Çalışması")
    st.write("Rastgele sayı:", random.randint(1, 158))
    st.write("Veritabanında 158 okuma parçası bulunmaktadır.")
    topic_no = st.number_input("Okuma parçasının numarasını giriniz (1-158):", min_value=1, max_value=158, step=1)
    
    # Kullanıcıya talimat verelim ama kutucuğu gizleyelim
    st.write("Lütfen bir .docx dosyası yüklemek için aşağıdaki alana tıklayın veya dosyayı sürükleyin:")
    uploaded_file = st.file_uploader("", type="docx", label_visibility="collapsed")
    st.write("Dosya durumu:", "Yüklenmiş" if uploaded_file else "Yüklenmemiş")
    st.write("Konu numarası:", topic_no)
    
    # CSS ile "Drag and drop file here" ve "Browse files" butonunu gizle
    st.markdown("""
    <style>
    [data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }
    [data-testid="stFileUploader"] button {
        display: none !important;
    }
    [data-testid="stFileUploader"] {
        border: 1px dashed #ccc;
        padding: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("Metni Yükle"):
        if uploaded_file and topic_no:
            text = get_text_from_docx(uploaded_file, topic_no)
            if text:
                st.success(f"KONU {topic_no} BAŞARIYLA YÜKLENDİ!")
                # Paragrafları ayrı ayrı göster
                for paragraph in text:
                    st.write(paragraph)
            else:
                st.error("Belirtilen konu numarasına ait metin bulunamadı. Lütfen 1-158 arasında bir numara giriniz.")
        else:
            st.error("Lütfen önce bir .docx dosyası yükleyin ve geçerli bir konu numarası girin!")

if __name__ == "__main__":
    main()