import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Titre de la page
st.set_page_config(page_title="Extracteur YouTube", page_icon="📺")
st.title("📺 Extracteur de Texte YouTube")
st.write("Cet outil est gratuit. Collez vos liens ci-dessous.")

# Zone pour coller les liens
urls_input = st.text_area("Collez vos liens ici (un par ligne) :", height=200)

# Le bouton magique
if st.button("Lancer l'extraction"):
    if not urls_input:
        st.warning("Il faut coller au moins un lien !")
    else:
        urls = urls_input.split('\n')
        
        for url in urls:
            url = url.strip()
            if len(url) < 10: continue # On saute les lignes vides

            st.divider() # Ligne de séparation visuelle
            
            try:
                # 1. Trouver l'ID de la vidéo
                video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
                if not video_id_match:
                    st.error(f"Lien bizarre ignoré : {url}")
                    continue
                video_id = video_id_match.group(1)

                # 2. Récupérer le texte
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr', 'en'])
                full_text = " ".join([i['text'] for i in transcript])
                
                # 3. Afficher le résultat
                st.success(f"✅ Vidéo trouvée : {video_id}")
                
                # Bouton pour télécharger le fichier
                st.download_button(
                    label=f"📥 Télécharger le texte de cette vidéo",
                    data=full_text,
                    file_name=f"texte_{video_id}.txt",
                    mime="text/plain"
                )
                
                # Petit aperçu du texte
                with st.expander("Voir un aperçu du texte"):
                    st.write(full_text[:500] + "...")

            except Exception as e:
                st.error(f"❌ Erreur pour ce lien (Pas de sous-titres ?) : {url}")
