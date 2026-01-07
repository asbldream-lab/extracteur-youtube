import streamlit as st
import re
import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

st.set_page_config(page_title="Extracteur Pro", page_icon="🚀")
st.title("🚀 Extracteur YouTube (Version Tout-Terrain)")

# --- FONCTIONS ---

def extract_video_id(url):
    """Extrait l'ID propre de la vidéo"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript_safe(video_id):
    """Méthode robuste utilisant la librairie officielle"""
    try:
        # 1. On récupère la liste de tous les transcripts dispos
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 2. On essaie de trouver français ou anglais (manuel ou auto)
        try:
            transcript = transcript_list.find_transcript(['fr', 'fr-FR', 'en', 'en-US'])
        except:
            # Si pas de FR/EN, on prend le premier qui vient (ex: Espagnol, Allemand...)
            transcript = next(iter(transcript_list))
            
        # 3. On télécharge
        final_data = transcript.fetch()
        full_text = " ".join([i['text'] for i in final_data])
        
        return full_text, transcript.language, "Via Librairie Officielle"

    except TranscriptsDisabled:
        return None, None, "Erreur: Sous-titres désactivés par le créateur"
    except NoTranscriptFound:
        return None, None, "Erreur: Aucun sous-titre trouvé"
    except Exception as e:
        return None, None, f"Erreur technique: {str(e)}"

# --- INTERFACE ---

urls_input = st.text_area("Collez vos liens ici (un par ligne) :", height=150)

if st.button("Lancer l'extraction"):
    if not urls_input:
        st.warning("Veuillez coller un lien.")
    else:
        urls = urls_input.split('\n')
        
        for url in urls:
            url = url.strip()
            if len(url) < 10: continue

            st.divider()
            
            # 1. Extraction ID
            video_id = extract_video_id(url)
            if not video_id:
                st.error(f"Lien invalide : {url}")
                continue
            
            st.info(f"Analyse de {video_id}...")
            
            # 2. Récupération du texte
            text, lang, status = get_transcript_safe(video_id)
            
            if text:
                st.success(f"✅ Succès ! (Langue: {lang})")
                st.download_button(
                    label=f"📥 Télécharger {video_id}.txt",
                    data=text,
                    file_name=f"{video_id}.txt",
                    mime="text/plain"
                )
                with st.expander("Voir un extrait"):
                    st.write(text[:500] + "...")
            else:
                st.error(f"❌ Échec pour {video_id} : {status}")
