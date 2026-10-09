# Parallel Mandelbrot Benchmark

C implementation of Mandelbrot set rendering in three versions:

- Sequential baseline
- OpenMP
- POSIX threads (Pthreads)

## Highlights

- Byte-for-byte validation against the sequential implementation.
- 5,600 timed measurements across multiple configurations.
- Benchmarks for Full Picture, Seahorse Valley, Elephant Valley, and Triple
  Spiral Valley.
- Raw measurements, statistical summaries, and generated plots are included.

## Build

Run:

    make

This creates `mandelbrot_seq`, `mandelbrot_omp`, and `mandelbrot_pth`.

## Run

Sequential:

    ./mandelbrot_seq -2.5 1.5 -2.0 2.0 512

OpenMP with four threads:

    OMP_NUM_THREADS=4 ./mandelbrot_omp -2.5 1.5 -2.0 2.0 512

Pthreads with four threads:

    ./mandelbrot_pth -2.5 1.5 -2.0 2.0 512 4

To benchmark without writing a PPM image, prefix a command with
`MANDELBROT_NO_IMAGE=1`.

## Reproduce the analysis

    python3 analisar_medicoes.py measurements_resumed.csv --output analise

The analysis script uses NumPy, pandas, SciPy, and Matplotlib.

`run_measurements.sh` starts a new full benchmark collection. Run it only
intentionally.

## Repository structure

    mandelbrot_seq.c, mandelbrot_omp.c, mandelbrot_pth.c
    Makefile
    run_measurements.sh
    analisar_medicoes.py
    measurements_resumed.csv
    analise/          # plots and statistical summaries
    compiler.txt
    cpu.txt

## Context

Originally developed as a parallel programming project, then organized here as
a reproducible benchmark and performance-analysis repository.
