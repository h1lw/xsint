# **xsint - Multi-source OSINT Aggregator**

`xsint` runs many OSINT lookups in parallel against a single target and prints a unified report.

## **Summary**

*One target, many sources, one report.*

Hand `xsint` an email, username, phone number, IP, address, hash, or other identifier and it dispatches every applicable module concurrently, then collapses the results into a single grouped report.

+ Async engine with parallel module execution
+ Auto-detects target type, with optional prefixes (`user:`, `email:`, `ip:`, ...) to disambiguate
+ Self-describing modules — each declares its supported types, returns, and credential requirements via an `INFO` dict
+ HTTP / SOCKS4 / SOCKS5 proxy support
+ Credential management for API-keyed and login-based modules
+ Pure stdlib output, no terminal-paint dependencies

## 🛠️ Installation


```bash
curl -fsSL https://raw.githubusercontent.com/memorypudding/xsint/main/install.sh | bash
```



## Documentation

| Topic                             | Location                                    |
| --------------------------------- | ------------------------------------------- |
| CLI usage, target prefixes, output | [docs/usage.md](docs/usage.md)             |
| Modules reference                 | [docs/modules.md](docs/modules.md)          |
| Authentication                    | [docs/auth.md](docs/auth.md)                |
| Proxy configuration               | [docs/proxy.md](docs/proxy.md)              |
| Writing a module                  | [docs/development.md](docs/development.md)  |

## License

[GNU General Public License v3.0](LICENSE)

Built for educational and authorized security research only.
