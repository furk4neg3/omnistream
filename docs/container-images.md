# Container Image Contract

## Purpose

This is an AWS-readiness image contract for OmniStream container images. The repository defines deterministic image names and tags for the three active services so CI can validate release-shaped builds and an opt-in manual workflow can publish the same immutable references to Amazon ECR.

This contract does not introduce Helm or deployment behavior. Docker Compose remains the local developer runtime. Terraform can optionally define the ECR repositories and GitHub Actions OIDC/IAM prerequisites for the existing manual publish workflow, but only when an environment root explicitly enables and applies `infra/modules/ecr-publishing-prereqs`.

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

Local verification and regular CI leave `OMNISTREAM_IMAGE_REGISTRY` empty. The manual ECR publishing workflow gets the registry hostname from `aws-actions/amazon-ecr-login` and passes it to the resolver.

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

An immutable tag must not be reassigned to different image contents. Manual publishing pushes this exact tag and should be run only for commits whose test, Compose validation, and Docker build checks have passed.

## CI Behavior

GitHub Actions resolves the contract tags with:

```bash
python3 scripts/resolve_image_tags.py
```

The Docker validation job then builds all three service images with the resolved immutable tags. The default CI workflow intentionally does not run `docker push`, does not request registry credentials, and does not use AWS credentials or AWS Actions.

## Manual ECR Publishing

`.github/workflows/publish-images.yml` is a manual-only `workflow_dispatch` workflow for publishing the three active service images to Amazon ECR. It does not run on push or pull request.

The workflow:

* checks out the repository;
* validates required GitHub repository variables;
* assumes an AWS role through GitHub Actions OIDC with `aws-actions/configure-aws-credentials`;
* logs in to Amazon ECR with `aws-actions/amazon-ecr-login`;
* resolves the final ECR image references with `scripts/resolve_image_tags.py`;
* verifies that the expected ECR repositories already exist;
* verifies that the resolved immutable tag has not already been published in those repositories;
* builds `query-api`, `processing-agent`, and `producer`; and
* pushes only the immutable `${APP_VERSION}-${GIT_SHA_SHORT}` tags.

It never pushes `latest`, never reassigns an existing immutable tag, never creates ECR repositories, and never deploys services.

The required ECR repositories and OIDC publish role may be created outside Terraform or by explicitly enabling and applying the optional `ecr-publishing-prereqs` module in an environment root. The workflow itself still only builds and pushes images.

### Required GitHub repository variables

Configure these repository variables before running the workflow:

| Variable | Required | Purpose |
| --- | --- | --- |
| `AWS_REGION` | Yes | AWS region containing the pre-existing ECR repositories. |
| `AWS_ROLE_TO_ASSUME` | Yes | IAM role ARN trusted by the repository's GitHub Actions OIDC provider. |
| `OMNISTREAM_IMAGE_NAMESPACE` | No | ECR repository namespace or prefix. Defaults to `omnistream`. |

Do not configure long-lived AWS access keys for this workflow. The intended authentication path is GitHub Actions OIDC.

The OIDC role needs permission to log in to ECR, describe the target repositories and image tags, and push image layers/manifests. Repository creation is intentionally outside this workflow. If the optional Terraform module is applied, its `ecr_publishing_role_arn` output is the value to configure as `AWS_ROLE_TO_ASSUME`.

### Required ECR repositories

The workflow assumes these ECR repositories already exist in `AWS_REGION`, either created manually or by applying the optional Terraform publishing prerequisites module:

```text
${OMNISTREAM_IMAGE_NAMESPACE}/query-api
${OMNISTREAM_IMAGE_NAMESPACE}/processing-agent
${OMNISTREAM_IMAGE_NAMESPACE}/producer
```

With the default namespace, those repository names are:

```text
omnistream/query-api
omnistream/processing-agent
omnistream/producer
```

If any repository is missing or the assumed role cannot describe it, the workflow fails before building or pushing images.

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
