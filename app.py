import streamlit as st
import re
import json
import requests
from urllib.parse import quote

st.set_page_config(page_title="Extracteur Pro", page_icon="🚀")
st.title("🚀 Extracteur YouTube (Version Tout-Terrain)")
st.write("Cet outil force la récupération des sous-titres, même automatiques.")

def extract_video_id(url):
    """Extrait l'ID de la vidéo YouTube"""
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

def get_subtitles_with_library(video_id):
    """Méthode 1 : Utiliser youtube-transcript-api"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Essayer différentes langues
        languages = [['fr'], ['en'], ['fr-FR'], ['en-US']]
        
        for lang in languages:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=lang)
                text = " ".join([item['text'] for item in transcript])
                return text, lang[0], "youtube-transcript-api"
            except:
                continue
        
        # Sans langue spécifique
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            text = " ".join([item['text'] for item in transcript])
            return text, "auto", "youtube-transcript-api"
        except:
            pass
            
        # list_transcripts
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = next(iter(transcript_list))
            data = transcript.fetch()
            text = " ".join([item['text'] for item in data])
            return text, transcript.language, "youtube-transcript-api (list)"
        except:
            pass
            
    except ImportError:
        pass
    except Exception as e:
        st.warning(f"Méthode bibliothèque échouée : {str(e)}")
    
    return None, None, None

def get_subtitles_direct_api(video_id):
    """Méthode 2 : Requête directe à l'API YouTube (timsub)"""
    try:
        # Récupérer la page YouTube pour obtenir les infos de sous-titres
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None, None, None
        
        # Chercher les URLs de sous-titres dans le HTML
        html = response.text
        
        # Pattern pour trouver les URLs de timedtext
        patterns = [
            r'"captionTracks":\[{"baseUrl":"([^"]+)"',
            r'"captionTracks":\[\{"baseUrl":"([^"]+)"',
        ]
        
        caption_url = None
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                caption_url = match.group(1).replace('\\u0026', '&')
                break
        
        if not caption_url:
            return None, None, None
        
        # Télécharger les sous-titres
        caption_response = requests.get(caption_url, headers=headers, timeout=10)
        
        if caption_response.status_code != 200:
            return None, None, None
        
        # Parser le XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(caption_response.text)
        
        # Extraire le texte
        texts = []
        for child in root:
            if child.text:
                # Nettoyer le texte
                text = child.text.strip()
                text = text.replace('\n', ' ')
                texts.append(text)
        
        full_text = " ".join(texts)
        return full_text, "auto-detecté", "API directe"
        
    except Exception as e:
        st.warning(f"Méthode API directe échouée : {str(e)}")
    
    return None, None, None

# Interface utilisateur
with st.expander("ℹ️ Informations importantes"):
    st.info("""
    **Ce qui est testé :**
    1. Bibliothèque youtube-transcript-api (3 méthodes)
    2. Requêtes directes à l'API YouTube
    
    **Limitations :**
    - La vidéo doit être publique
    - Les sous-titres doivent être activés
    """)

urls_input = st.text_area("Collez vos liens YouTube ici (un par ligne) :", height=150, 
                          placeholder="https://www.youtube.com/watch?v=...")

if st.button("🚀 Lancer l'extraction", type="primary"):
    if not urls_input:
        st.warning("⚠️ Aucun lien détecté.")
    else:
        urls = [u.strip() for u in urls_input.split('\n') if u.strip()]
        
        for idx, url in enumerate(urls, 1):
            if len(url) < 10: 
                continue
            
            st.divider()
            st.subheader(f"Vidéo {idx}/{len(urls)}")
            
            # Extraction ID
            video_id = extract_video_id(url)
            if not video_id:
                st.error(f"❌ Lien invalide : `{url}`")
                continue
            
            st.info(f"🔎 **ID Vidéo :** `{video_id}`")
            
            # Barre de progression
            progress = st.progress(0)
            status = st.empty()
            
            text = None
            language = None
            method = None
            
            # MÉTHODE 1 : youtube-transcript-api
            status.text("🔍 Méthode 1 : youtube-transcript-api...")
            progress.progress(25)
            text, language, method = get_subtitles_with_library(video_id)
            
            # MÉTHODE 2 : API directe
            if text is None:
                status.text("🔍 Méthode 2 : API YouTube directe...")
                progress.progress(50)
                text, language, method = get_subtitles_direct_api(video_id)
            
            progress.progress(100)
            status.empty()
            
            if text and len(text.strip()) > 0:
                # Succès !
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Langue", language or "Inconnue")
                with col2:
                    st.metric("Caractères", f"{len(text):,}")
                with col3:
                    st.metric("Méthode", method)
                
                st.success("✅ **Extraction réussie !**")
                
                # Aperçu
                with st.expander("👁️ Aperçu du texte", expanded=True):
                    preview = text[:1000] + "..." if len(text) > 1000 else text
                    st.text_area("", preview, height=200, label_visibility="collapsed")
                
                # Téléchargement
                st.download_button(
                    label="📥 Télécharger le texte complet",
                    data=text,
                    file_name=f"transcript_{video_id}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.error("❌ **Échec de toutes les méthodes**")
                st.warning("""
                Aucune méthode n'a réussi à extraire les sous-titres. Vérifiez :
                - La vidéo est bien publique
                - Les sous-titres sont activés (bouton CC sur YouTube)
                - Vous avez la bonne version de youtube-transcript-api
                """)
                
                with st.expander("🔧 Solutions possibles"):
                    st.code("""
# Réinstaller la bibliothèque
pip uninstall youtube-transcript-api
pip install youtube-transcript-api

# Ou essayer une version spécifique
pip install youtube-transcript-api==0.6.2
                    """)
            
            progress.empty()

st.markdown("---")
st.caption("💡 Cet outil essaie plusieurs méthodes automatiquement.")
