package controllers

import (
	"database/sql"
	"myapp/app"

	"github.com/revel/revel"
)

type Account struct {
	*revel.Controller
}

func (c Account) Get() revel.Result {

	id := c.Params.Get("id")

	//
	var result string
	var data1 string
	err := app.DB.QueryRow("select data1 from account where id=?", id).Scan(&data1)
	switch {
	case err == sql.ErrNoRows:
		result = "0"
	case err != nil:
		revel.ERROR.Println(err)
		result = "fail"
	default:
		result = data1
	}

	return c.RenderText(result)
}

func (c Account) Post() revel.Result {

	values, err := c.Request.GetForm()
	if err != nil {
		revel.ERROR.Println(err)
	}

	id := values.Get("id")
	data := values.Get("value")

	query := "insert into account (id,data1) values (?,?) on duplicate key update data1=?"
	result, err2 := app.DB.Exec(query, id, data, data)
	if err2 != nil {
		revel.ERROR.Println(err2)
	}

	_, err3 := result.LastInsertId()
	if err3 != nil {
		revel.ERROR.Println(err3)
	}

	_, err4 := result.RowsAffected()
	if err4 != nil {
		revel.ERROR.Println(err4)
	}

	return c.RenderText("success")
}
