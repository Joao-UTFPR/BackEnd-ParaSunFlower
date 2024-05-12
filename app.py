from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from payment.payment_handler import PaymentManager

# payment_handler = PaymentManager()
app = FastAPI()

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
    return "ola mundo"

# @app.get("/payment/create_payment")
# async def create_payment():
#     return PaymentManager.createPayment()
#
#
# @app.get("/hello/{name}")
# async def say_hello(name: str):
#     return {"message": f"Hello {name}"}
