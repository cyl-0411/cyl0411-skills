# PPT Master Technical Design

## Source Content Conversion

Conversion prefers native Python readers for deterministic extraction and uses
external converters only for formats the native readers cannot preserve. Every
conversion result becomes a project source so downstream roles operate on one
stable representation.

## Image Acquisition & Embedding

Images remain external while SVG pages are authored and reviewed. Finalization
embeds or normalizes assets for portable delivery, while native PPTX conversion
may consume the original resource to preserve crop and vector semantics.

## Project Structure & Lifecycle

Each project owns its sources, images, templates, SVG outputs, notes, backups, and
exports. Importing with `--move` prevents the workflow from silently switching
between an external source and a project copy.

## Spec Propagation: spec_lock.md as Execution Contract

`spec_lock.md` is the machine-readable design contract. Narrow updates propagate
only declared colors and font fields; they do not regenerate content or create
implicit backups. The Executor rereads this contract before each page.

## Post-Processing Pipeline

Speaker-note splitting, SVG finalization, and PPTX export are separate ordered
stages. `svg_output/` remains the authored source, `svg_final/` is the portable
rendered form, and the exporter may use either according to fidelity needs.
