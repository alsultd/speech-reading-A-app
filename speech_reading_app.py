#streamlit run speech_reading_app.py   /bunu cmd'de de H: yap bunu yaz enter yap

import docx
import re
#import speech_recognition as sr
from deep_translator import GoogleTranslator
import pronouncing
import difflib
import time
#import winsound
import random
import streamlit as st
from streamlit.components.v1 import html

# Sabitler
DOC_PATH = r"H:\OCR_Ana_Cikti_Guncel.docx"
ERROR_THRESHOLD = 0.3

def get_text_from_docx(uploaded_file, topic_no):
    if uploaded_file is not None:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        try:
            doc = docx.Document(tmp_file_path)
            paragraphs = [p for p in doc.paragraphs if p.text.strip()]  # Boş olmayan paragrafları al
            topics = []
            current_topic = ""
            current_number = None
            for p in paragraphs:
                match = re.match(r'^Konu\s*[:\s]*(\d+)', p.text, re.IGNORECASE)  # p.text kullan
                if match:
                    if current_topic and current_number is not None:
                        topics.append({"number": current_number, "text": current_topic})
                    current_number = int(match.group(1))
                    current_topic = ""
                else:
                    if current_number is not None:
                        current_topic += p.text + "\n"  # p.text kullan
            if current_topic and current_number is not None:
                topics.append({"number": current_number, "text": current_topic})
            for topic in topics:
                if topic["number"] == topic_no:
                    topic["text"] = topic["text"].replace("=== KONU SONU ===", "").strip()
                    return topic["text"]
            if not topics:
                st.write("Konu başlıkları bulunamadı, tüm metni döndürüyorum.")
                return "\n".join(p.text for p in paragraphs if p.text)
        finally:
            import os
            os.unlink(tmp_file_path)
    return None
def split_into_paragraphs(text):
    """Metni paragraflara böler ve boş satırları temizler."""
    return [p.strip() for p in text.split('\n') if p.strip()]

def preprocess_text(text):
    """Metni küçük harfe çevirir, noktalama işaretlerini kaldırır ve kelimelere ayırır."""
    return re.findall(r"\b\w+\b", text.lower())

def evaluate_speech(original, spoken):
    """Orijinal ve konuşulan metni karşılaştırarak hata oranı, fazla ve eksik kelimeleri hesaplar."""
    original_words = preprocess_text(original)
    spoken_words = preprocess_text(spoken)
    diff = difflib.SequenceMatcher(None, original_words, spoken_words)
    similarity = diff.ratio()
    error_rate = 1 - similarity
    extra_words = [word for word in spoken_words if word not in original_words]
    missing_words = [word for word in original_words if word not in spoken_words]
    return error_rate, extra_words, missing_words

#def listen_and_convert():
#    """Mikrofondan konuşmayı metne çevirir."""
#    recognizer = sr.Recognizer()
#    recognizer.pause_threshold = 2
#    recognizer.dynamic_energy_threshold = False
#    with sr.Microphone() as source:
#        st.write("Adjusting for ambient noise... please wait.")
#        recognizer.adjust_for_ambient_noise(source, duration=4)
#        winsound.Beep(1000, 500)
#        st.write("...Start speaking...")
#        try:
#            audio = recognizer.listen(source, timeout=2, phrase_time_limit=30)
#            return recognizer.recognize_google(audio, language="en-US")
#        except sr.UnknownValueError:
#            return "Could not understand the speech."
#        except sr.RequestError as e:
#            return f"Could not connect to the speech recognition service: {e}"

def translate_word(word):
    """Kelimeyi İngilizce'den Türkçe'ye çevirir."""
    try:
        return GoogleTranslator(source='en', target='tr').translate(word)
    except Exception as e:
        return f"Çeviri hatası: {e}"

def read_paragraph(paragraph):
    """Paragrafı tarayıcıda sesli olarak okur (Web Speech API ile)."""
    # Özel karakterleri temizle ve güvenli hale getir
    clean_text = " ".join(paragraph.splitlines())
    clean_text = (clean_text.replace('"', '\\"')
                  .replace("'", "\\'")
                  .replace('{', '')
                  .replace('}', '')
                  .replace('\n', ' ')
                  .replace('\r', ' ')
                  .replace('\t', ' '))
    st.write("Debug: Cleaned text:", clean_text)  # Hata ayıklaması için
    js_code = """
    <script>
        function speak(text) {
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'en-US';
                utterance.rate = 1.0;
                utterance.onstart = function() {
                    console.log('Speech started');
                };
                utterance.onend = function() {
                    console.log('Speech ended');
                };
                utterance.onerror = function(event) {
                    console.error('Speech error:', event.error);
                    alert('Sesli okuma sırasında bir hata oluştu: ' + event.error);
                };
                window.speechSynthesis.speak(utterance);
            } else {
                alert('Sesli okuma desteklenmiyor. Lütfen modern bir tarayıcı (Chrome, Firefox, Edge) kullanın.');
            }
        }
        speak("%s");
    </script>
    """ % clean_text  # % operatörü ile güvenli ekleme
    html(js_code)

def report_errors(error_rate, extra_words, missing_words):
    """Hata raporunu Streamlit arayüzünde gösterir."""
    error_rate_percent = round(error_rate * 100)
    st.write(f"**Hata Oranı:** {error_rate_percent}%")
    
    if extra_words:
        st.write("**Yanlış telaffuz edilen veya eklenen kelimeler:**")
        st.write(", ".join(extra_words))
    else:
        st.write("**Harika!** Fazladan kelime eklemediniz.")

    if missing_words:
        st.write("**Eksik söylenen kelimeler:**")
        missing_data = []
        for word in missing_words:
            phonetics = pronouncing.phones_for_word(word)
            phonetic = phonetics[0] if phonetics else "Telaffuz bulunamadı"
            translation = translate_word(word)
            missing_data.append({"Kelime": word, "Telaffuz": phonetic, "Türkçe": translation})
        st.table(missing_data)
def main():
    st.title("Sesle Okuma Çalışması")
    st.write("Rastgele sayı:", random.randint(1, 1000))
    st.write("Veritabanında 158 okuma parçası bulunmaktadır.")
    topic_no = st.number_input("Okuma parçasının numarasını giriniz (1-158):", min_value=1, max_value=158, step=1)
    
    # Daha etkili CSS ile "Drag and drop file here" metnini gizle
    st.markdown("""
    <style>
    [data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }
    [data-testid="stFileUploader"] button {
        margin-top: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # File uploader etiketini gizle
    uploaded_file = st.file_uploader("", type="docx", label_visibility="collapsed")
    
    if st.button("Metni Yükle") and uploaded_file and topic_no:
        text = get_text_from_docx(uploaded_file, topic_no)
        if text:
            st.success("METİN BAŞARIYLA YÜKLENDİ!")
            st.write(text)
        else:
            st.error("Belirtilen konu numarasına ait metin bulunamadı. Lütfen 1-158 arasında bir numara giriniz.")if __name__ == "__main__":
    main()
