#!/usr/bin/env python3
"""
Redrob Hackathon — Candidate Ranker
Usage: python rank.py --candidates ./candidates.jsonl --out ./submission.csv
Runs in ≤5 min, CPU-only, 16GB RAM, no network.
"""
import argparse, csv, time, sys
from src.ranker import run_ranking

import os, glob

def find_candidates_file(given_path):
    # 1. Try exact path given
    if os.path.exists(given_path):
        return given_path
    # 2. Search parent directory for any candidates.jsonl
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches = glob.glob(os.path.join(parent, '**', 'candidates.jsonl'), recursive=True)
    if matches:
        print(f'Auto-found: {matches[0]}')
        return matches[0]
    # 3. Also check .gz version
    gz_matches = glob.glob(os.path.join(parent, '**', 'candidates.jsonl.gz'), recursive=True)
    if gz_matches:
        print(f'Auto-found: {gz_matches[0]}')
        return gz_matches[0]
    print(f'ERROR: candidates.jsonl not found. Searched: {parent}')
    import sys; sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidates', default='candidates.jsonl')
    parser.add_argument('--out', default=None)
    parser.add_argument('--top-k', type=int, default=100)
    parser.add_argument('--participant-id', default='participant_redrob',
        help='Your registered Hack2Skill participant ID. Used as the CSV filename.')
    args = parser.parse_args()

    candidates_path = find_candidates_file(args.candidates)

    t0 = time.time()
    print(f'Loading candidates from {candidates_path}...')
    results = run_ranking(candidates_path, top_k=args.top_k)
    elapsed = time.time() - t0
    print(f'Ranked {len(results)} candidates in {elapsed:.1f}s')

    if args.out is None:
        args.out = f'{args.participant_id}.csv'
    out_path = args.out
    print(f'Output: {out_path}')

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['candidate_id', 'rank', 'score', 'reasoning'])
        for row in results:
            writer.writerow([row['candidate_id'], row['rank'],
                             f"{row['score']:.4f}", row['reasoning']])
    print(f'Written to {out_path}')

    # Self-validate
    import subprocess
    r = subprocess.run(['python','validate_submission.py', out_path], capture_output=True)
    print(r.stdout.decode())
    if r.returncode != 0:
        print('VALIDATION FAILED:', r.stderr.decode(), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__': main()
