# Label audit and null-road check (test, gemma3-1b-lora-n207, B1 probabilities)

Produced by `jev_rl/scripts/label_audit.py` from the gitignored cache. Read-only.

- A: candidate equals gold but B1 probability of gold < 0.1: 17 field cases
- B: candidate differs from gold, B1 gives candidate >= 0.9 and gold < 0.1: 10 field cases
- C: gold road with B1 road_match < 0.1: 1 case(s)

## A

| id | field | gold | candidate | B1 p(gold) | tags |
|---|---|---|---|---|---|
| te-007 | severity | medium | medium | 0.07 | - |
| te-009 | road_obstruction | unknown | unknown | 0.05 | - |
| te-023 | incident_type | road_closure | road_closure | 0.08 | contradictory |
| te-024 | incident_type | heavy_traffic | heavy_traffic | 0.09 | contradictory |
| te-062 | incident_type | road_hazard | road_hazard | 0.00 | - |
| te-062 | severity | low | low | 0.01 | - |
| te-065 | severity | low | low | 0.04 | - |
| te-067 | incident_type | road_hazard | road_hazard | 0.01 | - |
| te-069 | incident_type | road_hazard | road_hazard | 0.08 | - |
| te-079 | severity | high | high | 0.02 | - |
| te-088 | incident_type | flooding | flooding | 0.03 | noisy |
| te-092 | road_obstruction | full | full | 0.01 | - |
| te-132 | road_obstruction | none | none | 0.00 | - |
| te-135 | severity | unknown | unknown | 0.03 | ambiguous |
| te-150 | severity | unknown | unknown | 0.03 | ambiguous |
| te-150 | road_obstruction | unknown | unknown | 0.02 | ambiguous |
| te-170 | severity | unknown | unknown | 0.01 | contradictory |

## B

| id | field | gold | candidate | B1 p(gold) | tags |
|---|---|---|---|---|---|
| te-025 | road_obstruction | unknown | full | 0.00 | contradictory |
| te-060 | severity | high | medium | 0.02 | - |
| te-087 | severity | high | medium | 0.08 | - |
| te-147 | incident_type | unknown | heavy_traffic | 0.03 | ambiguous |
| te-168 | incident_type | unknown | heavy_traffic | 0.03 | noisy,ambiguous |
| te-168 | severity | unknown | medium | 0.04 | noisy,ambiguous |
| te-172 | severity | unknown | medium | 0.01 | contradictory |
| te-172 | road_obstruction | unknown | partial | 0.01 | contradictory |
| te-174 | road_obstruction | unknown | none | 0.03 | contradictory |
| te-175 | severity | unknown | low | 0.00 | contradictory |

## C

| id | field | gold | candidate | B1 p(gold) | tags |
|---|---|---|---|---|---|
| te-060 | road | SLEX | Marcos Highway | 0.01 | - |

Items with any disagreement in A or B: 23; of these tagged contradictory/ambiguous/noisy: 12 (te-023:contradictory, te-024:contradictory, te-025:contradictory, te-088:noisy, te-135:ambiguous, te-147:ambiguous, te-150:ambiguous, te-168:noisy, te-170:contradictory, te-172:contradictory, te-174:contradictory, te-175:contradictory)

## Null-road rule (B1 scores a null predicted road 0.0 with no call)

- B1: road AUROC all parseable (174) 0.809; non-null predicted road (145) 0.851; null predictions 29, of which gold-correct (null/null) 16
- B2: road AUROC all parseable (174) 0.885; non-null predicted road (145) 0.891; null predictions 29, of which gold-correct (null/null) 16
- gold road null items in test: 28
