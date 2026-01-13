from pydantic import BaseModel, EmailStr

from utils.data_generators.fake_credentials import (
    fake_email,
    fake_password,
    fake_username,
)


class RegisterUserDTO(BaseModel):
    email: EmailStr
    username: str
    password: str
    passwordConfirmation: str

    # ---------- методы-утилиты ----------

    @classmethod
    def random(cls, password: str | None = None) -> "RegisterUserDTO":
        """создаёт случайного валидного пользователя с одинаковыми паролями"""
        pwd = password or fake_password()
        return cls(
            email=f"ui_{fake_email()}",
            username=f"ui_{fake_username()}",
            password=pwd,
            passwordConfirmation=pwd,
        )

    @classmethod
    def minimal(cls) -> "RegisterUserDTO":
        """возвращает минимально валидного пользователя"""
        pwd = "Aa1PPPPP"
        return cls(
            email="a@a.aa",
            username="u",
            password=pwd,
            passwordConfirmation=pwd,
        )


class LoginUserDTO(BaseModel):
    email: EmailStr
    password: str

    @classmethod
    def from_register(cls, user: RegisterUserDTO) -> "LoginUserDTO":
        return cls(email=user.email, password=user.password)
