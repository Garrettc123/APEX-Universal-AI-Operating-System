package com.apex.os.data.model

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/** A connected (or connectable) service in the integrations hub. */
@JsonClass(generateAdapter = true)
data class Integration(
    val id: String,
    val name: String,
    val category: String,
    val connected: Boolean,
    val status: String,
    val automations: Int = 0,
    @Json(name = "last_sync") val lastSync: String? = null,
)

/** Integration plus its recent trigger runs (GET /api/integrations/{id}). */
@JsonClass(generateAdapter = true)
data class IntegrationDetail(
    val id: String,
    val name: String,
    val category: String,
    val connected: Boolean,
    val status: String,
    val automations: Int = 0,
    @Json(name = "last_sync") val lastSync: String? = null,
    @Json(name = "recent_runs") val recentRuns: List<IntegrationRun> = emptyList(),
)

/** A single sync/automation run record. */
@JsonClass(generateAdapter = true)
data class IntegrationRun(
    @Json(name = "run_id") val runId: String,
    @Json(name = "integration_id") val integrationId: String,
    val status: String,
    val detail: String,
    @Json(name = "started_at") val startedAt: String,
)
