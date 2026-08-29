# Contributing

Contributions should strengthen reliability evidence without expanding the private-business surface.

Before opening a pull request:

1. keep all fixtures synthetic and abstract;
2. add or update a regression test for behavioral changes;
3. run `python -m unittest discover -s tests -v`;
4. run `python scripts/public_audit.py .`;
5. update `docs/evidence-register.md` for material claims;
6. explain residual risk rather than claiming a guarantee.

Do not submit real market data, production logs, credentials, provider endpoints, private strategy rules or performance claims.
