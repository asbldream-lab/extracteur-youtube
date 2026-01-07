import streamlit as st
import re

st.set_page_config(page_title="Extracteur YouTube", page_icon="🚀")
st.title("🚀 Extracteur de Sous-titres YouTube")

# TEST D'INSTALLATION
st.sidebar.header("🔍 Diagnostic")

# Test 1: Import youtube_transcript_api
try:
    import youtube_transcript_api
    st.sidebar.success("✅ youtube-transcript-api installé")
    st.sidebar.caption(f"Version: {youtube_transcript_api.__version__ if hasattr(youtube_transcript_api, '__version__') else 'inconnue'}")
except ImportError:
    st.sidebar.error("❌ youtube-transcript-api NON installé")
    st.sidebar.code("pip install youtube-transcript-api")
    st.stop()

# Test 2: Vérifier les méthodes disponibles
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    methods = dir(YouTubeTranscriptApi)
    
    has_get_transcript = 'get_transcript' in methods
    has_list_transcripts = 'list_transcripts' in methods
    
    st.sidebar.write("**Méthodes disponibles:**")
    st.sidebar.write(f"- get_transcript: {'✅' if has_get_transcript else '❌'}")
    st.sidebar.write(f"- list_transcripts: {'✅' if has_list_transcripts else '❌'}")
    
    if not has_get_transcript and not has_list_transcripts:
        st.sidebar.error("⚠️ Version cassée!")
        st.sidebar.code("pip uninstall youtube-transcript-api\npip install youtube-transcript-api==0.6.2")
        
except Exception as e:
    st.sidebar.error(f"Erreur: {e}")

# INTERFACE PRINCIPALE
url_input = st.text_input("URL YouTube:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Extraire les sous-titres"):
    if not url_input:
        st.warning("Entrez une URL")
        st.stop()
    
    # Extraire video ID
    match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', url_input)
    if not match:
        st.error("URL invalide")
        st.stop()
    
    video_id = match.group(1)
    st.info(f"Video ID: `{video_id}`")
    
    # Import
    from youtube_transcript_api import YouTubeTranscriptApi
    
    with st.spinner("Extraction en cours..."):
        result_text = None
        result_lang = None
        result_method = None
        
        # APPROCHE 1: get_transcript simple
        if 'get_transcript' in dir(YouTubeTranscriptApi):
            try:
                st.write("🔄 Essai: get_transcript (sans langue)...")
                data = YouTubeTranscriptApi.get_transcript(video_id)
                result_text = " ".join([x['text'] for x in data])
                result_lang = "auto"
                result_method = "get_transcript()"
                st.success("✅ Réussi avec get_transcript()")
            except Exception as e:
                st.warning(f"get_transcript échoué: {str(e)[:100]}")
        
        # APPROCHE 2: get_transcript avec langue
        if not result_text and 'get_transcript' in dir(YouTubeTranscriptApi):
            for lang in ['fr', 'en']:
                try:
                    st.write(f"🔄 Essai: get_transcript(languages=['{lang}'])...")
                    data = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                    result_text = " ".join([x['text'] for x in data])
                    result_lang = lang
                    result_method = f"get_transcript(lang={lang})"
                    st.success(f"✅ Réussi avec langue {lang}")
                    break
                except Exception as e:
                    st.warning(f"Langue {lang} échouée: {str(e)[:50]}")
        
        # APPROCHE 3: list_transcripts
        if not result_text and 'list_transcripts' in dir(YouTubeTranscriptApi):
            try:
                st.write("🔄 Essai: list_transcripts()...")
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Prendre le premier transcript disponible
                for transcript in transcript_list:
                    try:
                        data = transcript.fetch()
                        result_text = " ".join([x['text'] for x in data])
                        result_lang = transcript.language
                        result_method = "list_transcripts()"
                        st.success(f"✅ Réussi avec list_transcripts (langue: {transcript.language})")
                        break
                    except:
                        continue
            except Exception as e:
                st.warning(f"list_transcripts échoué: {str(e)[:100]}")
        
        # RÉSULTAT
        if result_text and len(result_text) > 20:
            st.success("🎉 **EXTRACTION RÉUSSIE !**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Langue", result_lang)
            with col2:
                st.metric("Caractères", len(result_text))
            
            st.info(f"Méthode utilisée: `{result_method}`")
            
            # Aperçu
            st.text_area("Aperçu:", result_text[:500], height=150)
            
            # Téléchargement
            st.download_button(
                "📥 Télécharger",
                data=result_text,
                file_name=f"{video_id}.txt",
                mime="text/plain"
            )
        else:
            st.error("❌ **ÉCHEC TOTAL**")
            st.error("Aucune méthode n'a fonctionné pour cette vidéo")
            
            st.markdown("""
            ### 🔧 Solutions possibles:
            
            **1. Vérifier que la vidéo a des sous-titres:**
            - Allez sur YouTube et regardez si le bouton CC est disponible
            
            **2. Réinstaller la bibliothèque:**
            ```bash
            pip uninstall youtube-transcript-api
            pip install youtube-transcript-api==0.6.2
            ```
            
            **3. Tester manuellement dans Python:**
            ```python
            from youtube_transcript_api import YouTubeTranscriptApi
            print(YouTubeTranscriptApi.get_transcript('VIDEO_ID'))
            ```
            """)

st.markdown("---")
st.caption("Version de diagnostic - affiche toutes les tentatives")
