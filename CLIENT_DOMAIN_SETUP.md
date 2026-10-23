# GoDaddy steps for Shali Collections

Hi! Please make these two updates in GoDaddy to connect the website.

1. Open **My Products > shalicollections.com > Manage DNS**.

2. Find the existing **CNAME** record named **www**. Click Edit, change **Value / Points to** to `xyebi7xd.up.railway.app`, then **Save**.

3. Click **Add New Record** and enter:

   - **Type:** TXT
   - **Name:** `_railway-verify.www`
   - **Value:** copy the complete line below:

```text
railway-verify=ff1b8e7aaca0d129db38e493044938f37d96cfa6b72cb068dc6d76c0a4e79d36
```

Leave **TTL** as it is and click **Save**.

Please leave all other records unchanged. Send us a screenshot when finished, or if you get stuck, and we will guide you. You do not need to share your password.

That is all for now. We will verify the connection and guide the final forwarding step afterward.
