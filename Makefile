mount:
	minikube mount /Users:/Users

watch:
	kubectl -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8443:443

clean:
	kubectl delete cronjob --all
	kubectl delete jobs --all

run:
	chainlit run main.py

# Do this every time we make a change to tools/
build_job_image:
	docker build -t ai-job:latest -f orchestrator/Dockerfile .