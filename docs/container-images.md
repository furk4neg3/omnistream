# Container Image Contract

## Purpose

This is an AWS-readiness pre-publishing step for OmniStream container images. The repository now defines deterministic image names and tags for the three active services so CI can validate future release-shaped builds without publishing images or depending on AWS.

This contract does not introduce ECR, registry credentials, Terraform, Helm, AWS Actions, or deployment behavior. Docker Compose remains the local developer runtime.

## Services

| Service | Dockerfile | Local image name |
| --- | --- | --- |
| `query-api` | `services/query-api/Dockerfile` | `omnistream/query-api:local` |
| `processing-agent` | `services/processing-agent/Dockerfile` | `omnistream/processing-agent:local` |
| `producer` | `services/producer/Dockerfile` | `omnistream/producer:local` |

The `:local` tag is a mutable developer convenience tag. It is acceptable for manual local builds and should not be used as a promoted deployment tag.

## Repository Variables

Image references are assembled from these variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OMNISTREAM_IMAGE_REGISTRY` | empty | Optional future registry host, such as an ECR registry hostname. Leave empty for local and CI build validation until image publishing is intentionally added. |
| `OMNISTREAM_IMAGE_NAMESPACE` | `omnistream` | Image namespace or repository prefix shared by all three services. |
| `APP_VERSION` | value from `.env.example`, currently `0.1.0` | Application version component for immutable image tags. |
| `GITHUB_SHA` or local `git rev-parse HEAD` | current commit | Git commit component for immutable image tags. |

With no registry configured, image repositories resolve to:

```text
omnistream/query-api
omnistream/processing-agent
omnistream/producer
```

With a future registry configured, the same repositories resolve to:

```text
${OMNISTREAM_IMAGE_REGISTRY}/${OMNISTREAM_IMAGE_NAMESPACE}/query-api
${OMNISTREAM_IMAGE_REGISTRY}/${OMNISTREAM_IMAGE_NAMESPACE}/processing-agent
${OMNISTREAM_IMAGE_REGISTRY}/${OMNISTREAM_IMAGE_NAMESPACE}/producer
```

Do not configure a live registry in CI until a separate publishing step is explicitly implemented.

## Immutable Tags

The immutable tag format is:

```text
${APP_VERSION}-${GIT_SHA_SHORT}
```

`GIT_SHA_SHORT` is the first 12 lowercase characters of the commit SHA. Example:

```text
omnistream/query-api:0.1.0-abc123def456
omnistream/processing-agent:0.1.0-abc123def456
omnistream/producer:0.1.0-abc123def456
```

An immutable tag must not be reassigned to different image contents. Future publishing should push this exact tag after tests, Compose validation, and Docker builds pass.

## CI Behavior

GitHub Actions resolves the contract tags with:

```bash
python3 scripts/resolve_image_tags.py
```

The Docker validation job then builds all three service images with the resolved immutable tags. CI intentionally does not run `docker push`, does not request registry credentials, and does not use AWS credentials or AWS Actions.

## Local Verification

The helper can be run directly to inspect the resolved image references for the current checkout:

```bash
python3 scripts/resolve_image_tags.py
```

Manual local builds may continue to use the mutable local aliases:

```bash
docker build \
  --build-arg INSTALL_SENTENCE_TRANSFORMERS=false \
  -f services/query-api/Dockerfile \
  -t omnistream/query-api:local .

docker build \
  --build-arg INSTALL_SENTENCE_TRANSFORMERS=false \
  -f services/processing-agent/Dockerfile \
  -t omnistream/processing-agent:local .

docker build \
  -f services/producer/Dockerfile \
  -t omnistream/producer:local .
```
