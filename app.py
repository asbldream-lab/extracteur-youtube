import streamlit as st
import re

st.set_page_config(page_title="Extracteur Pro", page_icon="🚀")
st.title("🚀 Extracteur YouTube (Version Tout-Terrain)")
st.write("Cet outil force la récupération des sous-titres, même automatiques.")

# Message d'information
with st.expander("ℹ️ Informations importantes"):
    st.info("""
    **Limitations :**
    - La vidéo doit avoir des sous-titres (manuels ou automatiques)
    - La vidéo doit être publique
    - Si le créateur a désactivé les sous-titres, extraction impossible
    
    **Astuce :** Sur YouTube, vérifiez si le bouton CC (sous-titres) est disponible sur la vidéo avant d'essayer l'extraction.
    """)

urls_input = st.text_area("Collez vos liens YouTube ici (un par ligne) :", height=150)

if st.button("🚀 Lancer l'extraction", type="primary"):
    if not urls_input:
        st.warning("⚠️ Aucun lien détecté.")
    else:
        # Import ici pour éviter les problèmes
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import (
                TranscriptsDisabled, 
                NoTranscriptFound, 
                VideoUnavailable
            )
        except ImportError as e:
            st.error("❌ Bibliothèque manquante ou version incorrecte")
            st.code("pip uninstall youtube-transcript-api\npip install youtube-transcript-api==0.6.2")
            st.stop()
        
        urls = [u.strip() for u in urls_input.split('\n') if u.strip()]
        
        for idx, url in enumerate(urls, 1):
            if len(url) < 10: 
                continue
            
            st.divider()
            st.subheader(f"Vidéo {idx}/{len(urls)}")
            
            # 1. Extraction ID
            video_id_match = re.search(r"(?:v=|youtu\.be/|/embed/|/v/)([0-9A-Za-z_-]{11})", url)
            if not video_id_match:
                st.error(f"❌ Lien invalide : `{url}`")
                st.info("Format attendu : `https://www.youtube.com/watch?v=XXXXXXXXXXX`")
                continue
            
            video_id = video_id_match.group(1)
            st.info(f"🔎 **ID Vidéo :** `{video_id}`")
            st.caption(f"🔗 Lien : https://www.youtube.com/watch?v={video_id}")
            
            # Barre de progression
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("⏳ Recherche des sous-titres disponibles...")
                progress_bar.progress(25)
                
                transcript_data = None
                used_language = None
                method_used = None
                
                # MÉTHODE 1 : Essayer des langues spécifiques
                status_text.text("🔍 Tentative avec langues spécifiques (FR/EN)...")
                progress_bar.progress(50)
                
                languages_priority = [
                    (['fr'], "Français"),
                    (['fr-FR'], "Français (France)"),
                    (['en'], "Anglais"),
                    (['en-US'], "Anglais (US)"),
                    (['en-GB'], "Anglais (UK)"),
                ]
                
                for lang_codes, lang_name in languages_priority:
                    try:
                        transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=lang_codes)
                        used_language = lang_name
                        method_used = "Langue spécifique"
                        break
                    except:
                        continue
                
                # MÉTHODE 2 : Sans langue spécifique
                if transcript_data is None:
                    status_text.text("🔍 Tentative sans langue spécifique...")
                    progress_bar.progress(65)
                    try:
                        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
                        used_language = "Auto-détectée"
                        method_used = "Auto"
                    except:
                        pass
                
                # MÉTHODE 3 : list_transcripts (si disponible)
                if transcript_data is None:
                    status_text.text("🔍 Tentative avec list_transcripts...")
                    progress_bar.progress(80)
                    try:
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                        
                        # Essayer d'abord les sous-titres manuels
                        try:
                            transcript_obj = transcript_list.find_manually_created_transcript(['fr', 'en'])
                            transcript_data = transcript_obj.fetch()
                            used_language = f"{transcript_obj.language} (Manuel)"
                            method_used = "Manuel"
                        except:
                            # Sinon, prendre les auto-générés
                            try:
                                transcript_obj = transcript_list.find_generated_transcript(['fr', 'en'])
                                transcript_data = transcript_obj.fetch()
                                used_language = f"{transcript_obj.language} (Auto)"
                                method_used = "Généré auto"
                            except:
                                # En dernier recours, prendre n'importe quoi
                                transcript_obj = next(iter(transcript_list))
                                transcript_data = transcript_obj.fetch()
                                used_language = transcript_obj.language
                                method_used = "Premier disponible"
                    except:
                        pass
                
                progress_bar.progress(100)
                status_text.empty()
                
                if transcript_data is None or len(transcript_data) == 0:
                    raise NoTranscriptFound(video_id, [], None)
                
                # Extraction du texte
                full_text = " ".join([item['text'] for item in transcript_data])
                
                if not full_text.strip():
                    raise Exception("Le texte extrait est vide")
                
                # Affichage succès
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Langue", used_language)
                with col2:
                    st.metric("Caractères", f"{len(full_text):,}")
                with col3:
                    st.metric("Méthode", method_used)
                
                st.success("✅ **Extraction réussie !**")
                
                # Aperçu
                with st.expander("👁️ Aperçu du texte", expanded=True):
                    preview = full_text[:1000] + "..." if len(full_text) > 1000 else full_text
                    st.text_area("", preview, height=200, label_visibility="collapsed")
                
                # Téléchargement
                st.download_button(
                    label="📥 Télécharger le texte complet",
                    data=full_text,
                    file_name=f"transcript_{video_id}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
                progress_bar.empty()
                
            except TranscriptsDisabled:
                progress_bar.empty()
                status_text.empty()
                st.error("❌ **Sous-titres désactivés**")
                st.warning("Le créateur de cette vidéo a désactivé tous les sous-titres.")
                
            except NoTranscriptFound:
                progress_bar.empty()
                status_text.empty()
                st.error("❌ **Aucun sous-titre trouvé**")
                st.warning("""
                Cette vidéo n'a pas de sous-titres disponibles. Raisons possibles :
                - Pas de sous-titres manuels ajoutés
                - Sous-titres automatiques non générés par YouTube
                - Vidéo trop récente (YouTube n'a pas encore généré les sous-titres)
                """)
                st.info(f"💡 Vérifiez sur YouTube : https://www.youtube.com/watch?v={video_id}")
                
            except VideoUnavailable:
                progress_bar.empty()
                status_text.empty()
                st.error("❌ **Vidéo indisponible**")
                st.warning("La vidéo est privée, supprimée ou restreinte.")
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                error_msg = str(e).lower()
                
                if "attribute" in error_msg:
                    st.error("❌ **Problème de version de bibliothèque**")
                    st.code("pip uninstall youtube-transcript-api\npip install youtube-transcript-api==0.6.2")
                else:
                    st.error(f"❌ **Erreur inattendue**")
                    with st.expander("Détails de l'erreur"):
                        st.code(str(e))

# Footer
st.markdown("---")
st.caption("💡 **Astuce :** Sur YouTube, cliquez sur le bouton CC pour vérifier si des sous-titres existent avant d'utiliser cet outil.")
