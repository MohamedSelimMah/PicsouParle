# Architecture Technique — Video Shorts Generator

---

## Langage

**Node.js (TypeScript)** ou **Python** — au choix du candidat.

Les deux sont acceptes. Le choix doit etre justifie dans le CLAUDE.md.

| | Node.js / TypeScript | Python |
|---|---|---|
| Points forts | Typage, async natif, ecosystem npm | Pillow pour l'image, ffmpeg-python, libs audio |
| TTS | OpenAI SDK natif | OpenAI SDK natif |
| FFmpeg | `fluent-ffmpeg` ou `child_process` | `ffmpeg-python` ou `subprocess` |
| Traitement image | `sharp`, `canvas` | `Pillow (PIL)` |
| Traitement audio | `wav-decoder`, `audiobuffer-to-wav` | `pydub`, `librosa`, `numpy` |

---

## Structure du projet

```
picsou-shorts/
|-- package.json (ou pyproject.toml / requirements.txt)
|-- CLAUDE.md
|-- README.md
|-- .env.example
|-- .gitignore
|
|-- src/
|   |-- index.ts (ou main.py)         # Point d'entree CLI
|   |-- pipeline.ts                    # Orchestrateur du pipeline
|   |
|   |-- steps/
|   |   |-- 01-script.ts              # Generation du script via LLM
|   |   |-- 02-voice.ts               # Generation audio TTS
|   |   |-- 03-visuals.ts             # Preparation des assets visuels
|   |   |-- 04-subtitles.ts           # Generation des sous-titres
|   |   |-- 05-compose.ts             # Assemblage FFmpeg
|   |
|   |-- services/
|   |   |-- llm.ts                    # Client LLM (Claude/OpenAI/Gemini)
|   |   |-- tts.ts                    # Client TTS
|   |   |-- whisper.ts                # Client Whisper (timestamps)
|   |   |-- image-gen.ts              # Client generation d'images (optionnel)
|   |   |-- ffmpeg.ts                 # Wrapper FFmpeg
|   |
|   |-- utils/
|   |   |-- audio.ts                  # Analyse audio (amplitude, duree)
|   |   |-- image.ts                  # Manipulation d'images (resize, overlay)
|   |   |-- time.ts                   # Helpers de formatage de temps
|   |
|   |-- types/
|   |   |-- pipeline.ts               # Types du pipeline (entree/sortie de chaque etape)
|   |   |-- api.ts                    # Types des reponses API
|   |
|   |-- prompts/
|       |-- script-system.txt         # System prompt pour la generation du script
|       |-- script-user.txt           # Template du user prompt
|
|-- assets/
|   |-- picsou_mouth_closed.png       # Personnage bouche fermee
|   |-- picsou_mouth_open.png         # Personnage bouche ouverte
|   |-- fonts/
|       |-- Montserrat-Bold.ttf       # Police pour les sous-titres
|
|-- output/                           # Videos generees (gitignored sauf demo)
|   |-- demo.mp4                      # Video de demonstration
|
|-- tests/                            # Tests (bonus)
    |-- script.test.ts
    |-- subtitles.test.ts
```

---

## Prerequis systeme

Le candidat doit documenter ces prerequis dans le README :

- **FFmpeg** installe et accessible dans le PATH
  - macOS : `brew install ffmpeg`
  - Linux : `apt install ffmpeg`
  - Windows : `choco install ffmpeg`
- **Node.js 20+** (si TypeScript) ou **Python 3.11+** (si Python)
- **Cles API** : au moins une parmi Claude / OpenAI / Gemini

---

## Variables d'environnement

```env
# .env.example

# Au moins une cle API LLM requise
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_AI_API_KEY=AI...

# Configuration optionnelle
LLM_PROVIDER=anthropic          # anthropic | openai | google
TTS_PROVIDER=openai             # openai | google
TTS_VOICE=onyx                  # Voix TTS a utiliser
OUTPUT_DIR=./output
DEFAULT_LANGUAGE=fr
```

---

## Pattern du pipeline

### Architecture recommandee

Chaque etape du pipeline doit :
1. Recevoir un **contexte** (resultat des etapes precedentes)
2. Effectuer son traitement
3. Retourner un **resultat type** ajoute au contexte
4. Ecrire ses fichiers intermediaires dans un dossier temporaire

```typescript
// Exemple de type pour le pipeline (TypeScript)

interface PipelineContext {
  prompt: string;
  workDir: string;              // Dossier temporaire pour cette generation

  // Rempli par etape 1
  script?: {
    text: string;
    backgroundDescription: string;
    mood: string;
    wordCount: number;
  };

  // Rempli par etape 2
  voice?: {
    audioPath: string;
    durationSeconds: number;
  };

  // Rempli par etape 3
  visuals?: {
    backgroundPath: string;
    characterFrames: {
      mouthClosed: string;
      mouthOpen: string;
    };
  };

  // Rempli par etape 4
  subtitles?: {
    entries: SubtitleEntry[];
    assFilePath?: string;
  };

  // Rempli par etape 5
  output?: {
    videoPath: string;
    resolution: string;
    durationSeconds: number;
  };
}

interface SubtitleEntry {
  text: string;
  startMs: number;
  endMs: number;
  highlightWord?: string;
}
```

### Gestion des erreurs

Chaque etape doit :
- Logger clairement ce qu'elle fait
- Echouer proprement avec un message explicite si une API est indisponible
- Permettre de **reprendre le pipeline a une etape donnee** (si les fichiers intermediaires existent)

```bash
# Relancer seulement l'assemblage si les etapes 1-4 sont deja faites
node generate.js --prompt "..." --from-step 5 --work-dir ./tmp/gen_20260415
```

---

## Gestion de l'audio pour l'animation

### Analyse d'amplitude

Pour faire "parler" le personnage, il faut detecter quand il y a de la voix active dans l'audio.

**Approche recommandee :**

1. Charger le fichier audio
2. Decouper en frames (ex: toutes les 33ms pour 30 FPS)
3. Calculer l'amplitude RMS de chaque frame
4. Definir un seuil : au-dessus = bouche ouverte, en dessous = bouche fermee

```typescript
// Pseudo-code
function getAmplitudePerFrame(audioPath: string, fps: number): number[] {
  const audio = loadAudio(audioPath);
  const frameDuration = 1 / fps;
  const amplitudes: number[] = [];

  for (let t = 0; t < audio.duration; t += frameDuration) {
    const chunk = audio.slice(t, t + frameDuration);
    amplitudes.push(calculateRMS(chunk));
  }

  return amplitudes;
}

function isMouthOpen(amplitude: number, threshold: number): boolean {
  return amplitude > threshold;
}
```

### Seuil adaptatif

Le seuil d'amplitude ne doit pas etre une valeur fixe. Recommandation :
- Calculer l'amplitude moyenne sur l'ensemble de l'audio
- Le seuil = `moyenne * 0.6` (a ajuster)
- Cela s'adapte aux voix plus ou moins fortes

---

## Assemblage FFmpeg

### Approche recommendee

Plutot qu'une seule commande FFmpeg monstrueuse, decomposer en sous-etapes :

1. **Generer la sequence d'images du personnage** (frames PNG)
   - Pour chaque frame (30/s) : choisir bouche ouverte ou fermee selon l'amplitude
   - Ecrire `frame_0001.png`, `frame_0002.png`, etc.

2. **Composer chaque frame complete** (fond + personnage + sous-titre)
   - Superposer le personnage sur le fond
   - Ajouter le texte du sous-titre actif
   - Ecrire la frame composite finale

3. **Assembler les frames en video + audio**
   ```bash
   ffmpeg -framerate 30 -i frames/frame_%04d.png -i voice.mp3 \
          -c:v libx264 -pix_fmt yuv420p -c:a aac output.mp4
   ```

**Alternative** (plus performante, plus complexe) : utiliser les filtres FFmpeg (`overlay`, `drawtext`, `select`) pour tout faire en un seul pass.

Les deux approches sont acceptees. La premiere est plus lisible, la seconde plus performante.

---

## Performance et cout

Le candidat doit documenter dans le CLAUDE.md :

- **Temps de generation** estime pour une video de 30 secondes
- **Cout API** estime par video (tokens LLM + TTS + Whisper + image gen)
- **Strategies d'optimisation** envisagees (cache, parallelisation des appels API, etc.)
