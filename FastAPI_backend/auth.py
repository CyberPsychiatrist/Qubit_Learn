from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse

class AuthMiddleware:
    def __init__(self):
        self.login_url = "/"
        
    async def __call__(self, request: Request):
        user = request.session.get("user")
        if not user:
            return RedirectResponse(
                url=self.login_url,
                status_code=status.HTTP_303_SEE_OTHER
            )
        return user

auth_required = AuthMiddleware()
