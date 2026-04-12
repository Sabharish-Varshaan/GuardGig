import json
from datetime import datetime, timezone

import razorpay
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse

from ..config import get_settings
from ..dependencies import require_current_user
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
    )


@router.get("/checkout", response_class=HTMLResponse)
def checkout_page(order_id: str, amount: int, currency: str, token: str):
        settings = get_settings()

        if not settings.razorpay_key_id:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Razorpay is not configured")

        if amount <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment amount")

        if not order_id.strip() or not token.strip():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing checkout parameters")

        title = "GuardGig Premium Payment"
        description = "Complete weekly premium to activate policy"
        success_message = "Payment successful. You can return to GuardGig now."
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
            const bearer = {_to_js_string(token)};
            const verifyEndpoint = '/api/payment/verify';
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
                handler: async function (response) {{
                    try {{
                        setStatus('Verifying payment...');
                        const verifyResponse = await fetch(verifyEndpoint, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${{bearer}}`
                            }},
                            body: JSON.stringify({{
                                order_id: orderId,
                                payment_id: response.razorpay_payment_id || orderId
                            }})
                        }});

                        const payload = await verifyResponse.json().catch(() => ({{}}));

                        if (!verifyResponse.ok) {{
                            throw new Error(payload.detail || payload.message || 'Verification failed');
                        }}

                        setStatus({_to_js_string(success_message)});
                    }} catch (error) {{
                        setStatus(`Verification failed: ${{error.message || 'Unknown error'}}`);
                    }}
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

    payment_id = request.payment_id or request.order_id
    activated_at = datetime.now(timezone.utc).isoformat()

    try:
        response = (
            admin.table(settings.supabase_policies_table)
            .update(
                {
                    "payment_status": "success",
                    "payment_id": payment_id,
                    "activated_at": activated_at,
                    "updated_at": activated_at,
                }
            )
            .eq("id", policy["id"])
            .execute()
        )
    except Exception as exc:
        message = str(exc)
        if "activated_at" not in message.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to verify premium payment: {message}") from exc

        try:
            response = (
                admin.table(settings.supabase_policies_table)
                .update(
                    {
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

    return PaymentVerifyResponse(
        payment_status="success",
        payment_id=payment_id,
        activated_at=activated_at,
        order_id=request.order_id,
    )