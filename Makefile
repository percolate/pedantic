build:
	docker build --tag prclt/pedantic .
	docker images --format "{{.Repository}}: {{.Size}}" | grep prclt/pedantic

dev:
	docker run --volume $$(pwd):/pedantic --interactive --tty --entrypoint sh prclt/pedantic
