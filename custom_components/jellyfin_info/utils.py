def get_api_url(server_url: str, auth_token: str, endpoint: str) -> str:
    return f"{server_url}/{endpoint}?ApiKey={auth_token}"
