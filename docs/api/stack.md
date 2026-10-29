# Stack

## Profiles and environments

Set Compose profiles and interpolation files once on the stack; they apply to
all its Compose operations. For example, select the environment before creating
the stack:

```python
import os
from orche import Stack

environment = os.environ.get("ORCHE_ENV", "dev")
if environment not in {"dev", "prod"}:
    raise ValueError(f"Unknown environment: {environment}")

stack = Stack(
    path=".",
    profiles=["debug"] if environment == "dev" else [],
    env_files=[".env", f".env.{environment}"],
)
```

Run with `ORCHE_ENV=prod orche up`. Relative env file paths are resolved against
`Stack.path`; explicit files must exist when the stack is created. Compose reads
the files in order, with later files overriding earlier ones. Shell variables
take precedence for Compose interpolation. When no env files are supplied,
Compose's normal default `.env` behavior applies. These are Compose CLI
interpolation files, distinct from a service's `env_file` setting. See the
[Docker Compose interpolation documentation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/).

::: orche.stack.Stack
