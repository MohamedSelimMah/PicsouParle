# Test Technique #2 — Generateur de Video Shorts par IA

## "Picsou Parle" — Pipeline de generation de short videos

---

**Duree estimee :** 4 heures
**Stack :** Node.js ou Python + API IA (Claude / OpenAI / Gemini) + FFmpeg
**Livrable :** Repository Git + au moins 1 video generee de demo

---

## Concept

Vous connaissez peut-etre le compte Instagram **@rabintouchable** : des videos courtes (15-60 secondes) avec un personnage illustre qui "parle" sur un fond simple, accompagne de sous-titres dynamiques. Le format est viral, simple visuellement, mais techniquement interessant a automatiser.

**Votre mission :** construire un pipeline qui, a partir d'un simple prompt texte, genere automatiquement une video de type Shorts/Reels prete a etre publiee.

Le personnage utilise pour ce test sera **Uncle Scrooge (Picsou)**.

### Exemple de prompt en entree

```
Explique pourquoi il ne faut jamais prêter d'argent à ses amis, sur un ton
humoristique et cynique, comme si Picsou donnait un conseil financier.
```

### Resultat attendu

Une video MP4 de 15 a 45 secondes contenant :
- Un **fond** sobre ou thematique (couleur unie, gradient, ou image generee)
- Le **personnage Picsou** au centre/premier plan, avec une animation de parole
- Une **voix off** generee par IA lisant le texte
- Des **sous-titres** dynamiques synchronises mot par mot ou phrase par phrase

---

## Contrainte technique majeure

> **Aucun service proprietaire de generation video** (Higgsfield, HeyGen, Synthesia, D-ID, Runway, etc.)
>
> Uniquement des **API generiques d'IA** (Claude, OpenAI, Gemini) combinees a des **outils open source** (FFmpeg, Pillow/Sharp, etc.) pour l'assemblage.

L'objectif est d'evaluer votre capacite a **orchestrer plusieurs API d'IA** et a **assembler le resultat** vous-meme, pas a brancher un SaaS qui fait tout.

---

## Documents

1. **[SUJET.md](./SUJET.md)** — Specifications detaillees du pipeline
2. **[ARCHITECTURE.md](./ARCHITECTURE.md)** — Contraintes techniques et structure du projet
3. **[EVALUATION.md](./EVALUATION.md)** — Grille d'evaluation
4. **[CLAUDE_MD_GUIDE.md](./CLAUDE_MD_GUIDE.md)** — Attentes pour le fichier CLAUDE.md

---

## Rendu

- Un **repository Git** avec historique de commits propre
- Un fichier **CLAUDE.md** a la racine
- Au moins **1 video de demo** generee (commitee ou lien de telechargement)
- Les **prompts utilises** pour chaque etape documentes dans le code
- Un **README** avec les instructions pour generer une video depuis un prompt

---

## Note sur l'utilisation de l'IA

L'utilisation d'outils d'IA est **autorisee et encouragee** — c'est meme le coeur du sujet. Vous serez evalue sur votre capacite a :
- Choisir la bonne API pour chaque etape du pipeline
- Rediger des prompts efficaces (prompt engineering)
- Orchestrer les appels et gerer les erreurs
- Assembler le resultat final avec des outils programmatiques
