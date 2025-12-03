# # xrf_explorer/server/auth.py
# from flask_httpauth import HTTPTokenAuth
# from xrf_explorer.server.database.models import User

# # Create the global HTTPTokenAuth instance
# auth = HTTPTokenAuth(scheme='Bearer')


# @auth.verify_token
# def verify_token(token):
#     """
#     Verify the provided Bearer token and return the associated User.
#     Return None if verification fails (unauthorized).
#     """
#     if not token:
#         return None

#     user = User.verify_auth_token(token)
#     return user  # Returning None means authentication failed


# @auth.get_user_roles
# def get_user_roles(user):
#     """
#     Return a list of role names for the authenticated user.
#     This enables role-based route protection.
#     """
#     if not user:
#         return []
#     return [user.role.name]


# def provide_auth() -> HTTPTokenAuth:
#     """
#     Provides the singleton HTTPTokenAuth instance.
#     (Optional helper function — not strictly required.)
#     """
#     return auth
