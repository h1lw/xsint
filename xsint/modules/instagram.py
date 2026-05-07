import asyncio
import json
import os
import random
import re
import uuid

import aiohttp
from yarl import URL

from xsint.config import get_config

INFO = {
    "free": ["username"],
    "returns": ["recovery methods"],
    "themes": {"Instagram": {"color": "magenta", "icon": "IG"}},
}


class InstagramRecoveryWorkflow:
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    START_APPID = "com.bloks.www.caa.ar.search.async"
    START_APPID_FALLBACK = "com.bloks.www.caa.ar.search"
    AUTH_METHOD_APPID = "com.bloks.www.caa.ar.auth_method"
    AUTH_METHOD_ASYNC_APPID = "com.bloks.www.caa.ar.auth_method.async"
    AUTH_CONFIRM_APPID = "com.bloks.www.caa.ar.authentication_confirmation"
    AUTH_CONFIRM_ASYNC_APPID = "com.bloks.www.caa.ar.authentication_confirmation.async"
    INITIATE_VIEW_APPID = "com.bloks.www.caa.ar.initiate_view"
    PF_AUTH_FLOW_ASYNC_APPID = "com.bloks.www.fx.pf.auth_flow.async"
    UHL_APPID = "com.bloks.www.caa.ar.uhl.nav.async"
    UHL_REQ_APPID = "com.bloks.www.caa.ar.uhl.nav"
    UHL_API_ID = "1217981644879628"
    UHL_BLOKS_VER = "89260ab7c284bc53283ddb1870bf272c0c189a1a497762c002b28865952b5415"
    MAX_STEPS = 10
    TOKEN_MIN_LEN = 128

    APPID_REWRITE = {
        "com.bloks.www.caa.ar.uhl.nav": UHL_APPID,
    }

    BLOCKED = {"com.bloks.www.caa.ar.submit_code.async"}
    IGNORED_APPID_PREFIXES = (
        "com.bloks.www.bloks.caa.reg.",
        "com.bloks.www.bloks.caa.login.async.",
    )

    APPID_RE = re.compile(r"com\.bloks\.www\.[a-zA-Z0-9_.]+")
    ASYNC_ACTION_RE = re.compile(r'AsyncActionWithDataManifestV2\s*,\s*"([^"]+)"')
    PUSH_APPID_RE = re.compile(r'"app_id"\s*,\s*"([^"]+)"')
    ASYNC_ACTION_ESC_RE = re.compile(r'AsyncActionWithDataManifestV2\s*,\s*\\"([^"\\]+)\\"')
    PUSH_APPID_ESC_RE = re.compile(r'\\"app_id\\"\s*,\s*\\"([^"\\]+)\\"')
    CONTEXT_TOKEN_RE = re.compile(r'context_data\\?"\s*:\s*\\?"([^"\\]*\|arm)')
    TOKEN_RE = re.compile(r"[A-Za-z0-9_+/=-]{20,}\|arm")
    METHOD_TEXT_RE = re.compile(r'"(?:text|title|subtitle|value|label)":"([^"]{3,220})"')
    EMAIL_RE = re.compile(r"[a-zA-Z0-9][\w.*]*\*+[\w.*]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    PHONE_RE = re.compile(r"[+]\d[\d\s./*-]*\*[\d\s./*-]*\d+")
    UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")

    def __init__(self, username, proxy_url="", base_session=None):
        self.username = username
        self.proxy_url = proxy_url
        self.base_session = base_session
        self.use_proxy = bool(proxy_url)
        self.using_shared_connector = False
        self.session = None

        self.device_id = str(uuid.uuid4()).upper()
        self.machine_id = ""
        self.lsd = ""
        self.token = ""
        self.search_async_text_input_id = f"{uuid.uuid4().hex[:5]}:101"

        self.web_sessionid = os.getenv("IG_WEB_SESSIONID", "")
        self.web_ds_user_id = os.getenv("IG_WEB_DS_USER_ID", "")
        self.delay_min = float(os.getenv("XSINT_IG_DELAY_MIN", "0.2"))
        self.delay_max = float(os.getenv("XSINT_IG_DELAY_MAX", "0.7"))
        self.allow_direct_fallback = os.getenv("XSINT_IG_PROXY_FALLBACK", "").lower() in {"1", "true", "yes", "on"}
        self.debug = os.getenv("XSINT_IG_DEBUG", "").lower() in {"1", "true", "yes", "on"}

    def _debug(self, msg):
        if self.debug:
            print(f"[IG] {msg}")

    async def open(self):
        if self.session and not self.session.closed:
            return

        headers = {
            "Host": "www.instagram.com",
            "User-Agent": self.USER_AGENT,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.instagram.com",
            "Referer": "https://www.instagram.com/accounts/password/reset/",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-IG-App-ID": self.UHL_API_ID,
        }

        connector = None
        connector_owner = True
        if not self.use_proxy and self.base_session is not None:
            base_connector = getattr(self.base_session, "connector", None)
            if base_connector is not None and not base_connector.closed:
                connector = base_connector
                connector_owner = False
                self.using_shared_connector = True

        if connector is None:
            connector = aiohttp.TCPConnector(ssl=False, force_close=True)
            self.using_shared_connector = False

        self.session = aiohttp.ClientSession(
            connector=connector,
            connector_owner=connector_owner,
            timeout=aiohttp.ClientTimeout(total=30),
            headers=headers,
            cookie_jar=aiohttp.CookieJar(unsafe=True),
        )

        base = URL("https://www.instagram.com")
        cookies = {"ig_did": self.device_id}
        if self.web_sessionid:
            cookies["sessionid"] = self.web_sessionid
        if self.web_ds_user_id:
            cookies["ds_user_id"] = self.web_ds_user_id
        self.session.cookie_jar.update_cookies(cookies, base)

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def _cookie(self, name):
        if not self.session:
            return ""
        cookies = self.session.cookie_jar.filter_cookies(URL("https://www.instagram.com/"))
        cookie = cookies.get(name)
        return cookie.value if cookie else ""

    def _set_cookie(self, name, value):
        if self.session:
            self.session.cookie_jar.update_cookies({name: value}, URL("https://www.instagram.com/"))

    async def _request(self, method, url, **kwargs):
        await self.open()
        request_proxy = self.proxy_url if (self.use_proxy and not self.using_shared_connector) else None

        for attempt in range(3):
            try:
                async with self.session.request(method, url, proxy=request_proxy, **kwargs) as resp:
                    return resp.status, await resp.text(errors="replace")
            except (aiohttp.ClientProxyConnectionError, aiohttp.ClientConnectorError) as e:
                self._debug(f"request error ({type(e).__name__}) for {url}")
                if request_proxy and self.allow_direct_fallback:
                    request_proxy = None
                    self.use_proxy = False
                    continue
                return 0, ""
            except aiohttp.ClientOSError as e:
                self._debug(f"request error ({type(e).__name__}) for {url}")
                if request_proxy and self.allow_direct_fallback:
                    request_proxy = None
                    self.use_proxy = False
                    continue
                if attempt < 2:
                    await self.close()
                    self.session = None
                    await self.open()
                    continue
                return 0, ""
            except Exception as e:
                self._debug(f"request exception ({type(e).__name__}) for {url}: {e}")
                return 0, ""
        return 0, ""

    @classmethod
    def _parse_token(cls, text):
        decoded = text.replace("for (;;);", "").replace("\\/", "/").replace('\\"', '"')
        context_tokens = cls.CONTEXT_TOKEN_RE.findall(decoded)
        if context_tokens:
            return max(context_tokens, key=len)
        tokens = cls.TOKEN_RE.findall(decoded)
        return max(tokens, key=len) if tokens else ""

    @classmethod
    def _parse_methods(cls, text):
        decoded = text.encode("utf-8", "replace").decode("unicode_escape", "replace")
        chunks = cls.METHOD_TEXT_RE.findall(decoded)
        methods = [("EMAIL", email) for chunk in chunks for email in cls.EMAIL_RE.findall(chunk)]
        methods += [("SMS", phone.strip()) for chunk in chunks for phone in cls.PHONE_RE.findall(chunk)]
        return list(dict.fromkeys(methods))

    def _candidate_appids(self, text, current):
        decoded = text.replace('\\"', '"')
        # Prefer concrete push-screen targets, then async action manifests.
        push_ids = self.PUSH_APPID_RE.findall(decoded)
        async_ids = self.ASYNC_ACTION_RE.findall(decoded)
        if not push_ids and not async_ids:
            # Fallback for still-escaped payloads.
            push_ids = self.PUSH_APPID_ESC_RE.findall(text)
            async_ids = self.ASYNC_ACTION_ESC_RE.findall(text)

        raw = push_ids + async_ids
        if not raw:
            # Last-resort fallback for unknown response shapes.
            raw = self.APPID_RE.findall(decoded)
        raw = [self.APPID_REWRITE.get(appid, appid) for appid in raw]
        out = []
        seen = set()
        for appid in raw:
            if (
                appid in seen
                or appid == current
                or appid == self.START_APPID_FALLBACK
                or appid in self.BLOCKED
                or any(appid.startswith(prefix) for prefix in self.IGNORED_APPID_PREFIXES)
            ):
                continue
            seen.add(appid)
            out.append(appid)
        return out

    def _choose_next_appid(self, current, candidates):
        if not candidates:
            return ""

        if current == self.START_APPID:
            allowed = {
                self.AUTH_CONFIRM_APPID,
                self.AUTH_CONFIRM_ASYNC_APPID,
                self.INITIATE_VIEW_APPID,
                self.AUTH_METHOD_APPID,
                self.AUTH_METHOD_ASYNC_APPID,
                self.PF_AUTH_FLOW_ASYNC_APPID,
                self.UHL_APPID,
            }
            for appid in candidates:
                if appid in allowed:
                    return appid
            preferred = ()
        elif current == self.AUTH_METHOD_APPID:
            preferred = (
                self.AUTH_METHOD_ASYNC_APPID,
                self.INITIATE_VIEW_APPID,
                self.AUTH_CONFIRM_APPID,
                self.AUTH_CONFIRM_ASYNC_APPID,
                self.UHL_APPID,
            )
        elif current == self.AUTH_METHOD_ASYNC_APPID:
            preferred = (
                self.INITIATE_VIEW_APPID,
                self.AUTH_CONFIRM_APPID,
                self.AUTH_CONFIRM_ASYNC_APPID,
                self.UHL_APPID,
            )
        elif current == self.PF_AUTH_FLOW_ASYNC_APPID:
            preferred = (
                self.AUTH_METHOD_APPID,
                self.AUTH_METHOD_ASYNC_APPID,
                self.INITIATE_VIEW_APPID,
                self.AUTH_CONFIRM_APPID,
                self.AUTH_CONFIRM_ASYNC_APPID,
                self.UHL_APPID,
            )
        elif current == self.INITIATE_VIEW_APPID:
            preferred = (
                self.AUTH_CONFIRM_APPID,
                self.AUTH_CONFIRM_ASYNC_APPID,
                self.AUTH_METHOD_APPID,
                self.AUTH_METHOD_ASYNC_APPID,
                self.UHL_APPID,
            )
        else:
            preferred = ()

        for appid in preferred:
            if appid in candidates:
                return appid
        return candidates[0]

    def _extract_manifest_section(self, text, appid):
        decoded = text.replace('\\"', '"')
        pattern = rf'AsyncActionWithDataManifestV2\s*,\s*"{re.escape(appid)}"'
        match = re.search(pattern, decoded)
        if not match:
            return decoded
        return decoded[match.start() : match.start() + 140000]

    def _dynamic_params(self, text, appid):
        params = {}
        if not text:
            return params

        section = self._extract_manifest_section(text, appid)
        token = self._parse_token(section)
        if token:
            params["context_data"] = token

        if match := self.UUID_RE.search(section):
            params["waterfall_id"] = match.group(0)

        if match := re.search(r'"INTERNAL_INFRA_screen_id"\s*:\s*"([^"]*)"', section):
            params["screen_id"] = match.group(1)

        if appid == self.AUTH_METHOD_ASYNC_APPID:
            if match := re.search(r'"auth_method"\s*:\s*"(phone|email|password)"', section):
                params["auth_method"] = match.group(1)
            if match := re.search(r'auth_method_async_params[^A-Za-z0-9+/_=-]+([A-Za-z0-9+/_=-]{20,})', section):
                params["auth_method_async_params"] = match.group(1)

        return params

    def _payload(self, appid, app_type, parsed):
        parsed = parsed or {}

        if appid == self.START_APPID:
            return {
                "server_params": {
                    "event_request_id": str(uuid.uuid4()),
                    "INTERNAL__latency_qpl_marker_id": 36707139,
                    "INTERNAL__latency_qpl_instance_id": str(int(uuid.uuid4().int % 10**12)),
                    "device_id": self.machine_id or self.device_id,
                    "family_device_id": None,
                    "waterfall_id": str(uuid.uuid4()),
                    "offline_experiment_group": None,
                    "layered_homepage_experiment_group": None,
                    "is_platform_login": 0,
                    "is_from_logged_in_switcher": 0,
                    "is_from_logged_out": 0,
                    "access_flow_version": "pre_mt_behavior",
                    "login_surface": "unknown",
                    "context_data": self.token or "",
                },
                "client_input_params": {
                    "zero_balance_state": None,
                    "search_query": self.username,
                    "fetched_email_list": [],
                    "fetched_email_token_list": {},
                    "sso_accounts_auth_data": [],
                    "sfdid": "",
                    "text_input_id": self.search_async_text_input_id,
                    "encrypted_msisdn": "",
                    "headers_infra_flow_id": "",
                    "was_headers_prefill_available": 0,
                    "was_headers_prefill_used": 0,
                    "ig_oauth_token": [],
                    "android_build_type": "",
                    "is_whatsapp_installed": 0,
                    "device_network_info": None,
                    "accounts_list": [],
                    "is_oauth_without_permission": 0,
                    "search_screen_type": "email_or_username",
                    "ig_vetted_device_nonce": "",
                    "gms_incoming_call_retriever_eligibility": "client_not_supported",
                    "auth_secure_device_id": "",
                    "cloud_trust_token": None,
                    "network_bssid": None,
                    "lois_settings": {"lois_token": ""},
                    "aac": "",
                },
            }

        if appid == self.AUTH_METHOD_APPID:
            return {
                "server_params": {
                    "device_id": self.machine_id or self.device_id,
                    "waterfall_id": parsed.get("waterfall_id") or str(uuid.uuid4()),
                    "is_platform_login": 0,
                    "is_from_logged_out": 0,
                    "access_flow_version": "pre_mt_behavior",
                    "context_data": parsed.get("context_data") or self.token or "",
                    "back_nav_action": "BACK",
                    "INTERNAL_INFRA_screen_id": parsed.get("screen_id", ""),
                },
                "client_input_params": {
                    "lois_settings": {"lois_token": ""},
                    "zero_balance_state": "",
                    "aac": "",
                },
            }

        if appid == self.AUTH_METHOD_ASYNC_APPID:
            server_params = {
                "device_id": self.machine_id or self.device_id,
                "auth_method": parsed.get("auth_method", "phone"),
                "is_auth_method_rejected": 1,
                "context_data": parsed.get("context_data") or self.token or "",
                "INTERNAL__latency_qpl_marker_id": 36707139,
                "INTERNAL__latency_qpl_instance_id": str(int(uuid.uuid4().int % 10**12)),
                "family_device_id": None,
                "waterfall_id": parsed.get("waterfall_id") or str(uuid.uuid4()),
                "offline_experiment_group": None,
                "layered_homepage_experiment_group": None,
                "is_platform_login": 0,
                "is_from_logged_in_switcher": 0,
                "is_from_logged_out": 0,
                "access_flow_version": "pre_mt_behavior",
                "login_surface": "unknown",
            }
            if parsed.get("auth_method_async_params"):
                server_params["auth_method_async_params"] = parsed["auth_method_async_params"]

            return {
                "server_params": server_params,
                "client_input_params": {
                    "zero_balance_state": "",
                    "android_build_type": "",
                    "cloud_trust_token": None,
                    "network_bssid": None,
                    "lois_settings": {"lois_token": ""},
                    "aac": "",
                },
            }

        if appid == self.AUTH_CONFIRM_APPID:
            return {
                "server_params": {
                    "device_id": self.machine_id or self.device_id,
                    "waterfall_id": parsed.get("waterfall_id") or str(uuid.uuid4()),
                    "is_platform_login": 0,
                    "is_from_logged_out": 0,
                    "access_flow_version": "pre_mt_behavior",
                    "context_data": parsed.get("context_data") or self.token or "",
                    "back_nav_action": "BACK",
                    "INTERNAL_INFRA_screen_id": parsed.get("screen_id", ""),
                },
                "client_input_params": {
                    "lois_settings": {"lois_token": ""},
                    "aac": "",
                },
            }

        if appid == self.AUTH_CONFIRM_ASYNC_APPID:
            return {
                "server_params": {
                    "device_id": self.machine_id or self.device_id,
                    "event_request_id": str(uuid.uuid4()),
                    "is_auth_method_rejected": 1,
                    "INTERNAL__latency_qpl_marker_id": 36707139,
                    "INTERNAL__latency_qpl_instance_id": str(int(uuid.uuid4().int % 10**12)),
                    "access_flow_version": "pre_mt_behavior",
                    "context_data": parsed.get("context_data") or self.token or "",
                },
                "client_input_params": {"cloud_trust_token": None, "lois_settings": {"lois_token": ""}},
            }

        if appid == self.INITIATE_VIEW_APPID:
            return {
                "server_params": {
                    "device_id": self.machine_id or self.device_id,
                    "waterfall_id": parsed.get("waterfall_id") or str(uuid.uuid4()),
                    "is_platform_login": 0,
                    "is_from_logged_out": 0,
                    "access_flow_version": "pre_mt_behavior",
                    "context_data": parsed.get("context_data") or self.token or "",
                    "back_nav_action": "BACK",
                    "INTERNAL_INFRA_screen_id": parsed.get("screen_id", ""),
                },
                "client_input_params": {
                    "lois_settings": {"lois_token": ""},
                    "machine_id": self.machine_id,
                    "zero_balance_state": "",
                    "aac": "",
                },
            }

        server_params = {
            "device_id": self.machine_id or self.device_id,
            "event_request_id": str(uuid.uuid4()),
            "waterfall_id": parsed.get("waterfall_id") or str(uuid.uuid4()),
            "access_flow_version": "pre_mt_behavior",
            "context_data": parsed.get("context_data") or self.token or "",
            "is_platform_login": 0,
            "is_from_logged_out": 0,
            "is_from_logged_in_switcher": 0,
        }
        client_params = {
            "search_query": self.username,
            "lois_settings": {"lois_token": ""},
            "zero_balance_state": "",
            "aac": "",
        }
        if app_type == "app":
            server_params["back_nav_action"] = "BACK"
            server_params["INTERNAL_INFRA_screen_id"] = parsed.get("screen_id", "")
            client_params["machine_id"] = self.machine_id

        return {"server_params": server_params, "client_input_params": client_params}

    async def _post(self, appid, payload, app_type):
        if self.delay_max > 0:
            await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))

        if appid == self.UHL_APPID:
            headers = {
                "X-CSRFToken": self._cookie("csrftoken"),
                "X-Ig-App-Id": self.UHL_API_ID,
                "X-Bloks-Version-Id": self.UHL_BLOKS_VER,
                "X-Ig-Device-Id": self.device_id,
                "X-Fb-Friendly-Name": "api",
                "X-Requested-With": "XMLHttpRequest",
            }
            signed = {
                "params": json.dumps(payload, separators=(",", ":")),
                "bloks_versioning_id": self.UHL_BLOKS_VER,
                "bk_client_context": '{"styles_id":"instagram","pixel_ratio":3.0}',
            }
            return await self._request(
                "POST",
                f"https://www.instagram.com/api/v1/bloks/async_action/{appid}/",
                headers=headers,
                data={"signed_body": "SIGNATURE." + json.dumps(signed, separators=(",", ":"))},
            )

        data = {
            "__a": "1",
            "__hs": "",
            "__comet_req": "7",
            "lsd": self.lsd,
            "jazoest": "22339",
            "__crn": "comet.igweb.PolarisWebBloksAccountRecoveryRoute",
            "params": json.dumps({"params": json.dumps(payload, separators=(",", ":"))}),
        }
        params = {
            "appid": self.UHL_REQ_APPID if "uhl.nav" in appid else appid,
            "type": "app" if "uhl.nav" in appid else app_type,
            "__bkv": "549e3ff69ef67a13c41791a62b2c14e2a0979de8af853baac859e53cd47312a8",
        }
        headers = {"Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors"}
        return await self._request(
            "POST",
            "https://www.instagram.com/async/wbloks/fetch/",
            params=params,
            data=data,
            headers=headers,
        )

    async def _search(self):
        status, text = await self._post(self.START_APPID, self._payload(self.START_APPID, "action", None), "action")
        if status != 200:
            self._debug(f"search step {self.START_APPID} failed status={status}")
            return "", ""

        token = self._parse_token(text)
        if token and len(token) >= self.TOKEN_MIN_LEN:
            self.token = token

        candidates = self._candidate_appids(text, self.START_APPID)
        next_appid = self._choose_next_appid(self.START_APPID, candidates)
        if not next_appid:
            next_appid = self.AUTH_METHOD_APPID
            self._debug(f"search step {self.START_APPID}: forcing fallback next={next_appid}")

        self._debug(
            f"search step {self.START_APPID} -> next={next_appid or '-'} "
            f"token_len={len(token) if token else 0} candidates={candidates}"
        )
        return next_appid, text

    async def _direct_initiate_view(self, prev_text):
        if not self.token or len(self.token) < self.TOKEN_MIN_LEN:
            return None

        parsed = self._dynamic_params(prev_text, self.INITIATE_VIEW_APPID) if prev_text else {}
        payload = self._payload(self.INITIATE_VIEW_APPID, "app", parsed)
        status, text = await self._post(self.INITIATE_VIEW_APPID, payload, "app")
        self._debug(f"direct step: {self.INITIATE_VIEW_APPID} status={status}")
        if status != 200 or not text:
            return None

        token = self._parse_token(text)
        if token and len(token) >= self.TOKEN_MIN_LEN:
            self.token = token

        methods = self._parse_methods(text)
        candidates = self._candidate_appids(text, self.INITIATE_VIEW_APPID)
        next_appid = self._choose_next_appid(self.INITIATE_VIEW_APPID, candidates)
        self._debug(
            f"direct step: next from {self.INITIATE_VIEW_APPID}: {candidates} -> {next_appid or '-'}"
        )
        return text, methods, next_appid

    async def run(self):
        status, text = await self._request(
            "GET",
            "https://www.instagram.com/accounts/password/reset/",
            headers={"Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document"},
        )
        if status != 200:
            return []

        datr = self._cookie("datr")
        machine_id_match = re.search(r'"machine_id":"([^"]+)"', text)
        lsd_match = re.search(r'\["LSD",\[\],\{"token":"(.*?)"\}', text)
        if not datr or not machine_id_match or not lsd_match:
            return []

        self.machine_id = machine_id_match.group(1)
        self.lsd = lsd_match.group(1)
        self._set_cookie("mid", self.machine_id)
        if not self._cookie("csrftoken"):
            self._set_cookie("csrftoken", self.lsd)

        appid, prev_text = await self._search()
        methods = []
        seen = set()
        steps = 0

        direct = await self._direct_initiate_view(prev_text)
        if direct:
            prev_text, direct_methods, appid = direct
            methods.extend(direct_methods)
            seen.add(self.INITIATE_VIEW_APPID)
            steps = 1

        while appid and steps < self.MAX_STEPS:
            if appid in seen or appid in self.BLOCKED:
                break
            seen.add(appid)
            steps += 1
            self._debug(f"step {steps}: running {appid}")

            app_type = "action" if appid.endswith(".async") else "app"
            parsed = self._dynamic_params(prev_text, appid) if prev_text else {}
            payload = self._payload(appid, app_type, parsed)
            status, text = await self._post(appid, payload, app_type)
            if status == 0 or not text:
                self._debug(f"step {steps}: request failed for {appid} (status={status})")
                break

            token = self._parse_token(text)
            if token and len(token) >= self.TOKEN_MIN_LEN:
                self.token = token

            methods.extend(self._parse_methods(text))

            candidates = self._candidate_appids(text, appid)
            next_appid = self._choose_next_appid(appid, candidates)
            self._debug(f"step {steps}: next candidates from {appid}: {candidates}")

            prev_text = text
            appid = next_appid

        return list(dict.fromkeys(methods))


async def _run_workflow_once(target, proxy_url, base_session, use_base_session=True):
    flow = InstagramRecoveryWorkflow(
        target,
        proxy_url=proxy_url,
        base_session=base_session if use_base_session else None,
    )
    await flow.open()
    try:
        return await flow.run()
    finally:
        await flow.close()


async def run(session, target):
    configured_proxy = get_config().get("proxy")
    allow_direct_fallback = os.getenv("XSINT_IG_PROXY_FALLBACK", "").lower() in {"1", "true", "yes", "on"}
    methods = await _run_workflow_once(target, configured_proxy, session, use_base_session=True)

    if not methods and configured_proxy and allow_direct_fallback:
        methods = await _run_workflow_once(target, "", session, use_base_session=False)

    if not methods:
        return 0, []

    rows = [{"label": "Recovery options", "value": str(len(methods)), "source": "Instagram", "risk": "medium"}]
    rows.extend(
        [{"label": kind, "value": value, "source": "Instagram", "risk": "medium"} for kind, value in methods[:10]]
    )
    if len(methods) > 10:
        rows.append({"label": "More", "value": f"+{len(methods) - 10} more", "source": "Instagram", "risk": "low"})
    return 0, rows
