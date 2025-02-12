import random
import os
import base64

from sqlalchemy import Text, Column, create_engine, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from faker import Faker
from faker.providers import DynamicProvider
from pydantic import BaseModel


Base = declarative_base()


class EmployeeModel(Base):

    __tablename__ = "Employees"
    Index = Column(INTEGER, primary_key=True)
    ID = Column(Text)
    FullNameRus = Column(Text)
    DepartmentID = Column(Text)
    OrganizationID = Column(Text)
    Boleet = Column(INTEGER)
    Email = Column(Text)
    Photo = Column(Text)
    Phone = Column(Text)
    Mobile = Column(Text)
    Address = Column(Text)
    Workplace = Column(Text)



class EmployeeSchema(BaseModel):
    Index: int
    ID: str
    FullNameRus: str
    DepartmentID: str
    OrganizationID: str
    Boleet: int
    Email: str
    Photo: str
    Phone: str
    Mobile: str
    Address: str
    Workplace: str

    class Config:
        from_attributes = True

class DepartmentModel(Base):

    __tablename__ = "Departments"
    Index = Column(INTEGER, primary_key=True)
    ID = Column(Text)
    Name = Column(Text)
    OrganizationID = Column(Text)
    ParentID = Column(Text)

    def __repr__(self):
        return f'DepartmentModel(Index={self.Index}, ID={self.ID}, Name={self.Name}, OrganizationID={self.OrganizationID}, ParentID={self.ParentID})'

class OrganizationModel(Base):

    __tablename__ = "Organizations"
    Index = Column(INTEGER, primary_key=True)
    ID = Column(Text)
    Name = Column(Text)

    def __repr__(self):
        return f'OrganizationModel(Index={self.Index}, ID={self.ID}, Name={self.Name})'


class DataBase:

    def __init__(self):
        engine = create_engine('sqlite:///database.db')
        Base.metadata.create_all(bind=engine)
        self.__Session = sessionmaker(bind=engine, autoflush=True)
        if not self.__Session().query(OrganizationModel).all():
            self.__fill_database()


    def __fill_database(self):
        with open(os.getcwd() + '/photo.jpg', 'rb') as file:
            photo = base64.b64encode(file.read())
        fake_data = Faker('ru_RU')
        session = self.__Session()
        organization_rows = [OrganizationModel(ID=fake_data.unique.uuid4(), Name=fake_data.unique.company()) for _ in range(10)]
        session.add_all(organization_rows)
        session.commit()

        department_rows = [DepartmentModel(ID=fake_data.unique.uuid4(), Name=fake_data.unique.bs()) for _ in range(1000)]
        for organization in organization_rows:
            for _ in range(5):
                while True:
                    random_index = random.randint(0, 999)
                    if not department_rows[random_index].OrganizationID:
                        department_rows[random_index].OrganizationID = organization.ID
                        department_rows[random_index].ParentID = '0000000-0000-0000-0000-000000000000'
                        break
        for department in filter(lambda row: row.ParentID, department_rows):
            DataBase.add_department_parent(department, list(filter(lambda row: not row.ParentID, department_rows)))

        department_rows_test = list(filter(lambda x: x.ParentID, department_rows))
        print(len(department_rows_test))
        for organization in organization_rows:
            print(organization.Name, len(list(filter(lambda x: x.OrganizationID == organization.ID, department_rows_test))))

        department_rows = list(filter(lambda row: row.ParentID, department_rows))
        session.add_all(department_rows)
        session.commit()

        organizations_provider = DynamicProvider(
            provider_name='organizations_provider',
            elements=list(map(lambda row: row.ID, organization_rows))
        )
        departments_provider = DynamicProvider(
            provider_name='departments_provider',
            elements=list(map(lambda row: row.ID, department_rows))
        )
        fake_data.add_provider(organizations_provider)
        fake_data.add_provider(departments_provider)
        employee_rows = [
            EmployeeModel(
                ID=fake_data.unique.uuid4(),
                FullNameRus=f'{fake_data.last_name()} {fake_data.first_name()} {fake_data.last_name()}',
                DepartmentID=fake_data.departments_provider(),
                OrganizationID=fake_data.organizations_provider(),
                Boleet=random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
                Email=fake_data.unique.email(),
                Photo=random.choice(['', photo]),
                Phone=fake_data.unique.passport_number()[-6:],
                Mobile=fake_data.unique.phone_number(),
                Address=fake_data.address(),
                Workplace=random.randint(99, 9999),
            )
             for _ in range(10_000)
        ]

        session.add_all(employee_rows)
        session.commit()

    @staticmethod
    def add_department_parent(parent_department: DepartmentModel, departments: list, level=0):
        level += 1
        if level > 10:
            return
        random_range = random.randint(0, 5)
        for i in range(random_range):
            if random_range < len(departments) and not departments[i].ParentID:
                departments[i].OrganizationID = parent_department.OrganizationID
                departments[i].ParentID = parent_department.ID
                DataBase.add_department_parent(departments[i], list(filter(lambda row: not row.ParentID, departments)), level)

    def get_session(self):
        with self.__Session() as session:
            yield session



if __name__ == '__main__':
    DataBase()