"""services/payment.py – Payment integration. Works in demo mode without keys."""
import hashlib
import hmac
import time
import config
from typing import Optional, Dict


def get_payment_provider() -> str:
    if config.RAZORPAY_KEY_ID:
        return "razorpay"
    if config.STRIPE_SECRET_KEY:
        return "stripe"
    return "demo"


def create_razorpay_order(amount_inr: int) -> Optional[Dict]:
    try:
        import razorpay
        client = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))
        order = client.order.create({
            "amount": amount_inr * 100,  # paise
            "currency": "INR",
            "payment_capture": 1,
        })
        return {"order_id": order["id"], "amount": amount_inr, "currency": "INR"}
    except Exception as e:
        return {"error": str(e)}


def verify_razorpay_payment(order_id: str, payment_id: str, signature: str) -> bool:
    try:
        msg = f"{order_id}|{payment_id}"
        expected = hmac.new(
            config.RAZORPAY_KEY_SECRET.encode(),
            msg.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


def get_payment_link(amount_inr: int = None) -> str:
    """Returns Razorpay payment link or demo confirmation URL."""
    amount_inr = amount_inr or config.PRO_PRICE_INR
    provider = get_payment_provider()
    if provider == "razorpay":
        # In production, generate dynamic link via API
        return f"https://razorpay.com/payment-link/careeros-pro"
    return f"demo://upgrade?amount={amount_inr}&ts={int(time.time())}"


def is_demo_mode() -> bool:
    return get_payment_provider() == "demo"
