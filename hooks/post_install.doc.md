# hooks/post_install.sh

Post-install sanity check. Verifies that the bridge imports, the
`health` subcommand works, and pytest passes. Best-effort — non-zero
exit only on the import/health checks, not on pytest (which is a
soft gate for the release).

## When it runs

The hook is wired up by future `pip install` improvements. For v0.1,
run it manually after install:

```bash
bash hooks/post_install.sh
```

## Touched by

- Nothing at install time yet. Documented here so release engineers
  know to invoke it before tagging.
