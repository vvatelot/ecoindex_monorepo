#!/bin/sh

celery -A ecoindex.worker.tasks worker -Q ecoindex