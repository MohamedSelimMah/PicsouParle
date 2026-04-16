# Sujet — Pipeline de Generation de Video Shorts

---

## Vue d'ensemble du pipeline

Le pipeline transforme un **prompt texte** en une **video MP4** en 5 etapes :

```
[Prompt utilisateur]
       |
       v
  1. SCRIPT -----> LLM genere le texte du monologue
       |
       v
  2. VOICE ------> TTS genere l'audio du monologue
       |
       v
  3. VISUALS ----> Generation/preparation des assets visuels
       |
       v
  4. SUBTITLES --> Decoupage et synchronisation des sous-titres
       |
       v
  5. COMPOSE ----> Assemblage final en video MP4
       |
       v
  [Video MP4 prete]
```

Chaque etape est detaillee ci-dessous.

---

## Etape 1 — Generation du script (LLM)

### Objectif

A partir du prompt utilisateur, generer un **monologue court** adapte au format Shorts.

### API au choix

- **Claude** (Anthropic) — `claude-sonnet-4-20250514` ou superieur
- **GPT-4o** (OpenAI)
- **Gemini** (Google)

### Specifications

- Le texte genere doit faire **80 a 200 mots** (soit ~15-45 secondes de parole)
- Le ton doit correspondre au personnage Picsou : **avare, cynique, obsede par l'argent, mais drole**
- Le texte doit etre en **francais**
- Le LLM doit aussi generer une **description de fond/ambiance** (pour l'etape 3)

### Sortie attendue

```json
{
  "script": "Alors comme ça, tu veux prêter de l'argent à ton ami ? ...",
  "background_description": "Un coffre-fort géant rempli de pièces d'or, ambiance dorée et luxueuse",
  "mood": "sarcastique",
  "estimated_duration_seconds": 25
}
```

### Ce qu'on evalue

- Qualite du **system prompt** : est-ce que Picsou "sonne" comme Picsou ?
- Structure du prompt : instructions claires, contrainte de longueur, format de sortie
- Gestion du cas ou le LLM genere un texte trop long ou trop court (retry, truncation)

---

## Etape 2 — Generation de la voix (TTS)

### Objectif

Convertir le script en **fichier audio** avec une voix qui evoque le personnage.

### API au choix

- **OpenAI TTS** — `tts-1` ou `tts-1-hd` (recommande pour la qualite et la simplicite)
  - Voix suggerees : `onyx` (grave, autoritaire) ou `fable` (expressif)
- **Google Cloud TTS** — voix francaises disponibles
- **Gemini TTS** — si disponible dans votre region

> **Interdit :** ElevenLabs, Play.ht, ou tout autre service TTS proprietaire specialise.
> L'idee est de rester dans l'ecosysteme des API generiques des grands modeles.

### Specifications

- Format de sortie : **MP3** ou **WAV**
- Langue : **francais**
- Le choix de la voix doit etre **documente et justifie** dans le CLAUDE.md
- Si possible, recuperer les **timestamps par mot ou par phrase** (word-level timestamps) pour la synchronisation des sous-titres

### Sortie attendue

- Fichier audio `voice.mp3`
- Fichier de timestamps (JSON) si disponible :

```json
{
  "words": [
    { "word": "Alors", "start": 0.0, "end": 0.35 },
    { "word": "comme", "start": 0.35, "end": 0.55 },
    { "word": "ça", "start": 0.55, "end": 0.72 }
  ]
}
```

### Si les timestamps mot-a-mot ne sont pas disponibles

Deux approches acceptables :
1. **Estimation par duree** : diviser la duree totale de l'audio par le nombre de mots
2. **Transcription avec timestamps** : utiliser **OpenAI Whisper** (`/v1/audio/transcriptions` avec `timestamp_granularities[]=word`) pour retranscrire l'audio genere et obtenir les timestamps

> L'approche Whisper est recommandee car elle donne des timestamps reels, pas estimes.

---

## Etape 3 — Preparation des assets visuels

### Objectif

Preparer les elements visuels de la video : fond, personnage, et animation de parole.

### 3.1 Image du personnage

Fournissez une image de **Uncle Scrooge / Picsou** qui servira de base. Deux approches :

**Option A — Image statique fournie (approche recommandee)**
- Utilisez une image PNG de Picsou sur fond transparent
- Incluez l'image dans le repo dans un dossier `assets/`
- C'est l'approche la plus pragmatique dans le temps imparti

**Option B — Image generee par IA (bonus)**
- Utiliser **DALL-E 3** (via OpenAI) ou **Imagen** (via Gemini) pour generer une illustration de Picsou
- Prompt a documenter

### 3.2 Animation de parole

Le personnage doit donner l'**illusion de parler**. Sans outil de lip-sync proprietaire, voici les approches acceptees (de la plus simple a la plus ambitieuse) :

**Niveau 1 — Bounce / Scale (minimum attendu)**
- Le personnage bouge legerement (scale up/down, oscillation verticale) en rythme avec l'audio
- Detection des pics d'amplitude dans l'audio pour declencher les mouvements
- Realisable avec FFmpeg + filtres

**Niveau 2 — Bouche ouverte / fermee (attendu)**
- Deux versions de l'image : bouche ouverte + bouche fermee
- Alternance basee sur l'amplitude audio (au-dessus d'un seuil = bouche ouverte)
- Les deux images peuvent etre preparees manuellement (Pillow/Sharp) ou etre deux assets distincts

**Niveau 3 — Multi-frames + phonemes (bonus)**
- Plusieurs positions de bouche (ferme, ouvert, semi-ouvert, "O", "E")
- Mapping basique audio → position de bouche
- Plus realiste mais significativement plus complexe

> **Le Niveau 2 est le niveau attendu.** Le Niveau 1 seul est acceptable si le reste du pipeline est solide. Le Niveau 3 est un vrai bonus.

### 3.3 Fond / Background

Le fond de la video doit etre coherent avec le contenu. Approches :

- **Couleur unie ou gradient** : simple, propre (ex: fond dore pour Picsou)
- **Image generee par IA** : utiliser la `background_description` de l'etape 1 pour generer un fond via DALL-E 3 ou Imagen
- **Image statique thematique** : une image dans `assets/` (coffre-fort, bureau, etc.)

### Sortie attendue

- Fichier(s) image du personnage (PNG, fond transparent)
- Fichier image de fond (ou parametres de couleur/gradient)
- Logique d'animation definie (seuil d'amplitude, mapping frames)

---

## Etape 4 — Generation des sous-titres

### Objectif

Generer des sous-titres **dynamiques** synchronises avec l'audio, dans le style des Shorts/Reels viraux.

### Specifications

- Affichage **mot par mot** ou **par groupe de 3-5 mots**
- Le mot en cours de prononciation doit etre **mis en evidence** (couleur differente, gras, scale)
- Police lisible, grande taille (style Shorts viral)
- Position : **tiers inferieur** de la video (ou centre-bas)
- Couleur : blanc avec contour/ombre noire pour lisibilite sur tout fond

### Style de sous-titres a viser

```
Style "mot en surbrillance" :
- Afficher un bloc de 3-5 mots
- Le mot actuellement prononce est en JAUNE ou avec un highlight
- Les autres mots sont en blanc
- Transition fluide vers le bloc suivant
```

### Implementation

- Utiliser les timestamps de l'etape 2 pour synchroniser
- Generer les frames de sous-titres via **Pillow** (Python) ou **Canvas/Sharp** (Node.js)
- Ou utiliser les filtres `drawtext` de **FFmpeg** avec des timings precis

### Sortie attendue

- Fichier ASS/SRT de sous-titres **OU** logique de rendu integree dans le compositing FFmpeg

---

## Etape 5 — Assemblage final (FFmpeg)

### Objectif

Combiner tous les assets en une **video MP4** au format Shorts.

### Specifications techniques

| Parametre | Valeur |
|---|---|
| Resolution | **1080x1920** (9:16 portrait) |
| FPS | 30 |
| Codec video | H.264 |
| Codec audio | AAC |
| Format | MP4 |
| Duree | 15-45 secondes |

### Composition

```
+-------------------+
|                   |
|   [Background]    |
|                   |
|                   |
|    +---------+    |
|    |         |    |
|    | PICSOU  |    |
|    | (anime) |    |
|    |         |    |
|    +---------+    |
|                   |
|  "Sous-titres"    |
|  "dynamiques"     |
|                   |
+-------------------+
     1080x1920
```

### Implementation

Utiliser **FFmpeg** via :
- Appel CLI direct (`child_process` en Node.js ou `subprocess` en Python)
- Ou wrapper : `fluent-ffmpeg` (Node.js) / `ffmpeg-python` (Python)

### Commande FFmpeg de reference (a adapter)

```bash
ffmpeg \
  -loop 1 -i background.png \
  -i picsou_mouth_closed.png \
  -i picsou_mouth_open.png \
  -i voice.mp3 \
  -filter_complex "
    [0:v]scale=1080:1920[bg];
    [1:v]scale=400:-1[closed];
    [2:v]scale=400:-1[open];
    ... (logique d'alternance basee sur l'audio) ...
    ... (ajout des sous-titres) ...
  " \
  -c:v libx264 -c:a aac \
  -shortest \
  output.mp4
```

> La commande exacte dependra de votre approche d'animation et de sous-titres. Ce n'est qu'un point de depart.

---

## Interface utilisateur

### Minimum attendu : CLI

```bash
# Generer une video depuis un prompt
node generate.js --prompt "Explique pourquoi il ne faut jamais prêter d'argent"

# Ou en Python
python generate.py --prompt "Explique pourquoi il ne faut jamais prêter d'argent"
```

Le CLI doit afficher la **progression** de chaque etape :

```
[1/5] Generating script...        ✓ (142 words, ~28s)
[2/5] Generating voice...         ✓ (voice.mp3, 31.2s)
[3/5] Preparing visuals...        ✓ (background + character frames)
[4/5] Generating subtitles...     ✓ (47 subtitle entries)
[5/5] Composing video...          ✓ (output.mp4, 1080x1920, 31.2s)

✅ Video generated: output/video_20260415_143022.mp4
```

### Bonus : Interface web

Une interface web minimale avec :
- Champ de saisie du prompt
- Bouton "Generer"
- Barre de progression en temps reel
- Lecteur video pour previsualiser le resultat
- Historique des videos generees

---

## Recapitulatif des API autorisees

| Etape | API autorisees |
|---|---|
| Script (LLM) | Claude, GPT-4o, Gemini |
| Voix (TTS) | OpenAI TTS, Google Cloud TTS, Gemini TTS |
| Timestamps | OpenAI Whisper |
| Image fond | DALL-E 3 (OpenAI), Imagen (Gemini) |
| Image personnage | DALL-E 3, Imagen, ou asset statique |
| Assemblage | FFmpeg (obligatoire), Pillow/Sharp pour le traitement d'images |

| Interdit |
|---|
| Higgsfield, HeyGen, Synthesia, D-ID, Runway, Pika, ElevenLabs, Play.ht |
| Tout SaaS de generation/edition video ou de lip-sync |

---

## Bonus (non obligatoires)

- [ ] Interface web avec preview en temps reel
- [ ] Choix du personnage (pas seulement Picsou)
- [ ] Musique de fond generee ou selectionnee automatiquement
- [ ] Effet "Ken Burns" sur le fond (zoom lent)
- [ ] Transitions d'entree/sortie du personnage
- [ ] Export multi-format (Shorts, Reels, TikTok avec watermark different)
- [ ] Cache des assets generes pour eviter les appels API redondants
- [ ] Estimation du cout API avant generation (afficher le cout estime)
