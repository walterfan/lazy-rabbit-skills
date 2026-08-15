# Command playbook

Raw commands for when the script is unavailable, plus how to read the output.

## The one command that usually settles it

```bash
openssl s_client -connect api.example.com:443 \
  -servername api.example.com </dev/null 2>&1 \
  | grep -E "subject=|issuer=|Verify return code"
```

Both flags matter:

- `-servername` sends SNI. Without it, a host serving many sites may hand back an unrelated certificate and send you chasing a phantom mismatch.
- `</dev/null` supplies EOF so the command exits instead of waiting for interactive input.

Read the **issuer**. The subject is almost always the name you asked for; the issuer tells you who signed it.

## Add hostname validation explicitly

`s_client` does not check that the certificate matches the hostname unless you ask:

```bash
openssl s_client -connect api.example.com:443 \
  -servername api.example.com \
  -verify_hostname api.example.com </dev/null 2>&1 \
  | grep -E "verify error|Verify return code"
```

Without `-verify_hostname`, a certificate issued for a completely different host still reports `Verify return code: 0 (ok)`. Browsers and curl always validate the name, so skipping this makes openssl disagree with them and hides real mismatches.

## See the whole chain

```bash
openssl s_client -connect api.example.com:443 \
  -servername api.example.com -showcerts </dev/null 2>&1 \
  | grep -E "^ [0-9] s:|^ *i:"
```

A healthy public chain has several entries:

```
 0 s:CN=www.example.com
   i:C=US, O=Let's Encrypt, CN=YE2
 1 s:C=US, O=Let's Encrypt, CN=YE2
   i:C=US, O=ISRG, CN=Root YE
```

A single entry means the server sent leaf-only. What that implies depends on the issuer:

- Issuer is a real public CA → the server forgot the intermediate. **Server's problem.**
- Issuer is a company or security-vendor name → interception. **Trust store's problem.**

## Prove interception

If you suspect a proxy and can get its CA certificate:

```bash
openssl s_client -connect api.example.com:443 \
  -servername api.example.com -CAfile /path/to/proxy-ca.pem </dev/null 2>&1 \
  | grep "Verify return code"
```

Flipping from a failure code to `0 (ok)` proves that CA signed the chain. The certificate is not broken — your runtime simply does not trust the signer.

## Through an explicit proxy

```bash
openssl s_client -proxy 10.0.0.1:8080 \
  -connect api.example.com:443 -servername api.example.com </dev/null
```

## Verify a chain offline

Useful when you have the files but no live server:

```bash
openssl verify -CAfile root-ca.pem -untrusted intermediate.pem server.pem
```

`-untrusted` supplies intermediates that are not trust anchors. If this succeeds while the live connection fails, the server is not sending the intermediate.

## Inspect a certificate file

```bash
openssl x509 -in cert.pem -noout -subject -issuer -dates -ext subjectAltName
```

Checklist:

- `notAfter` in the past → expired
- Requested name absent from `subjectAltName` → mismatch (CN alone is not enough for modern clients)
- Leaf must be `CA:FALSE`; intermediates `CA:TRUE`

## Verify error codes

| Code | Text | Meaning | Usual owner |
|---|---|---|---|
| 10 | certificate has expired | Past `notAfter` | Server |
| 18 | self signed certificate | Leaf signed itself, no chain | Server or deliberate |
| 19 | self signed certificate in certificate chain | Chain ends in an untrusted self-signed root | Trust store |
| 20 | unable to get local issuer certificate | Cannot find the issuer of some certificate | Ambiguous — check issuer name |
| 21 | unable to verify the first certificate | Chain stops too early | Server (usually leaf-only) |
| 62 | hostname mismatch | Valid certificate, wrong name | DNS or server |

Codes come from `X509_V_ERR_*` in OpenSSL's `x509_vfy.h`. 20 and 21 commonly appear together.

Distinguishing 20/21 is the crux: **chain length plus issuer identity** decides whether it is a server problem or a trust problem.

## Cross-check with curl

curl validates hostnames by default, so it is a good second opinion:

```bash
curl -vI https://api.example.com/ 2>&1 | grep -iE "issuer|subject|SSL certificate"
```

`curl: (60)` is the certificate-verification failure.

## DNS cross-checks

Only needed when the certificate names a host you did not expect.

```bash
dig +short api.example.com                  # local resolver
dig @8.8.8.8 +short api.example.com         # public resolver
dig +short NS example.com                   # authoritative servers
```

Disagreement between resolvers means internal override or hijack.

Two traps:

**`dig` returns exit code 0 even for NXDOMAIN.** It reports "the query completed", not "a record exists". Test the output:

```bash
[ -z "$(dig +short "$name" A)" ] && echo "no answer"
dig +noall +comments "$name" | grep -o 'status: [A-Z]*'
```

**`dig` and `nslookup` both ignore `/etc/hosts`.** Applications do not. To see what a program will actually get:

```bash
getent hosts api.example.com                       # Linux
dscacheutil -q host -a name api.example.com        # macOS
grep api.example.com /etc/hosts
```

A `dig` NXDOMAIN combined with a working `ping` means a hosts-file entry is in play.

## CNAME chains

```bash
dig +noall +answer www.example.com
```

If the name resolves through a CNAME and the final server's certificate only covers the CNAME target, you get a hostname mismatch. Common with CDNs and managed hosting.

## Quick decision table

| Observation | Conclusion |
|---|---|
| Chain length 1, issuer is a public CA | Server omitted the intermediate |
| Chain length 1, issuer is a company/vendor name | Interception proxy |
| Proxy CA verifies the chain | Interception confirmed |
| Code 62, certificate valid for another name | Wrong host reached — check DNS |
| `notAfter` in the past | Expired |
| No certificate received at all | Network or non-TLS port, not a certificate problem |
| Browser fine, code fails | Different trust stores |
