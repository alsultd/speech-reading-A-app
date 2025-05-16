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
    """Yüklenen Word belgesinden belirtilen konu numarasının metnini çeker."""
    if uploaded_file is not None:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            # uploaded_file.getvalue() yerine .read() kullan
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        try:
            doc = docx.Document(tmp_file_path)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            topics = []
            current_topic = ""
            current_number = None
            for p in paragraphs:
                match = re.match(r'^Konu\s*:\s*(\d+)', p)
                if match:
                    if current_topic and current_number is not None:
                        topics.append({"number": current_number, "text": current_topic})
                    current_number = int(match.group(1))
                    current_topic = ""
                else:
                    if current_number is not None:
                        current_topic += p + "\n"
            if current_topic and current_number is not None:
                topics.append({"number": current_number, "text": current_topic})
            for topic in topics:
                if topic["number"] == topic_no:
                    topic["text"] = topic["text"].replace("=== KONU SONU ===", "").strip()
                    return topic["text"]
        finally:
            import os
            os.unlink(tmp_file_path)  # Geçici dosyayı sil
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
    """Ana fonksiyon, Streamlit uygulamasını başlatır."""
    st.title("Sesle Okuma Çalışması")
    st.write("Rastgele sayı:", random.randint(1, 149))

    # Oturum durumunu başlat
    if "paragraphs" not in st.session_state:
        st.session_state["paragraphs"] = []
        st.session_state["current_index"] = 0
        st.session_state["selected_word"] = None
        st.session_state["translation"] = ""

    # Konu numarası girişi
    topic_no = st.number_input("Konu No giriniz:", min_value=1, step=1)

    if st.button("Metni Yükle"):
        try:
            text = get_text_from_docx(DOC_PATH, topic_no)
            if text:
                paragraphs = split_into_paragraphs(text)
                st.session_state["paragraphs"] = paragraphs
                st.session_state["current_index"] = 0
                st.session_state["selected_word"] = None
                st.session_state["translation"] = ""
                st.success("Metin yüklendi!")
            else:
                st.error("Konu bulunamadı!")
        except Exception as e:
            st.error(f"Dosya yüklenirken hata oluştu: {e}")

    if st.session_state["paragraphs"]:
        paragraphs = st.session_state["paragraphs"]
        current_index = st.session_state["current_index"]
        
        # Paragraf gösterimi
        st.subheader(f"Paragraf {current_index + 1}/{len(paragraphs)}")
        st.write(paragraphs[current_index])
        
        # Kelime çevirisi için tıklanabilir kelimeler
        st.write("**Kelime çevirisi için kelimelere tıklayın:**")
        cols = st.columns(5)
        for i, word in enumerate(paragraphs[current_index].split()):
            with cols[i % 5]:
                if st.button(word, key=f"word_{i}_{current_index}"):
                    st.session_state["selected_word"] = word
                    st.session_state["translation"] = translate_word(word)
        
        # Çeviriyi göster
        if st.session_state["selected_word"]:
            st.write(f"'{st.session_state['selected_word']}' çevirisi: {st.session_state['translation']}")
        
        # Düğmeler
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Paragrafı Oku", key="read_paragraph"):
                read_paragraph(paragraphs[current_index])
        with col2:
            if st.button("Sesimi Kaydet", key="record_speech"):
                st.warning("Ses kaydı özelliği şu anda bulutta devre dışı. Mobil cihazda tarayıcı tabanlı bir çözüm eklenebilir.")
        with col3:
            if st.button("Paragrafı Çevir", key="translate_paragraph"):
                translated = GoogleTranslator(source='en', target='tr').translate(paragraphs[current_index])
                st.write(f"**Çeviri:** {translated}")
        with col4:
            if st.button("Sonraki Paragraf", key="next_paragraph"):
                if current_index < len(paragraphs) - 1:
                    st.session_state["current_index"] += 1
                    st.session_state["selected_word"] = None
                    st.session_state["translation"] = ""
                    st.rerun()  # Arayüzü yeniden render et
                else:
                    st.success("Tüm paragraflar tamamlandı!")

if __name__ == "__main__":
    main()
