# Dinosaur

This package is a vendored, editable copy of the upstream `dinosaur` package used
by NeuralGCM. It is the canonical Dinosaur dycore implementation used by
Dynamaxx.

- Upstream package: `dinosaur`
- Vendored version: `1.3.6`
- License: Apache License 2.0, preserved in `LICENSE`
- Runtime modules and package data are copied locally so Dynamaxx can apply
  dycore-specific optimizations without depending on the external package.

The vendored package intentionally uses internal
`dynamaxx.dycore.models.dinosaur` imports instead of importing the external
`dinosaur` package. When `dinosaur` is registered as a Dynamaxx dycore, it runs
this vendored implementation.
