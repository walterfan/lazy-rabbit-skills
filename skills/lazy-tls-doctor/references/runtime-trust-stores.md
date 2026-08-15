# Runtime trust stores

Why "the browser works but my code doesn't": runtimes do not share one trust store. Installing a CA system-wide fixes some of them and is invisible to others.

| Runtime | Reads | Add a CA via |
|---|---|---|
| Browsers | OS store (Firefox uses its own) | OS install |
| curl | OS bundle | `CURL_CA_BUNDLE`, or `--cacert` |
| git | Its own TLS backend | `git config --global http.sslCAInfo <pem>` |
| Go | OS store | OS install — usually nothing else needed |
| Python `ssl` | OpenSSL paths | `SSL_CERT_FILE`, or `load_verify_locations()` |
| Python requests | **certifi**, not the OS | `REQUESTS_CA_BUNDLE`, or `verify=<pem>` |
| Node.js | Bundled list, ignores OS | `NODE_EXTRA_CA_CERTS=<pem>` |
| Java | Its own `cacerts` keystore | `keytool -importcert` |
| Docker containers | Whatever the image ships | Copy the CA in, run `update-ca-certificates` |
| AWS CLI / boto3 | certifi-ish bundle | `AWS_CA_BUNDLE` |

Survey the current machine:

```bash
python3 scripts/tls_doctor.py truststore
```

## Get the CA first

If a proxy is intercepting, extract the signer it presents:

```bash
openssl s_client -connect api.example.com:443 \
  -servername api.example.com -showcerts </dev/null 2>/dev/null \
  | awk '/BEGIN CERT/{f=1} f{print} /END CERT/{f=0}' > presented-chain.pem
```

Prefer the official copy from your IT team over one scraped off the wire — a certificate handed to you by the thing you are trying to identify is not strong provenance. Confirm whichever copy you use actually signed the chain:

```bash
python3 scripts/tls_doctor.py diagnose api.example.com --proxy-ca corp-ca.pem
```

## System trust stores

**Debian / Ubuntu**

```bash
sudo cp corp-ca.crt /usr/local/share/ca-certificates/corp-ca.crt   # must end in .crt
sudo update-ca-certificates
```

**RHEL / Fedora / CentOS**

```bash
sudo cp corp-ca.crt /etc/pki/ca-trust/source/anchors/
sudo update-ca-trust extract
```

**Alpine**

```bash
apk add --no-cache ca-certificates
cp corp-ca.crt /usr/local/share/ca-certificates/
update-ca-certificates
```

**macOS**

```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain corp-ca.crt
```

Note that Homebrew's OpenSSL keeps its own bundle at `$(brew --prefix)/etc/openssl@3/cert.pem`, separate from the keychain.

## Python

`requests` uses certifi, so a system install alone will not help it.

```bash
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
```

In code, prefer being explicit over mutating globals:

```python
import requests
requests.get(url, verify="/etc/ssl/certs/ca-certificates.crt", timeout=10)
```

```python
import ssl, socket
ctx = ssl.create_default_context(cafile="/path/to/ca-bundle.pem")
with socket.create_connection((host, 443), timeout=5) as sock:
    with ctx.wrap_socket(sock, server_hostname=host) as tls:
        print(tls.version(), tls.getpeercert())
```

Check what Python currently uses:

```bash
python3 -c "import ssl; print(ssl.get_default_verify_paths())"
python3 -c "import certifi; print(certifi.where())"
```

To append a CA to certifi's bundle (rebuild on every image build, or an upgrade silently drops it):

```bash
cat corp-ca.crt >> "$(python3 -c 'import certifi; print(certifi.where())')"
```

## Node.js

Node ignores the OS store entirely.

```bash
export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/corp-ca.pem
```

Set it before the process starts — Node reads it at startup. `NODE_TLS_REJECT_UNAUTHORIZED=0` disables verification globally and should not survive past local debugging.

## Java

```bash
keytool -importcert -trustcacerts \
  -alias corp-ca -file corp-ca.crt \
  -keystore "$JAVA_HOME/lib/security/cacerts" \
  -storepass changeit -noprompt
```

Or point at a separate store:

```bash
java -Djavax.net.ssl.trustStore=/path/to/truststore.jks \
     -Djavax.net.ssl.trustStorePassword=... -jar app.jar
```

Debug with `-Djavax.net.debug=ssl:handshake`. `PKIX path building failed` is Java's phrasing for "cannot build a chain to a trusted root".

## Go

Go reads the OS store, so a system install is usually sufficient. To be explicit:

```go
pool, _ := x509.SystemCertPool()
pem, _ := os.ReadFile("/etc/ssl/certs/corp-ca.pem")
pool.AppendCertsFromPEM(pem)
client := &http.Client{Transport: &http.Transport{
    TLSClientConfig: &tls.Config{RootCAs: pool},
}}
```

`x509: certificate signed by unknown authority` is Go's version of the same failure. `InsecureSkipVerify: true` is not a fix.

## Docker

The most common cause of "works locally, fails in the container": the image never had the CA.

```dockerfile
# Debian/Ubuntu base
COPY corp-ca.crt /usr/local/share/ca-certificates/corp-ca.crt
RUN update-ca-certificates

# Alpine base
COPY corp-ca.crt /usr/local/share/ca-certificates/corp-ca.crt
RUN apk add --no-cache ca-certificates && update-ca-certificates
```

Add the language-specific variable too when the app is Python or Node:

```dockerfile
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
```

Verify inside the built image, not on the host:

```bash
docker run --rm my-image python3 -c "import ssl; print(ssl.get_default_verify_paths())"
```

## CI

CI runners are fresh machines with default trust stores. Install the CA as an early pipeline step, or bake it into the runner image. Store it as a regular file artifact — it is a public certificate, not a secret, but its integrity matters, so fetch it from a controlled location rather than copying it between laptops.

## Why not just disable verification

`verify=False`, `curl -k`, `NODE_TLS_REJECT_UNAUTHORIZED=0`, and `InsecureSkipVerify: true` all keep the traffic encrypted while removing the check that you are talking to the right server. That is the half that stops impersonation, so the connection becomes encrypted-to-someone-unverified.

For a throwaway local reproduction it is fine. In committed code it is a standing vulnerability that outlives whoever added it. If you need something quick, pass an explicit CA file instead — you still know who you are trusting.
