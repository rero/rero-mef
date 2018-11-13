#! /bin/sh

# preparations -----------------------------------------------------------------
# create a namespace
kubectl apply -f mef-namespace.yaml
# create volume claims
# for osx change to storageclass.kubernetes.io/is-default-class: "true"
kubectl apply -f mef-volume-claim-db.yaml --namespace=mef
kubectl apply -f mef-volume-claim-es.yaml --namespace=mef
kubectl apply -f mef-volume-claim-mq.yaml --namespace=mef
kubectl apply -f mef-volume-claim-data.yaml --namespace=mef

# init the volume data
kubectl apply -f mef-volume-init-data.yaml --namespace=mef
...
kubectl exec -it init-data -n mef  -- /bin/bash
    apt-get update
    apt-get install rsync openssh-client -y
    rsync -av wep@plexus.rero.ch:/rero/tmp/latest /claim/
    exit
kubectl delete -f mef-volume-init-data.yaml --namespace=mef

# secrets must be set once
# kubectl get secrets mef -o yaml > mef-secrets.yaml
kubectl apply -f mef-secrets.yaml --namespace=mef
# apply the limits
kubectl apply -f mef-limits.yaml --namespace=mef
# apply configmap
kubectl apply -f mef-configmap.yaml --namespace=mef
# apply services
kubectl apply -f mef-services.yaml --namespace=mef

# # kubernets dashboard install with graphs ------------------------------------
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/heapster/master/deploy/kube-config/influxdb/influxdb.yaml
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/heapster/master/deploy/kube-config/influxdb/grafana.yaml
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/heapster/master/deploy/kube-config/influxdb/heapster.yaml
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/heapster/master/deploy/kube-config/rbac/heapster-rbac.yaml
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v1.10.1/src/deploy/recommended/kubernetes-dashboard.yaml
# # start the kubernets dashboard server ---------------------------------------
# kubectl proxy
# http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace=mef
