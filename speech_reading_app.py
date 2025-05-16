#streamlit run speech_reading_app.py   /bunu cmd'de de H: yap bunu yaz enter yap

import streamlit as st
import docx
import re
import random

def get_text_from_docx(uploaded_file, topic_no):
    st.write("get_text_from_docx fonksiyonu çağrıldı!")
    if uploaded_file is not None:
        st.write(f"Yüklenen dosya: {uploaded_file.name}")
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            try:
                st.write("Dosya yazma denemesi yapılıyor...")
                tmp_file.write(uploaded_file.getvalue())  # Binary veri al
                tmp_file_path = tmp_file.name
                st.write("Dosya yazma başarılı, işleniyor:", tmp_file_path)
            except Exception as e:
                st.error(f"Dosya yazma hatası: {str(e)}")
                return None
        try:
            st.write("Belge açılıyor...")
            doc = docx.Document(tmp_file_path)
            paragraphs = [p for p in doc.paragraphs if p.text.strip()]
            st.write("Toplam paragraf sayısı:", len(paragraphs))
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
                    st.write(f"Yeni konu numarası tespit edildi: {current_number}")
                else:
                    if current_number is not None:
                        current_topic += p.text + "\n"
                        st.write(f"Mevcut konuya metin eklendi: '{p.text}'")
            if current_topic and current_number is not None:
                topics.append({"number": current_number, "text": current_topic})
                st.write(f"Son konu eklendi: {current_number}")
            st.write("Oluşturulan topics listesi:", topics)
            for topic in topics:
                if topic["number"] == topic_no:
                    st.write(f"Eşleşen konu bulundu: {topic_no}")
                    import os
                    os.unlink(tmp_file_path)
                    return topic["text"]
            st.error(f"Konu {topic_no} bulunamadı!")
            import os
            os.unlink(tmp_file_path)
            return None
        except Exception as e:
            st.error(f"Metin işleme hatası: {str(e)}")
            import os
            os.unlink(tmp_file_path)
            return None
    else:
        st.error("Dosya yüklenmedi!")
    return None

def main():
    st.title("Sesle Okuma Çalışması")
    st.write("Rastgele sayı:", random.randint(1, 158))
    st.write("Veritabanında 158 okuma parçası bulunmaktadır.")
    topic_no = st.number_input("Okuma parçasının numarasını giriniz (1-158):", min_value=1, max_value=158, step=1)
    
    # Dosya yükleme alanını tamamen gizlemek için talimatı sadeleştirip uploader'ı optimize edelim
    st.write("Lütfen bir .docx dosyası yüklemek için aşağıya dosya sürükleyin veya tıklayın:")
    uploaded_file = st.file_uploader("", type="docx", label_visibility="collapsed")
    st.write("Dosya durumu:", "Yüklenmiş" if uploaded_file else "Yüklenmemiş")
    st.write("Konu numarası:", topic_no)
    
    # Daha kapsamlı CSS ile file uploader'ı tamamen gizle
    st.markdown("""
    <style>
    [data-testid="stFileUploader"] {
        display: none !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        display: none !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }
    [data-testid="stFileUploader"] button {
        display: none !important;
    }
    [data-testid="stFileUploader"] > div > div > div > div {
        display: none !important;
    }
    [data-testid="stFileUploader"] > div {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("Metni Yükle"):
        st.write("Metni Yükle butonuna tıklandı!")
        if uploaded_file and topic_no:
            st.write("Koşullar sağlandı, metin yükleniyor...")
            text = get_text_from_docx(uploaded_file, topic_no)
            if text:
                st.success(f"KONU {topic_no} BAŞARIYLA YÜKLENDİ!")
                st.write(text)
            else:
                st.error("Belirtilen konu numarasına ait metin bulunamadı. Lütfen 1-158 arasında bir numara giriniz.")
        else:
            st.error("Lütfen önce bir .docx dosyası yükleyin ve geçerli bir konu numarası girin!")

if __name__ == "__main__":
    main()