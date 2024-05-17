from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from flask import Flask
from flask_cors import CORS
from flask_sse import sse
from fastapi.middleware.wsgi import WSGIMiddleware

from payment.payment_handler import PaymentManager
from postgres import Postgres
from datetime import datetime, timezone, timedelta
from open_wheater import get_wind_speeds

payment_handler = PaymentManager()
postgres = Postgres()
app = FastAPI()
flask_app = Flask(__name__)
CORS(flask_app)
flask_app.config["REDIS_URL"] = "redis://redis"
flask_app.register_blueprint(sse, url_prefix="/sse/rental")

app.mount("/sse", WSGIMiddleware(flask_app))


origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/teste")
async def teste():
    with flask_app.app_context():
        sse.publish(
            {
                "teste": "teste",

            },
            type="type",
        )
    return "vc e um viadao"


@app.post("/api/create_rental/{parasun_id}/{time_rented}")
async def create_rental(parasun_id, time_rented):
    lat, long = postgres.perform_get_query("get_lat_long_from_parasun", parasun_id)[0]
    if get_wind_speeds(lat, long) > 19:
        return {"status": 400, "message": "wind speeds too high for parasun's function"}
    response, status_code = payment_handler.createPayment(time_rented=time_rented)
    if status_code not in [201, 200]:
        raise HTTPException(status_code=400, detail="error on payment_creation")
    rental_id = postgres.perform_insert_or_update_returning_query(
        "create_rental", (parasun_id)
    )[0]
    postgres.perform_insert_or_update_query(
        "create_payment",
        (response.get("id"), int(rental_id), int(time_rented), response.get("status")),
    )
    return {
        "status": 200,
        "rental_id": rental_id,
        "qr_code": response.get("point_of_interaction")
        .get("transaction_data")
        .get("qr_code"),
    }


@app.get("/api/check_payment/{rental_id}")
async def check_payment(rental_id):
    if (
        postgres.perform_get_query("get_latest_payment_status", rental_id)[0][0]
        == "approved"
    ):
        return postgres.perform_get_query(
            "get_rental_current_expiration_date", rental_id
        )[0][0]
    payment_id = postgres.perform_get_query("get_payment_id_latest", (rental_id))[0][0]
    print(payment_id)
    response, status_code = payment_handler.checkPayment(payment_id)
    if status_code not in [200, 201]:
        raise HTTPException(status_code=status_code, detail="error on payment_check")
    if response.get("status") == "approved":
        time = postgres.perform_insert_or_update_returning_query(
            "update_payment_status",
            (response.get("status"), int(rental_id), int(rental_id)),
        )
        expiration_date = postgres.perform_insert_or_update_returning_query(
            "update_rental_expiration_first",
            (int(time), int(rental_id), int(rental_id)),
        )
        return expiration_date - timedelta(hours=3)
    else:
        return response.get("status")


@app.get("/api/add_time/{rental_id}/{time_rented}")
async def create_time_addition_payment(rental_id, time_rented):
    response, status_code = payment_handler.createPayment(time_rented=time_rented)
    if status_code not in [201, 200]:
        raise HTTPException(status_code=400, detail="error on payment_creation")
    postgres.perform_insert_or_update_query(
        "create_payment",
        (response.get("id"), int(rental_id), int(time_rented), response.get("status")),
    )


@app.post("/api/update_payment", status_code=200)
async def payment_updated_webhook(request: Request):
    json_body = await request.json()
    print(json_body)
    payment_id = json_body.get("data").get("id")
    response, status_code = payment_handler.checkPayment(payment_id)
    if status_code == 404:
        return
    rental_id = postgres.perform_get_query("get_rental_from_payment", int(payment_id))[
        0
    ][0]
    parasun_id = postgres.perform_get_query("get_parasun_from_rental", int(rental_id))[
        0
    ][0]

    if response.get("status") == "pending":
        sse.publish(
            {
                "status": "pending",
                "parasun_id": parasun_id,
            },
            type=rental_id,
        )
    if response.get("status") == "approved":
        time, payment_status = postgres.perform_insert_or_update_returning_query(
            "update_payment_status",
            (response.get("status"), f"""'{response.get("date_approved")}'""", int(rental_id), int(rental_id)),
        )
        expiration_date = postgres.perform_insert_or_update_returning_query(
            "update_rental_expiration_first",
            (int(time), int(rental_id), int(rental_id)),
        )[0]
        sse.publish(
            {
                "status": "approved",
                "parasun_id": parasun_id,
                "expiration_date": expiration_date,
            },
            type=rental_id,
        )
    if response.get("status") == "cancelled":
        postgres.perform_insert_or_update_returning_query(
            "update_payment_status",
            (response.get("status"),"null", int(rental_id), int(rental_id)),
        )
        sse.publish({"status": "cancelled"}, type=rental_id)
    return "ok"


#
#
# @app.get("/hello/{name}")
# async def say_hello(name: str):
#     return {"message": f"Hello {name}"}
