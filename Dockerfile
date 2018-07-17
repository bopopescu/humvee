FROM golang:1.10.3

RUN go get github.com/revel/revel
RUN go get github.com/revel/cmd/revel
RUN go get github.com/go-sql-driver/mysql

EXPOSE 9000

CMD revel run humvee