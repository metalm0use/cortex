---
schema_version: 1
tags:
  - "forensics"
  - "network"
  - "evidence"
topics:
  - "packet capture"
  - "network forensics"
  - "pcap analysis"
status: seed
created: 2026-05-31
updated: 2026-06-07
sources:
  - "https://github.com/sandbornm/my-claude-skills/tree/main/pcap-analyzer"
source_count: 1
aliases:
  - "pcap"
  - "packet capture"
  - "pcap analysis"
skill_id: forensics/pcap
summary: "Preserve original packet captures and analyze derived copies for network-forensics artifacts, anomalies, and evidence."
model_role: reference
depends_on: []
related:
  - forensics/ja4
  - meta/contributing
---

# Packet Capture Handling

<!-- learned: 2026-05 | project: cortex-bootstrap | model: seed -->

Treat packet capture files as evidence. Keep the original `.pcap` or
`.pcapng` file unchanged, record its hash, and perform filtering or
extraction on a copy.

Example preservation pass:

```bash
sha256sum capture.pcapng > capture.pcapng.sha256
cp capture.pcapng work-capture.pcapng
```

When exporting a subset, name the filter and tool version in notes beside
the derived file. A future agent should be able to tell whether a missing
packet was absent from the original capture or removed by the filter.

## Core Rule

Never make the analyzer more important than the evidence. Preserve the
original capture, write derived outputs to a separate work directory, and
record enough commands, filters, tool versions, and hashes for another
analyst to reproduce or challenge the result.

## Analysis Workflow

1. Record source metadata before analysis: absolute path, size, file
   type, packet count, first and last packet timestamps, and SHA-256 hash.
2. Create a work directory beside the case notes. Copy or filter the
   capture into that directory; keep outputs, logs, and extracted files
   there rather than beside the original evidence.
3. Start broad, then narrow. Produce top talkers, conversations,
   protocol distribution, service or destination-port summary, DNS
   queries, TLS Server Name Indication (SNI), and HTTP hosts or URLs when
   plaintext traffic exists.
4. Use display or Berkeley Packet Filter (BPF) filters only after the
   broad pass. Save the exact filter string with the derived file.
5. Extract higher-risk artifacts deliberately: streams, credentials,
   cookies, files, and HTTP bodies may contain secrets or malware. Store
   hashes and redact report output when sharing.
6. Treat anomaly detectors as leads, not conclusions. Beaconing,
   scanning, DNS tunneling, exfiltration, and unusual port findings need
   packet examples, timestamps, endpoints, and supporting context.
7. Use the vendored PCAP analyzer scripts when a repeatable Scapy-based
   artifact extraction pass is useful and dependencies are available.
   Keep their output in the derived work directory.
8. For JA4-family fingerprints or TLS interpretation, also read
   `skills/forensics/ja4/SKILL.md`.

## Useful First-Pass Commands

Use installed local tools first for capture metadata and quick summaries:

```bash
capinfos capture.pcapng
tshark -r capture.pcapng -q -z io,phs
tshark -r capture.pcapng -q -z conv,ip
tshark -r capture.pcapng -q -z endpoints,ip
tshark -r capture.pcapng -Y dns -T fields -e frame.time -e ip.src -e dns.qry.name
tshark -r capture.pcapng -Y http -T fields -e frame.time -e ip.src -e http.host -e http.request.uri
tshark -r capture.pcapng -Y tls.handshake.extensions_server_name -T fields -e frame.time -e ip.src -e tls.handshake.extensions_server_name
```

For large captures, filter first and write a derived capture:

```bash
tshark -r capture.pcapng -f "host 192.0.2.10" -w work-host-192.0.2.10.pcapng
sha256sum work-host-192.0.2.10.pcapng > work-host-192.0.2.10.pcapng.sha256
```

If using Python or Scapy for extraction, prefer scripts that accept the
capture path as an argument, write only to an explicit output directory,
and avoid network access. Review dependencies before installing them.

## Vendored Analyzer Scripts

<!-- learned: 2026-06 | project: cortex-pcap-import | model: codex -->

This skill vendors the upstream `pcap-analyzer` package from
`https://github.com/sandbornm/my-claude-skills/tree/main/pcap-analyzer`
under `skills/forensics/pcap/vendor/pcap-analyzer/`. See
`skills/forensics/pcap/vendor/pcap-analyzer/VENDORED-SOURCES.txt` before
changing inherited files. Only the runnable analyzer scripts are
vendored; Cortex keeps its own `SKILL.md` as the single instruction
source.

Use the wrapper when Python 3.8+, Scapy, and a POSIX shell are available:

```bash
skills/forensics/pcap/vendor/pcap-analyzer/scripts/pcap-analyze.sh \
  -s analyze_all.py \
  -o ./analysis \
  capture.pcap
```

Available analysis scripts:

- `analyze_all.py`: overview, protocol distribution, endpoints,
  conversations, and notable findings.
- `extract_streams.py`: TCP and UDP stream reconstruction; accepts
  script arguments such as `--host`, `--port`, and `--max-streams`.
- `extract_dns.py`: DNS queries, responses, unique domains, and
  timeline output.
- `extract_http.py`: HTTP requests, responses, headers, and bodies.
- `export_endpoints.py`: endpoint, port, MAC, subnet, and connection
  mapping.
- `export_statistics.py`: protocol hierarchy, packet sizes, timing,
  TCP flags, and TTL hints.
- `find_anomalies.py`: beaconing, scans, C2-like intervals,
  exfiltration, DNS tunneling, unusual protocol use, cleartext sensitive
  data, and TLS anomalies.
- `extract_credentials.py`: cleartext credential indicators with partial
  password redaction in output.
- `extract_files.py`: file carving from supported cleartext transfers
  and stream magic bytes, with hashes.

Common scripted pass:

```bash
mkdir -p ./forensics
skills/forensics/pcap/vendor/pcap-analyzer/scripts/pcap-analyze.sh \
  -s analyze_all.py \
  -s export_endpoints.py \
  -s extract_dns.py \
  -s find_anomalies.py \
  -s extract_credentials.py \
  -s extract_files.py \
  -o ./forensics \
  evidence.pcap
```

For large captures, apply a BPF filter before running expensive scripts:

```bash
skills/forensics/pcap/vendor/pcap-analyzer/scripts/pcap-analyze.sh \
  --bpf "host 192.0.2.10" \
  -s analyze_all.py \
  -o ./host-192.0.2.10 \
  capture.pcap
```

Treat the script output as generated evidence. Record the wrapper command,
script names, BPF filters, dependency versions, and output hashes in the
case notes.

## Artifact Checklist

For ordinary network-forensics triage, aim to produce:

- Capture metadata and original hash.
- Tool versions and exact commands.
- Top endpoints and conversations.
- Protocol and port summaries.
- DNS query and response summaries.
- TLS SNI, certificate, or JA4-family fingerprints when visible.
- Plain HTTP request and response metadata when present.
- Extracted streams or files with hashes, only when needed.
- Credential or token findings with secrets redacted in shared reports.
- Anomaly leads with timestamps, endpoints, and packet filters.

## Caveats

Encrypted TLS content cannot be reconstructed from a capture alone.
Traffic decryption needs matching key material such as `SSLKEYLOGFILE`
and compatible tooling, and that key material becomes sensitive evidence.

Live capture is a different workflow from capture analysis. Use tools
such as tcpdump, dumpcap, Wireshark, or tshark directly, and document the
capture interface, filter, snap length, clock source, and permissions.

Wireless 802.11, NetFlow/IPFIX, IDS rule replay, and malware sandbox
execution each have specialized tooling. Use this skill for packet
capture evidence handling and first-pass network artifact analysis, then
branch to the domain-specific workflow.

## Completion Criteria

The PCAP work is complete when the original capture remains untouched,
all derived captures and extracted artifacts are named and hashed, the
analysis commands and filters are reproducible, sensitive findings are
handled as evidence, and every conclusion can be traced back to packet
timestamps, endpoints, filters, or exported artifacts.
