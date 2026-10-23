# dbsliceAI dataset format

Specification version: **1.1**

This document defines the portable data format understood by dbsliceAI
and `dbslice-ai-connector`. A dataset is a directory containing configuration,
an item list and optional per-item extract payloads.

## Directory structure

`config/config.json` is required at the dataset root. A conventional layout,
including the optional curated-reference manifest, is:

```text
example-dataset/
├── config/
│   └── config.json
├── curated_references/
│   └── papers.json
└── data/
    ├── metadata/
    │   └── items.json
    └── extracts/
        └── pressure/
            ├── item_1.png
            └── item_2.png
```

Extract files do not have to use this exact directory convention, but keeping
each extract under `data/extracts/<extractId>/` is recommended. Every entry
(or row) in `items.json` contains an `itemId`. Each extract filename for that
item must contain the exact `itemId` value, normally by using the `${itemId}`
placeholder in its declared path.

## Configuration

`config/config.json` must be a JSON object with these fields:

| Field | Requirement | Meaning |
|---|---|---|
| `dataset` | required object | dataset-level description and context |
| `metaData` | required object | item-list location and descriptive metadata |
| `extracts` | required array | zero or more extract declarations |
| `curatedReferences` | optional object | location of a linked curated-reference manifest |

A minimal configuration is:

```json
{
  "dataset": {
    "title": "Example study"
  },
  "metaData": {
    "path": "data/metadata/items.json",
    "config": {
      "title": "Example study",
      "description": "Two example cases"
    }
  },
  "extracts": [
    {
      "extractId": "pressure",
      "type": "image",
      "description": "Pressure for each case",
      "format": "png",
      "path": "data/extracts/pressure/${itemId}.png"
    }
  ]
}
```

### Dataset description and context

`dataset.title` is recommended. Other JSON fields may be used as descriptive
metadata. dbsliceAI currently understands these optional `dataset.context`
fields:

| Field | Shape | Meaning |
|---|---|---|
| `summary` | string | concise study description |
| `primaryInputs` | array of property-name strings | important input properties in the item metadata |
| `primaryOutputs` | array of property-name strings | important output properties in the item metadata |
| `primaryExtracts` | array of extract-ID strings | important `extractId` values from `extracts` |

Every `primaryInputs` and `primaryOutputs` entry must exactly match a property
name on the item objects in the metadata file named by `metaData.path`. Every
`primaryExtracts` entry must exactly match an `extractId` in the top-level
`extracts` array. These references are case-sensitive. dbsliceAI does not
currently verify that the references exist, so dataset authors must keep them
consistent. These fields guide presentation and analysis; they do not change
how files are loaded.

### Curated references

A dataset may declare literature selected to help interpret its results:

```json
{
  "curatedReferences": {
    "path": "curated_references/papers.json"
  }
}
```

The path follows the same containment rules as other dataset paths and names a
UTF-8 JSON file containing an array. Every entry requires non-empty `paperId`,
`title` and `url` strings. `paperId` values must be unique within the manifest,
and `url` must use HTTP or HTTPS. An entry may also contain `authors`, `year`,
`venue`, `doi`, `contentType`, `rights`, `summary`, `summaryBrief`,
`summaryExtended`, `keyFindings`, `figures`, `citations`, `tags` and
`summaryData`.

The connector loads the manifest and exposes its citation, summary and web-link
metadata as `dataset.curatedReferences`; it never exposes
`curatedReferences.path`. This portable declaration does not transfer local
documents through the connector. References link to an authoritative repository
or publisher page instead of including a local copy of a paper. Dataset authors
are responsible for respecting the linked work's licence and must not assume
that public download access grants redistribution rights.

### Item-list declaration

`metaData.path` must be a non-empty dataset-relative path to the item-list JSON
file. `metaData.config` must be an object and is exposed as descriptive dataset
metadata. Its contents are otherwise application-defined.

Local filesystem fields are private. The connector exposes `dataset`,
`metaData.config` and public extract declarations to dbsliceAI clients, but it
does not expose `metaData.path`, extract paths or embedding paths.

## Items

The file named by `metaData.path` must be a JSON object containing an `items`
array:

```json
{
  "items": [
    { "itemId": "item_1", "angle": 12.5, "efficiency": 0.91 },
    { "itemId": "item_2", "angle": 14.0, "efficiency": 0.93 }
  ]
}
```

Every array entry must be an object with a non-empty string `itemId`. Item IDs
should be unique within the dataset; duplicate IDs make lookup results
ambiguous. Other properties may contain ordinary JSON strings, numbers,
booleans, arrays, objects or `null`.

Properties intended for numeric filtering or analysis must be encoded as JSON
numbers rather than numeric strings. Server-local legacy data may coerce some
numeric strings, but connector-backed datasets preserve native JSON types.

`itemId`, `label`, `embeddings` and fields whose names start with `_` are
reserved or descriptive and are not treated as ordinary discoverable analysis
properties.

## Extract declarations

Every entry in `extracts` must be an object containing non-empty string values
for:

- `extractId`, unique within the dataset;
- `type`, exactly `image`, `line`, `glb` or `embedding`;
- `description`; and
- `path`, a dataset-relative payload path or path template for visual extracts.
  An `embedding` extract instead requires an `embedding` declaration with a
  stored-data path and configured shape; no top-level visual path is needed.

The optional common fields are:

| Field | Meaning |
|---|---|
| `format` | payload format; defaults by type to `png`, `json` or `glb` |
| `xLabel`, `yLabel` | axis labels for line presentation |
| `filter` | descriptive filter object with a non-empty `type` and optional `settings` object |
| `render` | GLB rendering defaults |
| `embedding` | required stored declaration for `type: "embedding"`; optional stored or computed declaration for other extract types |

The legacy fields `images`, `line`, `imageId`, `embedId` and
`embedding.embedId` are not supported.

### Path templates and containment

`${itemId}` is the only supported placeholder. It is replaced literally with
the selected item's ID. Any unresolved `${...}` placeholder is rejected.

All configuration paths must resolve within the configured dataset root.
Absolute paths, `..` traversal and symbolic links that resolve outside that
root are not portable and are rejected by the readers. A referenced path must
name a regular file. Payload files are loaded only when requested.

Each decoded image, line, GLB or stored embedding payload must be no larger
than 16 MB. JSON payloads must be UTF-8 encoded.

## Image extracts

An image declaration has `type: "image"`:

```json
{
  "extractId": "pressure",
  "type": "image",
  "description": "Surface pressure",
  "format": "png",
  "path": "data/extracts/pressure/${itemId}.png"
}
```

Supported formats are PNG, JPEG (`jpg` or `jpeg`), GIF and SVG. Supplying
`format` explicitly is recommended; when omitted, PNG is the default.

## Line extracts

A line declaration has `type: "line"` and normally `format: "json"`:

```json
{
  "extractId": "velocity-profile",
  "type": "line",
  "description": "Velocity through the passage",
  "format": "json",
  "xLabel": "Distance",
  "yLabel": "Velocity",
  "path": "data/extracts/velocity-profile/${itemId}.json"
}
```

The JSON payload may be an array of points:

```json
[
  { "x": 0.0, "y": 12.1 },
  { "x": 0.5, "y": 14.8 }
]
```

or an object with a `data` array and optional string `label`:

```json
{
  "label": "item_1",
  "data": [
    { "x": 0.0, "y": 12.1 },
    { "x": 0.5, "y": 14.8 }
  ]
}
```

Every point must be an object with finite JSON-number `x` and `y` values. A
line used for computed bins must also be monotonic along the configured axis.

## GLB extracts

A GLB declaration uses `type: "glb"`, normally with `format: "glb"`:

```json
{
  "extractId": "geometry",
  "type": "glb",
  "description": "Three-dimensional geometry",
  "format": "glb",
  "path": "data/extracts/geometry/${itemId}.glb"
}
```

GLB payloads use the binary glTF media type `model/gltf-binary`.

An optional `render` object may provide defaults used when dbsliceAI renders
the model. Recognised fields are `width`, `height`, `backgroundColor`,
`cameraDirection`, `distanceMultiplier`, `ambientLightIntensity` and
`directionalLightIntensity`. `cameraDirection` is an object with numeric `x`,
`y` and `z` components. Explicit render-tool arguments override these defaults.

## Embeddings

An extract may declare an `embedding` used for spatial or cell-based analysis.
Canonical embedding types are exactly `grid` and `cells`; canonical sources
are exactly `file` and `computed`.

New datasets should explicitly provide `source`. Readers also recognise an
existing file-backed declaration with `path` and no `source` as `file`.

### Standalone embedding extracts

An embedding can be an extract in its own right, without an image, line, or GLB:

```json
{
  "extractId": "Yp-3d",
  "type": "embedding",
  "description": "Logical stack of Yp hub, mid-span, and tip slice cells",
  "embedding": {
    "type": "cells",
    "source": "file",
    "path": "data/extracts/Yp-3d/${itemId}_cells_embed.json",
    "settings": { "shape": [2, 5, 3] }
  }
}
```

The extract type describes its role; `embedding.type` describes the numeric
representation. Standalone extracts currently require stored embeddings and
`settings.shape`. They use the same analysis selectors and access operations
as embeddings attached to visual extracts. `render_extracts` uses configured physical geometry when present, independently
of array rank. Without geometry it displays 1D bars, 2D heatmaps, or 3D translucent blocks. The blocks touch, forming a continuous
array. Axis-aligned slices are optional; requesting both views produces
separate PNGs. Higher ranks support numerical analysis and configured physical geometry;
logical display requires explicit slicing.

### Stored embeddings

A file-backed embedding requires `source: "file"` and a non-empty
dataset-relative `path`:

```json
{
  "extractId": "pressure",
  "type": "image",
  "description": "Surface pressure",
  "format": "png",
  "path": "data/extracts/pressure/${itemId}.png",
  "embedding": {
    "type": "grid",
    "source": "file",
    "description": "A two by two pressure summary",
    "path": "data/extracts/pressure/${itemId}_embedding.json",
    "settings": { "shape": [2, 2] }
  }
}
```

The stored JSON payload must be an object with `shape` and `cells` arrays:

```json
{
  "shape": [2, 2],
  "cells": [
    { "index": [0, 0], "avg": 0.12, "label": "upper left" },
    { "index": [0, 1], "avg": 0.18, "label": "upper right" },
    { "index": [1, 0], "avg": 0.15, "label": "lower left" },
    { "index": [1, 1], "avg": 0.21, "label": "lower right" }
  ]
}
```

Shapes contain one or more positive integers, with at most 100,000 total cells.
Each payload contains every declared cell exactly once, in lexicographic order
with the last index varying fastest. Indices are integers within shape bounds. For a one-dimensional `cells` shape,
`index` may be omitted: position `n` means `[n]`. Mixed explicit/implicit entries
are allowed, but explicit indices must still match their canonical position.
An explicit `null`, wrong-rank or out-of-range index is invalid. Higher ranks
require explicit indices. Readers expand the 1D shorthand once at the data boundary;
internal and returned cell records use explicit `index` tuples.
For `[ni, nj, nk]`, the array offset is `(i * nj + j) * nk + k`.
All items for an extract use the same shape and cell correspondence. Configured
`settings.shape`, when present, must match the payload. The producer supplies
the cell values; dbsliceAI does not infer physical coordinates or interpolate
these stored embeddings.

`avg` must be a finite number or `null`. Keep an empty cell in its ordinal slot
with `avg: null`; zero is a real measurement. Labels, region names, and other
numeric fields such as `min`/`max` may accompany each cell. Invalid payloads
fail analysis; absent files can be omitted from analysis with per-cell sample
counts reflecting the available values.

`cells` supports arbitrary dimensionality. `grid` retains its two-dimensional
contract and requires `settings.shape`. The 3D renderer accepts up to 4096
cells and offers `blocks` (default), `slices`, and `both` views with uniform opacity,
camera direction, and a bounded number of slices. `sliceAxis` holds `i` (0),
`j` (1), or `k` (2, default) constant; the remaining axes retain their order as
rows and columns. `maxSlices` defaults to 6 (range 1–12). If capped, slices are
evenly spaced including both endpoints; a limit of 1 selects index 0. The PNG
and rendering metadata report the axis, selected indices and omitted count.
These display options do not alter numerical results. Connector installations must include the protocol
schema that recognizes the `embedding` extract type.

### Shared physical cell geometry and names

Physical geometry belongs to `embedding.settings` in the extract config, shared
by all items. It is optional. Numerical files continue to contain only `shape`,
`cells`, and their values/optional existing labels. Geometry does not change cell
correspondence, analysis, regression or ranking. Item responses do not repeat
vertices or boundary connectivity; renderers receive them explicitly from config.

`settings.regions` maps logical cells to optional `name` and boundary references.
There is no `geometry.cells` list. Names are optional with or without geometry:
display names resolve from a nonblank cell `label`, then cell `region`, then
config region `name`, then `Cell(i,j,...)`. Existing payload names remain valid.
Without geometry, `regions` can be omitted or sparse. With geometry, it must map
every slot exactly once. Explicit region indices may be reordered. For shape
`[N]`, an omitted region index means its array position `[n]`; mixed entries must
still resolve to distinct, in-range indices. Higher ranks require indices.

The same four physical cells can use a `[2,2]` or `[4]` numerical layout:

```json
{
  "shape": [2, 2],
  "geometry": {
    "type": "polygons",
    "units": "mm",
    "vertices": [[0,0],[1,0],[2,0],[0,1],[1,1],[2,1],[0,2],[1,2],[2,2]]
  },
  "regions": [
    {"index":[0,0], "name":"inlet", "boundaryVertexIndices":[0,1,4,3]},
    {"index":[0,1], "boundaryVertexIndices":[1,2,5,4]},
    {"index":[1,0], "boundaryVertexIndices":[3,4,7,6]},
    {"index":[1,1], "boundaryVertexIndices":[4,5,8,7]}
  ]
}
```

For the flat version, retain `geometry`, use `shape: [4]`, and omit the four
region indices (or use `[0]` through `[3]`). Its numerical payload can be:

```json
{"shape":[4], "cells":[{"avg":0.12},{"avg":0.18},{"avg":null},{"avg":0.21}]}
```

`geometry.type` selects physical dimensionality independently of logical shape:

- `polygons`: each vertex is `[x,y]`. Each region has `boundaryVertexIndices`,
  an ordered simple polygon boundary of at least three vertices. Do not repeat
  the first vertex at the end. Either winding is accepted; holes, crossings,
  zero-area boundaries and disconnected patches are unsupported.
- `polyhedra`: each vertex is `[x,y,z]`. Each region has `triangleVertexIndices`,
  an array of three-index triangles forming one closed, outward-wound shell.
  Every edge belongs to two oppositely oriented triangles; every vertex has a
  connected face fan. Duplicate/degenerate triangles and nonpositive signed
  volume are rejected. Open surface patches and multiple shells are unsupported.

Coordinates must be finite and share one Cartesian frame; optional `units` is a
nonblank display label applying to all coordinates. No unit conversion occurs.
Vertex references are zero-based integer positions in `geometry.vertices`.
Validation uses coordinates normalized by each region's longest extent, with a
relative tolerance of `1e-12`; degenerate or unrepresentable extents are invalid.
Shell checks do not certify that distant triangles or different cells do not
intersect; producers remain responsible for geometrically valid disjoint cells.

Limits are 100,000 vertices and 600,000 vertex references per geometry, 512
vertices per polygon, and 4096 triangles per polyhedron. Physical rendering is
limited to 4096 cells. Invalid supplied geometry raises an error, including when
logical rendering is requested; it never silently falls back to guessed geometry.

Rendering options are shared by raw embedding extracts, correlation maps and
regression coefficient maps. `coordinateSpace` defaults to `auto` (physical when
configured); `logical` uses array coordinates; `physical` requires geometry.
`view: "blocks"` is the default physical overview (polygons or volumes).
`slices` and `both` require rank three and select **logical** array planes, even
when geometry exists; physical plane cuts/caps are not implemented. 3D
`creaseAngle` is in degrees (default 1, range 0–180); coplanar triangulation
diagonals are hidden while boundaries are outlined separately for each cell.
`opacity` and `cameraDirection` apply to 3D overviews. Missing physical cells
remain visible as grey polygons or unfilled volume outlines. Plot provenance
retains exact geometry, names, mapping, units and effective render options.

Connector protocol v1 now permits omitted 1D indices. Existing explicit-index
payloads remain compatible; update both connector and host to this schema before
using the shorthand. Older protocol-v1 installations may reject it. Inline
geometry travels through the existing config operation without new endpoints.

### Computed line-bin embeddings

Computed embeddings currently support one interoperable form:

```json
{
  "type": "cells",
  "source": "computed",
  "method": "line_bins",
  "description": "Five summaries along the span",
  "settings": {
    "monotonicAxis": "y",
    "bins": 5,
    "aggregation": "length_weighted"
  }
}
```

Requirements:

- `type` must be `cells`;
- `method` must be `line_bins`;
- `settings` must be an object;
- `settings.monotonicAxis` must be `x` or `y`;
- optional `settings.bins` must be a positive integer and defaults to 5; and
- optional `settings.aggregation` must be `length_weighted` and defaults to
  that value.

A computed embedding has no source payload file and must not be requested as a
stored connector payload. dbsliceAI derives it from the associated line data.

## Connector registration

Run the connector with the dataset root:

```bash
dbslice-ai-connector run \
  --dataset /absolute/path/to/example-dataset
```

The connector reads the display name from `dataset.title` and derives the
dataset ID from that title. Connector-local filesystem paths stay private and
are never returned in client-facing dataset results.
