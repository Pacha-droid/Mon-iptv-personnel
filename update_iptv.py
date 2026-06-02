import requests
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION DU TESTEUR ---
MAX_THREADS = 40         # Nombre de vérifications simultanées (ajustable selon ta connexion)
TIMEOUT_CONNEXION = 3.0  # Temps max d'attente par flux (en secondes)

def optimiser_et_fusionner():
    FICHIER_LOCAL = "ma_playlist.m3u"
    FICHIER_SORTIE = "playlist_finale.m3u"
    
    IP_ACTUELLE = "151.80.18.177:86"
    NOUVELLE_IP = "151.80.18.177:86" 
    TOKEN_SPORT = "" 
    
    USER_AGENT_FORCÉ = "|User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # --- 1. SOURCES PERMANENTES ET SÛRES ---
    SOURCES_STABLES = {
        "Pacha-droid": "https://raw.githubusercontent.com/Pacha-droid/playlist-iptv/main/playlist.m3u",
        "Free_TV_Global": "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
        "Pluto_TV_FR": "https://i.mjh.nz/PlutoTV/fr.m3u8"
    }

    # --- 2. SOURCES TEMPORAIRES MISES À JOUR QUOTIDIENNEMENT (SPORTS PREMIUM) ---
    # Ces dépôts GitHub sont mis à jour toutes les 24h par des scripts automatiques
    SOURCES_TEMPORAIRES = {
        "Daily_Auto_Sport": "https://raw.githubusercontent.com/FazzR9/IPTV-Daily/master/Sport.m3u",
        "StaySane_Daily": "https://raw.githubusercontent.com/StaySaneApp/Daily-IPTV/main/sport.m3u",
        "Arab_Daily_Channels": "https://iptv-org.github.io/iptv/languages/ara.m3u"
    }
    
    # Fusion de toutes les sources dans un seul dictionnaire pour le traitement
    TOUTES_SOURCES = {**SOURCES_STABLES, **SOURCES_TEMPORAIRES}
    
    candidats_chaines = []
    lignes_finales = ["#EXTM3U\n"]
    urls_uniques_detection = set() # Pour éviter de tester deux fois exactement le même lien HTTP

    def attribuer_groupe_intelligent(ligne_extinf):
        nom_chaine = ligne_extinf.split(",")[-1].lower() if "," in ligne_extinf else ""
        if any(mot in nom_chaine for mot in ["sport", "bein", "foot", "eurosport", "golf", "canal+", "rmc", "arena", "ssc", "alkass"]):
            if any(ar in nom_chaine for ar in ["ar", "arabic", "arab", "بين", "الكأس", "ssc"]):
                return 'group-title="Sports AR"'
            elif any(en in nom_chaine for en in ["en", "uk", "us", "usa", "english"]):
                return 'group-title="Sports EN"'
            elif any(es in nom_chaine for es in ["es", "esp", "spain"]):
                return 'group-title="Sports ES"'
            else:
                return 'group-title="Sports FR"'
        elif any(ar in nom_chaine for ar in ["ar:", "arabic", "mbc", "rotana", "al jazeera", "news"]):
            return 'group-title="Chaines AR"'
        elif any(en in nom_chaine for en in ["en:", "sky", "bbc"]):
            return 'group-title="Chaines EN"'
        return 'group-title="Chaines FR"'

    def extraire_nom_pur(ligne_extinf):
        """Extrait proprement le nom de la chaîne après la virgule pour la détection des doublons"""
        if "," in ligne_extinf:
            return ligne_extinf.split(",")[-1].strip().upper()
        return ligne_extinf.strip().upper()

    def verifier_un_flux(item):
        """Teste la validité du flux en arrière-plan"""
        extinf, url_complete = item
        url_pure = url_complete.split('|')[0].strip()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        try:
            # Requête GET légère (stream=True) pour passer les protections
            with requests.get(url_pure, headers=headers, timeout=TIMEOUT_CONNEXION, stream=True) as r:
                if r.status_code == 200:
                    return extinf, url_complete
        except Exception:
            pass
        return None

    # --- ÉTAPE 1 : LECTURE DU FICHIER LOCAL ---
    print("⏳ Analyse de votre playlist locale...")
    if os.path.exists(FICHIER_LOCAL):
        with open(FICHIER_LOCAL, "r", encoding="utf-8") as f:
            lignes = f.readlines()
            
        extinf_temp = None
        for ligne in lignes:
            ligne = ligne.strip()
            if ligne.startswith("#EXTINF"):
                nouveau_groupe = attribuer_groupe_intelligent(ligne)
                ligne = re.sub(r'group-title="[^"]*"', nouveau_groupe, ligne) if 'group-title=' in ligne else ligne.replace(',', f' {nouveau_groupe},')
                extinf_temp = ligne
            elif ligne.startswith("http") and extinf_temp:
                ligne_modifiee = ligne.replace(IP_ACTUELLE, NOUVELLE_IP)
                if "stream.m3u8?d=w&id=" in ligne_modifiee and TOKEN_SPORT:
                    ligne_modifiee += TOKEN_SPORT
                if "|User-Agent=" not in ligne_modifiee:
                    ligne_modifiee += USER_AGENT_FORCÉ
                
                if ligne_modifiee not in urls_uniques_detection:
                    urls_uniques_detection.add(ligne_modifiee)
                    candidats_chaines.append((extinf_temp, ligne_modifiee))
                extinf_temp = None

    # --- ÉTAPE 2 : DOSSIER DES SOURCES DISTANTES (STABLES + QUOTIDIENNES) ---
    for nom_source, url in TOUTES_SOURCES.items():
        print(f"⏳ Aspiration de la source : {nom_source}...")
        try:
            response = requests.get(url, timeout=12)
            if response.status_code == 200:
                lignes_distantes = response.text.splitlines()
                extinf_temp = None
                for ligne in lignes_distantes:
                    ligne = ligne.strip()
                    if ligne.startswith("#EXTINF"):
                        nouveau_groupe = attribuer_groupe_intelligent(ligne)
                        ligne = re.sub(r'group-title="[^"]*"', nouveau_groupe, ligne) if 'group-title=' in ligne else ligne.replace(',', f' {nouveau_groupe},')
                        extinf_temp = ligne
                    elif ligne.startswith("http") and extinf_temp:
                        if "|User-Agent=" not in ligne:
                            ligne += USER_AGENT_FORCÉ
                        
                        # Anti-doublon d'URL primaire (inutile de tester deux fois le même lien exact)
                        if ligne not in urls_uniques_detection:
                            urls_uniques_detection.add(ligne)
                            candidats_chaines.append((extinf_temp, ligne))
                        extinf_temp = None
        except Exception as e:
            print(f"❌ Erreur de téléchargement pour {nom_source}")

    # --- ÉTAPE 3 : LE FILTRE MULTI-THREADÉ ---
    total_liens = len(candidats_chaines)
    print(f"\n🚀 Nettoyage et vérification en cours sur {total_liens} flux capturés...")
    
    chaines_valides_brutes = []
    compteur = 0
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(verifier_un_flux, item): item for item in candidats_chaines}
        for future in as_completed(futures):
            compteur += 1
            resultat = future.result()
            if resultat:
                chaines_valides_brutes.append(resultat)
            if compteur % 150 == 0 or compteur == total_liens:
                print(f"🔄 Analyse : {compteur}/{total_liens} liens testés...")

    # --- ÉTAPE 4 : DÉDUPLICATION STRICTE PAR NOM DE CHAÎNE ET GROUPE ---
    print("\n🧹 Suppression des chaînes en doublon...")
    chaines_uniques_finales = []
    cles_chaines_vues = set() # Format de clé : ("NOM DE CHAINE", "GROUPE")

    for extinf, url in chaines_valides_brutes:
        nom_pur = extraire_nom_pur(extinf)
        
        # Extraction du groupe pour affiner la clé unique
        match_groupe = re.search(r'group-title="([^"]+)"', extinf)
        groupe = match_groupe.group(1) if match_groupe else "Chaines FR"
        
        cle_unique = (nom_pur, groupe)
        
        # Si cette chaîne dans ce groupe n'a pas encore de lien fonctionnel validé, on la garde !
        if cle_unique not in cles_chaines_vues:
            cles_chaines_vues.add(cle_unique)
            chaines_uniques_finales.append((extinf, url))

    # --- ÉTAPE 5 : ÉCRITURE DU FICHIER M3U UNIQUE ---
    print(f"✍️ Génération de '{FICHIER_SORTIE}'...")
    for extinf, url in chaines_uniques_finales:
        lignes_finales.append(extinf + "\n")
        lignes_finales.append(url + "\n")
        
    with open(FICHIER_SORTIE, "w", encoding="utf-8") as f:
        f.writelines(lignes_finales)
        
    doublons_elimines = len(chaines_valides_brutes) - len(chaines_uniques_finales)
    print(f"🎉 Nettoyage réussi !")
    print(f"✅ Liens fonctionnels trouvés : {len(chaines_valides_brutes)}")
    print(f"🗑️ Doublons fonctionnels éliminés : {doublons_elimines}")
    print(f"📦 Total de chaînes uniques et actives sauvegardées : {len(chaines_uniques_finales)} dans '{FICHIER_SORTIE}'.")

if __name__ == "__main__":
    optimiser_et_fusionner()


