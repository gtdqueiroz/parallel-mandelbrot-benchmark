#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"

export LC_ALL=C
export OMP_DYNAMIC=FALSE
unset MANDELBROT_NO_IMAGE

REPETITIONS=${REPETITIONS:-10}
MAX_SIZE=${MAX_SIZE:-8192}
THREADS=(1 2 4 8 16 32)

make
mkdir -p results
RESULT_DIR=$(mktemp -d results/run_XXXXXX)
CSV="$RESULT_DIR/measurements.csv"

printf 'version,region,size,threads,mode,repetition,seconds\n' > "$CSV"

# Guarda informações e códigos usados nesta coleta.
lscpu > "$RESULT_DIR/cpu.txt"
gcc --version > "$RESULT_DIR/compiler.txt"
cp Makefile mandelbrot_seq.c mandelbrot_omp.c mandelbrot_pth.c \
    "$0" "$RESULT_DIR/"

printf 'Resultados: %s\n' "$CSV"

measure() {
    local version=$1 mode=$2 threads=$3
    local repetition elapsed
    local -a command=("./mandelbrot_$version" "${coords[@]}" "$size")

    if [[ $version == pth ]]; then
        command+=("$threads")
    fi

    printf '%s | %s | N=%s | threads=%s | %s\n' \
        "$version" "$region" "$size" "$threads" "$mode"

    for ((repetition=1; repetition<=REPETITIONS; repetition++)); do
        if [[ $mode == full ]]; then
            elapsed=$("${command[@]}")
        else
            elapsed=$(MANDELBROT_NO_IMAGE=1 OMP_NUM_THREADS="$threads" \
                "${command[@]}")
        fi

        if [[ ! $elapsed =~ ^[0-9]+\.[0-9]+$ ]]; then
            printf 'Tempo invalido: %s\n' "$elapsed" >&2
            exit 1
        fi

        printf '%s,%s,%s,%s,%s,%s,%s\n' \
            "$version" "$region" "$size" "$threads" "$mode" \
            "$repetition" "$elapsed" >> "$CSV"
    done
}

for region in full seahorse elephant triple_spiral; do
    case "$region" in
        full)          coords=(-2.5 1.5 -2.0 2.0) ;;
        seahorse)      coords=(-0.8 -0.7 0.05 0.15) ;;
        elephant)      coords=(0.175 0.375 -0.1 0.1) ;;
        triple_spiral) coords=(-0.188 -0.012 0.554 0.754) ;;
    esac

    for ((size=16; size<=MAX_SIZE; size*=2)); do
        measure seq full 1
        measure seq compute 1

        for threads in "${THREADS[@]}"; do
            measure omp compute "$threads"
            measure pth compute "$threads"
        done
    done
done

printf 'Concluido! CSV: %s\n' "$CSV"
