# Security Policy 🔒

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

---

## 🛡️ Reporting a Vulnerability

The BoardMorph team takes the security of our software and users seriously.

If you discover a security vulnerability or sensitive information leakage within BoardMorph, **please do NOT create a public issue**. Instead, follow these steps:

1. **Email Disclosure**: Send a detailed description of the vulnerability to the project maintainers or open a [GitHub Private Security Advisory](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-communicating-vulnerabilities/privately-reporting-a-security-vulnerability).
2. **Include Reproduction Details**:
   - Step-by-step reproduction instructions.
   - Affected endpoints or files.
   - Potential impact and suggested mitigations (if available).
3. **Acknowledgment**: We will acknowledge receipt of your report within 48 hours and work with you on a resolution.

---

## ⚠️ Protecting API Keys & Tokens

- **Never commit `.env`**: Always ensure `.env` is listed in `.gitignore` and never committed to version control.
- **Miro OAuth Tokens**: Keep your Miro App client secret and access tokens private. If compromised, revoke them immediately in the [Miro Developer Portal](https://developers.miro.com/).
- **LLM API Keys**: If your OpenRouter or OpenAI keys are accidentally exposed, regenerate them immediately in your provider's dashboard.
