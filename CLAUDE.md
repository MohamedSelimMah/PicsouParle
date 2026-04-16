# CLAUDE.md — Picsou Parle

Guide technique pour un assistant IA reprenant ce projet.

---

## Vue d'ensemble du pipeline

```
[Prompt utilisateur]
        │
        ▼
  1. generate_script    → LLM (OpenRouter) → Script JSON (title, lines, mood…)
        │
        ▼
  2. generate_voice     → edge-tts → voice.mp3 + word timestamps
        │
        ▼
  3. generate_timestamps→ Whisper (fallback) ou timestamps edge-tts natifs
        │
        ▼
  4. prepare_visuals    → Pillow → background.png + amplitudes par frame
        │
        ▼
  5. build_subtitles    → Pillow → frames sous-titres pre-rendues
        │
        ▼
  6. compose_video      → FFmpeg → output/{run_id}.mp4 1080×1920 H.264/AAC
```

Chaque étape reçoit un `PipelineContext` (dataclass) et retourne une version enrichie.
L'état est porté par `context.py` — pas de variables globales entre étapes.

---

## 1. Dépendances système

```bash
# FFmpeg obligatoire
ffmpeg -version   # >= 4.x

# Python >= 3.11
pip install -r requirements.txt
```

Variables d'environnement dans `.env` (copier `.env.example`) :

```
OPENROUTER_API_KEY=sk-or-v1-...   # openrouter.ai
LLM_MODEL=google/gemma-4-26b-a4b-it:free
TTS_VOICE=fr-FR-HenriNeural
```

---

## 2. Commandes

### Générer une vidéo (CLI)

```bash
python -m backend.cli --prompt "Pourquoi ne jamais prêter d'argent à ses amis"

# Options utiles
python -m backend.cli \
  --prompt "Ton prompt" \
  --voice fr-FR-HenriNeural \
  --model google/gemma-4-26b-a4b-it:free \
  --from-step compose_video \   # reprendre depuis une étape
  --keep-temp                   # garder les fichiers tmp/
  --verbose
```

### Démarrer l'API web

```bash
uvicorn backend.main:app --reload --port 8000
# Frontend statique servi sur http://localhost:8000
# API sur http://localhost:8000/api/generate
```

### Lancer les tests

```bash
pytest tests/ -v
# Test d'intégration complet
python test_pipeline.py
```

---

## 3. Prompt engineering — Génération du script

**Fichier :** `prompts/picsou_script.txt`

### Le system prompt

Le prompt place directement l'assistant en personnage (« Tu es Balthazar Picsou ») plutôt que de demander de l'imiter. Cette formulation donne un ancrage plus fort : les premiers tests avec « Imite Picsou » produisaient un personnage générique sans saveur.

Points clés du prompt :
- **Contrainte de longueur explicite** : 80–200 mots, 4–10 répliques courtes → évite les monologues trop longs qui dépassent la durée cible des Shorts
- **Format JSON strict** avec les champs `title`, `lines[]`, `background_description`, `mood`, `estimated_duration_seconds` → parsing fiable sans post-traitement
- **Liste d'émotions** (grumpy, sarcastic, proud…) → permet l'animation future par émotion
- **Température à 0.8** → assez de créativité pour varier les scripts, assez bas pour rester dans le personnage

### Gestion des échecs

Si le LLM retourne un JSON invalide ou un script trop court/long, le pipeline relance jusqu'à `MAX_SCRIPT_RETRIES` fois (défaut : 3) avec un message de correction joint à la conversation :

```python
correction = f"Le script précédent avait {word_count} mots. Respecte la contrainte de 80–200 mots."
```

### Fallback de modèles

Si le modèle primaire est rate-limité (HTTP 429), le client bascule automatiquement sur une chaîne de fallback définie dans `backend/providers/llm.py` :

```python
FALLBACK_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "z-ai/glm-4.5-air:free",
    "openai/gpt-oss-120b:free",
    ...
]
```

---

## 4. Génération de voix (TTS)

**Provider choisi : `edge-tts` (Microsoft Edge TTS — gratuit, pas de clé API)**

### Pourquoi edge-tts ?

| Option | Qualité | Coût | Timestamps natifs |
|---|---|---|---|
| OpenAI TTS | ★★★★★ | ~$15/1M chars | Non (Whisper requis) |
| Google Cloud TTS | ★★★★☆ | ~$4/1M chars | Oui (SSML) |
| **edge-tts** | ★★★★☆ | **Gratuit** | **Oui (WordBoundary)** |
| ElevenLabs | ★★★★★ | $22+/mois | Non |

edge-tts retourne des événements `WordBoundary` en temps réel pendant la synthèse, donnant des timestamps mot-à-mot sans appel Whisper supplémentaire. La voix `fr-FR-HenriNeural` est la voix masculine française la plus naturelle disponible gratuitement.

**Voix testées :** `fr-FR-HenriNeural` (retenu — grave, posé), `fr-FR-AlainNeural` (trop neutre), `fr-FR-RemyMultilingualNeural` (bon mais moins caractérisé).

### Sortie

```
tmp/{run_id}_timestamps.json   → [{word, start, end}, …]
tmp/{run_id}/voice.mp3
```

---

## 5. Animation du personnage (Niveau 2)

### Approche retenue : bouche ouverte / fermée

Deux assets : `assets/character/picsou_mouth_closed.png` et `picsou_mouth_open.png`.

Pour chaque frame vidéo (30fps), l'amplitude RMS de l'audio est comparée à un seuil adaptatif :

```python
threshold = mean_amplitude * 0.6
mouth_open = amplitude[frame] > threshold
```

Le seuil est **adaptatif** : calculé sur les stats de l'audio de chaque run, pas un magic number. Cela gère les différences de volume entre voix.

### Extraction d'amplitude

FFmpeg décode l'audio en PCM 16kHz mono via `pipe:1`, puis Python calcule le RMS par intervalle de 33ms (1 frame à 30fps).

### Effets visuels supplémentaires

- **Ken Burns** sur le fond : zoom lent 1.0 → 1.04 sur toute la durée
- **Fade in/out** du personnage : 0.6s en entrée, 0.4s en sortie (opacité via canal alpha)

---

## 6. Sous-titres dynamiques

### Approche : frames pré-rendues via Pillow

Les sous-titres sont rendus directement dans chaque frame PNG avant l'encodage FFmpeg, plutôt que via `drawtext` FFmpeg. Cela permet un contrôle pixel-perfect sur :
- La police (Montserrat Bold ou fallback système)
- Le fond semi-transparent du bloc sous-titre
- La couleur du mot courant (jaune `#FFD700`) vs les autres (blanc)
- Les ombres portées pour lisibilité

Les mots sont groupés par blocs de 5 mots maximum ou 2.5s maximum. Le mot actuellement prononcé est mis en surbrillance en comparant le timestamp de la frame avec les intervalles `[start, end]` de chaque mot.

---

## 7. Assemblage FFmpeg

Un seul appel FFmpeg lit les frames PNG depuis stdin (pipe), ajoute l'audio MP3, et encode en H.264/AAC :

```
-c:v libx264 -preset fast -crf 23
-c:a aac -b:a 192k
-pix_fmt yuv420p   # compatibilité maximale
-movflags +faststart  # lecture progressive web
```

Si un fichier `assets/music/*.mp3` existe, il est mixé à volume réduit (`MUSIC_VOLUME=0.12`) via `amix` :

```
[voice][music]amix=inputs=2:weights=1 0.12:normalize=0
```

---

## 8. Structure des fichiers intermédiaires

```
tmp/
└── {run_id}/
    ├── voice.mp3              # Audio TTS
    ├── background.png         # Fond généré (gradient + vignette)
    ├── character_closed.png   # Asset copié depuis assets/
    ├── character_open.png
    ├── subtitles.ass          # Fichier ASS de sous-titres
    └── visuals/               # Frames PNG composites (supprimées après encodage)
        ├── frame_0001.png
        └── …
tmp/{run_id}_timestamps.json   # Timestamps mot-à-mot
output/{run_id}.mp4            # Vidéo finale
```

Par défaut les fichiers `tmp/` sont supprimés après composition. Utiliser `--keep-temp` pour les conserver (debug).

---

## 9. Coût et performance

| Étape | Outil | Coût |
|---|---|---|
| Script | OpenRouter (modèles gratuits) | **$0.00** |
| TTS | edge-tts | **$0.00** |
| Timestamps | edge-tts natif | **$0.00** |
| Fond | Gradient Pillow | **$0.00** |
| Composition | FFmpeg local | **$0.00** |
| **Total** | | **$0.00 / vidéo** |

Avec des modèles payants (ex: Claude Sonnet + OpenAI TTS) : ~$0.05–0.10/vidéo.

**Performance typique** (machine avec 8 cœurs, pas de GPU) :
- Script : 3–8s
- TTS : 2–5s
- Visuals + frames : 15–40s (dépend de la durée)
- FFmpeg encode : 3–8s
- **Total : ~25–60s**

---

## 10. Limites connues et améliorations possibles

**Ce qui ne marche pas parfaitement :**
- La synchronisation bouche/parole peut avoir un décalage de ±1 frame (33ms) dû à la granularité des timestamps edge-tts
- Sur des voix très rapides, les blocs de sous-titres de 5 mots peuvent défiler trop vite
- L'animation se limite à 2 états (bouche ouverte/fermée) — pas de visèmes

**Ce qu'il faudrait plus de temps pour faire :**
- **Lip-sync avancé (Level 3)** : extraire les phonèmes de l'audio via `phonemizer` + mapper sur 5–6 positions de bouche (fermé, ouvert, rond, dents, etc.)
- **Génération du fond par IA** : appeler DALL-E 3 avec la `background_description` du script
- **Multi-personnages** : support d'un deuxième personnage qui interagit
- **Cache des assets** : éviter de régénérer le fond si le `mood` est identique au run précédent

**Edge cases non gérés :**
- Prompt vide ou contenant uniquement des caractères spéciaux
- Audio de durée nulle retourné par le TTS
- FFmpeg absent du PATH sur certaines distributions Windows
