# Run this in terminal
mount:
	minikube mount /Users:/Users

watch:
	kubectl -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8443:443

dashboard-token:
	kubectl -n kubernetes-dashboard create token default

clean:
	kubectl delete cronjob --all
	kubectl delete jobs --all

run:
	chainlit run main.py

# Do this every time we make a change to tools/
push-job-image:
	docker build -t ai-job:latest -f orchestrator/Dockerfile .
	docker tag ai-job:latest dean27/orchestrai:latest
	docker push dean27/orchestrai:latest

# When a job is failing
inspect-job-logs:
	@kubectl logs $$(kubectl get pods -n default --no-headers | awk 'NR==1{print $$1}') -n default