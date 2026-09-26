"""Freeze full inputs once. This stage prepares experiments without running models."""
import json
import random
from pathlib import Path
from .identity import digest, resume_key


def freeze(tickets, candidates, truth, n=60, seed=1, k=5, excluded=()):
    if n < 1 or k < 1:
        raise ValueError("n and k must be positive")
    by = {t['key']: t for t in tickets}
    labels = {}
    for row in truth:
        labels.setdefault((row['src'], row['dst']), set()).add(row['relation'])
    eligible = sorted({r['key'] for r in candidates if r['key'] in by
                       and by[r['key']]['created'] >= '2025-01-01'} - set(excluded))
    chosen = random.Random(seed).sample(eligible, min(n, len(eligible)))
    shortlist = {r['key']: r['candidates'] for r in candidates}
    jobs = []
    for key in chosen:
        seen = set()
        cs = []
        for c in shortlist[key]:
            dest = c['key']
            if dest in seen or dest not in by or by[dest]['created'] >= by[key]['created']:
                continue
            seen.add(dest)
            cs.append(by[dest])
            if len(cs) == k:
                break
        jobs.append({'key': key, 'ticket': by[key], 'candidates': cs,
                     'truth': {c['key']: sorted(labels.get((key, c['key']), set())) for c in cs}})
    plan = {'schema': 1, 'seed': seed, 'requested_n': n, 'k': k, 'eligible_n': len(eligible),
            'scope': 'available-candidate-snapshot-diagnostic', 'injected': False,
            'limitations': ['Candidate file is not the full eligible stream.',
                            'Snapshot metadata is not historically reconstructed.',
                            'Missing labels are unknown, not negative truth.'],
            'source_hashes': {'tickets': digest(tickets), 'candidates': digest(candidates), 'truth': digest(truth)},
            'jobs': jobs}
    return {**plan, 'plan_id': digest(plan)}


def validate(plan):
    if digest({k: v for k, v in plan.items() if k != 'plan_id'}) != plan.get('plan_id'):
        raise ValueError('Plan changed: hash mismatch')
    keys = [j['key'] for j in plan['jobs']]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate tasks')
    return plan


def save(plan, path):
    validate(plan)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)


def pending(plan, config, completed):
    validate(plan)
    done = {r['run_id'] for r in completed if r.get('status') == 'complete'}
    return [j for j in plan['jobs'] if resume_key(j['key'], config['config_id'], plan['plan_id']) not in done]
