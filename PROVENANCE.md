# Provenance

## Source study

The `v1.1.0` sample is derived from the axial compressor stator study stored as
`data-repo/test-data-comp` in the private development history of `dbslice-ai`.
The study and the derived sample are copyright Graham Pullan.

The source comprises CFD cases spanning stator geometry and operating-point
changes. The declining number of available converged cases at higher exit
pressure is part of the source study and is intentionally visible in the
sample.

## Selection

The release builder preserves a source item when both conditions hold:

- `nstat` is the JSON number `100`; and
- `pexit` is one of `120000`, `124000`, `128000`, `132000`, `136000`,
  `140000`, `144000` or `148000` Pa.

All matching lean designs and every scalar property on each matching item are
retained. This produces 61 unique items, ordered as in the source metadata,
from `run_190` through `run_892`. The number of items at each pressure is:

| Exit pressure (Pa) | Items |
|---:|---:|
| 120000 | 9 |
| 124000 | 9 |
| 128000 | 9 |
| 132000 | 9 |
| 136000 | 9 |
| 140000 | 8 |
| 144000 | 5 |
| 148000 | 3 |

## Retained payloads

Four source files are copied for every selected item:

| Public extract | Kind | Source content |
|---|---|---|
| `Yp-downstream` | PNG image | downstream loss-coefficient slice |
| `Yp-downstream` embedding | JSON | 3x3 spatial summary of the image |
| `stator_exit_line_Yp` | JSON line | spanwise exit loss coefficient |
| `stator_3d_surface` | GLB | stator blades and exit cut plane |

The line extract also declares a computed five-bin, length-weighted cell
embedding along its monotonic `y` axis. It has no stored source payload.

Other images, other line variables, generated plots, `.DS_Store` files and
test artifacts are excluded.

## Transformations

The build is a selection and layout transformation, not a numerical
reprocessing step:

1. Matching item objects are copied without coercing JSON value types.
2. The metadata wrapper is reduced to the required `items` array.
3. Configuration descriptions and context are narrowed to the public sample.
4. Extract declarations and paths are narrowed to the three retained extracts.
5. Selected payload bytes are copied unchanged into the public layout.
6. Files are written to a deterministic ZIP in sorted path order with fixed
   timestamps and permissions.

The versioned release manifest records the SHA-256 digest and byte length of
every file inside the archive. The release `SHA256SUMS` file separately records
the digests of the archive and manifest.

## Curated reference

Release `v1.1.0` adds one URL-only curated reference:

- James V. Taylor and Robert J. Miller, *Competing Three-Dimensional
  Mechanisms in Compressor Flows*, Journal of Turbomachinery 139(2), 021009,
  DOI `10.1115/1.4034685`.

The metadata and original structured summary are stored in
`curated_references/papers.json`. The URL points to the authoritative
University of Cambridge repository record. That record identifies the accepted
manuscript as all rights reserved, so the paper itself is not copied into this
repository or the release archive. The repository's CC BY 4.0 licence applies
to the sample's metadata and summary, not to the externally linked paper.
