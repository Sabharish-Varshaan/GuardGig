import json
from datetime import datetime, timedelta, timezone

import razorpay
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse

from ..config import get_settings
from ..dependencies import require_current_user
from ..metrics_utils import update_metrics_on_premium
from ..schemas import PaymentOrderResponse, PaymentVerifyRequest, PaymentVerifyResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/payment", tags=["payment"])


def _build_client() -> razorpay.Client:
    settings = get_settings()

    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Razorpay is not configured")

    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


def _get_policy(admin, settings, user_id: str) -> dict:
    response = (
        admin.table(settings.supabase_policies_table)
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No policy found for this user")

    return rows[0]


def _to_js_string(value: str) -> str:
    return json.dumps(value or "")


@router.post("/create-order", response_model=PaymentOrderResponse)
def create_order(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()
    policy = _get_policy(admin, settings, current_user["id"])

    premium = float(policy.get("premium") or 0)
    if premium <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid premium amount")

    client = _build_client()
    amount_paise = int(round(premium * 100))

    order = client.order.create(
        {
            "amount": amount_paise,
            "currency": settings.razorpay_currency,
            "payment_capture": 1,
            "notes": {
                "user_id": current_user["id"],
                "policy_id": policy["id"],
                "source": "guardgig_premium_payment",
            },
        }
    )

    order_id = str(order.get("id") or "")
    if not order_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create Razorpay order")

    return PaymentOrderResponse(
        order_id=order_id,
        amount=amount_paise,
        currency=settings.razorpay_currency,
        premium=premium,
        key_id=settings.razorpay_key_id,
    )


@router.get("/checkout", response_class=HTMLResponse)
def checkout_page(order_id: str, amount: int, currency: str, token: str, redirect_uri: str = "guardgig://payment-success"):
        settings = get_settings()

        if not settings.razorpay_key_id:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Razorpay is not configured")

        if amount <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment amount")

        if not order_id.strip() or not token.strip():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing checkout parameters")

        title = "GuardGig Premium Payment"
        description = "Complete weekly premium to activate policy"
        success_message = "Payment successful. Redirecting to GuardGig..."
        cancel_message = "Payment cancelled. You can close this tab and retry from the app."

        html = f"""
<!doctype html>
<html lang=\"en\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>{title}</title>
        <script src=\"https://checkout.razorpay.com/v1/checkout.js\"></script>
        <style>
            body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(120deg, #081427, #0e2b4a);
                color: #e8f0ff;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .card {{
                width: min(420px, 92vw);
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 16px;
                padding: 24px;
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
            }}
            h1 {{
                margin: 0 0 10px;
                font-size: 22px;
            }}
            p {{
                margin: 8px 0;
                color: #c6d9f7;
            }}
            button {{
                width: 100%;
                margin-top: 18px;
                padding: 12px 14px;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                color: #081427;
                background: #64d6ff;
            }}
            #status {{
                margin-top: 14px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <main class=\"card\">
            <h1>{title}</h1>
            <p>{description}</p>
            <p>Order: <strong>{order_id}</strong></p>
            <button id=\"pay-now\">Open Razorpay Checkout</button>
            <p id=\"status\">Waiting to start payment...</p>
        </main>
        <script>
            const orderId = {_to_js_string(order_id)};
            const amount = {amount};
            const currency = {_to_js_string(currency)};
            const redirectUri = {_to_js_string(redirect_uri)};
            const statusNode = document.getElementById('status');

            const setStatus = (message) => {{
                statusNode.textContent = message;
            }};

            const options = {{
                key: {_to_js_string(settings.razorpay_key_id)},
                amount,
                currency,
                name: 'GuardGig',
                description: {_to_js_string(description)},
                order_id: orderId,
                handler: function (response) {{
                    setStatus({_to_js_string(success_message)});
                    const paymentId = encodeURIComponent(response.razorpay_payment_id || '');
                    const returnedOrderId = encodeURIComponent(response.razorpay_order_id || orderId);
                    const signature = encodeURIComponent(response.razorpay_signature || '');
                    const join = redirectUri.includes('?') ? '&' : '?';
                    window.location.href = `${{redirectUri}}${{join}}order_id=${{returnedOrderId}}&payment_id=${{paymentId}}&signature=${{signature}}`;
                }},
                modal: {{
                    ondismiss: function () {{
                        setStatus({_to_js_string(cancel_message)});
                    }}
                }}
            }};

            document.getElementById('pay-now').addEventListener('click', function () {{
                setStatus('Opening Razorpay checkout...');
                const rzp = new Razorpay(options);
                rzp.open();
            }});
        </script>
    </body>
</html>
        """

        return HTMLResponse(content=html)


@router.post("/verify", response_model=PaymentVerifyResponse)
def verify_payment(request: PaymentVerifyRequest, current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()
    policy = _get_policy(admin, settings, current_user["id"])

    # Extract and validate request parameters
    order_id = (request.order_id or "").strip()
    payment_id = (request.payment_id or "").strip()
    signature = (request.signature or "").strip()
    
    if not order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Razorpay order id")
    if not payment_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Razorpay payment id")
    if not signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Razorpay signature")

    # Step 1: Verify Razorpay signature BEFORE activating policy (fail-safe security)
    client = _build_client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment signature. Payment verification failed.") from exc

    # Step 2: Only after successful signature verification → activate policy
    activated_at_dt = datetime.now(timezone.utc)
    expires_at_dt = activated_at_dt + timedelta(days=7)
    activated_at = activated_at_dt.isoformat()
    expires_at = expires_at_dt.isoformat()

    try:
        response = (
            admin.table(settings.supabase_policies_table)
            .update(
                {
                    "status": "active",
                    "payment_status": "success",
                    "payment_id": payment_id,
                    "activated_at": activated_at,
                    "expires_at": expires_at,
                    "updated_at": activated_at,
                }
            )
            .eq("id", policy["id"])
            .execute()
        )
    except Exception as exc:
        message = str(exc)
        if "activated_at" not in message.lower() and "expires_at" not in message.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to verify premium payment: {message}") from exc

        try:
            response = (
                admin.table(settings.supabase_policies_table)
                .update(
                    {
                        "status": "active",
                        "payment_status": "success",
                        "payment_id": payment_id,
                        "updated_at": activated_at,
                    }
                )
                .eq("id", policy["id"])
                .execute()
            )
        except Exception as fallback_exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to verify premium payment: {str(fallback_exc)}") from fallback_exc

    rows = response.data or []
    if not rows:
        rows = (
            admin.table(settings.supabase_policies_table)
            .select("*")
            .eq("id", policy["id"])
            .limit(1)
            .execute()
            .data
            or []
        )

    if not rows:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update policy payment state")

    # Track premium in system metrics (non-blocking)
    premium_amount = float(policy.get("premium", 0))
    if premium_amount > 0:
        try:
            update_metrics_on_premium(admin, premium_amount)
        except Exception as exc:
            # Don't fail payment if metrics update fails - log and continue
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to update metrics on premium payment: {exc}")

    return PaymentVerifyResponse(
        payment_status="success",
        payment_id=payment_id,
        activated_at=activated_at,
        expires_at=expires_at,
        order_id=order_id,
    )