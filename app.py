import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import re

st.set_page_config(page_title="Extracteur Pro", page_icon="🚀")
st.title("🚀 Extracteur YouTube (Version Tout-Terrain)")
st.write("Cet outil force la récupération des sous-titres, même automatiques.")

urls_input = st.text_area("Collez vos liens ici :", height=150)

if st.button("Lancer l'extraction"):
    if not urls_input:
        st.warning("Pas de lien détecté.")
    else:
        urls = urls_input.split('\n')
        for url in urls:
            url = url.strip()
            if len(url) < 10: 
                continue
            
            st.divider()
            
            # 1. Extraction ID
            video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
            if not video_id_match:
                st.error(f"Lien invalide : {url}")
                continue
            
            video_id = video_id_match.group(1)
            st.info(f"🔎 Analyse de la vidéo : {video_id}")
            
            try:
                # Méthode robuste : on essaie plusieurs langues dans l'ordre
                languages_to_try = [
                    ['fr'],           # Français
                    ['fr-FR'],        # Français France
                    ['en'],           # Anglais
                    ['en-US'],        # Anglais US
                    ['en-GB'],        # Anglais UK
                ]
                
                transcript_data = None
                used_language = None
                
                # On essaie chaque langue
                for lang_list in languages_to_try:
                    try:
                        transcript_data = YouTubeTranscriptApi.get_transcript(
                            video_id, 
                            languages=lang_list
                        )
                        used_language = lang_list[0]
                        break
                    except:
                        continue
                
                # Si aucune langue spécifique ne marche, on prend ce qui est disponible
                if transcript_data is None:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
                    used_language = "auto"
                
                # Extraction du texte
                full_text = " ".join([item['text'] for item in transcript_data])
                
                st.success(f"✅ Trouvé ! (Langue : {used_language})")
                
                # Afficher un aperçu
                preview = full_text[:500] + "..." if len(full_text) > 500 else full_text
                st.text_area("Aperçu :", preview, height=150)
                
                st.download_button(
                    label=f"📥 Télécharger le texte ({video_id})",
                    data=full_text,
                    file_name=f"transcript_{video_id}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                error_msg = str(e)
                if "Subtitles are disabled" in error_msg or "disabled for this video" in error_msg:
                    st.error("❌ Le créateur de la vidéo a désactivé les sous-titres.")
                elif "No transcripts were found" in error_msg or "Could not retrieve" in error_msg:
                    st.error("❌ Aucun sous-titre (même auto) trouvé pour cette vidéo.")
                else:
                    st.error(f"❌ Erreur technique : {error_msg}")
