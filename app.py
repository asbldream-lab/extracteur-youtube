import streamlit as st
import re

st.set_page_config(page_title="Extracteur Pro", page_icon="🚀")
st.title("🚀 Extracteur YouTube (Version Tout-Terrain)")
st.write("Cet outil force la récupération des sous-titres, même automatiques.")

urls_input = st.text_area("Collez vos liens ici :", height=150)

if st.button("Lancer l'extraction"):
    if not urls_input:
        st.warning("Pas de lien détecté.")
    else:
        # Import ici pour éviter les problèmes
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError:
            st.error("❌ La bibliothèque youtube-transcript-api n'est pas installée correctement.")
            st.info("Exécutez : `pip install --upgrade youtube-transcript-api`")
            st.stop()
        
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
                transcript_data = None
                used_language = None
                
                # Méthode 1 : Essayer avec des langues spécifiques
                languages_to_try = [['fr'], ['fr-FR'], ['en'], ['en-US'], ['en-GB']]
                
                for lang_list in languages_to_try:
                    try:
                        transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=lang_list)
                        used_language = lang_list[0]
                        break
                    except:
                        continue
                
                # Méthode 2 : Sans spécifier de langue
                if transcript_data is None:
                    try:
                        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
                        used_language = "détectée automatiquement"
                    except:
                        pass
                
                # Méthode 3 : Forcer avec list_transcripts (si disponible)
                if transcript_data is None:
                    try:
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                        # Essayer de trouver des sous-titres générés automatiquement
                        try:
                            transcript_obj = transcript_list.find_generated_transcript(['fr', 'en'])
                        except:
                            # Prendre le premier disponible
                            transcript_obj = next(iter(transcript_list))
                        
                        transcript_data = transcript_obj.fetch()
                        used_language = transcript_obj.language
                    except:
                        pass
                
                if transcript_data is None or len(transcript_data) == 0:
                    raise Exception("Aucun sous-titre disponible")
                
                # Extraction du texte
                full_text = " ".join([item['text'] for item in transcript_data])
                
                if not full_text.strip():
                    raise Exception("Le texte extrait est vide")
                
                st.success(f"✅ Sous-titres trouvés ! (Langue : {used_language})")
                st.info(f"📊 Longueur : {len(full_text)} caractères")
                
                # Afficher un aperçu
                preview = full_text[:500] + "..." if len(full_text) > 500 else full_text
                st.text_area("Aperçu :", preview, height=150)
                
                st.download_button(
                    label=f"📥 Télécharger ({video_id}.txt)",
                    data=full_text,
                    file_name=f"transcript_{video_id}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                error_msg = str(e).lower()
                
                if "disabled" in error_msg:
                    st.error("❌ Les sous-titres sont désactivés pour cette vidéo.")
                elif "no transcript" in error_msg or "not found" in error_msg or "aucun sous-titre" in error_msg:
                    st.error("❌ Aucun sous-titre disponible (même automatique).")
                elif "attribute" in error_msg:
                    st.error("❌ Problème de version de la bibliothèque.")
                    st.info("🔧 Solution : Dans votre terminal, exécutez :")
                    st.code("pip uninstall youtube-transcript-api\npip install youtube-transcript-api==0.6.2")
                else:
                    st.error(f"❌ Erreur : {str(e)}")
