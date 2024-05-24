from asyncio import sleep
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask
from flask_cors import CORS
from flask_sse import sse

from open_wheater import get_wind_speeds
from payment.payment_handler import PaymentManager
from postgres import Postgres

payment_handler = PaymentManager()
postgres = Postgres()
# app = FastAPI()
app = Flask(__name__)
CORS(app)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/sse/event')
# flask_app.run(debug=True, host='0.0.0.0', port=5000)

#app.mount("/sse/event", WSGIMiddleware(flask_app))


origins = ["*"]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# async def letras_generator():
#     for letra in ['a', 'b', 'c']:
#         yield letra
#         await sleep(1)


@app.route("/api/teste", methods=['GET'])
async def teste():
    # with flask_app.app_context():
    #     sse.publish(
    #         {
    #             "teste": "teste",
    #         },
    #         type="publish",
    #     )
    return "vc eh um viadao"


@app.route("/api/create_rental/{parasun_id}/{time_rented}", methods=['POST'])
async def create_rental(parasun_id, time_rented):
    # if not isinstance(time_rented, int):
    #     raise HTTPException(status_code=400, detail="time rentede should be INT")
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


@app.route("/api/check_payment/{rental_id}", methods=["GET"])
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


@app.route("/api/add_time/{rental_id}/{time_rented}", methods=["GET"])
async def create_time_addition_payment(rental_id, time_rented):
    response, status_code = payment_handler.createPayment(time_rented=time_rented)
    if status_code not in [201, 200]:
        raise HTTPException(status_code=400, detail="error on payment_creation")
    postgres.perform_insert_or_update_query(
        "create_payment",
        (response.get("id"), int(rental_id), int(time_rented), response.get("status")),
    )


@app.route("/api/update_payment", methods=["POST"])
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

    with app.app_context():
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
                (int(time), int(rental_id), int(time), int(rental_id)),
            )[0]
            sse.publish(
                {
                    "status": "approved",
                    "parasun_id": parasun_id,
                    "expiration_date": expiration_date,
                },
                type="approved",
            )
        if response.get("status") == "cancelled":
            postgres.perform_insert_or_update_returning_query(
                "update_payment_status",
                (response.get("status"),"null", int(rental_id), int(rental_id)),
            )
            sse.publish({"status": "cancelled"}, type="cancelled")
    return "ok"

@app.route("/api/get_parasuns_positions", methods=["GET"])
async def get_parasuns_positions():
    positions_list = postgres.perform_get_query("get_parasuns_positions")
    response = [{"latitude": position[0], "longitude":position[1]} for position in positions_list]
    return response

@app.route("/api/create_location_entry/{latitude}/{longitude}/{parasun_id}", methods=["POST"])
async def create_location_entry(latitude, longitude, parasun_id):
    postgres.perform_insert_or_update_query("create_location_entry", (parasun_id, latitude, longitude))
    return "created"
#
#
# @app.get("/hello/{name}")
# async def say_hello(name: str):
#     return {"message": f"Hello {name}"}
