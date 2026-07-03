---
schema_version: 1
tags:
  - "forensics"
  - "network"
  - "fingerprinting"
topics:
  - "JA4"
  - "traffic fingerprinting"
  - "TLS fingerprinting"
status: seed
created: 2026-06-05
updated: 2026-06-05
sources:
  - "https://github.com/FoxIO-LLC/ja4/tree/main/technical_details"
  - "https://github.com/FoxIO-LLC/ja4/blob/main/technical_details/README.md"
  - "https://github.com/FoxIO-LLC/ja4/blob/main/technical_details/JA4.md"
  - "https://github.com/FoxIO-LLC/ja4/blob/main/technical_details/JA4H.md"
source_count: 4
aliases:
  - "ja4"
  - "JA4"
  - "JA4+"
  - "traffic fingerprints"
skill_id: forensics/ja4
summary: "Interpret JA4-family network fingerprints and avoid common implementation mistakes when working from packet captures or logs."
model_role: reference
depends_on: []
related:
  - forensics/pcap
  - meta/contributing
---

# JA4 Network Fingerprints

<!-- learned: 2026-06 | project: cortex-ja4 | model: thinking-model -->

Use this skill when interpreting, implementing, validating, or explaining
JA4-family traffic fingerprints from packet captures, flow logs, sensor
output, detection rules, or network-forensics notes.

## Core Rule

Treat JA4 as a structured family of protocol fingerprints, not as one
opaque hash. Preserve each visible field, separator, count, ordering
rule, and zero-value convention before comparing or hashing values.
For packet-capture work, read `skills/forensics/pcap/SKILL.md` before altering
captures or extracting subsets.

## Family Map

The upstream technical-details folder names these JA4+ methods:

| Method | Short name | Purpose |
| --- | --- | --- |
| JA4 | JA4 | TLS client fingerprinting |
| JA4Server | JA4S | TLS server response or session fingerprinting |
| JA4HTTP | JA4H | HTTP client fingerprinting |
| JA4Latency | JA4L | client-to-server latency or light-distance measurement |
| JA4LatencyServer | JA4LS | server-to-client latency or light-distance measurement |
| JA4X509 | JA4X | X.509 certificate fingerprinting |
| JA4SSH | JA4SSH | SSH traffic fingerprinting |
| JA4TCP | JA4T | TCP client fingerprinting |
| JA4TCPServer | JA4TS | TCP server response fingerprinting |
| JA4TCPScan | JA4TScan | active TCP fingerprint scanner |
| JA4DHCP | JA4D | DHCP fingerprinting |
| JA4DHCPv6 | JA4D6 | DHCPv6 fingerprinting |

The full name and short name are interchangeable in upstream JA4 docs.

## JA4 TLS Client Workflow

JA4 fingerprints a TLS Client Hello. Build the visible `JA4_a` prefix,
then append two 12-character lowercase SHA-256 truncations:

```text
<transport><version><sni><cipher-count><extension-count><alpn>_<cipher-hash>_<extension-hash>
```

1. Set transport to `q` for QUIC, `d` for Datagram Transport Layer
   Security (DTLS), or `t` for TLS over TCP.
2. Determine TLS or DTLS version from supported_versions extension
   `0x002b` when present, using the highest non-GREASE value. If absent,
   use the Protocol Version field. Ignore the handshake version field.
3. Set Server Name Indication (SNI) flag to `d` when extension `0x0000`
   exists, otherwise `i`.
4. Count cipher suites as two digits, capping above 99 at `99`. Ignore
   GREASE values, but count SCSV, experimental, and reserved values.
5. Count extensions the same way, ignoring GREASE but including SNI and
   Application-Layer Protocol Negotiation (ALPN).
6. Set ALPN to the first and last ASCII alphanumeric characters of the
   first ALPN value. Use `00` if ALPN is absent, empty, or has no values.
   For a one-character ALPN, repeat that character. If the first or last
   byte is not ASCII alphanumeric, use the first and last characters of
   the hex representation instead.
7. Build `JA4_b` from lower-case 4-character cipher hex values, comma
   delimited, GREASE removed, sorted in hex order, then SHA-256 hash and
   truncate to 12 characters. If no ciphers remain, use `000000000000`.
8. Build `JA4_c` from lower-case 4-character extension hex values,
   GREASE removed, SNI `0000` and ALPN `0010` removed, sorted in hex
   order. Append `_` and signature algorithms in original order when
   signature algorithms exist. SHA-256 hash and truncate to 12
   characters. If no extensions remain, use `000000000000`.

Example from the upstream spec:

```text
JA4 = t13d1516h2_8daaf6152771_e5627efa2ab1
```

For raw JA4 output, keep sorted raw values in `JA4_r`. When preserving
original order with the `-o` option, keep original ordering after
removing GREASE values, include SNI and ALPN, and rename `ja4` to
`ja4_o`.

## Diagram-Derived Family Fields

The upstream diagrams carry important field maps that are not all
duplicated in markdown. Use them as reference notes, then check current
upstream docs or implementation code before writing production parsers.

- `JA4S`: protocol, TLS version, extension count, chosen ALPN, chosen
  cipher suite, and a truncated SHA-256 hash of extensions in observed
  order.
- `JA4H`: HTTP method, HTTP version, cookie-present flag, referer-present
  flag, header count excluding Cookie and Referer, first four characters
  of primary Accept-Language or `0000`, then hashes for headers in
  observed order, cookie fields sorted, and cookie fields plus values
  sorted.
- `JA4T` or `JA4TS`: TCP window size, TCP options in observed order,
  maximum segment size, TCP window scale multiplier, and retransmission
  timings for JA4TScan.
- `JA4X`: hashes issuer relative distinguished names (RDNs), subject
  RDNs, and extensions in order; hash the RDN or extension structure,
  not certificate values.
- `JA4SSH`: over a default 200-packet window, records mode of client
  packet length, mode of server packet length, SSH packets sent from
  client, SSH packets sent from server, bare ACKs sent from client, and
  bare ACKs sent from server.
- `JA4L`: records one-way TCP latency in microseconds, observed TTL, and
  one-way application handshake latency. Distance estimates depend on
  speed of light per microsecond and a hop-count propagation-delay
  factor; treat them as approximate location evidence.
- `JA4D`: DHCP message type, maximum DHCP message size, requesting
  specific IP or new-IP flag, domain or no-domain flag, DHCP options
  list excluding options 50, 53, 81, and 255, and DHCP parameter request
  list.
- `JA4D6`: DHCPv6 message type, client DUID length, requesting specific
  IP or new-IP flag, domain or no-domain flag, DHCPv6 options list, and
  DHCPv6 option request list.

## Caveats

The detailed JA4 TLS algorithm is documented in markdown; several other
family members are currently diagram-only in the technical-details
folder. When the task is implementation rather than interpretation,
verify against upstream code, test vectors, or current FoxIO material
instead of relying only on OCR-derived notes.

Ignore GREASE anywhere the JA4 TLS algorithm says to ignore it. Do not
hash empty cipher or extension lists as an empty string; upstream uses
`000000000000` as an explicit no-values marker.

JA4 and JA4+ are FoxIO trademarks, and upstream technical details include
license and patent notices. Preserve attribution when writing user-facing
documentation or distributing derived implementation material.

## Completion Criteria

The skill has been applied when the agent can identify the JA4-family
method in use, explain the visible fields, name which values are hashed
or preserved in order, call out confidence limits for diagram-derived
methods, and avoid mutating original packet-capture evidence.
