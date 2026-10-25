#!/bin/bash
set -euo pipefail

docker compose config -q
ruff check backend
pytest -q backend || [ $? -eq 5 ]
