# dbsliceAI sample data

This repository is the canonical home of the
[dbsliceAI dataset format](DATASET_FORMAT.md) and the release metadata for
compact, user-facing sample datasets. Large binary datasets are published as
GitHub Release assets and are not committed to ordinary Git history.

## Axial compressor sample

Release `v1.0.0` contains 61 converged cases from an axial compressor stator
study. Every case has scalar operating and performance properties plus:

- a downstream loss-coefficient (`Yp`) PNG and 3x3 grid embedding;
- a spanwise exit `Yp` line with a computed five-bin embedding; and
- a GLB model of the stator blades and exit cut plane.

The selection fixes `nstat` at 100 and retains the available lean designs at
alternate exit pressures from 120 kPa through 148 kPa. See
[PROVENANCE.md](PROVENANCE.md) for the exact selection and transformations.

Download `dbslice-ai-sample-data-1.0.0.zip` from the
[`v1.0.0` release](https://github.com/dbslice/dbslice-ai-sample-data/releases/tag/v1.0.0),
then verify it using the release's `SHA256SUMS` file:

```bash
shasum -a 256 -c SHA256SUMS
unzip dbslice-ai-sample-data-1.0.0.zip
```

While the repository is private, downloading the release requires access to
the `dbslice` GitHub organisation. The GitHub CLI can download all release
assets for an authorised user:

```bash
gh release download v1.0.0 \
  --repo dbslice/dbslice-ai-sample-data \
  --pattern 'dbslice-ai-sample-data-1.0.0*' \
  --pattern 'SHA256SUMS'
```

Register the extracted dataset with the public connector:

```bash
dbslice-ai-connector run \
  --dataset /absolute/path/to/dbslice-ai-sample-data-1.0.0
```

## Release contents

The archive has one dataset root:

```text
dbslice-ai-sample-data-1.0.0/
├── config/
│   └── config.json
└── data/
    ├── metadata/
    │   └── items.json
    └── extracts/
        ├── Yp-downstream/
        ├── stator_exit_line_Yp/
        └── stator_3d_surface/
```

The versioned manifest in [`releases/v1.0.0`](releases/v1.0.0) records every
archive file, its size and its SHA-256 digest. `SHA256SUMS` covers both the ZIP
and the manifest. The reproducible build and validation flow is implemented by
[`scripts/build_release.py`](scripts/build_release.py); its output directory
must be outside this Git worktree.

## Licence

The specification, documentation and released sample data are licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See
[LICENSE.md](LICENSE.md) for the copyright and attribution notice. Names,
logos and trademarks are not licensed.
