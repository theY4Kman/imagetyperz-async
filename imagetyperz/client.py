"""
Async client for the imagetyperz API

Implementation details from: https://github.com/imagetyperz-api/imagetyperz-api-python3
API Docs: https://www.imagetyperz.com/Forms/api/api.html
Additional docs: https://github.com/imagetyperz-api/API-docs
"""
import asyncio
from datetime import datetime
from typing import Union

import httpx

from .auth import TokenDataAuth
from .constants import reCAPTCHAType
from .exceptions import (raise_on_error, ImageTimedOut, NotDecoded,
                         ImageTyperzError, LimitExceeded, MaximumAttemptsReached)
from .util.logging import getLogger, ClassLoggingProperty

logger = getLogger(__name__)


class ImageTyperzClient:
    session: httpx.AsyncClient
    log = ClassLoggingProperty(logger)

    _access_token: str

    _is_logged_in: bool

    class Endpoints:
        CAPTCHA_CONTENT = 'http://captchatypers.com/Forms/UploadFileAndGetTextNEWToken.ashx'
        CAPTCHA_URL = 'http://captchatypers.com/Forms/FileUploadAndGetTextCaptchaURLToken.ashx'
        RECAPTCHA_SUBMIT = 'http://captchatypers.com/captchaapi/UploadRecaptchaToken.ashx'
        RECAPTCHA_RETRIEVE = 'http://captchatypers.com/captchaapi/GetRecaptchaTextToken.ashx'
        BALANCE = 'http://captchatypers.com/Forms/RequestBalanceToken.ashx'
        BAD_IMAGE = 'http://captchatypers.com/Forms/SetBadImageToken.ashx'
        PROXY_CHECK = 'http://captchatypers.com/captchaAPI/GetReCaptchaTextTokenJSON.ashx'
        GEETEST_SUBMIT = 'http://captchatypers.com/captchaapi/UploadGeeTestToken.ashx'

    def __init__(self, access_token):
        self._access_token = access_token

        self.session = httpx.AsyncClient(auth=TokenDataAuth(self._access_token))

    async def __aenter__(self):
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.__aexit__(exc_type, exc_val, exc_tb)

    async def aclose(self):
        """Close the httpx client session"""
        await self.session.aclose()

    def _raise_on_error(self, response: httpx.Response, msg: str, *format_args,
                        no_log_exceptions=(ImageTimedOut, NotDecoded)):
        try:
            raise_on_error(response)
        except ImageTyperzError as e:
            if not isinstance(e, no_log_exceptions):
                self.log.error('%s: %s', msg, *format_args, e)
            raise

    async def retrieve_balance(self) -> float:
        """Retrieve the amount of funds in the authenticated account

        :return:
            Float representing the amount of money available in the account,
            in USD.

        """
        data = {
            'action': 'REQUESTBALANCE',
        }
        res = await self.session.post(self.Endpoints.BALANCE, data=data)
        self._raise_on_error(res, 'Error retrieving account balance')

        return float(res.text)

    async def submit_recaptcha(
        self, *,
        page_url: str,
        site_key: str,
        user_agent: str = None,
        recaptcha_type: Union[int, reCAPTCHAType] = reCAPTCHAType.AUTO,
        recaptcha_action: str = None,
        recaptcha_min_score: float = None,
        data_s: str = None,
    ) -> str:
        """Submit a reCAPTCHA v2 or v3 job

        :param page_url:
            Page URL of website, eg. abc.com

        :param site_key:
            Site key passed to reCAPTCHA JS API, has to be scraped from site

        :param user_agent:
            User-Agent used in solving recaptcha

        :param recaptcha_type:
            Can be one of this 3 values:
                0 - determine automatically (default)
                1 - normal
                2 - invisible
                3 - v3

        :param recaptcha_action:
            Action parameter used in solving v3 recaptcha

        :param recaptcha_min_score:
            Score targeted, check being done against a test recaptcha

        :param data_s:
            Required with some reCAPTCHAs. A one-time token generated with each
            captcha loaded.

        :return:
            ID of the reCAPTCHA job, used to retrieve the response separately,
            afterward.

        """
        data = {
            'action': 'UPLOADCAPTCHA',
            'pageurl': page_url,
            'googlekey': site_key,
            'useragent': user_agent,
            'recaptchatype': recaptcha_type,
            'captchaaction': recaptcha_action,
            'score': recaptcha_min_score,
            'data-s': data_s,
        }
        data = {
            k: v
            for k, v in data.items()
            if v is not None
        }

        self.log.trace('Submitting reCAPTCHA job: %s', data)
        res = await self.session.post(url=self.Endpoints.RECAPTCHA_SUBMIT, data=data)
        self._raise_on_error(res, 'Error submitting reCAPTCHA job')

        job_id = res.text.strip()
        self.log.debug('Successfully submitted reCAPTCHA job: %s', job_id)
        return job_id

    async def retrieve_recaptcha(self, job_id: str) -> str:
        """Retrieve results of a reCAPTCHA job

        :param job_id:
            reCAPTCHA job ID, as returned by submit_captcha()

        :return:
            The g-response of the completed captcha, which may be used to bypass
            the captcha on the website.

        """
        data = {
            'action': 'GETTEXT',
            'captchaid': job_id,
        }

        self.log.trace('Retrieving reCAPTCHA job: %s', data)
        res = await self.session.post(self.Endpoints.RECAPTCHA_RETRIEVE, data=data)
        self._raise_on_error(res, 'Error retrieving reCAPTCHA job %s', job_id)

        g_response = res.text
        self.log.debug('Retrieved reCAPTCHA job %s: %s', job_id, g_response)
        return g_response

    async def complete_recaptcha(
        self, *,
        page_url: str,
        site_key: str,
        user_agent: str = None,
        recaptcha_type: Union[int, reCAPTCHAType] = reCAPTCHAType.AUTO,
        recaptcha_action: str = None,
        recaptcha_min_score: float = None,
        data_s: str = None,
        max_attempts: int = 10,
        poll_interval: float = 2.5,
    ) -> str:
        """Submit reCAPTCHA v2 or v3 job and return its result when available

        This method will await the results of a reCAPTCHA job. If an error of
        IMAGE_TIMED_OUT or LIMIT_EXCEED is returned, the job will be resubmitted
        up to max_attempts-1 times.

        :param page_url:
            Page URL of website, eg. abc.com

        :param site_key:
            Site key passed to reCAPTCHA JS API, has to be scraped from site

        :param user_agent:
            User-Agent used in solving recaptcha

        :param recaptcha_type:
            The version/flavour of the reCAPTCHA. Can be one of:
                0 - determine automatically (default)
                1 - normal
                2 - invisible
                3 - v3

        :param recaptcha_action:
            Action parameter used in solving v3 recaptcha

        :param recaptcha_min_score:
            Score targeted, check being done against a test recaptcha

        :param data_s:
            Required with some reCAPTCHAs. A one-time token generated with each
            captcha loaded.

        :param max_attempts:
            Maximum number of times to submit

        :param poll_interval:
            Time to wait between checking for job results

        :return:
            The g-response of the completed captcha, which may be used to bypass
            the captcha on the website.

        """
        start_at = datetime.utcnow()

        for attempt in range(max_attempts):
            job_id = await self.submit_recaptcha(
                page_url=page_url,
                site_key=site_key,
                user_agent=user_agent,
                recaptcha_type=recaptcha_type,
                recaptcha_action=recaptcha_action,
                recaptcha_min_score=recaptcha_min_score,
                data_s=data_s,
            )

            while True:
                try:
                    g_response = await self.retrieve_recaptcha(job_id)
                except NotDecoded:
                    await asyncio.sleep(poll_interval)
                except (ImageTimedOut, LimitExceeded) as e:
                    attempts_left = max_attempts - attempt - 1
                    if attempts_left > 0:
                        next_step = f'Resubmitting job ({attempts_left} attempts left)'
                    else:
                        next_step = f'Maximum attempts ({max_attempts}) reached. Aborting.'

                    self.log.debug('reCAPTCHA solve job %s expired (%s). %s', job_id, e, next_step)
                    break
                else:
                    end_at = datetime.utcnow()
                    elapsed = end_at - start_at
                    self.log.info('Solved reCAPTCHA job %s in %ss: %s', job_id, elapsed, g_response)
                    return g_response

        else:
            raise MaximumAttemptsReached(
                f'Maximum number of attempts ({max_attempts}) reached while '
                f'trying to solve reCAPTCHA')
