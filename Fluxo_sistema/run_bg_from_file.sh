#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   ./run_bg_from_file.sh extrair.sh 4
#   (segundo argumento é o número de jobs em paralelo; padrão = 4)

SCRIPT_FILE="${1:-}"
JOBS="${2:-4}"

if [[ -z "$SCRIPT_FILE" || ! -f "$SCRIPT_FILE" ]]; then
  echo "Uso: $0 <arquivo_com_comandos.sh> [jobs_em_paralelo]"
  exit 1
fi

# Evita CRLF (Windows) e ignora linhas vazias/comentários
# Não modifica o arquivo original: cria um temporário limpo
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

# limpa: remove CR no fim, ignora vazias e comentários
sed 's/\r$//' "$SCRIPT_FILE" | grep -vE '^\s*($|#)' > "$tmp"

total="$(wc -l < "$tmp" | tr -d ' ')"
if [[ "$total" == "0" ]]; then
  echo "Nada para executar (arquivo vazio/sem comandos úteis)."
  exit 0
fi

echo "Executando $total comandos (até $JOBS em paralelo) a partir de: $SCRIPT_FILE"

# (Opcional) Ajustes de cache para evitar problemas de permissão em OpenGL/mesa
export HOME="${HOME:-/tmp}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/.cache}"
export MESA_SHADER_CACHE_DIR="${MESA_SHADER_CACHE_DIR:-/tmp/.cache/mesa}"
mkdir -p "$XDG_CACHE_HOME" "$MESA_SHADER_CACHE_DIR" >/dev/null 2>&1 || true

pids=()
fails=0
i=0

start_job() {
  local cmd="$1"
  i=$((i+1))

  # limita concorrência
  while (( $(jobs -rp | wc -l) >= JOBS )); do
    sleep 1
  done

  echo ">> START $i/$total: $(date) | $cmd"
  # executa cada linha exatamente como um comando (sem quebrar aspas)
  bash -lc "$cmd" &
  pids+=("$!")
}

# dispara todos
while IFS= read -r line; do
  start_job "$line"
done < "$tmp"

echo "Aguardando finalizar ${#pids[@]} jobs..."
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    fails=$((fails+1))
  fi
done

if (( fails > 0 )); then
  echo "ERRO: $fails job(s) falharam."
  exit 1
fi

echo "OK: todos os jobs finalizaram com sucesso."