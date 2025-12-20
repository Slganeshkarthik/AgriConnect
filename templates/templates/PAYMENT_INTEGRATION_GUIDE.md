# Real Payment Integration Guide for AgriConnect

This guide explains how to set up real payment processing for your e-commerce website using Razorpay.

## 🚀 Quick Start

### 1. Create Razorpay Account

1. Go to [https://razorpay.com](https://razorpay.com)
2. Sign up for a free account
3. Complete basic verification

### 2. Get API Keys

1. Login to Razorpay Dashboard
2. Go to **Settings** → **API Keys**
3. Click **Generate Test Key** (for development)
4. You'll get:
   - **Key ID**: `rzp_test_xxxxxxxxxxxxx`
   - **Key Secret**: `xxxxxxxxxxxxx`

### 3. Update Your Code

**In `payment.html`** (line 9):
```javascript
key: 'rzp_test_YOUR_KEY_HERE', // Replace with your actual Key ID
```

**In `payment_backend_example.py`**:
```python
RAZORPAY_KEY_ID = 'rzp_test_YOUR_KEY_ID'  # Your Test Key ID
RAZORPAY_KEY_SECRET = 'YOUR_SECRET_KEY'   # Your Secret Key
```

### 4. Install Dependencies

```bash
pip install razorpay flask
```

### 5. Run Your Backend

```bash
python payment_backend_example.py
```

### 6. Test Payment

Use these test credentials:

**Test Cards:**
- Card Number: `4111 1111 1111 1111`
- CVV: `123`
- Expiry: `12/25` (any future date)
- Name: `Test User`

**Test UPI:**
- UPI ID: `success@razorpay` (for successful payment)
- UPI ID: `failure@razorpay` (to test failure)

**Test Net Banking:**
- Select any bank
- Login with any username/password in test mode

---

## 📋 Features Implemented

### ✅ Multiple Payment Methods
- 💵 Cash on Delivery (COD)
- 📱 UPI Payment (Google Pay, PhonePe, Paytm)
- 💳 Credit/Debit Cards (Visa, MasterCard, RuPay)
- 🏦 Net Banking (All major banks)

### ✅ Real Payment Processing
- Razorpay SDK integration
- Payment signature verification
- Webhook handling for payment events
- Order creation and tracking

### ✅ Security Features
- HMAC signature verification
- Secure payment gateway
- PCI DSS compliant
- Encrypted transactions

### ✅ User Experience
- Card number auto-formatting
- Expiry date auto-formatting
- Input validation
- Payment status tracking
- Redirect to invoice page

---

## 🔧 Backend Implementation

### Required Endpoints:

1. **GET /get-cart-total**
   - Returns cart subtotal and delivery charges
   - Used to display order summary

2. **POST /create-order**
   - Creates order in database
   - Creates Razorpay order for online payments
   - Returns order details

3. **POST /verify-payment**
   - Verifies Razorpay payment signature
   - Updates order status
   - Confirms payment success

4. **POST /razorpay-webhook**
   - Handles payment events from Razorpay
   - Updates order status automatically
   - Sends confirmations

### Database Schema Example:

```sql
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id VARCHAR(50) UNIQUE,
    user_id INT,
    amount DECIMAL(10, 2),
    payment_method VARCHAR(20),
    payment_status VARCHAR(20),
    razorpay_order_id VARCHAR(100),
    razorpay_payment_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## 🌐 Going Live (Production)

### Step 1: Complete KYC
- Upload business documents
- Bank account details
- GST information (if applicable)

### Step 2: Generate Live Keys
1. Go to Razorpay Dashboard
2. Settings → API Keys
3. Switch to **Live Mode**
4. Generate Live Keys

### Step 3: Update Code
Replace test keys with live keys:
```javascript
key: 'rzp_live_xxxxxxxxxxxxx', // Live Key
```

### Step 4: Setup Webhook
1. Go to Settings → Webhooks
2. Add webhook URL: `https://yourdomain.com/razorpay-webhook`
3. Select events: `payment.captured`, `payment.failed`
4. Copy webhook secret and add to backend

### Step 5: Enable Payment Methods
1. Go to Settings → Configuration
2. Enable required payment methods
3. Set payment capture mode (auto/manual)

### Step 6: Configure Settlement
1. Set settlement schedule
2. Add bank account for settlements
3. Configure instant settlements (optional)

---

## 💰 Pricing

### Razorpay Charges:
- **Domestic Cards**: 2% per transaction
- **UPI**: 0% (currently free)
- **Net Banking**: 2% per transaction
- **Wallets**: 2% per transaction
- **International Cards**: 3% + GST

### Settlement Time:
- T+2 days (standard)
- T+0 (instant settlements available at extra cost)

---

## 🔐 Security Best Practices

1. **Never expose secret keys in frontend**
   - Keep `RAZORPAY_KEY_SECRET` only on backend
   - Only use `RAZORPAY_KEY_ID` in frontend

2. **Always verify payment signature**
   - Verify on backend before confirming order
   - Don't trust frontend payment success alone

3. **Use HTTPS**
   - SSL certificate required for production
   - Razorpay won't work on HTTP in production

4. **Implement webhook**
   - Handle payment events asynchronously
   - Update order status from webhook

5. **Store payment details**
   - Save payment ID, order ID, signature
   - Keep audit trail for disputes

---

## 🛠️ Alternative Payment Gateways

### 1. Stripe (International)
- Website: https://stripe.com
- Best for: International payments
- Charges: 2.9% + $0.30 per transaction
- Countries: 46+ countries

### 2. PayPal
- Website: https://www.paypal.com/in/business
- Best for: International buyers
- Charges: 4.4% + fixed fee
- Widely recognized globally

### 3. Paytm Payment Gateway
- Website: https://business.paytm.com/payment-gateway
- Best for: Wallet payments
- Charges: 2% per transaction
- Popular in India

### 4. Cashfree
- Website: https://www.cashfree.com
- Best for: Payouts + Collections
- Charges: 1.75% onwards
- Good for businesses

### 5. PhonePe Payment Gateway
- Website: https://www.phonepe.com/business-solutions
- Best for: UPI payments
- Charges: Competitive rates
- UPI focused

---

## 📞 Support

### Razorpay Support:
- Email: support@razorpay.com
- Phone: 1800-102-5071
- Documentation: https://razorpay.com/docs

### Integration Help:
- API Reference: https://razorpay.com/docs/api
- SDKs: https://razorpay.com/docs/payments/server-integration
- Postman Collection: Available on Razorpay docs

---

## ⚠️ Important Notes

1. **Test Mode vs Live Mode**
   - Always test thoroughly in test mode
   - Use test credentials (card numbers, UPI IDs)
   - No real money is charged in test mode

2. **Webhook Verification**
   - Always verify webhook signature
   - Prevent unauthorized access
   - Handle duplicate events

3. **Error Handling**
   - Handle payment failures gracefully
   - Show clear error messages
   - Provide retry option

4. **Compliance**
   - Follow RBI guidelines
   - Comply with data protection laws
   - Store card details as per PCI DSS

5. **Refunds**
   - Implement refund mechanism
   - Razorpay supports instant refunds
   - Maintain refund policy

---

## 📝 Testing Checklist

- [ ] Payment with test card succeeds
- [ ] Payment with test UPI succeeds
- [ ] Payment with test net banking succeeds
- [ ] COD order places successfully
- [ ] Payment failure handled correctly
- [ ] Order details saved in database
- [ ] Invoice generated after payment
- [ ] Webhook receives events
- [ ] Payment signature verified
- [ ] User redirected correctly
- [ ] Amount calculation is correct
- [ ] Mobile responsive design works

---

## 🎯 Next Steps

1. **Implement Order Management**
   - Create orders table
   - Track order status
   - Send order confirmations

2. **Add Invoice Generation**
   - PDF invoice creation
   - Email invoice to customer
   - Invoice number generation

3. **Implement Notifications**
   - Email notifications
   - SMS notifications
   - WhatsApp notifications (via Razorpay)

4. **Add Refund Feature**
   - Customer refund requests
   - Admin refund processing
   - Partial refunds support

5. **Analytics Dashboard**
   - Payment success rate
   - Revenue tracking
   - Payment method distribution

---

**Last Updated**: December 2025
**Version**: 1.0
**Status**: Ready for Production ✅
