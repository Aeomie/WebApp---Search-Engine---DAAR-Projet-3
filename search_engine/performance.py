from __future__ import annotations
import os
import sys
import time
import argparse
import csv
import re
from pathlib import Path
from search_algorithms.kmp import KMP
from search_algorithms.nfa import NFA
from search_algorithms.dfa import DFA
from search_algorithms.boyer_moore import Boyer


def merge_books(folder="livres", output="merged.txt", ignore_case=False):
    with open(output, "w", encoding="utf-8") as out:
        for fname in os.listdir(folder):
            if fname.endswith(".txt"):
                with open(os.path.join(folder, fname), "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
                    if ignore_case:
                        text = text.lower()
                    out.write(text.strip() + "\n\n")  # preserve lines + separate books
    print(f"[+] All books merged into {output}")


def word_counter(file="merged.txt"):
    with open(file, encoding="utf-8") as f:
        return len(f.read().split())


def line_counter(file="merged.txt"):
    with open(file, encoding="utf-8") as f:
        return sum(1 for _ in f)


def benchmark_by_words(algorithm, text, step=1000, max_words=50000):
    words = text.split()
    times = []
    occurrences = 0
    for i in range(step, min(len(words), max_words) + 1, step):
        sample = " ".join(words[:i])
        start = time.perf_counter()

        count = 0
        if isinstance(algorithm, KMP):
            indexes, count = algorithm.match_kmp(sample)
        elif isinstance(algorithm, Boyer):
            indexes, count = algorithm.match_boyer(sample)
        elif isinstance(algorithm, DFA):
            indexes, count = algorithm.match_dfa(sample)

        occurrences += count
        end = time.perf_counter()
        times.append((i, end - start))
        #print(f"{algorithm.__class__.__name__}: {i} words -> {end - start:.5f}s")
    return times, occurrences


def benchmark_by_words(algorithm, text, step=1000, max_words=50000):
    """
    Benchmark the algorithm in increments of words, processing only new words each step.
    """
    words = text.split()
    times = []
    occurrences = 0

    for start_idx in range(0, min(len(words), max_words), step):
        end_idx = min(start_idx + step, len(words), max_words)
        sample = " ".join(words[start_idx:end_idx])  # only new words
        start_time = time.perf_counter()

        count = 0
        if isinstance(algorithm, KMP):
            indexes, count = algorithm.match_kmp(sample)
        elif isinstance(algorithm, Boyer):
            indexes, count = algorithm.match_boyer(sample)
        elif isinstance(algorithm, DFA):
            indexes, count = algorithm.match_dfa(sample)

        occurrences += count
        end_time = time.perf_counter()
        times.append((end_idx, end_time - start_time))
        #print(f"{algorithm.__class__.__name__}: words {start_idx}-{end_idx} -> {end_time - start_time:.5f}s")

    return times, occurrences



def benchmark_by_lines(algorithm, file="merged.txt", max_lines=50000):
    """
    Benchmark the algorithm line by line, each line independently.
    """
    times = []
    occurrences = 0

    with open(file, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if i > max_lines:
                break
            start = time.perf_counter()

            count = 0
            if isinstance(algorithm, KMP):
                indexes, count = algorithm.match_kmp(line)
            elif isinstance(algorithm, Boyer):
                indexes, count = algorithm.match_boyer(line)
            elif isinstance(algorithm, DFA):
                indexes, count = algorithm.match_dfa(line)

            occurrences += count
            end = time.perf_counter()
            times.append((i, end - start))
            #print(f"{algorithm.__class__.__name__}: {i} lines -> {end - start:.5f}s")

    return times, occurrences


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pertest",
        description="Performance tester utilisant KMP, Boyer–Moore ou DFA (regex).",
        allow_abbrev=False,
    )
    p.add_argument("pattern", help="Pattern à chercher.")
    p.add_argument("-f", "--folder", default="livres",
                   help="Dossier contenant les fichiers texte à fusionner.")
    p.add_argument("-m", "--mode", choices=["kmp", "boyer", "regex"], default="regex",
                   help="Choisir le moteur (regex par défaut).")
    p.add_argument("-i", "--ignore-case", action="store_true",
                   help="Ignorer la casse (tout mettre en minuscules).")

    group = p.add_mutually_exclusive_group()
    group.add_argument("-l", "--lines", action="store_true", default=True,
                       help="Benchmark par lignes (mode par défaut).")
    group.add_argument("-w", "--words", action="store_true",
                       help="Benchmark par mots (active --step et --max-words).")

    p.add_argument("--max", type=int, default=50000,
                   help="Nombre maximal de trucs à lire soit mots soit lignes.")
    p.add_argument("--step", type=int, default=1000,
                   help="Nombre de mots à ajouter à chaque itération (uniquement en mode mots).")

    return p


def save_to_csv(data, filename="benchmark_results.csv"):
    file = Path(filename)
    write_header = not file.exists()

    with open(file, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Units Processed", "Time (s)"])
        writer.writerows(data)

    print(f"[+] Results saved to {file.resolve()}")


# ... (all imports and functions unchanged) ...

def main():
    args = build_arg_parser().parse_args()

    if not (args.words or args.lines):
        args.lines = True

    pattern = args.pattern.lower() if args.ignore_case else args.pattern

    merge_books(args.folder, ignore_case=args.ignore_case)

    text = open("merged.txt", encoding="utf-8").read()

    print(f"Number of words in the merged file: {word_counter()}")
    print(f"Number of lines in the merged file: {line_counter()}")

    if args.mode == "kmp":
        print(f"[+] Preprocessing KMP pattern: {pattern}")
        algorithm = KMP(pattern)
    elif args.mode == "boyer":
        print(f"[+] Preprocessing Boyer-Moore pattern: {pattern}")
        algorithm = Boyer(pattern)
    elif args.mode == "regex":
        print(f"[+] Compiling regex pattern: {pattern}")
        algorithm = DFA(NFA(pattern))
    else:
        sys.stderr.write(f"[ERREUR] Mode inconnu : {args.mode}\n")
        return 2

    times, occurrences = ([], 0)
    if args.words:
        times, occurrences = benchmark_by_words(algorithm, text, step=args.step, max_words=args.max)
    elif args.lines:
        times, occurrences = benchmark_by_lines(algorithm, max_lines=args.max)

    # Directory where you want to save CSVs
    output_folder = f"TestResultsLines/{args.mode}" if args.lines else f"TestResultsWords/{args.mode}"
    os.makedirs(output_folder, exist_ok=True)

    # Clean pattern for filenames
    pattern_clean = args.pattern.strip()

    # Save benchmark CSV
    filename = os.path.join(output_folder, f"{args.mode}_{pattern_clean}.csv")
    save_to_csv(times, filename)

    # Save occurrences in a separate summary CSV
    summary_folder = os.path.join(output_folder, "Summaries")
    os.makedirs(summary_folder, exist_ok=True)
    summary_filename = os.path.join(summary_folder, f"{args.mode}_{pattern_clean}_summary.csv")

    with open(summary_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Total Occurrences"])
        writer.writerow([occurrences])
    print(f"[+] Total occurrences saved to {summary_filename}")

    print(f"Total occurrences found: {occurrences}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
