Cheat Sheet
kubetctl apply -f deployment.yaml
kubectl get nodes -o wide 
kubectl get pods
kubectl describe pod <podname>

k3s-agent
k3s


kubernetes dashboard 
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard
kubectl -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8443:443
ssh -L 8443:localhost:8443 rmangana@k3s-server
kubectl get serviceaccounts -n kubernetes-dashboard
kubectl -n kubernetes-dashboard create token dashboard-admin-sa

patch the service so that it uses node port instread of cluserip
kubectl -n kubernetes-dashboard patch svc kubernetes-dashboard-kong-proxy \
  -p '{"spec": {"type": "NodePort"}}'
