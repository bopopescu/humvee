FROM golang:1.10.3

ADD . /go/src/github.com/underthepixel/humvee

RUN go get github.com/revel/revel
RUN go get github.com/revel/cmd/revel
RUN go get github.com/go-sql-driver/mysql

ENTRYPOINT revel run github.com/underthepixel/humvee dev 8080

EXPOSE 8080