from fastapi import HTTPException, Request, status
from fastapi_limiter.depends import RateLimiter


class RateLimiters:
    TIMES = 20
    SECONDS = 60

    @staticmethod
    def global_limiter():
        """IP-based global rate limiter"""
        return RateLimiter(times=RateLimiters.TIMES, seconds=RateLimiters.SECONDS)

    @staticmethod
    def user_rate_limiter():
        """User-based rate limiter"""

        async def identifier(request: Request):
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
                )
            return f"user:{user.id}"

        return RateLimiter(
            times=RateLimiters.TIMES,
            seconds=RateLimiters.SECONDS,
            identifier=identifier,
        )
