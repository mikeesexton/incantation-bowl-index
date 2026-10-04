# Mike-only source passages

Source passages hold manuscript, literary and other comparisons separately from
physical bowls and their editions. They are searchable at `#/contexts` in Mike
Access and the localhost reader. They never contribute to bowl reading counts,
and the public/shared projection does not expose them.

The database's private directory may contain `reader/source_contexts.json`, a
version1 registry whose entries bind each copy to an immutable document assessment,
its extraction index, a checked context bundle, the registered source capture and
their hashes. Each entry retains attribution, source pages, language/script,
reviewer/time, uncertainty and editorial interventions. Earlier checked pairs
must be explicitly referenced by the current bundle and their retained review.

Keep the registry and its intake manifests outside Git. Retain previous manifests
before appending new entries. A corrected copy needs a new immutable copy/review;
never change a retained file to satisfy its registered hash. The loader rejects
changed content, attribution, notes, annotations, source assignment, assessment
bindings, duplicate IDs and paths outside the project. It returns no vault paths.

The static builder packages the validated rows in its ignored private directory,
and its inventory checks every row against the private projection. The localhost
endpoint is `/api/private-source-contexts`. Neither route grants public reuse or
claims an original manuscript/clay check. Source links use registered capture IDs
and the supplied PDF page; retained HTML remains a download.

Rebuild with `PYTHONPATH=src .venv/bin/python scripts/build_mike_access.py` after a
registry change. Check source search, attribution, notes, source links and narrow
screen layout before closing the working session.
