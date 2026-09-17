# Documentation de la Ruche numérique

La documentation de l'incubateur de services numériques du ministère de l'Agriculture, de l'Agro-Alimentaire et de la Souveraineté Alimentaire (MAASA).

Site publié : https://jenniferstephan.github.io/ruche-documentation/

Pour proposer une modification : voir [Contribuer](docs/contribuer.md).

---

## Mise en place (à faire une seule fois)

### 1. Remplacer les identifiants

Dans tous les fichiers, remplacer :

- `GITHUB_USER` par ton identifiant GitHub ;
- `ANNE_GITHUB` et `DENIS_GITHUB` par ceux d'Anne et de Denis (dans `.github/CODEOWNERS`).

```bash
grep -rl GITHUB_USER . | xargs sed -i '' 's/GITHUB_USER/ton-identifiant/g'   # macOS
grep -rl GITHUB_USER . | xargs sed -i 's/GITHUB_USER/ton-identifiant/g'      # Linux
```

### 2. Importer les pages depuis GitBook

```bash
python3 scripts/import_gitbook.py
```

Le script liste les pages non récupérées et celles qui contiennent encore de la syntaxe GitBook à reprendre à la main. Vérifier le rendu avec `mkdocs serve` (voir CONTRIBUTING.md).

Les images restent hébergées chez GitBook. Si le site GitBook doit être fermé, les rapatrier dans `docs/assets/` et mettre à jour les liens.

### 3. Créer le dépôt et pousser

Créer sur GitHub un dépôt **public** nommé `ruche-documentation`, vide (sans README), puis :

```bash
git init -b main
git add .
git commit -m "Import initial depuis GitBook"
git remote add origin https://github.com/jenniferstephan/ruche-documentation.git
git push -u origin main
```

### 4. Activer GitHub Pages

*Settings → Pages → Build and deployment → Source : **GitHub Actions***.

Le site est en ligne quelques minutes après (onglet *Actions* pour suivre).

### 5. Donner les droits à Anne et Denis

*Settings → Collaborators → Add people* : ajouter Anne et Denis. Ils reçoivent le droit d'écriture, nécessaire pour valider les propositions. Toute autre personne contribue par proposition (pull request) sans avoir besoin d'être invitée.

### 6. Protéger la branche principale

*Settings → Rules → Rulesets → New branch ruleset* :

- **Ruleset name** : `Protection main`
- **Enforcement status** : Active
- **Bypass list** : laisser **vide** (sinon les administrateurs peuvent publier sans relecture)
- **Target branches** : *Add target → Include default branch*
- Cocher :
    - **Restrict deletions**
    - **Block force pushes**
    - **Require a pull request before merging**
        - Required approvals : **1**
        - **Dismiss stale pull request approvals when new commits are pushed**
        - **Require review from Code Owners**
        - **Require approval of the most recent reviewable push** (empêche de valider sa propre modification ajoutée en dernier)
    - **Require status checks to pass** → ajouter `build`

Résultat : personne, ni toi, ni Anne, ni Denis, ne peut publier sans qu'une autre des trois personnes ait approuvé. Une proposition dont la construction échoue (lien cassé) ne peut pas être fusionnée.

> Si tu veux pouvoir corriger une coquille seule sans attendre une relecture, ajoute-toi dans la *Bypass list* : c'est un choix, pas un défaut.

### 7. Réglages recommandés

- *Settings → General → Pull Requests* : cocher **Allow squash merging** uniquement, et **Automatically delete head branches**.
- *Settings → Actions → General → Fork pull request workflows* : laisser **Require approval for first-time contributors** (protège contre l'exécution de code non relu).
- *Settings → General → Features* : garder **Issues** activé (formulaire « Signaler un manque »).
- *Watch → Custom → Pull requests* : pour que vous trois soyez notifiés de chaque proposition.

### 8. Côté GitBook

Une fois le site GitHub en ligne, ajouter en tête du site GitBook un encadré renvoyant vers la nouvelle adresse, puis le dépublier à la date choisie, pour éviter deux versions divergentes.
