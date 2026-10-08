# GitHub Actions

`test-pipeline.yml` runs on push/PR/manual dispatch, installs Python/Node with caches, distro CPU tools, tests and typechecks, and renders the 30s draft example. Optional backend tests can skip when dependencies aren't installed; CI does not claim those passed. CI has a 20-minute timeout and uploads example diagnostics for 3 days.

`render-video.yml` is workflow_dispatch only: project, resolution, preset, keep_intermediates. It requires a `videos/<safe-project-id>` path and validates existence before rendering/caching. Input values enter shell steps via environment variables and quoted arguments, not expression interpolation into executable code. Core runtime additionally confines paths and validates resolutions/specs.

The workflow has read-only contents permissions, one job (no expensive matrix), per-branch concurrency, pip/scene caches and a 45-minute timeout. Scene cache keys include commit/preset/project; content hashes decide which restored scenes remain valid. Artifacts retain for 7 days and are uploaded on failures for diagnostics. Caches/artifacts still consume account storage.

Manual workflows generally need to exist on the default branch before GitHub exposes the Run workflow button. Merge your reviewed working branch first; select the appropriate ref/project. No secrets are required for the core path. External providers, if implemented later, must use GitHub Secrets and explicit permission; never print credentials.

No hosted Actions run is claimed merely because YAML was syntax-checked locally. View actual checks after pushing. Account allowances vary; check GitHub billing/usage and shorten drafts/resolution/retention before expensive jobs. The workflow does not query private billing APIs or pretend it can guarantee remaining minutes.
