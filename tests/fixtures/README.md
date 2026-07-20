# Test fixtures — the frozen parity corpus

Fixed inputs for R→Python parity checks. **Committed and immutable**: the R golden outputs
under `tests/golden/` (gitignored, regenerable) are captured from *these exact bytes*, so a
Python port is compared against R on identical inputs. Do not edit a fixture without
re-capturing the affected goldens (`python tests/parity/capture.py <module>`).

## `corpus/` — real raw workbooks

A small representative subset of the R project's raw import workbooks, copied verbatim from

    <whep-digitalization>/data/1-import/10-raw_import/

The directory layout mirrors the source (`<yearbook>/<yearbook>_<category>/<file>.xlsx`), so
`corpus/` is a drop-in raw-import root for future ingest-stage (Stage 1) parity captures. One
smallest-available workbook per data category was chosen to span the ingest surface while
keeping the committed binary footprint tiny (~37 KB total):

| Category   | File |
|------------|------|
| crops      | `fao_1949/fao_1949_crops/r_fao_1949_crops_92_92_date.xlsx` |
| livestock  | `fao_1949/fao_1949_livestock/r_fao_1949_livestock_162_162_milk.xlsx` |
| population | `fao_1949/fao_1949_population/r_fao_1949_population_24_24_population_agriculture.xlsx` |
| inputs     | `fao_1955/fao_1955_inputs/r_fao_1955_inputs_228_229_pesticide_fluoride.xlsx` |
| land       | `fao_1952/fao_1952_land/r_fao_1952_land_3_9_irrigation_permanent_meadows_pastures.xlsx` |
| trade      | `fao_1950/fao_1950_trade/r_fao_1950_trade_106_106_palm_kernel_oil.xlsx` |

## `synthetic/` — edge-case fixtures

Tiny hand-authored fixtures that force the edge cases real workbooks may not contain.

### `normalize_string_inputs.json`

A JSON array of raw strings (read by `jsonlite::fromJSON` in R → character vector, and by
`json.load` in Python → `list[str | None]`). JSON is used because it is the only format that
round-trips the **NA-vs-empty-string** distinction unambiguously: JSON `null` ⇄ R `NA` ⇄
Python `None`, kept distinct from `""`. That distinction is what pipeline match keys hinge on.

Every listed migration edge case is covered:

| Edge case            | Element(s) |
|----------------------|------------|
| plain / lowercasing  | `"Hello World"` |
| accented / unicode   | `"café résumé"`, `"Peña"`, `"Côte d'Ivoire"`, `"Åland"` |
| empty string         | `""` |
| NA / null            | `null` |
| whitespace squish    | `"North  America"`, `"  leading  "` |
| duplicates           | `"North  America"` ×2 (exercises the unique→match fast path) |
| wildcard token       | `"__ANY__"` → `any` |
| punctuation stripping| `"RICE-01"`, `"test@#$123"` |
| anyascii-vs-ICU risk | `"groß"` (ß→ss), `"½ kg"` (½→"1 2"), `"œuvre"` (œ→oe), `"ßharp"` |

The last row is the point of highest parity risk (transliteration divergence between Python
`anyascii` and R ICU `Latin-ASCII`). See `.claude/docs/r-to-python-mapping.md`.

### `file_metadata_inputs.json`

A JSON array of file-path strings fed to `extract_file_metadata` (`10-metadata.R` →
`ingest/file_io/metadata.py`). The first six are the real `corpus/` workbook paths
(relative, forward-slash); the rest force the positional-parsing edge cases:

| Edge case                         | Element |
|-----------------------------------|---------|
| real corpus paths (basename via `path_file`) | the six `tests/fixtures/corpus/.../*.xlsx` |
| `<=6` tokens → no commodity       | `r_fao_1961_crops_1_1.xlsx` |
| no 4-digit token → no yearbook    | `r_fao_crops_wheat.xlsx` |
| `<2` tokens → no yearbook         | `2020.xlsx` |
| first 4-digit token wins          | `r_fao_1961_a_b_c_2000_wheat.xlsx` → yearbook `fao_1961`, commodity `2000_wheat` |
| non-ASCII name (`is_ascii=FALSE` + error message) | `r_fao_1949_a_b_c_wheat_café.xlsx` |

## Regenerating goldens

Goldens are derived from these fixtures via the R source of truth:

    .venv/Scripts/python.exe tests/parity/capture.py            # all modules
    .venv/Scripts/python.exe tests/parity/capture.py string_normalization

Then verify the Python port matches:

    .venv/Scripts/python.exe -m pytest -m parity
