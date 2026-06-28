#!/data/data/com.termux/files/usr/bin/bash
# GARCAR CLI — Termux Mobile Command Center
# Install: cp garcar.sh $PREFIX/bin/garcar && chmod +x $PREFIX/bin/garcar
# First run: garcar setup

CREDS="$HOME/.garcar/credentials"
[ -f "$CREDS" ] && source "$CREDS"
API="${GARCAR_API_URL:-https://garcar-enterprise-production.railway.app}"

R='\033[0;31m' G='\033[0;32m' Y='\033[1;33m' C='\033[0;36m' N='\033[0m'
hdr() { echo -e "${C}⚡ GARCAR${N} — $1\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; }
ok()  { echo -e "${G}✅ $1${N}"; }
err() { echo -e "${R}❌ $1${N}"; }
auth() { echo "Authorization: Bearer ${GARCAR_API_KEY}"; }
supabase_get() { curl -sf -H "apikey: ${SUPABASE_ANON_KEY}" -H "$(auth)" "${SUPABASE_URL}/rest/v1/$1" | python3 -m json.tool 2>/dev/null || err "Supabase unreachable"; }

cmd_status() {
  hdr "System Status"
  curl -sf -H "$(auth)" "$API/health" | python3 -m json.tool 2>/dev/null || err "API unreachable"
}

cmd_deploy() {
  local SVC="${1:-all}"
  hdr "Deploy: $SVC"
  deploy_repo() {
    curl -sf -X POST -H "Authorization: token ${GITHUB_TOKEN}" \
      -H "Accept: application/vnd.github.v3+json" \
      "https://api.github.com/repos/Garrettc123/$1/actions/workflows/deploy.yml/dispatches" \
      -d '{"ref":"main"}' && ok "$1" || err "Failed: $1"
  }
  if [ "$SVC" = "all" ]; then
    for r in atlas-agents garcar-enterprise-production tree-of-life-system; do deploy_repo $r; done
  else
    deploy_repo "$SVC"
  fi
}

cmd_logs() {
  hdr "Logs: ${1:-atlas-agents}"
  railway logs --service "${1:-atlas-agents}" --tail 50 2>/dev/null || err "railway CLI not available"
}

cmd_revenue() {
  hdr "Revenue Ledger"
  supabase_get "revenue_ledger?select=amount_cents,currency,status,created_at&order=created_at.desc&limit=10"
}

cmd_leads() {
  hdr "Lead Pipeline"
  supabase_get "leads?select=email,company,status,ai_score&order=created_at.desc&limit=20"
}

cmd_treasury() {
  hdr "Treasury Positions"
  supabase_get "treasury_positions?select=*"
}

cmd_tasks() {
  hdr "ATLAS Tasks (last 10)"
  supabase_get "atlas_tasks?select=task_type,status,created_at,duration_ms&order=created_at.desc&limit=10"
}

cmd_watch() {
  local INT="${1:-30}"
  hdr "Live Monitor — refreshing every ${INT}s (Ctrl+C to stop)"
  while true; do
    clear; cmd_status; echo ""; cmd_treasury
    sleep "$INT"
  done
}

cmd_setup() {
  hdr "CLI Setup"
  mkdir -p "$HOME/.garcar"
  read -p "GARCAR_API_URL: " a; read -p "GARCAR_API_KEY: " k
  read -p "SUPABASE_URL: " su; read -p "SUPABASE_ANON_KEY: " sk
  read -p "GITHUB_TOKEN: " gt; read -p "NTFY_TOPIC [garcar-alerts]: " nt
  cat > "$CREDS" <<EOF
export GARCAR_API_URL="$a"
export GARCAR_API_KEY="$k"
export SUPABASE_URL="$su"
export SUPABASE_ANON_KEY="$sk"
export GITHUB_TOKEN="$gt"
export NTFY_TOPIC="${nt:-garcar-alerts}"
EOF
  chmod 600 "$CREDS"; ok "Saved to $CREDS"
  echo -e "${Y}Add to ~/.bashrc: source ~/.garcar/credentials${N}"
}

cmd_help() { cat <<EOF
${C}⚡ GARCAR CLI${N}
  ${G}garcar status${N}           System health
  ${G}garcar deploy [svc]${N}     Trigger deploy (default: all)
  ${G}garcar logs [svc]${N}       Railway log tail
  ${G}garcar revenue${N}          Revenue ledger
  ${G}garcar leads${N}            Lead pipeline
  ${G}garcar treasury${N}         Treasury positions
  ${G}garcar tasks${N}            ATLAS task log
  ${G}garcar watch [sec]${N}      Live monitor (default 30s)
  ${G}garcar setup${N}            Store credentials
EOF
}

case "${1:-help}" in
  status)   cmd_status ;;
  deploy)   cmd_deploy "${2}" ;;
  logs)     cmd_logs "${2}" ;;
  revenue)  cmd_revenue ;;
  leads)    cmd_leads ;;
  treasury) cmd_treasury ;;
  tasks)    cmd_tasks ;;
  watch)    cmd_watch "${2}" ;;
  setup)    cmd_setup ;;
  help|*)   cmd_help ;;
esac
