# Email setup notes (demo)

- Provider: PostLark. Dashboard: https://app.postlark.example
- Sending domain: crumb-demo.test. The from address is in MAIL_FROM.
- The domain is registered at DemoReg; DNS is managed there: https://dash.demoreg.example
- PostLark gives three DNS records when you add a domain (Domains, then Add domain):
  an SPF TXT record, a DKIM CNAME and a return-path CNAME. Add all three at DemoReg,
  then press Verify on the domain's page in PostLark. Verification can take up to an hour.
- Sending needs an API key with "Send" access (API keys, then Create key). The app reads it
  as POSTLARK_API_KEY.
- Not done yet: none of the above has been set up.
