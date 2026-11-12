# brakehydro
## Blog : publication automatique

- Les articles en attente sont dans `drafts/` (un fichier JSON par article, publiés dans l'ordre des numéros).
- Chaque lundi, l'action GitHub « Publier l'article de la semaine » publie le prochain : page `blog/<slug>/`, carte sur `/blog/` et sur le blog de l'accueil, entrée dans `sitemap.xml`.
- Publier tout de suite : onglet Actions → « Publier l'article de la semaine » → Run workflow.
- Les articles publiés sont archivés dans `drafts/published/`.
