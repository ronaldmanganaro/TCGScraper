Cheat Sheet
kubetctl apply -f deployment.yaml
kubectl get nodes -o wide 
kubectl get pods
kubectl describe pod <podname>

Adding Nodes
Install the k3s-agent

Installing the k3s server
k3s

kubernetes dashboard 
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard
kubectl -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8443:443
ssh -L 8443:localhost:8443 rmangana@k3s-server
kubectl get serviceaccounts -n kubernetes-dashboard
kubectl -n kubernetes-dashboard create token dashboard-admin-sa

traefik Dashboard
https://3.233.208.225:30001/dashboard/#/

Good way to gauge cpu needs
rmangana@k3s-server:~/k8s$ kubectl top pod streamlit-app-58dd6974f-lc6v4 -n streamlit
NAME                            CPU(cores)   MEMORY(bytes)
streamlit-app-58dd6974f-lc6v4   4m           191Mi

Sealed Secret 
installed the cli
downloaded the helm chart
created the application manifest
added app to argocd
added sealed_secrets_values.yaml to override the nodeSelector
exported the secret
kubectl get secret <secret_name> -n <namespace> -o yaml > <secret.yaml>
sealed the secret and added the sealed secret to git
kubeseal --controller-name=sealed-secrets --controller-namespace=kube-system --format yaml < dockerhub-pat.yaml > dockerhub-pat-sealed.yaml