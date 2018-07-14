# Use the official go docker image built on debian.
FROM golang:1.10.3# Grab the source code and add it to the workspace.
ADD . /go/src/github.com/humvee

# Install revel and the revel CLI.
RUN go get github.com/revel/revel
RUN go get github.com/revel/cmd/revel
RUN go get github.com/go-sql-driver/mysql

# Use the revel CLI to start up our application.
ENTRYPOINT revel run github.com/github.com/humvee dev 8080

# Open up the port where the app is running.
EXPOSE 8080
