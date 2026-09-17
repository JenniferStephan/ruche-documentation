# Contribuer

Le guide de contribution est publié sur le site : [docs/contribuer.md](docs/contribuer.md).

En résumé : clique sur le crayon d'une page, modifie, propose. Une personne de l'équipe de la Ruche relit et publie.

## Travailler en local (optionnel, pour les personnes à l'aise avec Git)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve        # aperçu sur http://127.0.0.1:8000/ruche-documentation/
```

Structure :

- `docs/` : les pages, une par fichier Markdown ;
- `docs/**/.pages` : l'ordre des pages dans le menu ;
- `mkdocs.yml` : la configuration du site.

Pour ajouter une page : créer le fichier dans le bon dossier de `docs/`, puis l'ajouter au fichier `.pages` du dossier à l'endroit voulu (sinon elle apparaît en fin de section).
