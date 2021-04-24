from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from starlette_prometheus import metrics, PrometheusMiddleware


app = FastAPI()

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics)

engine = create_engine("mysql+pymysql://root:admin@db:3306/mydb")


@app.get("/")
async def root():
    return {"message": "Hello World"}


class User(BaseModel):
    name: str
    age: int
    email: str


@app.post("/users/")
async def create_user(user: User):
    with engine.connect() as connection:
        try:
            result = connection.execute(
                "INSERT INTO users (name, age, email) VALUES (%s, %s, %s)",
                user.name,
                user.age,
                user.email,
            )

            return {"id": result.lastrowid}
        except IntegrityError:
            raise HTTPException(
                status_code=400, detail=f"Email {user.email} already taken"
            )


@app.get("/users/{user_id}")
async def get_user_by_id(user_id):
    with engine.connect() as connection:
        users = list(connection.execute("SELECT * FROM users WHERE id=%s", user_id))

        if users == []:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        return users[0]
