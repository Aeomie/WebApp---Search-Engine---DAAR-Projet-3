#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import sys
import os
import argparse
from typing import Iterable, Iterator, Optional, Tuple
from search_algorithms.kmp import KMP
from search_algorithms.nfa import NFA
from search_algorithms.dfa import DFA
from search_algorithms.boyer_moore import Boyer


# ============================================================
# Démo : moteur temporaire basé sur re.search
# ============================================================

DEMO: bool = False
_DEMO_STATE = {"pattern": None}

# ============================================================
# Stubs
# ============================================================

_engine = None  # stockage global provisoire

# ============================================================
# ENGINE FUNCTION
# ============================================================

def engine(pattern: str, file_to_run: str, mode: str,max_matches : int = 0, line_number : bool = False, ignore_case: bool = False) -> None:
    """
    Build and run the chosen engine on the given file.
    """
    # Build the matcher
    match mode:
        case "kmp":
            print("Using KMP algorithm")
            matcher = KMP(pattern)
        case "boyer":
            print("Using Boyer-Moore algorithm")
            matcher = Boyer(pattern)
        case "regex":
            print("Using Regex (DFA) algorithm")
            nfa = NFA(pattern)
            matcher = DFA(nfa)
        case _:
            raise ValueError(f"Unknown mode: {mode}")

    print("Engine built successfully.\n")

    all_indexes = []
    total_count = 0
    remaining = max_matches
    with open(file_to_run, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, start=1):
            line_proc = line.strip()
            if ignore_case:
                line_proc = line_proc.lower()
            match mode:
                case "kmp":
                    indexes, count = matcher.match_kmp(line_proc, max_matches)
                case "boyer":
                    indexes, count = matcher.match_boyer(line_proc, max_matches)
                case "regex":
                    indexes, count = matcher.match_dfa(line_proc, max_matches)
            if count == 0:
                continue
            if line_number:
                print(f"Line {i}: Total matches found: {count}")
                print(f"Indexes of matches: {indexes}\n")
            else:
                all_indexes.extend(indexes)
                total_count += count

            remaining -= count
            if max_matches > 0 and remaining <= 0:
                break

    if not line_number:
        print(f" Total matches found: {total_count} \n Indexes : {all_indexes}")


def engine_text(
    pattern: str,
    text: str,
    mode: str,
    max_matches: int = 0,
    ignore_case: bool = False,
    verbose: bool = False
) -> dict:

    match mode:
        case "kmp":
            matcher = KMP(pattern)
        case "boyer":
            matcher = Boyer(pattern)
        case "regex":
            nfa = NFA(pattern)
            matcher = DFA(nfa)
        case _:
            raise ValueError(f"Unknown mode: {mode}")

    if ignore_case:
        text = text.lower()

    match mode:
        case "kmp":
            indexes, count = matcher.match_kmp(text, max_matches)
        case "boyer":
            indexes, count = matcher.match_boyer(text, max_matches)
        case "regex":
            indexes, count = matcher.match_dfa(text, max_matches)

    if verbose:
        return {
            "total_count": count,
            "indexes": indexes
        }
    else:
        return {
            "total_count": count
        }


# ============================================================
# UTILITIES
# ============================================================

def open_maybe_stdin(path: str, *, encoding: str = "utf-8") -> Iterable[str]:
    if path == "-":
        for line in sys.stdin:
            yield line
    else:
        with open(path, "r", encoding=encoding, errors="replace") as f:
            for line in f:
                yield line


def enumerate_lines(lines: Iterable[str]) -> Iterator[Tuple[int, str]]:
    for i, line in enumerate(lines, start=1):
        yield i, line



# ============================================================
# CLI
# ============================================================

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="myegrep",
        description="Clone d’egrep utilisant KMP, Boyer–Moore ou DFA (regex).",
        allow_abbrev=False,
    )
    p.add_argument("pattern", help="Pattern a chercher.")
    p.add_argument("file", help="Chemin du fichier texte, ou '-' pour stdin.")
    p.add_argument("-m", "--mode", choices=["kmp", "boyer", "regex"], default="regex",
                   help="Choisir le moteur (regex par défaut).")
    p.add_argument("-n", "--line-number", action="store_true",
                   help="Afficher le numéro de ligne.")
    p.add_argument("-i", "--ignore-case", action="store_true",
                   help="Ignorer la casse.")
    p.add_argument("--max-matches", type=int, default=0,
                   help="Arrêter après N correspondances (>0).")
    p.add_argument("--dry-run", action="store_true",
                   help="N’affiche que la configuration (pas de match).")
    p.add_argument("--version", action="version",
                   version="myegrep 0.1 (DAAR – M2 STL)")
    return p


# ============================================================
# Main
# ============================================================

def main(argv: Optional[list[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    if args.file != "-" and not os.path.exists(args.file):
        sys.stderr.write(f"[ERREUR] Fichier introuvable : {args.file}\n")
        return 2

    try:
        pattern = args.pattern.lower() if args.ignore_case else args.pattern

        # Call the engine with the parsed arguments
        engine(
            pattern=pattern,
            file_to_run=args.file,
            mode=args.mode,
            max_matches=args.max_matches,
            line_number=args.line_number,
            ignore_case=args.ignore_case
        )

    except Exception as e:
        sys.stderr.write(f"[ERREUR] Échec : {e}\n")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
