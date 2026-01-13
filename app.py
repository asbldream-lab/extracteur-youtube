import streamlit as st
from googleapiclient.discovery import build

# --- CONFIGURATION DU SITE ---
st.set_page_config(page_title="Radar à Angles YouTube", page_icon="🎯", layout="wide")

st.title("🎯 Radar à Angles (Version Gratuite)")
st.markdown("""
**Mode d'emploi :**
1. Entrez un sujet (ex: "Cryptomonnaie", "Maquillage bio").
2. Le script scanne 50 vidéos et récupère les commentaires.
3. Il génère un texte magique à copier-coller dans ChatGPT.
""")

# --- BARRE LATÉRALE (Clé API) ---
with st.sidebar:
    st.header("Configuration")
    youtube_api_key = st.text_input("Clé API YouTube Data V3", type="password")
    st.info("Cette clé est nécessaire pour que le script puisse 'voir' YouTube.")
    st.markdown("[Tuto pour avoir la clé gratuite](https://blog.hubspot.fr/website/cle-api-youtube)")

# --- FONCTIONS TECHNIQUES ---

def get_video_ids(query, api_key):
    """Cherche les 50 vidéos les plus pertinentes."""
    youtube = build('youtube', 'v3', developerKey=api_key)
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=50,
        type='video',
        order='relevance'
    ).execute()
    return [item['id']['videoId'] for item in search_response['items']]

def get_comments_batch(video_ids, api_key):
    """Récupère les meilleurs commentaires."""
    youtube = build('youtube', 'v3', developerKey=api_key)
    all_comments = []
    
    # Barre de chargement visuelle
    bar = st.progress(0)
    status = st.empty()
    
    for i, video_id in enumerate(video_ids):
        # Mise à jour de la barre
        bar.progress((i + 1) / len(video_ids))
        status.text(f"Lecture de la vidéo {i+1}/50...")
        
        try:
            # On prend les 10 meilleurs commentaires par vidéo
            response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=10, 
                textFormat='plainText',
                order='relevance'
            ).execute()
            
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                # Petit nettoyage du texte
                clean_comment = comment.replace('\n', ' ').strip()
                # On garde que les commentaires de plus de 20 caractères (les vrais avis)
                if len(clean_comment) > 20: 
                    all_comments.append(clean_comment)
        except:
            continue # Si erreur (commentaires désactivés), on passe à la suivante
            
    status.empty()
    bar.empty()
    return all_comments

# --- INTERFACE PRINCIPALE ---

query = st.text_input("Sujet à analyser", "")

if st.button("Lancer l'analyse 🚀"):
    if not youtube_api_key:
        st.error("⚠️ Oups ! Il manque la clé API YouTube dans la barre latérale (à gauche).")
    elif not query:
        st.warning("Veuillez écrire un sujet dans la barre de recherche.")
    else:
        with st.spinner("Le robot travaille pour vous..."):
            try:
                # 1. On récupère les IDs des vidéos
                ids = get_video_ids(query, youtube_api_key)
                
                # 2. On récupère les commentaires
                comments = get_comments_batch(ids, youtube_api_key)
                
                # 3. On prépare le texte pour ChatGPT (on coupe à 120 commentaires max pour éviter que ce soit trop long)
                comments_sample = comments[:120] 
                comments_text = "\n- ".join(comments_sample)
                
                # 4. Le Prompt Expert (La consigne pour l'IA)
                final_prompt = f"""
Tu es un expert en stratégie de contenu YouTube et en psychologie des audiences. Je vais te fournir une liste brute de commentaires extraits des vidéos les plus populaires sur le sujet : "{query}".

TA MISSION :
Analyse ces données pour trouver les "trous dans le marché" (ce que les gens veulent mais ne trouvent pas). Ignore les commentaires simples comme "super vidéo" et concentre-toi sur les questions, les frustrations, les débats et les critiques.

RÉPONDS EXACTEMENT SOUS CE FORMAT :

1️⃣ ANALYSE DES FRUSTRATIONS (PAIN POINTS)
• Liste les 3 problèmes majeurs ou incompréhensions qui reviennent le plus.
• Quel est le sentiment dominant (Colère, Peur, Curiosité, Scepticisme) ?

2️⃣ LES 3 ANGLES DE VIDÉOS VIRAUX
Propose 3 concepts de vidéos conçus pour faire des vues, basés sur l'analyse ci-dessus. Pour chaque angle :
• L'Idée : En une phrase.
• Titre "Pute-à-clic" (Éthique mais irrésistible) : Doit créer du mystère ou de l'urgence.
• La Promesse : Ce que le spectateur va apprendre qu'il ne sait pas déjà.
• La Preuve : Cite un type de commentaire qui justifie ce choix.

Voici les commentaires à analyser :
{comments_text}
                """
                
                # 5. Affichage du résultat
                st.success(f"Terminé ! J'ai lu {len(comments)} commentaires.")
                st.divider()
                st.subheader("👇 Étape finale : Copiez ce texte dans ChatGPT")
                st.info("Cliquez sur le petit bouton 'copier' en haut à droite du bloc noir ci-dessous.")
                
                st.code(final_prompt, language="text")

            except Exception as e:
                st.error(f"Une erreur est survenue : {e}. Vérifiez votre clé API.")
