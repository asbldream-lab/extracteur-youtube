import streamlit as st
import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

st.set_page_config(page_title="Extracteur Pro", page_icon="🚀")
st.title("🚀 Extracteur YouTube (Version Finale)")

# Fonction de récupération sécurisée
def get_transcript(video_id):
    try:
        # On demande la liste des sous-titres
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # On essaie de trouver du français ou de l'anglais (manuel ou auto)
        try:
            transcript = transcript_list.find_transcript(['fr', 'fr-FR', 'en', 'en-US'])
        except:
            # Sinon on prend le premier disponible
            transcript = next(iter(transcript_list))
            
        return transcript.fetch(), transcript.language
    except Exception as e:
        return None, str(e)

# Interface
url = st.text_input("Collez votre lien YouTube ici :")

if st.button("Extraire le texte"):
    if url:
        # Extraction de l'ID vidéo
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        if video_id_match:
            video_id = video_id_match.group(1)
            st.info(f"Analyse de la vidéo {video_id}...")
            
            data, error_or_lang = get_transcript(video_id)
            
            if data:
                text = " ".join([i['text'] for i in data])
                st.success(f"✅ Trouvé ! (Langue : {error_or_lang})")
                st.download_button("📥 Télécharger le fichier", data=text, file_name=f"{video_id}.txt")
                st.text_area("Aperçu", text[:500], height=150)
            else:
                st.error(f"Erreur : {error_or_lang}")
        else:
            st.warning("Lien invalide.")
