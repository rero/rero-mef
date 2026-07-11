#!/bin/sh
# Deploy the German hyphenation-decompounder dictionary files
# (dictionary-de.txt, de_DR.xml) to the mef-indexer ECK Elasticsearch
# cluster on dockertest2, via a ConfigMap mounted into config/analysis/.
#
# Prerequisite: kubernetes/indexer.yaml in the deployment-mef repo must
# already have the mef-german-analysis volume + volumeMounts added to
# both the master and data nodeSets (see the diff handed over separately
# -- this script does not edit indexer.yaml for you).

set -eu

CONTEXT=kubernetes-admin@dockertest2
NAMESPACE=mef
ANALYSIS_DIR="$(cd "$(dirname "$0")" && pwd)"
INDEXER_YAML="${1:-}"

# 1. Generate the ConfigMap manifest from the files in this directory.
kubectl create configmap mef-german-analysis \
  --from-file=dictionary-de.txt="${ANALYSIS_DIR}/dictionary-de.txt" \
  --from-file=de_DR.xml="${ANALYSIS_DIR}/de_DR.xml" \
  --namespace="${NAMESPACE}" \
  --dry-run=client -o yaml > "${ANALYSIS_DIR}/mef-german-analysis-configmap.yaml"

# 2. Apply the ConfigMap.
kubectl --context "${CONTEXT}" -n "${NAMESPACE}" apply \
  -f "${ANALYSIS_DIR}/mef-german-analysis-configmap.yaml"

# 3. Apply the updated Elasticsearch CR (triggers ECK's rolling restart).
#    Pass the path to your deployment-mef indexer.yaml as the first argument,
#    e.g.: ./deploy-german-analysis.sh /path/to/deployment-mef/kubernetes/indexer.yaml
if [ -n "${INDEXER_YAML}" ]; then
  kubectl --context "${CONTEXT}" -n "${NAMESPACE}" apply -f "${INDEXER_YAML}"
else
  echo "Skipping indexer.yaml apply: no path given as \$1." >&2
  echo "Run again as: $0 /path/to/deployment-mef/kubernetes/indexer.yaml" >&2
fi

# 4. Verify the files landed on a data node once its pod has rolled.
kubectl --context "${CONTEXT}" -n "${NAMESPACE}" exec mef-indexer-es-data-0 -- \
  ls -la /usr/share/elasticsearch/config/analysis
