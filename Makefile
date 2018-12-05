.PHONY : build test server

server : build
	docker run --name tornado_tcp -p 8888:8888 -p 8889:8889 -d tornado_tcp

test : build
	docker run --name tornado_tcp_tests --rm tornado_tcp tests

build :
	docker build -t tornado_tcp .