# Contributing

Thanks for considering a contribution. This project is a reference
implementation, so contributions that keep it small, readable, and faithful
to current OpenChoreo conventions are the most valuable.

## Ground rules

- **Synthetic data only.** Do not commit anything that resembles real PII,
  real TINs, real NIDs, or real return figures. TINs must stay within the
  reserved test range (`900000001`–`999999999`).
- **Mirror OpenChoreo samples.** If you add or change anything under
  `openchoreo/`, base the change on the current
  [openchoreo/openchoreo samples](https://github.com/openchoreo/openchoreo/tree/release-v1.1/samples)
  for the same OpenChoreo version. Do not invent CRD fields.
- **Keep services minimal.** Each service should be small enough to read in
  one sitting. Resist adding ORMs, background workers, or auth frameworks
  beyond what the demo needs.
- **No marketing prose.** Documentation is for engineers. Short sentences,
  direct claims, no hype.

## Development workflow

1. Fork and clone.
2. Install Docker and `docker compose`.
3. From the repository root:
   ```
   make up        # build images and start the compose stack
   make smoke     # end-to-end curl smoke tests
   make down      # stop the stack
   ```
4. To run a single service's tests:
   ```
   cd services/taxpayer-registry
   docker build --target test -t srx-taxpayer-registry:test .
   docker run --rm srx-taxpayer-registry:test
   ```

## Pull requests

- One logical change per PR.
- Include a short rationale in the PR description.
- If you change an OpenChoreo resource, link to the upstream sample you
  adapted it from.
- New behaviour requires a smoke test in `scripts/smoke.sh` or a unit test
  in the affected service.

## Reporting issues

Open an issue with reproduction steps, expected vs. actual behaviour, and
the OpenChoreo version you ran against (`v1.1.x`).
