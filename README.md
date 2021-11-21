# imagetyperz-async

An asynchronous client for the [ImageTyperz CAPTCHA-solving API](http://imagetyperz.com/).

[httpx](https://github.com/encode/httpx) powers the HTTP requests.

**At the moment, only image CAPTCHAS and reCAPTCHAs are supported.**


# Installation

```bash
pip install imagetyperz-async
```


# Usage

```python
import asyncio

from imagetyperz import ImageTyperzClient, reCAPTCHAType
from imagetyperz.exceptions import NotDecoded

async def demo():
    ###
    # Context manager will handle the closing of connections in the underlying
    # httpx AsyncClient at block end.
    #
    # Alternatively, `await ita.aclose()` may be manually called to perform
    # cleanup.
    #
    # If no cleanup is performed, a warning may be emitted at Python exit.
    #
    async with ImageTyperzClient('6F0848592604C9E14F0EBEA7368493C5') as ita:
        print(await ita.retrieve_balance())
        #: 8.8325

        # Submit reCAPTCHA job
        job_id = await ita.submit_recaptcha(
            page_url='https://example.com/login',
            site_key='scraped-site-key',
            recaptcha_type=reCAPTCHAType.INVISIBLE,
        )
        print(job_id)
        #: 176140709

        # Check for results of the reCAPTCHA job
        while True:
            try:
                g_response = await ita.retrieve_recaptcha(job_id)
            except NotDecoded:
                await asyncio.sleep(5)
                continue
            else:
                print(g_response)
                #: 03AGdBq25hDTCjOq4QywdrY...
                break

        # Alternatively, use complete_recaptcha to automatically handle the polling
        # for results — returning with the result when ready.
        g_response = await ita.complete_recaptcha(
            page_url='https://example.com/login',
            site_key='scraped-site-key',
            recaptcha_type=reCAPTCHAType.INVISIBLE,
        )
        print(g_response)
        #: 03AGdBq25hDTCjOq4QywdrY...
```
