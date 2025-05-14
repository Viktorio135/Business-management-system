from pydantic import (BaseModel, ConfigDict, Field, EmailStr, field_validator)


from database.models import UserRoleEnum


class Token(BaseModel):
    access_token: str
    token_type: str


class RegUserModel(BaseModel):
    name: str = Field(max_length=20)
    lastname: str = Field(max_length=30)
    email: EmailStr
    password1: str = Field(max_length=128, min_length=8)
    password2: str = Field(max_length=128, min_length=8)
    role: str = Field(max_length=10)

    @field_validator("role")
    def check_role(cls, value):
        if value not in ('user', 'admin', 'manager'):
            raise ValueError('Нет такой роли')
        return value

    @field_validator('password2')
    def passwords_match(cls, v, values):
        if 'password1' in values.data and v != values.data['password1']:
            raise ValueError('Пароли не совпадают')
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    lastname: str
    email: EmailStr
    role: UserRoleEnum
