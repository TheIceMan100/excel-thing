# excel-thing

Local development trusts the standard `localhost:8000` and `127.0.0.1:8000`
origins over HTTP and HTTPS for Django CSRF checks. For another host or port,
set `CSRF_TRUSTED_ORIGINS` to a comma-separated list of full origins, including
the scheme (for example, `https://example.com`). On Render, the configured
external hostname is trusted automatically.

Demand imports require both the Demand by Work Center workbook and the ZSS
Analysis workbook. The ZSS report's On-Hand Stock, Actual Requirements, and
Open Orders rows are expanded into dated demand records; duplicate records
shared by the two workbooks are imported once.
