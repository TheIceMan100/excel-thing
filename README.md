# excel-thing

Local development trusts the standard `localhost:8000` and `127.0.0.1:8000`
origins over HTTP and HTTPS for Django CSRF checks. For another host or port,
set `CSRF_TRUSTED_ORIGINS` to a comma-separated list of full origins, including
the scheme (for example, `https://example.com`). On Render, the configured
external hostname is trusted automatically.

Demand imports use one Demand by Work Center workbook. It uses the same format
as a ZSS Analysis workbook regardless of its filename. Its On-Hand Stock,
Actual Requirements, and Open Orders rows are expanded into dated demand
records. The app uses `DATABASE_URL` when configured, and clears demand and
inventory imports from that database before the Render web server starts.
Django accounts and other application data are not affected.
