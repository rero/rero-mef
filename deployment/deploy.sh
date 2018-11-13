#! /bin/sh
set -e

VERSION=latest

cd ..
docker system prune -f
pipenv update
docker build --rm -t rero/rero-mef-nginx:${VERSION} docker/nginx/
docker push rero/rero-mef-nginx:${VERSION}
docker build --rm -t rero/rero-mef-base:${VERSION} -f Dockerfile.base .
docker build --rm -t rero/rero-mef:${VERSION} --build-arg VERSION=${VERSION} -f Dockerfile .
docker push rero/rero-mef:${VERSION}

cd ./deployment

sed -e "s/>>VERSION<</${VERSION}/g" kubernetes/frontend.tmpl > kubernetes/frontend.yaml
sed -e "s/>>VERSION<</${VERSION}/g" mef-setup.tmpl > mef-setup.yaml
sed -e "s/>>VERSION<</${VERSION}/g" mef-setup-viaf.tmpl > mef-setup-viaf.yaml
# preparations -----------------------------------------------------------------

# applay the cache, databse, frontend, indexer, mq, tasksui deployments
kubectl apply -f kubernetes --namespace=mef
# display the created pods
kubectl get pods --namespace=mef

# start setup
kubectl apply -f mef-setup.yaml --namespace=mef
# # display the log for the setup
# kubectl logs -f mef-setup --namespace=mef
# # delete setup
# kubectl delete -f mef-setup --namespace=mef

# start viaf setup
kubectl apply -f mef-setup-viaf.yaml --namespace=mef
# # display the log for the setup
# kubectl logs -f mef-setup-viaf --namespace=mef
# # delete setup
# kubectl delete -f mef-setup-viaf --namespace=mef
