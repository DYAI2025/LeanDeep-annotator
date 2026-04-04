# insight.leandeep.de — Static Marketing Site

High-impact, interactive landing page for LeanDeep LD5 with **Deutsch ↔ Englisch** language toggle.

## 📁 Structure

```
insight-leandeep/
├── index.html          # Main page (all content + i18n keys)
├── i18n.js            # Translation engine + localStorage persistence
├── chart-config.js    # Chart.js data configs for all use cases
├── main.js            # Tab switching + chart rendering
├── deploy.py          # Hostinger API deployment script
├── .env.local         # (Ignored) Hostinger credentials
└── README.md          # This file
```

## 🚀 Quick Start

### 1. Local Development

```bash
# Navigate to directory
cd insight-leandeep

# Serve locally (Python)
python3 -m http.server 8000

# Open browser
open http://localhost:8000
```

### 2. Language Toggle

- Click **EN/DE** button in top-right
- Language preference is saved in browser localStorage
- Both languages are baked into the HTML (no network calls)

## 📤 Deployment to Hostinger

### Prerequisites

1. **Hostinger Account** with `leandeep.de` domain
2. **Hostinger API Credentials:**
   - `HOSTINGER_API_KEY` — from Hostinger developer dashboard
   - `HOSTINGER_API_EMAIL` — your Hostinger account email
   - `HOSTINGER_ACCOUNT_ID` — your account ID (in URL or API docs)

### Setup

```bash
# Copy template and fill in credentials
cp .env.local.template .env.local

# Edit .env.local with your real credentials
# DO NOT commit .env.local (it's in .gitignore)
```

### Deploy via Python Script

```bash
# Requires: requests, python-dotenv
pip install requests python-dotenv

# Run deploy
python3 deploy.py

# Or with explicit args:
python3 deploy.py \
  --api-key YOUR_KEY \
  --api-email YOUR_EMAIL \
  --account-id YOUR_ACCOUNT_ID \
  --subdomain insight \
  --domain leandeep.de
```

### Deploy via Hostinger Dashboard (Manual)

1. Log in to **Hostinger Control Panel**
2. Navigate to **File Manager**
3. Create folder: `/public_html/insight.leandeep.de/`
4. Upload all files:
   - `index.html`
   - `i18n.js`
   - `chart-config.js`
   - `main.js`
5. Verify at: `https://insight.leandeep.de`

## 🎨 Features

### Language System (i18n)
- **No build step required** — translations are embedded
- **Fast toggle** — instant UI updates with localStorage persistence
- **Client-side only** — no backend needed
- **Extensible** — add languages by editing `translations` object in `i18n.js`

### Interactive Use Cases
- **4 tabs:** Psychotherapy, HR & Leadership, Research, B2B Sales
- **Dynamic charts** using Chart.js (line, radar, bar)
- **Smooth animations** — fade-in on tab switch
- **Responsive design** — Tailwind CSS (mobile-friendly)

### Branding
- **Color palette:** Warm neutrals (stone) + teal primary + amber accents
- **Typography:** Sans-serif (system fonts, no external downloads)
- **Performance:** Zero external assets except Tailwind CDN + Chart.js CDN

## 📊 Content Structure

### Sections
1. **Header/Vision** — High-impact value prop + hero image
2. **Architecture** — Four-Level Model (ATO → SEM → CLU → MEMA)
3. **Use Cases** — Interactive tabbed demos with visualizations
4. **Benefits** — 4-column value prop grid
5. **Footer/CTA** — Call to action + contact

### Styling
- Responsive grid layouts (Tailwind)
- Hover effects + transitions
- Semantic HTML (accessible)
- No SVG dependencies (all Unicode + CSS)

## 🔄 Future Roadmap

- [ ] Migrate to i18n JSON files for maintainability
- [ ] Add analytics (Plausible or Mixpanel)
- [ ] A/B test variants (CTAs, copy, colors)
- [ ] Newsletter signup integration
- [ ] Blog/Case studies section
- [ ] Multi-language support (French, Spanish, etc.)

## 📝 Adding New Languages

To add a new language (e.g., French):

1. **Open `i18n.js`**
2. **Add translation object:**
   ```javascript
   fr: {
     page_title: "LeanDeep LD5 - Intelligence de Communication",
     nav_vision: "Vision",
     // ... (translate all keys)
   }
   ```
3. **Update language toggle logic** (if desired)
4. **Test**: Toggle should work immediately

## 🐛 Troubleshooting

### Charts not loading?
- Ensure `chart-config.js` is loaded before `main.js`
- Check browser console for errors
- Verify Chart.js CDN is accessible

### Language toggle not working?
- Check browser console for JS errors
- Clear localStorage: `localStorage.clear()`
- Ensure `i18n.js` is loaded before page elements

### Subdomain not resolving?
- Wait 24-48 hours for DNS propagation
- Verify subdomain created in Hostinger dashboard
- Check DNS A record points to Hostinger IP

## 📞 Support

For Hostinger API issues:
- [Hostinger Developer Docs](https://developer.hostinger.com)
- [Hostinger Help Center](https://support.hostinger.com)

For deployment questions:
- Check `.env.local` credentials are correct
- Run `python3 deploy.py` with `--help` flag
- Check Hostinger File Manager manually

---

**Last Updated:** 2026-04-03  
**Maintainer:** LeanDeep Engineering
