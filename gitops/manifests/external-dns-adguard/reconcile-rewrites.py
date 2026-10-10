#!/usr/bin/env python3
"""Reconcile AdGuard $dnsrewrite user rules into proper DNS rewrites.

external-dns-provider-adguard writes CNAME rules as custom filtering rules
($dnsrewrite=NOERROR;CNAME;...).  AdGuard returns these as a bare CNAME
without the target A record, which glibc resolvers reject ("No address
associated with hostname").  AdGuard rewrites include the resolved A record
in the same response, so this script mirrors every $dnsrewrite user rule
into a real rewrite entry.

Run as a CronJob every few minutes.  Idempotent: only adds rewrites that
don't already exist.
"""

import os
import re
import sys

import httpx

DNSREWRITE_RE = re.compile(
    r"\|([^^]+)\^?\$dnsrewrite=NOERROR;CNAME;([^,]+)"
)

Auth = tuple[str, str]


def parse_dnsrewrite_rules(user_rules: list[str]) -> list[tuple[str, str]]:
    """Extract (domain, target) pairs from $dnsrewrite filtering rules."""
    pairs: list[tuple[str, str]] = []
    for rule in user_rules:
        if match := DNSREWRITE_RE.search(rule):
            domain, target = match.group(1), match.group(2)
            pairs.append((domain, target))
    return pairs


def get_existing_rewrites(
    client: httpx.Client, base_url: str, auth: Auth
) -> dict[str, str]:
    """Return {domain: answer} for all existing AdGuard rewrites."""
    resp = client.get(
        f"{base_url}/control/rewrite/list", auth=auth, timeout=10
    )
    resp.raise_for_status()
    return {
        entry["domain"]: entry.get("answer", "")
        for entry in resp.json()
    }


def get_dnsrewrite_user_rules(
    client: httpx.Client, base_url: str, auth: Auth
) -> list[str]:
    """Fetch AdGuard user filtering rules (where $dnsrewrite rules live)."""
    resp = client.get(
        f"{base_url}/control/filtering/status", auth=auth, timeout=10
    )
    resp.raise_for_status()
    return resp.json().get("user_rules", [])


def add_rewrite(
    client: httpx.Client, base_url: str, auth: Auth,
    domain: str, target: str,
) -> bool:
    """Add a single rewrite entry. Returns True on success."""
    resp = client.post(
        f"{base_url}/control/rewrite/add",
        auth=auth,
        json={"domain": domain, "answer": target},
        timeout=10,
    )
    resp.raise_for_status()
    return True


def reconcile(
    client: httpx.Client, base_url: str, auth: Auth
) -> tuple[int, int]:
    """Reconcile $dnsrewrite rules into AdGuard rewrites.

    Returns (added_count, total_dnsrewrite_count).
    """
    user_rules = get_dnsrewrite_user_rules(client, base_url, auth)
    dnsrewrite_pairs = parse_dnsrewrite_rules(user_rules)
    existing = get_existing_rewrites(client, base_url, auth)

    added = 0
    for domain, target in dnsrewrite_pairs:
        if existing.get(domain) == target:
            continue
        print(f"adding rewrite: {domain} -> {target}", flush=True)
        add_rewrite(client, base_url, auth, domain, target)
        added += 1
    return added, len(dnsrewrite_pairs)


def main() -> int:
    """Run the reconcile loop."""
    url = os.environ["ADGUARD_URL"]
    auth = (os.environ["ADGUARD_USER"], os.environ["ADGUARD_PASSWORD"])

    with httpx.Client(verify=True) as client:
        added, total = reconcile(client, url, auth)
        print(
            f"reconcile complete: {added} added, "
            f"{total} total $dnsrewrite rules",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
