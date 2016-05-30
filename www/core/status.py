__author__ = 'cloudy'

'''
    response status code.
'''


CODE_SUCCESS = 0

CODE_VALUE_INVALID = 1000
CODE_NOT_FOUND = 1001
CODE_FORBIDDEN = 1002
CODE_INTERNAL_ERROR = 1003
CODE_LOGIN_FAILED = 1004
CODE_TOKEN_EXPIRED = 1005

STATUS_CODE = {
    CODE_SUCCESS: 'success',
    CODE_VALUE_INVALID: 'value invalid',
    CODE_NOT_FOUND: 'resource not found',
    CODE_FORBIDDEN: 'permission forbidden',
    CODE_INTERNAL_ERROR: 'internal error',
    CODE_LOGIN_FAILED: 'auth failed',
    CODE_TOKEN_EXPIRED: 'token expired'
}


