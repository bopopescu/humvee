package controllers

import (
	"database/sql"

	_ "github.com/go-sql-driver/mysql"

	"github.com/revel/revel"
	"github.com/underthepixel/humvee/app"
)

type Account struct {
	*revel.Controller
}

func (c Account) Get() revel.Result {

	id := c.Params.Get("id")

	var response string
	var data1 string
	err := app.DB.QueryRow("select data1 from account where id=?", id).Scan(&data1)
	switch {
	case err == sql.ErrNoRows:
		response = "0"
	case err != nil:
		revel.ERROR.Println(err)
		response = "fail"
	default:
		response = data1
	}

	return c.RenderText(response)
}

func (c Account) Post() revel.Result {

	values, err := c.Request.GetForm()
	if err != nil {
		revel.ERROR.Println("err != nil, err=", err)
		return c.RenderText("fail")
	}

	id := values.Get("id")
	data := values.Get("value")

	query := "insert into account (id,data1) values (?,?) on duplicate key update data1=?"
	result, err2 := app.DB.Exec(query, id, data, data)
	if err2 != nil {
		revel.ERROR.Println("err2 != nil, err2=", err2)
		return c.RenderText("fail")
	}

	_, err3 := result.RowsAffected()
	if err3 != nil {
		revel.ERROR.Println("err3 != nil, err3=", err3)
		return c.RenderText("fail")
	}

	return c.RenderText("success")
}
