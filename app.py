import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
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
            if len(url) < 10: continue

            st.divider()
            
            # 1. Extraction ID
            video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
            if not video_id_match:
                st.error(f"Lien invalide : {url}")
                continue
            video_id = video_id_match.group(1)
            
            st.info(f"🔎 Analyse de la vidéo : {video_id}")

            try:
                # 2. La méthode "BOURRIN" (List_transcripts)
                # On demande la liste de TOUS les sous-titres disponibles
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # On essaie de trouver du français ou de l'anglais, même auto-généré
                # Si on ne trouve pas, on prend le premier disponible
                try:
                    transcript = transcript_list.find_transcript(['fr', 'fr-FR', 'en', 'en-US', 'en-GB'])
                except:
                    # Si pas de FR/EN, on prend n'importe quoi (espagnol, allemand...)
                    transcript = next(iter(transcript_list))

                # On récupère le texte
                final_data = transcript.fetch()
                full_text = " ".join([i['text'] for i in final_data])

                st.success(f"✅ Trouvé ! (Langue : {transcript.language})")
                
                st.download_button(
                    label=f"📥 Télécharger le texte ({video_id})",
                    data=full_text,
                    file_name=f"transcript_{video_id}.txt",
                    mime="text/plain"
                )

            except TranscriptsDisabled:
                st.error("❌ Le créateur de la vidéo a désactivé les sous-titres.")
            except NoTranscriptFound:
                st.error("❌ Aucun sous-titre (même auto) trouvé pour cette vidéo.")
            except Exception as e:
                st.error(f"❌ Erreur technique : {e}")
