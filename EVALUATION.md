# Grille d'Evaluation — Video Shorts Generator

## Bareme detaille — 100 points

---

## 1. Pipeline et orchestration (25 points)

### Architecture du pipeline (15 pts)
| Critere | Points | Attendu |
|---|---|---|
| Decoupage clair en etapes distinctes | 4 | Chaque etape dans son propre module, responsabilite unique |
| Typage des entrees/sorties de chaque etape | 3 | Types explicites pour le contexte du pipeline |
| Gestion des fichiers intermediaires | 3 | Dossier temporaire organise, fichiers nommes logiquement |
| Logging et progression | 3 | Affichage clair de l'avancement, temps par etape |
| Gestion des erreurs par etape | 2 | Erreurs explicites, pas de crash silencieux |

### Robustesse (10 pts)
| Critere | Points | Attendu |
|---|---|---|
| Gestion des erreurs API (retry, timeout, fallback) | 3 | Au moins un retry avec backoff sur les appels API |
| Validation des sorties intermediaires | 3 | Verifier que l'audio existe et a une duree > 0, etc. |
| Nettoyage des fichiers temporaires | 2 | Option pour garder ou supprimer les fichiers intermediaires |
| Configuration externalisee (.env, CLI args) | 2 | Pas de cles API ou chemins en dur dans le code |

---

## 2. Prompt engineering et usage des LLM (20 points)

### Generation du script (12 pts)
| Critere | Points | Attendu |
|---|---|---|
| System prompt qui capture le personnage Picsou | 4 | Ton, vocabulaire, obsessions du personnage |
| Contraintes de longueur respectees (80-200 mots) | 2 | Le texte genere est utilisable sans retouche manuelle |
| Format de sortie structure (JSON) | 2 | Parsing fiable du JSON retourne |
| Generation de la description de fond | 2 | Coherente avec le contenu du script |
| Prompts documentes et versiones dans le code | 2 | Dans `prompts/` ou en constantes avec commentaires |

### Utilisation des API (8 pts)
| Critere | Points | Attendu |
|---|---|---|
| Choix pertinent de l'API pour chaque etape | 3 | Justification technique (pas juste "c'est ce que je connais") |
| Configuration flexible du provider (swap Claude/OpenAI/Gemini) | 3 | Variable d'env ou parametre, pas de hardcode |
| Gestion des couts (tokens, requetes) | 2 | Documenter le cout estime, eviter le gaspillage |

---

## 3. Audio et synchronisation (15 points)

### Generation de la voix (7 pts)
| Critere | Points | Attendu |
|---|---|---|
| Voix generee lisible et naturelle | 3 | Pas de voix robotique, debit correct |
| Choix de voix justifie | 2 | Documenter pourquoi cette voix pour ce personnage |
| Recuparation des timestamps | 2 | Via Whisper ou estimation raisonnable |

### Analyse audio pour animation (8 pts)
| Critere | Points | Attendu |
|---|---|---|
| Extraction de l'amplitude par frame | 3 | RMS ou pic par intervalle de 33ms |
| Seuil de detection fonctionnel | 3 | Bouche ouverte/fermee coherente avec la parole |
| Seuil adaptatif (pas un magic number) | 2 | Calcule a partir des stats de l'audio |

---

## 4. Visuel et assemblage (25 points)

### Assets visuels (8 pts)
| Critere | Points | Attendu |
|---|---|---|
| Personnage avec au moins 2 etats (bouche ouverte/fermee) | 4 | Images preparees et utilisables |
| Fond coherent avec le contenu | 2 | Couleur unie acceptable, image generee = bonus |
| Format portrait 1080x1920 respecte | 2 | Pas de barres noires, pas d'etirement |

### Sous-titres (8 pts)
| Critere | Points | Attendu |
|---|---|---|
| Sous-titres presents et lisibles | 2 | Police grande, contraste suffisant |
| Synchronisation avec l'audio | 3 | Les mots apparaissent quand ils sont prononces |
| Style dynamique (highlight du mot courant) | 3 | Mot en surbrillance ou effet visuel equivalent |

### Assemblage FFmpeg (9 pts)
| Critere | Points | Attendu |
|---|---|---|
| Video MP4 valide et lisible | 3 | Ouvrable dans n'importe quel lecteur |
| Audio et video synchronises | 3 | Pas de decalage visible entre voix et animation |
| Qualite visuelle correcte (pas de pixelisation) | 2 | Resolution respectee, compression raisonnable |
| Duree coherente avec le script | 1 | Pas de silence en trop a la fin |

---

## 5. Fichier CLAUDE.md (15 points)

| Critere | Points | Attendu |
|---|---|---|
| Description du pipeline et de chaque etape | 2 | Un assistant IA comprend le flux complet |
| Prompts documentes avec leur logique | 3 | Pourquoi ce system prompt, quelles iterations |
| Choix techniques justifies (voix, provider, approche animation) | 3 | Tradeoffs explicites, alternatives envisagees |
| Commandes pour generer une video | 2 | Copier-coller et ca genere |
| Cout et performance documentes | 2 | Estimation realiste du cout par video |
| Limites connues et ameliorations possibles | 3 | Honnetete sur ce qui ne marche pas parfaitement |

---

## Bonus (hors bareme, +10 pts max)

| Critere | Points |
|---|---|
| Interface web fonctionnelle | +3 |
| Niveau 3 d'animation (multi-frames phonemes) | +2 |
| Generation du fond par IA (DALL-E/Imagen) | +1 |
| Musique de fond | +1 |
| Cache des assets pour eviter les appels redondants | +1 |
| Tests automatises | +1 |
| Reprise du pipeline a une etape donnee (`--from-step`) | +1 |

---

## Seuils de decision

| Score | Decision |
|---|---|
| **75 — 100+** | Profil senior, maitrise de l'orchestration IA |
| **55 — 74** | Profil confirme, bonne comprehension du sujet |
| **35 — 54** | Profil junior, bases presentes |
| **< 35** | Ne correspond pas au niveau recherche |

---

## Entretien de restitution (30 min)

1. **Demo live** — Le candidat lance une generation de video en direct avec un nouveau prompt
2. **Revue des prompts** — Discussion sur les choix de prompt engineering, iterations realisees
3. **Question technique** — "Comment gererais-tu le lip-sync si tu avais 2 semaines de plus ?"
4. **Modification en direct** — Changer la voix TTS, modifier le style de sous-titres, ou ajouter un effet visuel simple
5. **Discussion scaling** — "Comment transformer ca en service capable de generer 100 videos/heure ?"
