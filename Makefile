
activate:
	conda activate oai
	source .env

mount:
	minikube mount /Users:/Users

watch:
	kubectl -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8443:443

clean:
	kubectl delete cronjob --all
	kubectl delete jobs --all