import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'amack.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'CoffeeShop'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

#https://amack.us.auth0.com/authorize?audience=CoffeeShop&response_type=token&client_id=zC2eLAAz1QXKGVTqOOT81txy7pKBqGBc&redirect_uri=https://127.0.0.1:4200/

## TODO change; https://{{YOUR_DOMAIN}}/authorize?audience={{API_IDENTIFIER}}&response_type=token&client_id={{YOUR_CLIENT_ID}}&redirect_uri={{YOUR_CALLBACK_URI}}
#https://127.0.0.1:4200/
# #access_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InMxd1BDcXVzeC05UXJ4TEhIR05RcCJ9.eyJpc3MiOiJodHRwczovL2FtYWNrLnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExMDcxNDkyOTI1ODIyMjc3OTYyNSIsImF1ZCI6WyJDb2ZmZWVTaG9wIiwiaHR0cHM6Ly9hbWFjay51cy5hdXRoMC5jb20vdXNlcmluZm8iXSwiaWF0IjoxNjAzOTk2MzY1LCJleHAiOjE2MDQwMDM1NjUsImF6cCI6InpDMmVMQUF6MVFYS0dWVHFPT1Q4MXR4eTdwS0JxR0JjIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCJ9.Xf-oRetrFmyr6WvHP-mA5JMck4VR7xdfP7MLXjNpM_aB_au-FxEb46LdLCD4m42w9eZ9EZjOLkIcebIfd4yZ9KR9TTHjSWhfwTMiThD5tBzboHa2ZFm96wi7lFamrnv7iIerkoevQOY8qtqRKbdPDpDcCo56yIsW0OPTOw20Lbjo0qpLSEUO1dnyxLZPvMNdlqldEMtTqewqaQo8rlclbnM3z2J0voc1I-L0c3xu8hblKo0KOqU53saa6NnEWDaXLL9Ex9F7OFULNc6RhKaduLRxs1WixRrrqb_txntph_2gbfdmpPlPhQSWlBHR2KBThAhm2fgFv2j7tXHBeQyqZQ
# &scope=openid%20profile%20email&expires_in=7200
# &token_type=Bearer
# &state=g6Fo2SBVQjFZUmRfaUl4VUs1SHNtQnhCWkJwZnJtWHdXdlRCWaN0aWTZIEl2bEMxbGhYVC01SW1Fc2d5MFRLUEJ2anNJckxENXpio2NpZNkgekMyZUxBQXoxUVhLR1ZUcU9PVDgxdHh5N3BLQnFHQmM

#testingThis1!

def get_token_auth_header():

    if 'Authorization' not in request.headers: 
        print('no auth')
        raise AuthError({
            'code': 'no_authorization',
            'description': 'No authorization present in headers.'
        }, 401)
    auth_header = request.headers['Authorization']
    header_parts= auth_header.split(' ')

    if len(header_parts)!=2:
        raise AuthError({
                'code': 'header_parts',
                'description': 'more or less than 2 parts in auth_header.'
            }, 401)
    elif header_parts[0].lower()!='bearer':
        print('no bearer')
        raise AuthError({
                'code': 'no_bearer',
                'description': 'Bearer token not present.'
            }, 401)

    return header_parts[1]

'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    if 'permissions' not in payload: 
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT'
        }, 400)
    
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permissions not found. Unauthorized.'
        }, 401)
    print('passed it all')
    return True 
    raise Exception('Not Implemented')


def verify_decode_jwt(token):
    
    # get the public key from auth0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())

    #get data in header
    unverified_header = jwt.get_unverified_header(token)

    #get key
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            #use the key to validate the JWT
            
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            return payload

        except jwt.ExpiredSignatureError:
            print('expired')
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please check the audience and issuer.'
            }, 401)


        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)

    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key.'
    }, 400)
    raise Exception('Not Implemented')



def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except AuthError:
                raise AuthError({
                    'code': 'unauthorized',
                    'description': 'could not decode jwt'
                })
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator