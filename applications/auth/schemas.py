from pydantic import (BaseModel, Field, EmailStr, field_validator)


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

    # @field_validator('password1')
    # def validate_password(cls, v):
    #     if len(v) < 8:
    #         raise ValueError('Пароль должен быть не менее 8 символов')

    #     if not re.search(r'\d', v):
    #         raise ValueError('Пароль должен содержать хотя бы одну цифру')

    #     if not re.search(r'[A-Z]', v):
    #         raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')

    #     if not re.search(r'[a-z]', v):
    #         raise ValueError('Пароль должен содержать хотя бы одну строчную букву')

    #     if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
    #         raise ValueError('Пароль должен содержать хотя бы один специальный символ')

    #     if ' ' in v:
    #         raise ValueError('Пароль не должен содержать пробелов')

    #     return v


class UserOut(BaseModel):
    id: int
    name: str
    lastname: str
    email: EmailStr
    role: UserRoleEnum

    class Config:
        orm_mode = True
