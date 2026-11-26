from slowapi import Limiter
from slowapi.util import get_remote_address

# One shared limiter; endpoints opt in with @limiter.limit("...").
limiter = Limiter(key_func=get_remote_address, default_limits=[])