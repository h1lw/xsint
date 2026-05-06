"""Email account enumeration across consumer services.

Adapted from kaifcodec/user-scanner (MIT). All HTTP request logic
is inlined — no runtime dependency on the upstream package.
Each check returns (hit: bool|None, url: str|None, extra: str|None).
"""
import asyncio
import json
import re
import time
import httpx

INFO = {
    "free": ["email"],
    "returns": ["registered accounts"],
    "themes": {"EmailEnum": {"color": "magenta", "icon": "📧"}},
}

PARENT = "EmailEnum"
PER_CHECK_TIMEOUT = 8.0
CONCURRENCY = 25

async def _chk_adult_babestation(email: str):
    url = "https://www.babestation.tv/user/send/username-reminder"
    show_url = "https://babestation.tv"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Content-Type': "application/json",
        'x-requested-with': "XMLHttpRequest",
        'origin': "https://www.babestation.tv",
        'referer': "https://www.babestation.tv/forgot-password-or-username",
        'accept-language': "en-US,en;q=0.9",
    }

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code in [200, 404]:
                data = response.json()
                success = data.get("success")

                if success is True:
                    return (True, show_url, None)

                if success is False:
                    errors = data.get("errors", [])
                    if "Email not found" in errors:
                        return (False, show_url, None)

                return (None, None, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_adult_fapfolder(email: str):
    url = "https://fapfolder.club/includes/ajax/core/signup.php"
    show_url = "https://fapfolder.club"

    payload = {
        'username': "l0v3_d0n0t_3xist",
        'email': email,
        'email2': email,
        'password': "1",
        'field1': "",
        'privacy_agree': "on"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': "?1",
        'origin': "https://fapfolder.club",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://fapfolder.club/signup",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return (None, None, None)

            data = response.json()
            message = data.get("message", "")

            if "belongs to an existing account" in message:
                return (True, show_url, None)

            if "password must be at least" in message:
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_adult_flirtbate(email: str):
    url = "https://api.flirtbate.com/api/v1/customer/reset-password-email"
    show_url = "https://flirtbate.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Content-Type': "application/json",
        'origin': "https://flirtbate.com",
        'referer': "https://flirtbate.com/",
        'accept-language': "en-US,en;q=0.9",
    }

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 429:
                return (None, None, None)

            data = response.json()
            message = data.get("message", "")

            if "Reset password email sent" in message:
                return (True, show_url, None)

            if "Email invalid for reset password" in message:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_adult_lovescape(email: str):
    url = "https://lovescape.com/api/front/auth/signup"
    show_url = "https://lovescape.com"

    payload = {
        "username": "_W3ak3n3d_Cut3n3ss86541",
        "email": email,
        "password": "igy8868yiyy",
        "recaptcha": "",
        "fingerprint": "",
        "modelName": "",
        "isPwa": False,
        "affiliateId": "",
        "trafficSource": "",
        "isUnThrottled": False,
        "hasActionParam": False,
        "source": "page_signup",
        "device": "mobile",
        "deviceName": "Android Mobile",
        "browser": "Chrome",
        "os": "Android",
        "locale": "en",
        "authType": "native",
        "ampl": {
            "ep": {
                "source": "page_signup",
                "startSessionUrl": "/create-ai-sex-girlfriend/style",
                "firstVisitedUrl": "/create-ai-sex-girlfriend/style",
                "referrerHost": "hakurei.us-cdnbo.org",
                "referrerId": "us-cdnbo",
                "signupUrl": "/signup",
                "page": "signup",
                "project": "Lovescape",
                "isCookieAccepted": True,
                "displayMode": "browser"
            },
            "up": {
                "source": "page_signup",
                "startSessionUrl": "/create-ai-sex-girlfriend/style",
                "firstVisitedUrl": "/create-ai-sex-girlfriend/style",
                "referrerHost": "hakurei.us-cdnbo.org",
                "referrerId": "us-cdnbo",
                "signupUrl": "/signup"
            },
            "device_id": "",
            "session_id": 1774884558258
        }
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'Content-Type': "text/plain;charset=UTF-8",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': "?1",
        'Origin': "https://lovescape.com",
        'Referer': "https://lovescape.com/signup",
        'Priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 403:
                return (None, None, None)

            data = response.json()
            error_msg = data.get("error", "")

            if "Email is already used" in error_msg:
                return (True, show_url, None)

            if "Username is already used" in error_msg:
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_adult_made_porn(email: str):
    show_url = "https://made.porn"
    url = "https://made.porn/endpoint/api/json/change-password"

    payload = {
        'email': email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Origin': "https://made.porn",
        'Referer': "https://made.porn/login",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, data=payload, headers=headers)
            data = response.json()

            if "sent an email with a link" in data.get("Text", ""):
                return (True, show_url, None)

            if "The email address is incorrect" in data.get("Error", ""):
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_adult_xnxx(email: str):
    show_url = "https://xnxx.com"
    url = "https://www.xnxx.com/account/checkemail"
    params = {'email': email}
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Accept-Encoding': "identity",
        'X-Requested-With': "XMLHttpRequest",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': "?1",
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': "https://www.xnxx.com/",
        'Accept-Language': "en-US,en;q=0.9"
    }

    async with httpx.AsyncClient(http2=True, timeout=5.0) as client:
        try:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()
            exists_bool = data.get("result")

            if exists_bool is True:
                return (False, show_url, None)
            elif exists_bool is False:
                return (True, show_url, None)
            else:
                return (None, None, None)

        except Exception as e:
            return (None, None, None)

async def _chk_adult_xvideos(email: str):
    show_url = "https://xvideos.com"
    url = "https://www.xvideos.com/account/checkemail"
    params = {'email': email}

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Accept-Encoding': "identity",
        'X-Requested-With': "XMLHttpRequest",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua': "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        'sec-ch-ua-mobile': "?1",
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': "https://www.xvideos.com/",
        'Accept-Language': "en-US,en;q=0.9"
    }

    async with httpx.AsyncClient(http2=True, timeout=5.0) as client:
        try:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()

            exists_bool = data.get("result")

            if exists_bool is True:
                return (False, show_url, None)
            elif exists_bool is False:
                return (True, show_url, None)
            else:
                return (None, None, None)

        except Exception as e:
            return (None, None, None)

async def _chk_community_nextdoor(email: str):
    url = "https://auth.nextdoor.com/v2/token"
    show_url = "https://nextdoor.com"

    payload = {
        'scope': "openid",
        'client_id': "NEXTDOOR-WEB",
        'login_type': "basic",
        'grant_type': "password",
        'username': email,
        'password': "vhj87uyguu77"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': "?1",
        'Origin': "https://nextdoor.com",
        'Referer': "https://nextdoor.com/",
        'Priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return (None, None, None)

            data = response.json()
            error = data.get("error", "")

            if error == "invalid_grant":
                return (True, show_url, None)

            if error == "not_found":
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_creator_adobe(email: str):
    show_url = "https://adobe.com"
    url = "https://auth.services.adobe.com/signin/v2/users/accounts"

    payload = {
        "username": email,
        "usernameType": "EMAIL"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Content-Type': "application/json",
        'x-ims-clientid': "BehanceWebSusi1",
        'Origin': "https://auth.services.adobe.com",
        'Referer': "https://www.behance.net/",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                return (None, None, None)

            if not data:
                return (False, show_url, None)

            for account in data:
                methods = account.get("authenticationMethods", [])
                if any(m.get("id") == "password" for m in methods):
                    return (True, show_url, None)

            return (False, show_url, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_creator_flickr(email: str):
    url = "https://cognito-idp.us-east-1.amazonaws.com"
    show_url = "https://flickr.com"

    payload = {
        "ClientId": "3ck15a1ov4f0d3o97vs3tbjb52",
        "Username": email,
        "Password": "You#are-a-n80",
        "UserAttributes": [
            {"Name": "email", "Value": email},
            {"Name": "birthdate", "Value": "1983-02-05"},
            {"Name": "given_name", "Value": "John"},
            {"Name": "family_name", "Value": "Doe"},
            {"Name": "locale", "Value": "en-us"}
        ],
        "ValidationData": [{"Name": "recaptchaToken", "Value": "Not-required"}],
        "ClientMetadata": {"referrerUrl": ""}
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'x-amz-target': "AWSCognitoIdentityProviderService.SignUp",
        'content-type': "application/x-amz-json-1.1",
        'origin': "https://identity.flickr.com",
        'referer': "https://identity.flickr.com/sign-up"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            body = response.text

            if "An account with the given email already exists" in body:
                return (True, show_url, None)

            elif "PreSignUp failed with error Sign Up failure" in body:
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_dev_codecademy(email: str):
    show_url = "https://codecademy.com"
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.codecademy.com/register?redirect=%2F',
        'Content-Type': 'application/json',
        'Origin': 'https://www.codecademy.com',
    }

    try:
        async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
            init_res = await client.get("https://www.codecademy.com/register", headers=headers)

            csrf_match = re.search(
                r'name="csrf-token" content="([^"]+)"', init_res.text)
            if not csrf_match:
                return (None, None, None)

            headers["X-CSRF-Token"] = csrf_match.group(1)

            payload = {"user": {"email": email}}

            response = await client.post(
                'https://www.codecademy.com/register/validate',
                headers=headers,
                json=payload
            )

            if response.status_code == 400 and 'has already been taken' in response.text:
                return (True, show_url, None)
            elif response.status_code == 200:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_dev_codepen(email: str):
    show_url = "https://codepen.io"
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://codepen.io/accounts/signup/user/free',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://codepen.io',
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            init_res = await client.get("https://codepen.io/accounts/signup/user/free", headers=headers)

            csrf_match = re.search(
                r'name="csrf-token" content="([^"]+)"', init_res.text)
            if not csrf_match:
                return (None, None, None)

            headers["X-CSRF-Token"] = csrf_match.group(1)

            payload = {
                'attribute': 'email',
                'value': email,
                'context': 'user'
            }

            response = await client.post(
                'https://codepen.io/accounts/duplicate_check',
                headers=headers,
                data=payload
            )

            if "That Email is already taken." in response.text:
                return (True, show_url, None)
            elif response.status_code == 200:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_dev_codewars(email: str):
    show_url = "https://codewars.com"
    url = "https://www.codewars.com/join"

    params = {'language': 'javascript'}

    payload = {
        'utf8': "✓",
        '_method': "patch",
        'user[email]': email,
        'user[username]': "",
        'user[password]': "",
        'user[password_confirmation]': "",
        'utm[source]': "",
        'utm[medium]': "",
        'utm[campaign]': "",
        'utm[term]': "",
        'utm[content]': "",
        'utm[referrer]': "https://www.google.com/"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Origin': "https://www.codewars.com",
        'Referer': "https://www.codewars.com/join",
        'Upgrade-Insecure-Requests': "1",
    }

    try:
        async with httpx.AsyncClient(timeout=7.0, follow_redirects=True) as client:
            response = await client.post(url, params=params, data=payload, headers=headers)
            html = response.text

            if "is already taken" in html:
                return (True, show_url, None)

            if "can&#39;t be blank" in html:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_dev_devrant(email: str):
    show_url = "https://devrant.com"
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://devrant.com',
        'Referer': 'https://devrant.com/feed/top/month?login=1',
    }

    payload = {
        'app': '3',
        'type': '1',
        'email': email,
        'username': '',
        'password': '',
        'guid': '',
        'plat': '3',
        'sid': '',
        'seid': ''
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post('https://devrant.com/api/users', headers=headers, data=payload)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()
            error_msg = data.get('error', '')

            if error_msg == 'The email specified is already registered to an account.':
                return (True, show_url, None)

            return (False, show_url, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_dev_envato(email: str):
    url = "https://account.envato.com/api/public/validate_email"
    show_url = "https://elements.envato.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': "application/json",
        'Content-Type': "application/json",
        'x-client-version': "3.6.0",
        'origin': "https://elements.envato.com",
        'referer': "https://elements.envato.com/",
        'accept-language': "en-US,en;q=0.9",
    }

    payload = {
        "language_code": "en",
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 204:
                return (False, show_url, None)

            if response.status_code == 422:
                data = response.json()
                error_msg = data.get("error_message", "").lower()

                if "already in use" in error_msg:
                    return (True, show_url, None)

                return (None, None, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_dev_github(email: str):
    show_url = "https://github.com"
    async with httpx.AsyncClient(http2=True, follow_redirects=True) as client:
        try:
            url1 = "https://github.com/signup"
            headers1 = {
                'host': 'github.com',
                'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'sec-fetch-site': 'cross-site',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'referer': 'https://www.google.com/',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'accept-language': 'en-US,en;q=0.9',
                'priority': 'u=0, i'
            }

            res1 = await client.get(url1, headers=headers1)
            html = res1.text

            csrf_match = re.search(r'data-csrf="true"\s+value="([^"]+)"', html)

            if not csrf_match:
                return (None, None, None)

            csrf_token = csrf_match.group(1)

            url2 = "https://github.com/email_validity_checks"
            payload = {
                'authenticity_token': csrf_token,
                'value': email
            }

            headers2 = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                'Accept-Encoding': "gzip, deflate, br, zstd",
                'sec-ch-ua-platform': '"Linux"',
                'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
                'sec-ch-ua-mobile': "?0",
                'origin': "https://github.com",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://github.com/signup",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=1, i"
            }

            response = await client.post(url2, data=payload, headers=headers2)
            body = response.text

            if "already associated with an account" in body:
                return (True, show_url, None)
            elif response.status_code == 200 and "Email is available" in body:
                return (False, show_url, None)
            else:
                return (None, None, None)

        except Exception as e:
            return (None, None, None)

async def _chk_dev_hackerone(email: str):
    show_url = "https://hackerone.com"
    signup_url = "https://hackerone.com/sign_up"
    api_url = "https://hackerone.com/users"

    headers_init = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Encoding': "identity",
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-full-version': '"145.0.7632.109"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-platform': '"Linux"',
        'sec-ch-ua-platform-version': '""',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version-list': '"Not:A-Brand";v="99.0.0.0", "Google Chrome";v="145.0.7632.109", "Chromium";v="145.0.7632.109"',
        'upgrade-insecure-requests': "1",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "navigate",
        'sec-fetch-user': "?1",
        'sec-fetch-dest': "document",
        'referer': "https://hackerone.com/users/sign_in",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=0, i"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r_page = await client.get(signup_url, headers=headers_init)

            if r_page.status_code == 403:
                return (None, None, None)

            csrf_match = re.search(
                r'name="csrf-token" content="([^"]+)"', r_page.text)
            if not csrf_match:
                return (None, None, None)

            csrf_token = csrf_match.group(1)

            reg_headers = {
                'sec-ch-ua-full-version-list': '"Not:A-Brand";v="99.0.0.0", "Google Chrome";v="145.0.7632.109", "Chromium";v="145.0.7632.109"',
                'sec-ch-ua-platform': '"Linux"',
                'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
                'sec-ch-ua-bitness': '"64"',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-mobile': "?0",
                'sec-ch-ua-arch': '"x86"',
                'x-requested-with': "XMLHttpRequest",
                'sec-ch-ua-full-version': '"145.0.7632.109"',
                'accept': "application/json, text/javascript, */*; q=0.01",
                'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
                'x-csrf-token': csrf_token,
                'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
                'sec-ch-ua-platform-version': '""',
                'origin': "https://hackerone.com",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://hackerone.com/users/sign_up",
                'accept-encoding': "identity",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=1, i"
            }

            payload = {
                'user[name]': "St33l_h3art_g3t_n0_l0v3",
                'user[username]': "kn0wl3dg3_is_curs3",
                'user[email]': email,
                'user[password]': "thisw0rldwasn3v3rg00d",
                'user[password_confirmation]': "mismatch_on_purpose"
            }

            response = await client.post(api_url, data=payload, headers=reg_headers)
            status = response.status_code

            if status == 403:
                return (None, None, None)

            data = response.json()
            errors = data.get("errors", {})

            if "has already been taken" in str(errors.get("email", [])):
                return (True, show_url, None)

            if "email" not in errors:
                return (False, show_url, None)

            if status == 429:
                return (None, None, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

import urllib.parse

async def _chk_dev_hackthebox(email: str):
    show_url = "https://hackthebox.com"
    register_url = "https://account.hackthebox.com/register"
    api_url = "https://account.hackthebox.com/api/v1/user/email/verify"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not:A-Brand";v="99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145"',
        'sec-ch-ua-mobile': "?1",
        'x-requested-with': "XMLHttpRequest",
        'origin': "https://account.hackthebox.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://account.hackthebox.com/register",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r_init = await client.get(register_url, headers={'User-Agent': headers['User-Agent']})

            if r_init.status_code == 403:
                return (None, None, None)

            xsrf_token_encoded = client.cookies.get("XSRF-TOKEN")
            if not xsrf_token_encoded:
                return (None, None, None)

            xsrf_token = urllib.parse.unquote(xsrf_token_encoded)
            headers['x-xsrf-token'] = xsrf_token

            payload = {"email": email}
            response = await client.post(api_url, content=json.dumps(payload), headers=headers)

            status = response.status_code

            if status == 403:
                return (None, None, None)

            if status == 422:
                resp_data = response.json()
                if "cannot use this email address" in str(resp_data):
                    return (True, show_url, None)
                return (None, None, None)

            if status in [200, 204]:
                return (False, show_url, None)

            if status == 429:
                return (None, None, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_dev_howtogeek(email: str):
    url = "https://www.howtogeek.com/check-user-exists/"
    show_url = "https://www.howtogeek.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'Referer': "https://www.howtogeek.com/",
        'Priority': "u=1, i"
    }

    params = {
        'email': email
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()

            # Use the userExists key for validation
            if data.get("userExists") is True:
                return (True, show_url, None)

            elif data.get("userExists") is False:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_dev_huggingface(email: str):
    url = "https://huggingface.co/api/check-user-email"
    show_url = "https://huggingface.co"
    payload = {'email': email}

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        'Accept-Encoding': "identity",
        'referer': "https://huggingface.co/join",
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=5)
            res_text = response.text
            st_code = response.status_code

            if st_code == 429:
                return (None, None, None)

            if st_code == 200:
                if "already exists" in res_text:
                    return (True, show_url, None)

                if "This email address is available." in res_text:
                    return (False, show_url, None)

            return (None, None, None)

        except Exception as e:
            return (None, None, None)

async def _chk_dev_leetcode(email: str):
    show_url = "https://leetcode.com"
    url = "https://leetcode.com/graphql/"

    # Hardcoded values as leetcode accepting this value, weird but it works!
    static_csrf = "bMwA82bLs7IrhigK19Bu6uDj4DhZnVnE"

    payload = {
        "query": """
            mutation AuthRequestPasswordResetByEmail($email: String!) {
                authRequestPasswordResetByEmail(email: $email) {
                    ok
                    error
                }
            }
        """,
        "variables": {"email": email},
        "operationName": "AuthRequestPasswordResetByEmail"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Content-Type': "application/json",
        'x-csrftoken': static_csrf,
        'Origin': "https://leetcode.com",
        'Referer': "https://leetcode.com/accounts/password/reset/",
        'Cookie': f"csrftoken={static_csrf}"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            data = response.json()

            result_obj = data.get("data", {}).get(
                "authRequestPasswordResetByEmail", {})
            is_ok = result_obj.get("ok")
            error_msg = result_obj.get("error")

            if is_ok is True:
                return (True, show_url, None)

            if is_ok is False and error_msg == "Email does not exist":
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_dev_replit(email: str):
    url = "https://replit.com/data/user/exists"
    show_url = "https://replit.com"

    payload = {
        "email": email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua': "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
        'sec-ch-ua-mobile': "?1",
        'x-requested-with': "XMLHttpRequest",
        'origin': "https://replit.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://replit.com/signup",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    async with httpx.AsyncClient(http2=False, timeout=5.0) as client:
        try:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 403:
                return (None, None, None)

            data = response.json()
            exists = data.get("exists")

            if exists is True:
                return (True, show_url, None)
            if exists is False:
                return (False, show_url, None)

            return (None, None, None)

        except Exception as e:
            return (None, None, None)

async def _chk_dev_wix(email: str):
    show_url = "https://wix.com"
    url = "https://users.wix.com/wix-users/v1/userAccountsByEmail"

    payload = {
        "email": email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'x-wix-client-artifact-id': "login-react-app",
        'origin': "https://users.wix.com",
        'referer': "https://users.wix.com/signin/signup",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 200:
                data = response.json()
                if "accountsData" in data and len(data.get("accountsData", [])) > 0:
                    return (True, show_url, None)
                return (None, None, None)

            elif response.status_code == 404:
                return (False, show_url, None)

            elif response.status_code == 429:
                return (None, None, None)

            else:
                return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_dev_wondershare(email: str):
    csrf_url = "https://accounts.wondershare.com/api/v3/csrf-token"
    inspect_url = "https://accounts.wondershare.com/api/v3/account/inspect"
    show_url = "https://wondershare.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'x-lang': "en-us",
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': "?1",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://accounts.wondershare.com/m/login?source=&redirect_uri=https://www.wondershare.com/?source=&site=www.wondershare.com&verify=no",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:

            r_csrf = await client.get(csrf_url, headers=headers)
            if r_csrf.status_code != 200:
                return (None, None, None)

            token = client.cookies.get("req_identity")

            if not token:
                return (None, None, None)

            inspect_headers = headers.copy()
            inspect_headers.update({
                'x-csrf-token': token,
                'Content-Type': "application/json",
                'origin': "https://accounts.wondershare.com",
                'referer': "https://accounts.wondershare.com/m/register"
            })

            payload = {"email": email}

            response = await client.put(
                inspect_url,
                content=json.dumps(payload),
                headers=inspect_headers
            )

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data_final = response.json()
            status_obj = data_final.get("data")

            if not isinstance(status_obj, dict):
                return (None, None, None)

            status_code = status_obj.get("exist")

            # 1 = Registered, 2 = Not Registered
            if status_code == 1:
                return (True, show_url, None)
            elif status_code == 2:
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_dev_xda(email: str):
    show_url = "https://xda-developers.com"
    url = "https://www.xda-developers.com/check-user-exists/"

    params = {
        'email': email,
        'subscribe': "true"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Referer': "https://www.xda-developers.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            data = response.json()
            exists = data.get("userExists")

            if exists is True:
                return (True, show_url, None)

            if exists is False:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_entertainment_justwatch(email: str):
    url = "https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri"
    show_url = "https://justwatch.com"
    params = {
        'key': "AIzaSyDv6JIzdDvbTBS-JWdR4Kl22UvgWGAyuo8"
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'x-client-version': "Chrome/JsCore/10.14.1/FirebaseCore-web",
        'origin': "https://www.justwatch.com",
        'referer': "https://www.justwatch.com/",
    }
    payload = {
        "identifier": email,
        "continueUri": "https://www.justwatch.com/"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                params=params,
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                registered = data.get("registered")

                if registered is True:
                    return (True, show_url, None)
                elif registered is False:
                    return (False, show_url, None)

                return (None, None, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_entertainment_letterboxd(email: str):
    show_url = "https://letterboxd.com"
    home_url = "https://letterboxd.com/sign-in/"
    register_url = "https://letterboxd.com/user/standalone/register.do"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'X-Requested-With': "XMLHttpRequest",
        'Origin': "https://letterboxd.com",
        'Referer': "https://letterboxd.com/register/standalone/",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            await client.get(home_url, headers={'User-Agent': headers['User-Agent']})
            csrf_token = client.cookies.get("com.xk72.webparts.csrf")

            if not csrf_token:
                return (None, None, None)

            payload = {
                '__csrf': csrf_token,
                'token': "",
                'emailAddress': email,
                'username': "th3_t3erminal_w0rri0r",
                'password': "n3v3r_F3lt_softn3ss",
                'termsAndAge': "true",
                'g-recaptcha-response': "",
                'h-captcha-response': ""
            }

            response = await client.post(register_url, data=payload, headers=headers)
            data = response.json()

            messages = data.get("messages", [])
            error_fields = data.get("errorFields", [])

            is_taken = any(
                "already associated with an account" in msg for msg in messages)

            if is_taken or "emailAddress" in error_fields:
                return (True, show_url, None)

            if "result" in data and not is_taken:
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_entertainment_myanimelist(email: str):
    show_url = "https://myanimelist.net"
    url = "https://myanimelist.net/signup/email/validate"

    payload = {
        'email': email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'x-requested-with': "XMLHttpRequest",
        'origin': "https://myanimelist.net",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://myanimelist.net/register.php?",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()
            errors = data.get("errors", [])
            resp_data = data.get("data")

            if errors and any("already have an account" in err.get("message", "") for err in errors):
                return (True, show_url, None)

            elif isinstance(resp_data, list) and len(resp_data) == 0:
                return (False, show_url, None)

            else:
                return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_entertainment_stremio(email: str):
    show_url = "https://stremio.com"
    url = "https://api.strem.io/api/login"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'Origin': "https://www.stremio.com",
        'Referer': "https://www.stremio.com/",
        'Accept-Language': "en-US,en;q=0.9",
    }

    payload = {
        "authKey": None,
        "email": email,
        "password": "wrongpassword123"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                error_data = data.get("error", {})

                if error_data.get("wrongPass") is True:
                    return (True, show_url, None)
                elif error_data.get("wrongEmail") is True:
                    return (False, show_url, None)

                return (None, None, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_fitness_fitnessblender(email: str):
    base_url = "https://www.fitnessblender.com"
    api_url = "https://www.fitnessblender.com/api/v1/validate/unique-email"
    show_url = "https://www.fitnessblender.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'Origin': "https://www.fitnessblender.com",
        'Referer': "https://www.fitnessblender.com/join",
        'X-Requested-With': "XMLHttpRequest",
        'Priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            # Step 1: Visit homepage to get cookies (XSRF-TOKEN and FB_SESSION)
            # Laravel sets these in the Set-Cookie header
            r_init = await client.get(base_url, headers=headers)
            
            if r_init.status_code != 200:
                return (None, None, None)

            # Get the CSRF token from the cookies
            # Laravel allows using the XSRF-TOKEN cookie value as the x-csrf-token header
            csrf_token = client.cookies.get("XSRF-TOKEN")

            # If not in cookies, try to extract from the HTML script tag as a backup
            if not csrf_token:
                match = re.search(r'csrfToken:\s*"([^"]+)"', r_init.text)
                if match:
                    csrf_token = match.group(1)

            if not csrf_token:
                return (None, None, None)

            # Step 2: Post to the validation API
            headers['x-csrf-token'] = csrf_token
            headers['Content-Type'] = "application/json"

            payload = {
                "email": email,
                "force": 0
            }

            response = await client.post(
                api_url, 
                content=json.dumps(payload), 
                headers=headers
            )

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code == 419:
                return (None, None, None)

            data = response.json()
            status = data.get("status")
            message = data.get("message", "").lower()

            # Logic: error + "already registered" = TAKEN
            if status == "error" and "already registered" in message:
                return (True, show_url, None)

            # Logic: success + "ok" = AVAILABLE
            elif status == "success" and message == "ok":
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_fitness_myfitnesspal(email: str):
    url = "https://www.myfitnesspal.com/api/idm/user-exists"
    show_url = "https://www.myfitnesspal.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'Referer': "https://www.myfitnesspal.com/account/create",
        'Accept-Language': "en-US,en;q=0.9",
        'Priority': "u=1, i"
    }

    params = {
        'email': email
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()

            # Use the emailExists key for validation
            if data.get("emailExists") is True:
                return (True, show_url, None)

            elif data.get("emailExists") is False:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_gaming_addictinggames(email: str):
    show_url = "https://addictinggames.com"
    url = "https://prod.addictinggames.com/user/registerpass"

    params = {
        '_format': "json"
    }

    payload = {
        "name": [{"value": "tierd_knight"}],
        "mail": [{"value": email}],
        "pass": [{"value": "n0_0ne_asked_just_fight"}],
        "field_opt_in": [{"value": False}]
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Content-Type': "application/json",
        'Origin': "https://www.addictinggames.com",
        'Referer': "https://www.addictinggames.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.post(url, params=params, content=json.dumps(payload), headers=headers)
            body = response.text

            # Logic: If both 'tierd_knight' and 'email' are taken, the email exists.
            # If only 'tierd_knight' is mentioned as taken, the email is available.
            if response.status_code == 403:
                return (None, None, None)

            if "mail: The email address" in body and "is already taken" in body:
                return (True, show_url, None)

            if "name: The username tierd_knight is already taken" in body:
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_gaming_chess_com(email: str):
    async with httpx.AsyncClient(http2=True) as client:
        try:
            url = "https://www.chess.com/rpc/chesscom.authentication.v1.EmailValidationService/Validate"
            show_url = "https://chess.com"

            payload = {
                "email": email
            }

            headers = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
                'Accept': "application/json, text/plain, */*",
                'Accept-Encoding': "identity",
                'Content-Type': "application/json",
                'sec-ch-ua-platform': '"Android"',
                'accept-language': "en_US",
                'connect-protocol-version': "1",
                'origin': "https://www.chess.com",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'referer': "https://www.chess.com/register",
                'priority': "u=1, i"
            }

            response = await client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()
            status = data.get("status")

            if status == "EMAIL_STATUS_TAKEN":
                return (True, show_url, None)
            elif status == "EMAIL_STATUS_AVAILABLE":
                return (False, show_url, None)
            else:
                return (None, None, None)

        except Exception as e:
            return (None, None, None)

async def _chk_gaming_crazygames(email: str):
    url = "https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri"
    show_url = "https://crazygames.com"

    params = {
        'key': "AIzaSyAkBGn9sKEUBSMQ9CTFyHHxXas0tdcpts8"
    }

    payload = {
        "identifier": email,
        "continueUri": "https://www.crazygames.com/"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'origin': "https://www.crazygames.com",
        'referer': "https://www.crazygames.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, params=params, content=json.dumps(payload), headers=headers)
            data = response.json()

            is_registered = data.get("registered")

            if is_registered is True:
                return (True, show_url, None)

            elif is_registered is False:
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_hosting_neocities(email: str):
    show_url = "https://neocities.org"
    url = "https://neocities.org/create_validate"

    payload = {
        'field': "email",
        'value': email,
        'is_education': "false"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'x-requested-with': "XMLHttpRequest",
        'origin': "https://neocities.org",
        'referer': "https://neocities.org/",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, data=payload, headers=headers)

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()

            if "error" in data:
                if "already exists" in data["error"]:
                    return (True, show_url, None)
                return (None, None, None)

            if data.get("result") == "ok":
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_jobs_freelancer(email: str):
    url = "https://www.freelancer.com/api/users/0.1/users/check?compact=true&new_errors=true"
    show_url = "https://freelancer.com"

    payload = {
        "user": {
            "email": email
        }
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://www.freelancer.com',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 409 and "EMAIL_ALREADY_IN_USE" in response.text:
                return (True, show_url, None)

            elif response.status_code == 200:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_learning_alison(email: str):
    show_url = "https://alison.com"
    url = "https://alison.com/register"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        'Origin': "https://alison.com",
        'Referer': "https://alison.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=7.0, follow_redirects=True) as client:
            init_res = await client.get(url, headers=headers)

            token_match = re.search(
                r'name="_token"\s+value="([^"]+)"', init_res.text)
            if not token_match:
                return (None, None, None)

            csrf_token = token_match.group(1)

            payload = {
                '_token': csrf_token,
                'firstname': "The",
                'lastname': "SilentSowrd",
                'signup_email': email,
                'signup_password': "",
                'signup_tc_social': "1",
                'current': "https://alison.com",
                'route_name': "site.home"
            }

            response = await client.post(url, data=payload, headers=headers)
            body = response.text

            if "The signup email has already been taken" in body:
                return (True, show_url, None)

            if 'id="emailNew"' in body and "The signup email has already been taken" not in body:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_learning_coursera(email: str):
    show_url = "https://coursera.org"
    url = "https://www.coursera.org/api/userAccounts.v1"

    params = {
        'action': "getLoginMethods",
        'email': email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'X-Requested-With': "XMLHttpRequest",
        'X-Coursera-Application': "front-page",
        'Origin': "https://www.coursera.org",
        'Referer': "https://www.coursera.org/?authMode=signup"
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.post(url, params=params, json={}, headers=headers)
            data = response.json()

            if "loginMethods" not in data:
                return (None, None, None)

            methods = data["loginMethods"]

            if not isinstance(methods, list):
                return (None, None, None)
            if len(methods) > 0:
                return (True, show_url, None)
            else:
                return (False, show_url, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_learning_duolingo(email: str):
    show_url = "https://duolingo.com"
    headers = {
        'authority': 'www.duolingo.com',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
        'Referer': 'https://www.duolingo.com/',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            response = await client.get(
                f"https://www.duolingo.com/2017-06-30/users?email={email}",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                # Duolingo returns a list of users matching the email
                if data.get("users") and len(data["users"]) > 0:
                    return (True, show_url, None)
                else:
                    return (False, show_url, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_learning_vedantu(email: str):
    url = "https://user.vedantu.com/user/preLoginVerification"
    show_url = "https://www.vedantu.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json;charset=UTF-8",
        'sec-ch-ua-platform': '"Linux"',
        'Origin': "https://www.vedantu.com",
        'Referer': "https://www.vedantu.com/",
        'Priority': "u=1, i"
    }

    payload = {
        "email": email,
        "phoneCode": None,
        "phoneNumber": None,
        "version": 2,
        "ver": 1.033,
        "token": "",
        "sType": "",
        "sValue": "",
        "event": "NEW_FLOW"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url, 
                content=json.dumps(payload), 
                headers=headers
            )

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()

            # Primary check using the emailExists key
            if data.get("emailExists") is True:
                masked_phone = data.get("phone")
                if masked_phone:
                    # Passing the masked phone number to the result
                    return (True, show_url, f"Phone: {masked_phone}")
                return (True, show_url, None)

            elif data.get("emailExists") is False:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_music_deezer(email: str):
    show_url = "https://www.deezer.com"
    gw_url = "https://www.deezer.com/ajax/gw-light.php"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept-Encoding': "identity",
        'Content-Type': "text/plain;charset=UTF-8",
        'Origin': "https://account.deezer.com",
        'Referer': "https://account.deezer.com/"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            handshake_params = {
                'method': "deezer.getUserData",
                'input': "3",
                'api_version': "1.0",
                'api_token': ""
            }
            handshake_payload = {"APP_NAME": "Deezer"}

            r_handshake = await client.post(
                gw_url,
                params=handshake_params,
                content=json.dumps(handshake_payload),
                headers=headers
            )

            if r_handshake.status_code == 403:
                return (None, None, None)

            handshake_data = r_handshake.json()
            api_token = handshake_data.get("results", {}).get("checkForm")

            if not api_token:
                return (None, None, None)

            validate_params = {
                'method': "user_checkRegisterConstraints",
                'input': "3",
                'api_version': "1.0",
                'api_token': api_token
            }

            validate_payload = {
                "APP_NAME": "Deezer",
                "EMAIL": email
            }

            response = await client.post(
                gw_url,
                params=validate_params,
                content=json.dumps(validate_payload),
                headers=headers
            )

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()
            errors = data.get("results", {}).get("errors", {})

            if errors.get("email", {}).get("error") == "email_already_used":
                return (True, show_url, None)

            elif "country" in errors and "email" not in errors:
                return (False, show_url, None)

            else:
                return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_music_gaana(email: str):
    url = "https://jsso.indiatimes.com/sso/crossapp/identity/web/checkUserExists"
    show_url = "https://gaana.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'channel': "gaana.com",
        'platform': "WAP",
        'sdkversion': "0.7.3",
        'isjssocrosswalk': "true",
        'origin': "https://gaana.com",
        'referer': "https://gaana.com/",
        'priority': "u=1, i"
    }

    payload = {
        "identifier": email
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            
            if response.status_code == 403:
                return (None, None, None)
            
            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()
            user_status = data.get("data", {}).get("status", "")

            if user_status == "VERIFIED_EMAIL" or user_status == "UNVERIFIED_EMAIL":
                return (True, show_url, None)
            
            elif data.get("status") == "SUCCESS":
                return (False, show_url, None)

            else:
                return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_music_mixcloud(email: str):
    show_url = "https://mixcloud.com"
    register_url = "https://app.mixcloud.com/authentication/email-register/"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'x-requested-with': "XMLHttpRequest",
        'x-mixcloud-platform': "www",
        'origin': "https://www.mixcloud.com",
        'referer': "https://www.mixcloud.com/",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0, follow_redirects=True) as client:

            payload = {
                'email': email,
                'username': "you_ar3_al0n3_fight",
                'password': "",
                'ch': 'y'
            }

            response = await client.post(register_url, data=payload, headers=headers)
            status = response.status_code

            if status == 403:
                return (None, None, None)

            if status == 200:
                data = response.json()
                errors = data.get("data", {}).get("$errors", {})

                email_errors = errors.get("email", [])
                if any("already in use" in err for err in email_errors):
                    return (True, show_url, None)

                return (False, show_url, None)

            if status == 429:
                return (None, None, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_music_spotify(email: str):
    async with httpx.AsyncClient(http2=False, follow_redirects=True) as client:
        try:
            get_url = "https://www.spotify.com/in-en/signup"
            show_url = "https://spotify.com"
            get_headers = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                'Accept-Encoding': "identity",
                'sec-ch-ua': "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
                'sec-ch-ua-mobile': "?0",
                'sec-ch-ua-platform': "\"Linux\"",
                'upgrade-insecure-requests': "1",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "navigate",
                'sec-fetch-user': "?1",
                'sec-fetch-dest': "document",
                'referer': "https://www.spotify.com/us/signup",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=0, i"
            }

            await client.get(get_url, headers=get_headers)

            post_url = "https://spclient.wg.spotify.com/signup/public/v2/account/validate"

            payload = {
                "fields": [
                    {
                        "field": "FIELD_EMAIL",
                        "value": email
                    }
                ],
                "client_info": {
                    "api_key": "a1e486e2729f46d6bb368d6b2bcda326",
                    "app_version": "v2",
                    "capabilities": [1],
                    "installation_id": "3740cfb5-c76f-4ae9-9a94-f0989d7ae5a4",
                    "platform": "www",
                    "client_id": ""
                },
                "tracking": {
                    "creation_flow": "",
                    "creation_point": "https://www.spotify.com/us/signup",
                    "referrer": "",
                    "origin_vertical": "",
                    "origin_surface": ""
                }
            }

            post_headers = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                'Accept-Encoding': "identity",
                'Content-Type': "application/json",
                'sec-ch-ua-platform': "\"Linux\"",
                'sec-ch-ua': "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
                'sec-ch-ua-mobile': "?0",
                'origin': "https://www.spotify.com",
                'sec-fetch-site': "same-site",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://www.spotify.com/",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=1, i"
            }

            response = await client.post(post_url, content=json.dumps(payload), headers=post_headers)

            data = response.json()

            if "error" in data and "already_exists" in data["error"]:
                return (True, show_url, None)
            elif "success" in data:
                return (False, show_url, None)

            return (None, None, None)

        except Exception as e:
            return (None, None, None)

async def _chk_news_bbc(email: str):
    show_url = "https://bbc.com"
    login_url = "https://account.bbc.com/auth/identifier/signin?realm=%2F&clientId=Account&action=register&ptrt=https%3A%2F%2Fwww.bbc.com%2F&userOrigin=BBCS_BBC&purpose=free"
    check_url = "https://account.bbc.com/auth/identifier/check"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Origin': "https://account.bbc.com",
    }

    try:
        async with httpx.AsyncClient(timeout=7.0, follow_redirects=True) as client:
            response = await client.get(login_url, headers=headers)

            nonce_match = re.search(
                r'nonce=([a-zA-Z0-9\-_]+)', str(response.url))
            if not nonce_match:
                nonce_match = re.search(
                    r'"nonce":"([a-zA-Z0-9\-_]+)"', response.text)

                return (None, None, None)

            nonce = nonce_match.group(1)

            params = {
                'action': "sign-in",
                'clientId': "Account",
                'context': "international",
                'isCasso': "false",
                'journeyGroupType': "sign-in",
                'nonce': nonce,
                'ptrt': "https://www.bbc.com/",
                'purpose': "free",
                'realm': "/",
                'redirectUri': "https://session.bbc.com/session/callback?realm=/",
                'service': "IdRegisterService",
                'userOrigin': "BBCS_BBC"
            }

            payload = {"userIdentifier": email}

            check_res = await client.post(check_url, params=params, json=payload, headers=headers)
            data = check_res.json()

            if data.get("exists") is True:
                return (True, show_url, None)
            elif data.get("exists") is False:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_news_cnn(email: str):
    show_url = "https://cnn.com"
    url = "https://audience.cnn.com/core/api/1/identity"

    payload = {
        "identityRequests": [
            {
                "identityType": "EMAIL",
                "principal": email,
                "credential": "th3_sil3nt_fir3wall_hid3s_most"
            }
        ]
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'x-client-application': "Android|Android 10|Chrome 144.0.0.0",
        'Origin': "https://edition.cnn.com",
        'Referer': "https://edition.cnn.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            body = response.text

            if "identity.already.in.use" in body:
                return (True, show_url, None)

            if "cnn.createprofile" in body and "cnn.updatepassword" in body:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_news_foxnews(email: str):
    url = "https://id.fox.com/status/v1/status"
    show_url = "https://foxnews.com"

    params = {
        'email': email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "*/*",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'x-api-key': "049f8b7844b84b9cb5f830f28f08648c",
        'origin': "https://auth.fox.com",
        'referer': "https://auth.fox.com/",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()
            found = data.get("found")

            if found is True:
                return (True, show_url, None)

            elif found is False:
                return (False, show_url, None)

            else:
                return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_news_indiatimes(email: str):
    show_url = "https://timesofindia.com"
    url = "https://jsso.indiatimes.com/sso/crossapp/identity/web/checkUserExists"

    payload = {
        "identifier": email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'sdkversion': "0.8.1",
        'channel': "toi",
        'platform': "WAP",
        'Origin': "https://timesofindia.indiatimes.com",
        'Referer': "https://timesofindia.indiatimes.com/",
    }

    try:

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            response.raise_for_status()
            data = response.json()

            user_status = data.get("data", {}).get("status", "")

            if user_status == "VERIFIED_EMAIL":
                return (True, show_url, None)

            elif user_status == "UNREGISTERED_EMAIL":
                return (False, show_url, None)
            elif user_status == "UNVERIFIED_EMAIL":
                return (True, show_url, "However email is not verified on the site")

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

import html

async def _chk_news_nytimes(email: str):
    show_url = "https://nytimes.com"
    # hit this first to wake up the session and grab the token
    login_url = "https://myaccount.nytimes.com/auth/enter-email?response_type=cookie&client_id=vi&redirect_uri=https%3A%2F%2Fwww.nytimes.com"
    check_url = "https://myaccount.nytimes.com/svc/lire_ui/authorize-email/check"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Accept-Language': "en-US,en;q=0.9",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': "?1"
    }

    try:
        # NYT likes HTTP/2, helps avoid getting flagged as a bot
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, http2=True) as client:

            init_res = await client.get(login_url, headers=headers)

            if init_res.status_code == 403:
                return (None, None, None)

            # Digging out the auth_token from the mess of HTML/JS
            token_match = re.search(
                r'authToken(?:&quot;|"|\\")\s*:\s*(?:&quot;|"|\\")([^&"\\]+)',
                init_res.text
            )

            if not token_match:
                return (None, None, None)

            auth_token = html.unescape(token_match.group(1))

            payload = {
                "email": email,
                "abraTests": "{\"AUTH_new_regilite_flow\":\"1_Variant\",\"AUTH_FORGOT_PASS_LIRE\":\"1_Variant\",\"AUTH_B2B_SSO\":\"1_Variant\"}",
                "auth_token": auth_token,
                "form_view": "enterEmail",
                "environment": "production"
            }

            # The critical tracking/origin headers
            api_headers = headers.copy()
            api_headers.update({
                'Content-Type': "application/json",
                'Accept': "application/json",
                'req-details': "[[it:lui]]",
                'Origin': "https://myaccount.nytimes.com",
                'Referer': login_url,
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty"
            })

            response = await client.post(
                check_url,
                content=json.dumps(payload),
                headers=api_headers
            )

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            res_data = response.json()
            further_action = res_data.get("data", {}).get("further_action", "")

            # If it says show-login, they have an account. If show-register, they don't.
            if further_action == "show-login":
                return (True, show_url, None)
            elif further_action == "show-register":
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_other_anydo(email: str):
    url = "https://sm-prod2.any.do/check_email"
    show_url = "https://any.do"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Content-Type": "application/json; charset=UTF-8",
        "Origin": "https://desktop.any.do",
        "Referer": "https://desktop.any.do/",
    }

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                content=json.dumps(payload),
                headers=headers
            )

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()

            if data.get("user_exists") is True:
                return (True, show_url, None)

            elif data.get("user_exists") is False:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_other_eventbrite(email: str):
    show_url = "https://eventbrite.com"
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': '*/*',
        'Accept-Language': 'en,en-US;q=0.9',
        'Referer': 'https://www.eventbrite.com/signin/',
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.eventbrite.com',
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            await client.get("https://www.eventbrite.com/signin/", headers=headers)

            csrf_token = client.cookies.get("csrftoken")
            if not csrf_token:
                return (None, None, None)

            headers["X-CSRFToken"] = csrf_token
            payload = {"email": email}

            response = await client.post(
                'https://www.eventbrite.com/api/v3/users/lookup/',
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("exists") is True:
                    return (True, show_url, None)
                elif data.get("exists") is False:
                    return (False, show_url, None)
                else:
                    return (None, None, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

import uuid

async def _chk_other_moz(email: str):
    show_url = "https://moz.com"
    url = "https://moz.com/app-api/jsonrpc/user.create.validate"

    rpc_id = str(uuid.uuid4())

    payload = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "method": "user.create.validate",
        "params": {
            "data": {
                "create_session": True,
                "verification_email_redirect": "/checkout/freetrial/billing-payment/pro_medium/monthly",
                "user": {
                    "email": email,
                    "password": "W3n3v3r_t0uch3d_s0ftn33s"
                }
            }
        }
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'origin': "https://moz.com",
        'referer': "https://moz.com/checkout/freetrial/signup/pro_medium/monthly",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()
            result_data = data.get("result", {})
            errors = result_data.get("errors", [])

            if not errors:
                return (False, show_url, None)

            if any(err.get("data", {}).get("issue") == "param-is-duplicate" for err in errors):
                return (True, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

import random
import string

async def _chk_other_office365(email: str):
    base_url = "https://outlook.office365.com/autodiscover/autodiscover.json/v1.0"
    show_url = "https://office365.com"

    headers = {
        "User-Agent": "Microsoft Office/16.0 (Windows NT 10.0; Microsoft Outlook 16.0.12026; Pro)",
        "Accept": "application/json",
    }

    def get_random_string(length: int) -> str:
        return "".join(random.choice(string.digits) for _ in range(length))

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:

            r = await client.get(
                f"{base_url}/{email}?Protocol=Autodiscoverv1",
                headers=headers,
            )

        if r.status_code == 403:
            return (None, None, None)

        if r.status_code == 429:
            return (None, None, None)

        if r.status_code == 200:
            return (True, show_url, None)

        return (False, show_url, None)

    except httpx.ConnectTimeout:
        return (None, None, None)

    except httpx.ReadTimeout:
        return (None, None, None)

    except Exception as e:
        return (None, None, None)

from html import unescape

def _extract_form_fields(html: str) -> dict:
    fields = {}
    for tag in re.finditer(r"<input\s[^>]*>", html, re.IGNORECASE):
        tag_str = tag.group(0)
        name = re.search(r'name=["\']([^"\']*)["\']', tag_str)
        value = re.search(r'value=["\']([^"\']*)["\']', tag_str)
        if name and value:
            fields[name.group(1)] = value.group(1)
    return fields


def _is_captcha(html: str) -> bool:
    lower = html.lower()
    return any(
        marker in lower
        for marker in ("captcha", "type the characters", "robot check", "opf-captcha")
    )


def _extract_form_action(html: str) -> str | None:
    """Two-pass: find the signIn or claim form regardless of attribute order."""
    for form_tag in re.finditer(r"<form\s[^>]*>", html, re.IGNORECASE):
        tag = form_tag.group(0)
        action_match = re.search(r'action=["\']([^"\']*)["\']', tag)
        if not action_match:
            continue
        action = unescape(action_match.group(1))
        name_match = re.search(r'name=["\']([^"\']*)["\']', tag)
        if name_match and name_match.group(1) == "signIn":
            return action
        if "/ap/signin" in action or "/ax/claim" in action:
            return action
    return None


async def _chk_shopping_amazon(email: str):
    """
    Probe Amazon's sign-in flow to check if an email is registered.

    Amazon A/B tests between /ap/signin and /ax/claim pages; both are handled.
    Rate limits: may block after repeated requests from the same IP.
    """
    show_url = "https://www.amazon.com"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    signin_url = (
        "https://www.amazon.com/ap/signin?"
        "openid.pape.max_auth_age=0"
        "&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F"
        "%3F_encoding%3DUTF8%26ref_%3Dnav_ya_signin"
        "&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
        "&openid.assoc_handle=usflex"
        "&openid.mode=checkid_setup"
        "&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
        "&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
    )

    try:
        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True, headers=headers
        ) as client:
            # 1. Load the sign-in page and extract form fields + action URL
            resp = await client.get(signin_url)

            if resp.status_code != 200:
                return (None, None, None)

            if _is_captcha(resp.text):
                return (None, None, None)

            data = _extract_form_fields(resp.text)
            if not data:
                return (None, None, None)

            data["email"] = email

            post_url = _extract_form_action(resp.text)
            if not post_url:
                return (None, None, None)
            if post_url.startswith("/"):
                post_url = "https://www.amazon.com" + post_url

            # 2. Submit the email
            resp = await client.post(post_url, data=data)

            if resp.status_code == 429:
                return (None, None, None)

            if resp.status_code not in (200, 302):
                return (None, None, None)

            if _is_captcha(resp.text):
                return (None, None, None)

            # 3. Detect outcome from the rendered page.
            # Registered: the response asks for a password.
            # Not registered: Amazon's unified-claim flow lands on
            # /ax/claim/intent ("Looks like you're new to Amazon") with a
            # form posting to /ap/register.
            text = resp.text
            final_url = str(resp.url)

            registered_signals = (
                'id="auth-password-missing-alert"' in text
                or 'id="ap_password"' in text
                or ('name="password"' in text and 'type="password"' in text)
            )
            not_registered_signals = (
                "/ax/claim/intent" in final_url
                or "Looks like you" in text and "new to Amazon" in text
                or 'action="https://www.amazon.com:443/ap/register' in text
                or 'action="https://www.amazon.com/ap/register' in text
            )

            if registered_signals:
                return (True, show_url, None)
            if not_registered_signals:
                return (False, show_url, None)
            # Ambiguous response — don't guess.
            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_shopping_vivino(email: str):
    show_url = "https://vivino.com"
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Accept': 'application/json',
        'Referer': 'https://www.vivino.com/',
        'Accept-Language': 'en-US,en;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.get("https://www.vivino.com/", headers=headers)

            payload = {
                "email": email,
                "password": "password123"
            }

            response = await client.post(
                'https://www.vivino.com/api/login',
                headers=headers,
                json=payload
            )

            if response.status_code == 429:
                return (None, None, None)

            data = response.json()
            error_msg = data.get("error", "")

            if error_msg == "The supplied email does not exist":
                return (False, show_url, None)

            if not error_msg or "password" in error_msg.lower():
                return (True, show_url, None)

            if "account has been locked" in error_msg:
                return (True, show_url, "Account is locked by Vivino")

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

import uuid
import hashlib
import base64
import secrets

def generate_pkce_challenge():
    verifier = secrets.token_urlsafe(32)
    sha256_hash = hashlib.sha256(verifier.encode('ascii')).digest()
    challenge = base64.urlsafe_b64encode(sha256_hash).decode('ascii').replace('=', '')
    return challenge

async def _chk_shopping_walmart(email: str):
    url = "https://identity.walmart.com/orchestra/idp/graphql"
    show_url = "https://walmart.com"

    uid = str(uuid.uuid4()).replace("-", "")
    trace_id = f"00-{uid[:32]}-{uid[:16]}-00"
    # Use a shorter correlation ID format seen in recent captures
    corr_id = secrets.token_urlsafe(24)
    dynamic_challenge = generate_pkce_challenge()

    payload = {
        "query": "query GetLoginOptions($input:UserOptionsInput!){getLoginOptions(input:$input){loginOptions{...LoginOptionsFragment}canUseEmailOTP phoneCollectionRequired authCode errors{...LoginOptionsErrorFragment}}}fragment LoginOptionsFragment on LoginOptions{loginId loginIdType emailId phoneNumber{number countryCode isoCountryCode}canUsePassword canUsePhoneOTP canUseEmailOTP loginPhoneLastFour maskedPhoneNumberDetails{loginPhoneLastFour countryCode isoCountryCode}loginMaskedEmailId signInPreference loginPreference lastLoginPreference hasRemainingFactors isPhoneConnected otherAccountsWithPhone loginMaskedEmailId hasPasskeyOnProfile accountDomain residencyRegion{residencyCountryCode residencyRegionCode}isIdentityMergeRequired}fragment LoginOptionsErrorFragment on IdentityLoginOptionsError{code message version}",
        "variables": {
            "input": {
                "loginId": email,
                "loginIdType": "EMAIL",
                "ssoOptions": {
                    "wasConsentCaptured": True,
                    "callbackUrl": "https://www.walmart.com/account/verifyToken",
                    "clientId": "5f3fb121-076a-45f6-9587-249f0bc160ff",
                    "scope": "openid email offline_access",
                    "state": "/account/delete-account",
                    "challenge": dynamic_challenge
                }
            }
        }
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'x-o-mart': "B2C",
        'x-o-gql-query': "query GetLoginOptions",
        'sec-ch-ua-platform': '"Android"',
        'x-o-segment': "oaoh",
        'device_profile_ref_id': "xpmjgxfheteohb199lo0r5qewtwjywqaifje",
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'x-enable-server-timing': "1",
        'sec-ch-ua-mobile': "?1",
        'x-latency-trace': "1",
        'traceparent': trace_id,
        'wm_mp': "true",
        'x-apollo-operation-name': "GetLoginOptions",
        'tenant-id': "elh9ie",
        'downlink': "10",
        'wm_qos.correlation_id': corr_id,
        'x-o-platform': "rweb",
        'x-o-platform-version': "usweb-1.244.0-11a85c27f6b1cd480b5bbfc2090ace49df92f6fc-2190302r",
        'accept-language': "en-US",
        'x-o-ccm': "server",
        'x-o-bu': "WALMART-US",
        'dpr': "2.75",
        'wm_page_url': f"https://identity.walmart.com/account/login?scope=openid%20email%20offline_access&redirect_uri=https%3A%2F%2Fwww.walmart.com%2Faccount%2FverifyToken&client_id=5f3fb121-076a-45f6-9587-249f0bc160ff&tenant_id=elh9ie&code_challenge={dynamic_challenge}&state=%2Faccount%2Fdelete-account",
        'x-o-correlation-id': corr_id,
        'origin': "https://identity.walmart.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': f"https://identity.walmart.com/account/login?scope=openid%20email%20offline_access&redirect_uri=https%3A%2F%2Fwww.walmart.com%2Faccount%2FverifyToken&client_id=5f3fb121-076a-45f6-9587-249f0bc160ff&tenant_id=elh9ie&code_challenge={dynamic_challenge}&state=%2Faccount%2Fdelete-account",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code == 412:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()
            login_data = data.get("data", {}).get("getLoginOptions", {})
            login_options = login_data.get("loginOptions", {})
            errors = login_data.get("errors", [])

            pref = login_options.get("signInPreference", "")

            if pref in ["PASSWORD", "CHOICE"]:
                if any(err.get("code") == "COMPROMISED" for err in errors):
                    return (True, None, "Account flagged as compromised")
                return (True, show_url, None)

            elif pref == "CREATE":
                return (False, show_url, None)

            return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_social_mewe(email: str):
    url = "https://mewe.com/api/v2/auth/check/user/email"
    show_url = "https://mewe.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json; charset=UTF-8",
        'sec-ch-ua-platform': '"Android"',
        'Origin': "https://mewe.com",
        'Referer': "https://mewe.com/register",
        'Priority': "u=1, i"
    }

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url, 
                content=json.dumps(payload), 
                headers=headers
            )

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code == 429:
                return (None, None, None)

            if response.status_code != 200:
                return (None, None, None)

            data = response.json()

            if data.get("exists") is True:
                return (True, show_url, None)

            elif data.get("exists") is False:
                return (False, show_url, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except httpx.ReadTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_social_pinterest(email: str):
    url = "https://www.pinterest.com/resource/ApiResource/get/"
    show_url = "https://pinterest.com"

    data_str = json.dumps({
        "options": {
            "url": "/v3/register/exists/",
            "data": {"email": email}
        },
        "context": {}
    }, separators=(',', ':'))

    params = {
        'source_url': "/signup/step1/",
        'data': data_str,
        '_': str(int(time.time() * 1000))
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/javascript, */*, q=0.01",
        'Accept-Language': "en-US,en;q=0.9",
        'x-pinterest-pws-handler': "www/signup/[step].js",
        'x-app-version': "2503cde",
        'x-requested-with': "XMLHttpRequest",
        'x-pinterest-source-url': "/signup/step1/",
        'x-pinterest-appstate': "active",
        'origin': "https://www.pinterest.com",
        'referer': "https://www.pinterest.com/",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'priority': "u=1, i"
    }

    try:

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 200:
                resp_json = response.json()
                resource_response = resp_json.get("resource_response", {})

                exists = resource_response.get("data")

                if exists is True:
                    return (True, show_url, None)
                elif exists is False:
                    return (False, show_url, None)

                return (None, None, None)

            if response.status_code == 403:
                return (None, None, None)

            if response.status_code == 429:
                return (None, None, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_social_plurk(email: str):
    url = "https://www.plurk.com/Users/isEmailFound"
    show_url = "https://www.plurk.com"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.plurk.com",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                headers=headers,
                data={"email": email}
            )

        if response.status_code == 403:
            return (None, None, None)

        if response.status_code == 429:
            return (None, None, None)

        if response.status_code != 200:
            return (None, None, None)

        text = response.text.strip()

        if text == "True":
            return (True, show_url, None)

        if text == "False":
            return (False, show_url, None)

        return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)

    except httpx.ReadTimeout:
        return (None, None, None)

    except Exception as e:
        return (None, None, None)

async def _chk_social_x_twitter(email):
    url = "https://api.x.com/i/users/email_available.json"
    show_url = "https://x.com"
    params = {"email": email}
    headers = {
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        "accept-encoding": "gzip, deflate, br, zstd",
        "sec-ch-ua-platform": "\"Android\"",
        "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        "x-twitter-client-language": "en",
        "sec-ch-ua-mobile": "?1",
        "x-twitter-active-user": "yes",
        "origin": "https://x.com",
        "priority": "u=1, i"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                return (None, None, None)

            data = response.json()
            taken_bool = data.get("taken")

            if taken_bool is True:
                return (True, show_url, None)
            elif taken_bool is False:
                return (False, show_url, None)
            else:
                return (None, None, None)

        except Exception as e:
            return (None, None, None)

async def _chk_sports_espn(email: str):
    url = "https://registerdisney.go.com/jgc/v8/client/ESPN-ONESITE.WEB-PROD/guest-flow"
    show_url = "https://espn.com"
    params = {
        'langPref': "en",
        'feature': "no-password-reuse"
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Content-Type': "application/json",
        'origin': "https://cdn.registerdisney.go.com",
        'referer': "https://cdn.registerdisney.go.com/",
        'accept-language': "en-US,en;q=0.9",
    }
    payload = {"email": email}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                params=params,
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                flow = data.get("guestFlow")

                if flow == "LOGIN_FLOW":
                    return (True, show_url, None)
                elif flow == "REGISTRATION_FLOW":
                    return (False, show_url, None)

                return (None, None, None)

            return (None, None, None)

    except httpx.TimeoutException:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_sports_nba(email: str):
    show_url = "https://www.nba.com"
    url = "https://identity.nba.com/api/v1/profile/registrationStatus"

    payload = {
        "email": email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'x-client-platform': "web",
        'origin': "https://www.nba.com",
        'referer': "https://www.nba.com/",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            status = response.status_code

            if status == 403:
                return (None, None, None)

            if status == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("data", {}).get("isFull") is True:
                    return (True, show_url, None)

            if status == 400:
                data = response.json()
                if "INVALID_PROFILE_STATUS" in data.get("errorCodes", []) or "Profile not found" in data.get("data", {}).get("message", ""):
                    return (False, show_url, None)

            if status == 429:
                return (None, None, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_travel_emirates(email: str):
    show_url = "https://emirates.com"
    url = "https://www.emirates.com/service/ekl/validate-email"

    params = {
        'data': "null"
    }

    payload = {
        "emailAddress": email
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145\", \"Chromium\";v=\"145"',
        'sec-ch-ua-mobile': "?1",
        'origin': "https://www.emirates.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, params=params, content=json.dumps(payload), headers=headers)
            status = response.status_code

            if status == 403:
                return (None, None, None)

            if status == 200:
                data = response.json()
                body = data.get("body", {})
                errors = body.get("errors", [])

                if any(err.get("code") == "program.member.EmailExistsForAnotherMember" for err in errors):
                    return (True, show_url, None)

                if data.get("status") is True:
                    return (False, show_url, None)

                return (False, show_url, None)

            if status == 429:
                return (None, None, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)

async def _chk_travel_komoot(email: str):
    show_url = "https://www.komoot.com"
    url = "https://www.komoot.com/v1/signin"

    payload = {
        "email": email,
        "reason": "header",
        "new_tab": False
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': "?1",
        'origin': "https://www.komoot.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.komoot.com/signin?referrer=www.google.com&reason=header",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            status = response.status_code

            if status == 403:
                return (None, None, None)

            if status == 200:
                data = response.json()
                response_type = data.get("type")

                if response_type == "login":
                    return (True, show_url, None)

                if response_type == "register":
                    return (False, show_url, None)

            if status == 429:
                return (None, None, None)

            return (None, None, None)

    except httpx.ConnectTimeout:
        return (None, None, None)
    except Exception as e:
        return (None, None, None)


# --- holehe-derived checks (not present in user-scanner upstream) ---

async def _chk_security_lastpass(email):
    show_url = "https://lastpass.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://lastpass.com/",
    }
    params = {"check": "avail", "skipcontent": "1", "mistype": "1", "username": email}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get("https://lastpass.com/create_account.php", params=params, headers=headers)
        body = r.text.strip()
        if body == "no":
            return (True, show_url, None)
        if body in ("ok", "emailinvalid"):
            return (False, show_url, None)
        return (None, None, None)
    except Exception:
        return (None, None, None)


async def _chk_jobs_seoclerks(email):
    import random
    import string
    show_url = "https://seoclerks.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.seoclerks.com",
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get("https://www.seoclerks.com", headers=headers)
            try:
                token = r.text.split('token" value="')[1].split('"')[0]
                cr = r.text.split('__cr" value="')[1].split('"')[0]
            except (IndexError, AttributeError):
                return (None, None, None)

            rand = lambda n: "".join(random.choice(string.ascii_lowercase) for _ in range(n))
            data = {
                "token": token, "__cr": cr, "fsub": "1", "droplet": "",
                "user_username": rand(6), "user_email": email,
                "user_password": rand(8), "confirm_password": rand(8),
            }
            r2 = await client.post("https://www.seoclerks.com/signup/check", headers=headers, data=data)
        try:
            msg = r2.json().get("message", "")
        except Exception:
            return (None, None, None)
        if "already taken" in msg:
            return (True, show_url, None)
        return (False, show_url, None)
    except Exception:
        return (None, None, None)


async def _chk_dev_teamtreehouse(email):
    show_url = "https://teamtreehouse.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://teamtreehouse.com/subscribe/new?trial=yes",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://teamtreehouse.com",
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get("https://teamtreehouse.com/subscribe/new?trial=yes", headers=headers)
            m = re.search(r'name="csrf-token"\s+content="([^"]+)"', r.text)
            if not m:
                return (None, None, None)
            headers["X-CSRF-Token"] = m.group(1)
            r2 = await client.post(
                "https://teamtreehouse.com/account/email_address",
                headers=headers, data={"email": email},
            )
        body = r2.text
        if "that email address is taken." in body:
            return (True, show_url, None)
        if body.strip() == '{"success":true}':
            return (False, show_url, None)
        return (None, None, None)
    except Exception:
        return (None, None, None)


SERVICES = [
    ('adult', 'Babestation', _chk_adult_babestation),
    ('adult', 'Fapfolder', _chk_adult_fapfolder),
    ('adult', 'Flirtbate', _chk_adult_flirtbate),
    ('adult', 'Lovescape', _chk_adult_lovescape),
    ('adult', 'Made Porn', _chk_adult_made_porn),
    ('adult', 'Xnxx', _chk_adult_xnxx),
    ('adult', 'Xvideos', _chk_adult_xvideos),
    ('community', 'Nextdoor', _chk_community_nextdoor),
    ('creator', 'Adobe', _chk_creator_adobe),
    ('creator', 'Flickr', _chk_creator_flickr),
    ('dev', 'Codecademy', _chk_dev_codecademy),
    ('dev', 'Codepen', _chk_dev_codepen),
    ('dev', 'Codewars', _chk_dev_codewars),
    ('dev', 'Devrant', _chk_dev_devrant),
    ('dev', 'Envato', _chk_dev_envato),
    ('dev', 'Github', _chk_dev_github),
    ('dev', 'Hackerone', _chk_dev_hackerone),
    ('dev', 'Hackthebox', _chk_dev_hackthebox),
    ('dev', 'Howtogeek', _chk_dev_howtogeek),
    ('dev', 'Huggingface', _chk_dev_huggingface),
    ('dev', 'Leetcode', _chk_dev_leetcode),
    ('dev', 'Replit', _chk_dev_replit),
    ('dev', 'Teamtreehouse', _chk_dev_teamtreehouse),
    ('dev', 'Wix', _chk_dev_wix),
    ('dev', 'Wondershare', _chk_dev_wondershare),
    ('dev', 'Xda', _chk_dev_xda),
    ('entertainment', 'Justwatch', _chk_entertainment_justwatch),
    ('entertainment', 'Letterboxd', _chk_entertainment_letterboxd),
    ('entertainment', 'Myanimelist', _chk_entertainment_myanimelist),
    ('entertainment', 'Stremio', _chk_entertainment_stremio),
    ('fitness', 'Fitnessblender', _chk_fitness_fitnessblender),
    ('fitness', 'Myfitnesspal', _chk_fitness_myfitnesspal),
    ('gaming', 'Addictinggames', _chk_gaming_addictinggames),
    ('gaming', 'Chess Com', _chk_gaming_chess_com),
    ('gaming', 'Crazygames', _chk_gaming_crazygames),
    ('hosting', 'Neocities', _chk_hosting_neocities),
    ('jobs', 'Freelancer', _chk_jobs_freelancer),
    ('jobs', 'Seoclerks', _chk_jobs_seoclerks),
    ('learning', 'Alison', _chk_learning_alison),
    ('learning', 'Coursera', _chk_learning_coursera),
    ('learning', 'Duolingo', _chk_learning_duolingo),
    ('learning', 'Vedantu', _chk_learning_vedantu),
    ('music', 'Deezer', _chk_music_deezer),
    ('music', 'Gaana', _chk_music_gaana),
    ('music', 'Mixcloud', _chk_music_mixcloud),
    ('music', 'Spotify', _chk_music_spotify),
    ('news', 'Bbc', _chk_news_bbc),
    ('news', 'Cnn', _chk_news_cnn),
    ('news', 'Foxnews', _chk_news_foxnews),
    ('news', 'Indiatimes', _chk_news_indiatimes),
    ('news', 'Nytimes', _chk_news_nytimes),
    ('other', 'Anydo', _chk_other_anydo),
    ('other', 'Eventbrite', _chk_other_eventbrite),
    ('other', 'Moz', _chk_other_moz),
    ('other', 'Office365', _chk_other_office365),
    ('shopping', 'Amazon', _chk_shopping_amazon),
    ('shopping', 'Vivino', _chk_shopping_vivino),
    ('shopping', 'Walmart', _chk_shopping_walmart),
    ('social', 'Mewe', _chk_social_mewe),
    ('social', 'Pinterest', _chk_social_pinterest),
    ('social', 'Plurk', _chk_social_plurk),
    ('social', 'X (Twitter)', _chk_social_x_twitter),
    ('security', 'Lastpass', _chk_security_lastpass),
    ('sports', 'Espn', _chk_sports_espn),
    ('sports', 'Nba', _chk_sports_nba),
    ('travel', 'Emirates', _chk_travel_emirates),
    ('travel', 'Komoot', _chk_travel_komoot),
]

async def _safe(sem, cat, name, fn, email):
    async with sem:
        try:
            res = await asyncio.wait_for(fn(email), timeout=PER_CHECK_TIMEOUT)
            if isinstance(res, tuple):
                if len(res) == 3:
                    return cat, name, res
                if len(res) == 2:
                    return cat, name, (res[0], res[1], None)
            return cat, name, (None, None, None)
        except Exception:
            return cat, name, (None, None, None)


def _value(hit, url, extra):
    parts = []
    if hit is True:
        head = "registered"
        if url:
            head += f" ({url})"
        parts.append(head)
    elif hit is False:
        parts.append("not registered")
    else:
        parts.append("error")
    if extra:
        parts.append(str(extra))
    return " — ".join(parts)


async def run(session, target):
    if "@" not in target:
        return 1, []

    sem = asyncio.Semaphore(CONCURRENCY)
    results = await asyncio.gather(
        *(_safe(sem, cat, name, fn, target) for cat, name, fn in SERVICES)
    )

    findings = []
    for cat, name, (hit, url, extra) in results:
        if hit is not True:
            continue
        findings.append({
            "label": name,
            "value": _value(hit, url, extra),
            "source": PARENT,
            "group": cat.title(),
        })
    return 0, findings
