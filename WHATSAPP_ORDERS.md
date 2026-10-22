# WhatsApp purchase requests

The product-page Buy now button and bag's Proceed to WhatsApp to buy button open a
prefilled chat with **+65 8395 2511**. Override `WHATSAPP_ORDER_NUMBER` in the
server environment to change it; use international digits without a leading +.

The customer must sign in. Name, verified account email, phone, city and PIN
are read on the server from that customer's account. Submitted contact fields
and prices are ignored. Missing/invalid details lead to the contact editor;
after saving, the customer returns to their item with size and quantity retained.
The editor does not change email addresses or verification status.

The generated text includes:

- Product name, selected size (when applicable), quantity, current unit price,
  subtotal, and product link.
- A direct link to each product's main photo when an image is saved. Links use
  the configured public origin or the storage provider's absolute media URL.
  Click-to-chat accepts prefilled text, so these are photo links, not image
  attachments. WhatsApp controls link previews; a preview for every product is
  not guaranteed. Sending actual media requires a separate media-sharing flow
  or a WhatsApp Business Platform integration.
- Product-page sharing metadata explicitly names the product's own photo and
  title, rather than leaving the messaging client to select a logo from the page.
  The first available uploaded product image is used. Cached previews may take
  time to refresh, and the messaging client still decides which previews appear.
- For a bag request, every active item owned by that customer and the item total.
- Full name, email, phone, city and PIN from the saved account.
- A request to confirm availability, delivery arrangements and payment details.

Size, quantity and stock are checked again before redirecting. The response is
not cached and asks browsers not to pass the referring page to WhatsApp.
Sensitive contact information is generated only on the authenticated POST;
it is not embedded into public product markup.

WhatsApp opens with a message ready to review. The customer must press Send.
The website does not send messages itself, charge payment, reserve stock, clear
the saved bag, or mark an order as confirmed. Arrangements happen in the chat.

The public checkout action now points to WhatsApp. Previous shipping draft routes
and data remain available for future delivery work; they are not part of the
current purchasing journey.

Tests: `python manage.py test orders.test_whatsapp` covers contact accuracy,
tampered price/email fields, guest sign-in, missing details, selection retention,
CSRF/POST-only handling, stock checks, bag ownership and safe return URLs.
