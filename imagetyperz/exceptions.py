import httpx

__all__ = [
    'ImageTyperzError',
    'AuthenticationFailed',
    'InvalidDomain',
    'InvalidSiteKey',
    'InvalidCaptchaId',
    'NotDecoded',
    'ImageTimedOut',
    'AutomatedQueries',
    'NotInvisible',
    'LimitExceeded',
    'MaximumAttemptsReached',
    'raise_on_error',
]


class ImageTyperzError(Exception):
    pass


class AuthenticationFailed(ImageTyperzError):
    """Provided username and password and/or access key are invalid"""


class InvalidDomain(ImageTyperzError):
    """Wrong domain. Check your domain"""


class InvalidSiteKey(ImageTyperzError):
    """Wrong site key. Check your site key"""


class InvalidCaptchaId(ImageTyperzError):
    """Invalid/nonexistent captcha job ID"""


class NotDecoded(ImageTyperzError):
    """Captcha is still being completed

    This is not really an error, just notifies the captcha is still in progress.
    When you get this, retry after 5 seconds.
    """


class ImageTimedOut(ImageTyperzError):
    """Captcha wasn't completed by workers in time"""


class AutomatedQueries(ImageTyperzError):
    """Proxy sent is blocked temporarily. Change your proxy"""


class NotInvisible(ImageTyperzError):
    """Captcha is not invisible"""


class LimitExceeded(ImageTyperzError):
    """Server is overloaded"""


ERROR_TEXT_EXC_MAP = {
    'AUTHENTICATION_FAILED': AuthenticationFailed,
    'INVALID_DOMAIN': InvalidDomain,
    'INVALID_SITEKEY': InvalidSiteKey,
    'INVALID_CAPTCHA_ID': InvalidCaptchaId,
    'NOT_DECODED': NotDecoded,
    'IMAGE_TIMED_OUT': ImageTimedOut,
    'AUTOMATED_QUERIES': AutomatedQueries,
    'NOT_INVISIBLE': NotInvisible,
    'LIMIT_EXCEED': LimitExceeded,
}


class MaximumAttemptsReached(RuntimeError):
    """The maximum number of attempts has been made; cannot continue"""


def raise_on_error(response: httpx.Response) -> None:
    """Raise the appropriate exception if the response contains an ERROR: ...
    """
    text = response.text
    if 'ERROR:' in text:
        _, err_type = text.split('ERROR:', maxsplit=1)
        err_type = err_type.strip()
        exc_class = ERROR_TEXT_EXC_MAP.get(err_type, ImageTyperzError)
        raise exc_class(err_type)
