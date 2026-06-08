#!/usr/bin/env bash
set -euo pipefail

FAKE_GIT_SHA="0123456789abcdef0123456789abcdef01234567"
FAKE_GIT_SHA_SHORT="${FAKE_GIT_SHA:0:12}"

REQUIRED_FILES=(
  ".github/workflows/ci.yml"
  "docs/aws-readiness.md"
  "docs/configuration.md"
  "docs/container-images.md"
  "docs/ecs-deployment-design.md"
  "infra/README.md"
  "infra/ecs/README.md"
  "infra/ecs/task-definitions/query-api.taskdef.json"
  "infra/ecs/task-definitions/processing-agent.taskdef.json"
  "infra/modules/ecr-publishing-prereqs/main.tf"
  "infra/modules/ecr-publishing-prereqs/variables.tf"
  "infra/modules/ecr-publishing-prereqs/outputs.tf"
  "infra/modules/ecr-publishing-prereqs/README.md"
  "infra/environments/dev/main.tf"
  "infra/environments/dev/versions.tf"
  "infra/environments/dev/variables.tf"
  "infra/environments/dev/locals.tf"
  "infra/environments/dev/outputs.tf"
  "infra/environments/dev/terraform.tfvars.example"
  "infra/environments/prod/main.tf"
  "infra/environments/prod/versions.tf"
  "infra/environments/prod/variables.tf"
  "infra/environments/prod/locals.tf"
  "infra/environments/prod/outputs.tf"
  "infra/environments/prod/terraform.tfvars.example"
  "scripts/resolve_image_tags.py"
)

TASK_DEFINITIONS=(
  "infra/ecs/task-definitions/query-api.taskdef.json"
  "infra/ecs/task-definitions/processing-agent.taskdef.json"
)

fail() {
  echo "error: $*" >&2
  exit 1
}

echo "==> Checking required AWS-readiness files"
missing=0
for file in "${REQUIRED_FILES[@]}"; do
  if [[ -f "${file}" ]]; then
    echo "ok: ${file}"
  else
    echo "missing: ${file}" >&2
    missing=1
  fi
done

if [[ "${missing}" -ne 0 ]]; then
  fail "required AWS-readiness files are missing"
fi

echo "==> Checking ECS task-definition JSON syntax"
for task_definition in "${TASK_DEFINITIONS[@]}"; do
  python3 -m json.tool "${task_definition}" >/dev/null
  echo "ok: ${task_definition}"
done

echo "==> Checking deterministic image-tag resolution"
image_output="$(
  env \
    -u APP_VERSION \
    -u GITHUB_SHA \
    -u GIT_SHA \
    -u OMNISTREAM_IMAGE_REGISTRY \
    -u OMNISTREAM_IMAGE_NAMESPACE \
    python3 scripts/resolve_image_tags.py --git-sha "${FAKE_GIT_SHA}"
)"
if [[ "${image_output}" != *"git_sha=${FAKE_GIT_SHA}"* ]]; then
  fail "image resolver output did not include the expected fake git SHA"
fi
if [[ "${image_output}" != *"git_sha_short=${FAKE_GIT_SHA_SHORT}"* ]]; then
  fail "image resolver output did not include the expected short fake git SHA"
fi
for key in query_api_image processing_agent_image producer_image; do
  if [[ "${image_output}" != *"${key}="* ]]; then
    fail "image resolver output did not include ${key}"
  fi
done
echo "ok: scripts/resolve_image_tags.py --git-sha ${FAKE_GIT_SHA}"

echo "==> Checking Terraform formatting"
if ! command -v terraform >/dev/null 2>&1; then
  echo "error: terraform CLI is required for AWS-readiness formatting verification." >&2
  echo "Install Terraform and rerun: terraform fmt -check -recursive infra" >&2
  exit 127
fi
terraform fmt -check -recursive infra
echo "ok: terraform fmt -check -recursive infra"

echo "AWS-readiness verification passed without AWS credentials."
