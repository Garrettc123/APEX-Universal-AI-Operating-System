import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const TENANT_ID = Deno.env.get("APEX_TENANT_ID") ?? "f5d93048-7984-432e-afdf-9f6a4cfe3012";

const db = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false },
});

const headers = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-content-type-options": "nosniff",
  "referrer-policy": "no-referrer",
};

const rank: Record<string, number> = {
  declared: 1,
  inspected: 2,
  tested: 3,
  deployed: 4,
  verified: 5,
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers });
}

function bearer(req: Request) {
  return (req.headers.get("authorization") ?? "").replace(/^Bearer\s+/i, "").trim();
}

async function requireUser(req: Request) {
  const token = bearer(req);
  if (!token) return null;
  const { data, error } = await db.auth.getUser(token);
  if (error || !data.user) return null;
  return data.user;
}

async function requireTenantMember(userId: string) {
  const { data, error } = await db
    .from("crf_tenant_members")
    .select("role,status")
    .eq("tenant_id", TENANT_ID)
    .eq("user_id", userId)
    .eq("status", "active")
    .maybeSingle();
  if (error) throw error;
  return data;
}

async function controlState() {
  const { data, error } = await db
    .from("edge_control_state")
    .select("enabled,max_risk,maintenance_message,updated_at")
    .eq("id", true)
    .maybeSingle();
  if (error) throw error;
  return data ?? {
    enabled: false,
    max_risk: "L0",
    maintenance_message: "Control state unavailable",
    updated_at: null,
  };
}

async function audit(action: string, metadata: Record<string, unknown>) {
  await db.from("decision_log").insert({
    tenant_id: TENANT_ID,
    node: "apex_universal_operations",
    action_type: action,
    proposed_action: "APEX Universal Operations control-plane action.",
    confidence: 1,
    metadata: {
      ...metadata,
      created_at: new Date().toISOString(),
    },
  });
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers });

  try {
    const url = new URL(req.url);
    const path = url.pathname.replace(/\/+$/, "");

    // Public liveness probe. All operational and mutation routes remain authenticated below.
    if (req.method === "GET" && path.endsWith("/health")) {
      return json({
        ok: true,
        status: "healthy",
        service: "apex-universal-operations",
        deployment: "supabase-edge",
        governance: "crf + edge-control",
      });
    }

    const user = await requireUser(req);
    if (!user) return json({ error: "authenticated_user_required" }, 401);

    const member = await requireTenantMember(user.id);
    if (!member) return json({ error: "tenant_membership_required" }, 403);

    if (req.method === "GET" && (path.endsWith("/api/status") || path.endsWith("/status"))) {
      const [systems, workflows, opportunities, runs, failures, control] = await Promise.all([
        db.from("crf_systems").select("id,name,repository,environment,autonomy_level,status,updated_at").eq("tenant_id", TENANT_ID),
        db.from("revenue_workflows").select("id,name,status,updated_at").eq("tenant_id", TENANT_ID),
        db.from("revenue_opportunities").select("id,status,opportunity_type,confidence,detected_at").eq("tenant_id", TENANT_ID).order("detected_at", { ascending: false }).limit(25),
        db.from("crf_system_runs").select("id,status,run_type,parent_system_id,child_system_id,created_at").eq("tenant_id", TENANT_ID).order("created_at", { ascending: false }).limit(25),
        db.from("crf_failures").select("id,status,severity,last_seen_at").eq("tenant_id", TENANT_ID).order("last_seen_at", { ascending: false }).limit(25),
        Promise.resolve(await controlState()),
      ]);

      const errors = [systems, workflows, opportunities, runs, failures]
        .filter((x) => x.error)
        .map((x) => x.error!.message);

      if (errors.length) return json({ error: "status_read_failed", details: errors }, 500);

      return json({
        ok: true,
        generated_at: new Date().toISOString(),
        control,
        counts: {
          systems: systems.data?.length ?? 0,
          revenue_workflows: workflows.data?.length ?? 0,
          open_opportunities: opportunities.data?.length ?? 0,
          recent_runs: runs.data?.length ?? 0,
          recent_failures: failures.data?.length ?? 0,
        },
        data: {
          systems: systems.data ?? [],
          workflows: workflows.data ?? [],
          opportunities: opportunities.data ?? [],
          runs: runs.data ?? [],
          failures: failures.data ?? [],
        },
      });
    }

    if (req.method === "GET" && (path.endsWith("/api/operations") || path.endsWith("/operations"))) {
      const [systems, capabilities, contracts] = await Promise.all([
        db.from("crf_systems")
          .select("id,name,repository,environment,autonomy_level,status,updated_at")
          .eq("tenant_id", TENANT_ID)
          .order("name"),
        db.from("crf_system_capabilities")
          .select("id,system_id,capability,version,execution_adapter,evidence_level,enabled,description")
          .eq("tenant_id", TENANT_ID)
          .eq("enabled", true),
        db.from("crf_system_contracts")
          .select("id,system_id,version,trust_boundary,recursion_policy,timeout_ms,evidence_policy")
          .eq("tenant_id", TENANT_ID),
      ]);

      const errors = [systems, capabilities, contracts]
        .filter((x) => x.error)
        .map((x) => x.error!.message);

      if (errors.length) return json({ error: "operations_read_failed", details: errors }, 500);

      return json({
        ok: true,
        generated_at: new Date().toISOString(),
        systems: systems.data ?? [],
        capabilities: capabilities.data ?? [],
        contracts: contracts.data ?? [],
      });
    }

    if (req.method === "POST" && (path.endsWith("/api/operations/dispatch") || path.endsWith("/operations/dispatch"))) {
      const body = await req.json().catch(() => ({}));
      const capability = String(body.capability ?? "").trim();
      const parentSystemId = String(body.parent_system_id ?? "").trim();
      const input = body.input ?? {};
      const idempotencyKey = String(body.idempotency_key ?? crypto.randomUUID());

      if (!capability || !parentSystemId) {
        return json({ error: "capability_and_parent_system_id_required" }, 400);
      }

      const control = await controlState();
      if (!control.enabled) {
        return json({
          error: "execution_disabled",
          control,
          message: "No operation was queued because the control plane is disabled.",
        }, 423);
      }

      const { data: parent, error: parentError } = await db
        .from("crf_systems")
        .select("id,name,status,tenant_id")
        .eq("id", parentSystemId)
        .eq("tenant_id", TENANT_ID)
        .maybeSingle();

      if (parentError) return json({ error: parentError.message }, 500);
      if (!parent || parent.status !== "active") {
        return json({ error: "parent_system_unavailable" }, 409);
      }

      const { data: candidates, error: capError } = await db
        .from("crf_system_capabilities")
        .select("id,system_id,capability,version,execution_adapter,evidence_level,evidence,description")
        .eq("tenant_id", TENANT_ID)
        .eq("capability", capability)
        .eq("enabled", true);

      if (capError) return json({ error: capError.message }, 500);

      const eligible = (candidates ?? [])
        .filter((c: any) => (rank[c.evidence_level] ?? 0) >= rank.inspected)
        .sort((a: any, b: any) => (rank[b.evidence_level] ?? 0) - (rank[a.evidence_level] ?? 0));

      const selected = eligible[0];
      if (!selected) return json({ error: "no_eligible_capability_provider", capability }, 404);

      const { data: existing, error: existingError } = await db
        .from("crf_system_runs")
        .select("id,status,child_system_id,output,error,created_at")
        .eq("tenant_id", TENANT_ID)
        .eq("idempotency_key", idempotencyKey)
        .maybeSingle();

      if (existingError) return json({ error: existingError.message }, 500);
      if (existing) return json({ ok: true, replayed: true, run: existing });

      const { data: run, error: runError } = await db
        .from("crf_system_runs")
        .insert({
          tenant_id: TENANT_ID,
          parent_system_id: parentSystemId,
          child_system_id: selected.system_id,
          run_type: "delegate",
          status: "queued",
          idempotency_key: idempotencyKey,
          input: {
            capability,
            input,
            provider_capability_id: selected.id,
            execution_adapter: selected.execution_adapter,
            requested_by: user.id,
          },
        })
        .select("id,status,parent_system_id,child_system_id,run_type,idempotency_key,created_at")
        .single();

      if (runError) return json({ error: runError.message }, 500);

      await audit("operation_queued", {
        run_id: run.id,
        capability,
        parent_system_id: parentSystemId,
        child_system_id: selected.system_id,
        idempotency_key: idempotencyKey,
      });

      return json({
        ok: true,
        queued: true,
        run,
        provider: selected,
        governance: {
          control_plane: "edge_control_state",
          approval_gate: "preserved",
          evidence_required: true,
        },
      }, 202);
    }

    return json({ error: "not_found" }, 404);
  } catch (error) {
    console.error("apex_universal_operations_error", error);
    return json({ error: "internal_error" }, 500);
  }
});
