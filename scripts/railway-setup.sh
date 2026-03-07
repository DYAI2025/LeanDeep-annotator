#!/usr/bin/env bash
set -euo pipefail

# ══════════════════════════════════════════════════════════════
# Railway Multi-Service Setup
# Erstellt und verknuepft: LeanDeep + BAFE + Astro-Noctum
# ══════════════════════════════════════════════════════════════
#
# Voraussetzungen:
#   - railway CLI installiert (brew install railway)
#   - railway login (bereits eingeloggt)
#   - API Keys bereit (Gemini, Supabase, ElevenLabs)
#
# Usage:
#   ./scripts/railway-setup.sh              # Interaktiv (fragt nach Keys)
#   ./scripts/railway-setup.sh --dry-run    # Zeigt nur was passieren wuerde
#
# ══════════════════════════════════════════════════════════════

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

# ─── Farben ───
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

run() {
  if $DRY_RUN; then
    echo -e "  ${YELLOW}[DRY]${NC} $*"
  else
    "$@"
  fi
}

# ─── Preflight ───
command -v railway >/dev/null 2>&1 || err "Railway CLI nicht gefunden. Installiere: brew install railway"
railway whoami >/dev/null 2>&1 || err "Nicht eingeloggt. Erst: railway login"

echo ""
echo "══════════════════════════════════════════════════════"
echo "  Railway Multi-Service Setup"
echo "  LeanDeep + BAFE + Astro-Noctum"
echo "══════════════════════════════════════════════════════"
echo ""

# ─── Projekt-Pfade ───
LEANDEEP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BAFE_DIR="${BAFE_DIR:-$HOME/Projects/SaaS/BAFE - BaziEngine_v3/BAFE}"
ASTRO_DIR="${ASTRO_DIR:-$HOME/Projects/WEB/Astro-Noctum/Astro-Noctum}"

# Pruefen ob Verzeichnisse existieren
[[ -d "$LEANDEEP_DIR" ]] || err "LeanDeep nicht gefunden: $LEANDEEP_DIR"
[[ -d "$BAFE_DIR" ]] || warn "BAFE nicht gefunden: $BAFE_DIR (setze BAFE_DIR env var)"
[[ -d "$ASTRO_DIR" ]] || warn "Astro-Noctum nicht gefunden: $ASTRO_DIR (setze ASTRO_DIR env var)"

# ─── Secrets einsammeln ───
echo "Benoetigte API Keys (leer lassen = ueberspringen):"
echo ""

read -rp "  Google/Gemini API Key: " GEMINI_KEY
read -rp "  Supabase URL (https://xxx.supabase.co): " SUPABASE_URL
read -rp "  Supabase Anon Key: " SUPABASE_ANON_KEY
read -rp "  Supabase Service Role Key: " SUPABASE_SERVICE_KEY
read -rp "  ElevenLabs Tool Secret: " ELEVENLABS_SECRET
read -rp "  ElevenLabs Agent ID: " ELEVENLABS_AGENT_ID

echo ""

# ─── Generiere shared LeanDeep API Key ───
LEANDEEP_API_KEY=$(openssl rand -hex 24)
info "Generierter LeanDeep API Key: ${LEANDEEP_API_KEY:0:12}..."

# ══════════════════════════════════════════════════════════════
# 1. LeanDeep Service
# ══════════════════════════════════════════════════════════════

echo ""
info "━━━ [1/3] LeanDeep API ━━━"

if [[ -d "$LEANDEEP_DIR" ]]; then
  cd "$LEANDEEP_DIR"

  # API Key in api_keys.json schreiben (falls nicht dry-run)
  if ! $DRY_RUN; then
    echo "[\"$LEANDEEP_API_KEY\"]" > api/api_keys.json
    ok "api/api_keys.json geschrieben"
  fi

  info "Linke Railway Service..."
  run railway link 2>/dev/null || info "Bitte Railway Service manuell waehlen"

  info "Setze Environment Variables..."
  run railway variables set LEANDEEP_REQUIRE_AUTH=true
  run railway variables set LEANDEEP_RATE_LIMIT_PER_MINUTE=120

  if [[ -n "$GEMINI_KEY" ]]; then
    run railway variables set "LEANDEEP_GOOGLE_API_KEY=$GEMINI_KEY"
  fi

  # CORS wird spaeter gesetzt wenn wir die Astro-Noctum URL kennen
  ok "LeanDeep Variablen gesetzt"
fi

# ══════════════════════════════════════════════════════════════
# 2. BAFE Engine Service
# ══════════════════════════════════════════════════════════════

echo ""
info "━━━ [2/3] BAFE Engine ━━━"

if [[ -d "$BAFE_DIR" ]]; then
  cd "$BAFE_DIR"

  info "Linke Railway Service..."
  run railway link 2>/dev/null || info "Bitte Railway Service manuell waehlen"

  info "Setze Environment Variables..."
  run railway variables set SE_EPHE_PATH=/app/ephe
  run railway variables set EXPOSE_BUILD_METADATA=true

  if [[ -n "$ELEVENLABS_SECRET" ]]; then
    run railway variables set "ELEVENLABS_TOOL_SECRET=$ELEVENLABS_SECRET"
  fi

  ok "BAFE Variablen gesetzt"
else
  warn "BAFE Verzeichnis nicht gefunden, ueberspringe"
fi

# ══════════════════════════════════════════════════════════════
# 3. Astro-Noctum Service
# ══════════════════════════════════════════════════════════════

echo ""
info "━━━ [3/3] Astro-Noctum ━━━"

if [[ -d "$ASTRO_DIR" ]]; then
  cd "$ASTRO_DIR"

  info "Linke Railway Service..."
  run railway link 2>/dev/null || info "Bitte Railway Service manuell waehlen"

  info "Setze Environment Variables..."

  # Browser-seitig (VITE_)
  if [[ -n "$GEMINI_KEY" ]]; then
    run railway variables set "VITE_GEMINI_API_KEY=$GEMINI_KEY"
    run railway variables set "GEMINI_API_KEY=$GEMINI_KEY"
  fi

  if [[ -n "$SUPABASE_URL" ]]; then
    run railway variables set "VITE_SUPABASE_URL=$SUPABASE_URL"
  fi

  if [[ -n "$SUPABASE_ANON_KEY" ]]; then
    run railway variables set "VITE_SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY"
  fi

  if [[ -n "$ELEVENLABS_AGENT_ID" ]]; then
    run railway variables set "VITE_ELEVENLABS_AGENT_ID=$ELEVENLABS_AGENT_ID"
  fi

  # Server-only
  if [[ -n "$SUPABASE_SERVICE_KEY" ]]; then
    run railway variables set "SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_KEY"
  fi

  if [[ -n "$ELEVENLABS_SECRET" ]]; then
    run railway variables set "ELEVENLABS_TOOL_SECRET=$ELEVENLABS_SECRET"
  fi

  # LeanDeep Anbindung
  run railway variables set "VITE_LEANDEEP_API_KEY=$LEANDEEP_API_KEY"

  ok "Astro-Noctum Variablen gesetzt"
else
  warn "Astro-Noctum Verzeichnis nicht gefunden, ueberspringe"
fi

# ══════════════════════════════════════════════════════════════
# 4. Service-URLs verknuepfen (nach Deploy)
# ══════════════════════════════════════════════════════════════

echo ""
echo "══════════════════════════════════════════════════════"
echo "  Setup abgeschlossen!"
echo "══════════════════════════════════════════════════════"
echo ""
info "Naechste Schritte:"
echo ""
echo "  1. Deploye alle drei Services:"
echo "     cd \"$LEANDEEP_DIR\" && railway up"
echo "     cd \"$BAFE_DIR\" && railway up"
echo "     cd \"$ASTRO_DIR\" && railway up"
echo ""
echo "  2. Hole die generierten URLs und setze die Cross-Referenzen:"
echo ""
echo "     # In LeanDeep: CORS fuer Astro-Noctum erlauben"
echo "     cd \"$LEANDEEP_DIR\""
echo "     railway variables set LEANDEEP_CORS_ORIGINS=https://<astro>.up.railway.app"
echo ""
echo "     # In Astro-Noctum: BAFE + LeanDeep URLs setzen"
echo "     cd \"$ASTRO_DIR\""
echo "     railway variables set VITE_BAFE_BASE_URL=https://<bafe>.up.railway.app"
echo "     railway variables set BAFE_INTERNAL_URL=http://<bafe>.railway.internal:8080"
echo "     railway variables set VITE_LEANDEEP_URL=https://<leandeep>.up.railway.app"
echo ""
echo "  3. Redeploy nach URL-Updates:"
echo "     railway up (in jedem Verzeichnis)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  LeanDeep API Key (sicher aufbewahren!):"
echo "  $LEANDEEP_API_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
