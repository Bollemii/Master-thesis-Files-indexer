# TFE

[![pipeline status](https://gitlab.com/Masi-s-Matcas/tfe/badges/main/pipeline.svg)](https://gitlab.com/Masi-s-Matcas/tfe/-/commits/main) [![coverage report](https://gitlab.com/Masi-s-Matcas/tfe/badges/main/coverage.svg)](https://gitlab.com/Masi-s-Matcas/tfe/-/commits/main)

Code source du projet TFE de l'année académique 2024-2025.

## Installation

Le projet nécessite l'installation Docker et Docker Compose. Pour installer Docker, suivez les instructions sur le site officiel : [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/).


Pour installer le projet, il suffit de cloner le dépôt avec la commande suivante :

```console
$ git clone https://gitlab.com/Masi-s-Matcas/tfe.git
```
```console
$ cd tfe
```

## Utilisation

Attention, due à l'utilisation de Tesseract et de LibreOffice, le container backend nécessite 4GB d'espace disque minimum.

Pour lancer le projet, lancer la commande suivante :

```console
$ docker compose -f compose.yml up -d
```
Puis rendez-vous sur [http://localhost:3000](http://localhost:3000) pour accéder à l'application.


Pour arrêter le projet, lancer la commande suivante :

```console
$ docker compose -f compose.yml down
```

## Auteur

- Mateo Castreuil
