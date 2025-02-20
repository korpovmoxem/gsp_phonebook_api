from fastapi import FastAPI, Depends
from fastapi_pagination import Page, add_pagination
import uvicorn
from sqlalchemy.orm import Session
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_paginate

from database import DataBase, EmployeeModel, EmployeeSchema


tags_metadata = [
    {
        'name': 'Поиск',
        "description": 'Методы поиска сотрудников',
    },
]

app = FastAPI(
    title='Phonebook_API',
    openapi_tags=tags_metadata
)
add_pagination(app)
database = DataBase()


@app.get('/get_employees', response_model=Page[EmployeeSchema], tags=['Поиск'])
def get_filtered_employees(
        employee_id: str | None = None,
        department_id: str | None = None,
        organization_id: str | None = None,
        db: Session = Depends(database.get_session),
):
    """
    <h2>Поиск сотрудников по ID сотрудника, подразделения или организации</h2>\n
    При запросе без параметров выдаются все сотрудники\n
    <code>department_id</code> должен передаваться вместе с <code>organization_id</code>\n
    При передеаче <code>employee_id</code> остальные ID в запросе не учитываются\n
    """

    if all([not employee_id, not department_id, not organization_id]):
        return sqlalchemy_paginate(db.query(EmployeeModel))

    if employee_id:
        return sqlalchemy_paginate(db.query(EmployeeModel).where(
            EmployeeModel.ID == employee_id
        ))

    if department_id and organization_id:
        return sqlalchemy_paginate(db.query(EmployeeModel).where(
            EmployeeModel.DepartmentID == department_id,
            EmployeeModel.OrganizationID == organization_id
        ))

    if organization_id:
        return sqlalchemy_paginate(db.query(EmployeeModel).where(
            EmployeeModel.OrganizationID == organization_id
        ))


@app.get('/search', response_model=Page[EmployeeSchema], tags=['Поиск'])
def search(
        value: str,
        attribute: str,
        db: Session = Depends(database.get_session),
) -> list:
    """
    <h2>Поиск сотрудников по атрибутам</h2>\n
    **Параметры:**
    * **value:** Значение атрибута
    * **attribute:** Тип атрибута\n
    Допустимые типы атрибутов:
    * **phone** - телефон
    * **email** - почта
    * **name** - поиск по ФИО
    """
    match attribute:
        case 'phone':
            return sqlalchemy_paginate(db.query(EmployeeModel).where(EmployeeModel.Phone.contains(value)))
        case 'email':
            return sqlalchemy_paginate(db.query(EmployeeModel).where(EmployeeModel.Email.contains(value)))
        case 'name':
            return sqlalchemy_paginate(db.query(EmployeeModel).where(EmployeeModel.FullNameRus.contains(value)))


@app.get('/get_organization_tree')
def get_organization_tree() -> list:
    """
    <h2>Получить структуру организаций в древовидной структуре</h2>\n
    """
    return database.organization_tree


if __name__ == '__main__':
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
    )