# Guide de redaction du CLAUDE.md — Video Shorts Generator

## Specificites de ce projet

Ce projet est different d'une application web classique : c'est un **pipeline d'orchestration d'API IA**. Le CLAUDE.md doit refleter cette specificite. Un assistant IA qui reprend ce projet doit comprendre :

1. **Le flux de donnees** entre chaque etape du pipeline
2. **Les prompts utilises** et la logique derriere chaque choix
3. **Les dependances systeme** (FFmpeg notamment)
4. **Les couts** associes a chaque appel API

---

## Sections attendues

### 1. Vue d'ensemble du pipeline

Schema du flux de donnees : prompt → script → audio → visuels → sous-titres → video.
Pour chaque etape : quelle API, quelle entree, quelle sortie.

### 2. Prompts et prompt engineering

C'est la section la plus importante pour ce projet. Documentez :

- Le **system prompt** utilise pour la generation du script
- **Pourquoi** ce prompt : quelles iterations, quels echecs avant d'arriver a cette version
- Les **parametres** du LLM (temperature, max tokens, modele) et pourquoi
- Comment le **format de sortie** est contraint (JSON, longueur)

> **Exemple de bonne documentation :**
>
> *"Le system prompt insiste sur 'Tu es Picsou, le canard le plus riche du monde' plutot que 'Imite Picsou' car les premiers tests donnaient un personnage generique. Ajouter des references specifiques (coffre-fort, sous, avarice) dans le prompt a considerablement ameliore la coherence du personnage. Temperature a 0.8 pour garder de la creativite tout en restant dans le personnage."*

### 3. Choix techniques detailles

Pour chaque brique, expliquer le choix et les alternatives envisagees :

- **LLM** : pourquoi Claude / OpenAI / Gemini pour le script ?
- **TTS** : pourquoi cette voix ? Quelles voix testees ?
- **Animation** : quelle approche choisie (niveau 1/2/3) et pourquoi ?
- **Sous-titres** : rendu via FFmpeg drawtext ou via frames pre-rendues ?
- **FFmpeg** : un pass ou multi-pass ? Pourquoi ?

### 4. Commandes

```markdown
## Commandes

### Prerequis
- FFmpeg installe (`ffmpeg -version` pour verifier)
- Node.js 20+ / Python 3.11+
- Cles API configurees dans `.env`

### Generer une video
node src/index.ts --prompt "Ton prompt ici"

### Options
--voice onyx          # Choisir la voix TTS
--provider anthropic  # Choisir le provider LLM
--output ./output     # Dossier de sortie
--keep-temp           # Garder les fichiers intermediaires
```

### 5. Structure des fichiers intermediaires

Expliquer ce que le pipeline genere dans le dossier temporaire :

```
tmp/gen_20260415_143022/
|-- script.json          # Texte genere par le LLM
|-- voice.mp3            # Audio TTS
|-- timestamps.json      # Timestamps Whisper
|-- amplitudes.json      # Amplitude par frame
|-- background.png       # Image de fond
|-- frames/              # Frames composites (si approche multi-frames)
|   |-- frame_0001.png
|   |-- frame_0002.png
|   |-- ...
|-- subtitles.ass        # Fichier sous-titres
|-- output.mp4           # Video finale
```

### 6. Cout et performance

| Etape | API | Cout estime |
|---|---|---|
| Script | Claude Sonnet | ~$0.003 |
| TTS | OpenAI tts-1 | ~$0.015 / 1000 chars |
| Whisper | OpenAI Whisper | ~$0.006 / minute |
| Image fond | DALL-E 3 (optionnel) | ~$0.040 |
| **Total** | | **~$0.06 - $0.10 / video** |

### 7. Limites et ameliorations

Etre honnete sur :
- Ce qui ne marche pas parfaitement (synchro, qualite animation)
- Ce qui prendrait plus de temps (lip-sync avance, multi-personnages)
- Les edge cases non geres (texte trop long, API down, etc.)

---

## Criteres de qualite

Le CLAUDE.md de ce projet est juge plus severement sur :

| Critere | Pourquoi |
|---|---|
| **Documentation des prompts** | C'est le coeur du projet — un prompt mal documente est une boite noire |
| **Honnetete sur les limites** | L'animation simplifiee a des limites visibles — les documenter montre la maturite |
| **Reproductibilite** | Un autre dev doit pouvoir generer une video en < 5 min apres avoir lu le CLAUDE.md |
| **Estimation des couts** | Gerer un budget API est une competence cle pour un dev travaillant avec l'IA |
