package com.apex.os.data.model

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/** KPI snapshot returned by GET /api/overview and the /cycle endpoints. */
@JsonClass(generateAdapter = true)
data class Overview(
    val state: String,
    @Json(name = "intelligence_level") val intelligenceLevel: Double,
    @Json(name = "evolution_cycles") val evolutionCycles: Int,
    @Json(name = "systems_total") val systemsTotal: Int,
    @Json(name = "systems_healthy") val systemsHealthy: Int,
    @Json(name = "average_health") val averageHealth: Double,
    @Json(name = "average_performance") val averagePerformance: Double,
    @Json(name = "total_revenue") val totalRevenue: Double,
    @Json(name = "annual_projection") val annualProjection: Double,
    @Json(name = "uptime_seconds") val uptimeSeconds: Long,
    @Json(name = "generated_at") val generatedAt: String,
)

/** A single managed system, returned in GET /api/systems (worst health first). */
@JsonClass(generateAdapter = true)
data class SystemRow(
    val name: String,
    val status: String,
    @Json(name = "health_score") val healthScore: Double,
    @Json(name = "last_update") val lastUpdate: String,
    val metrics: Map<String, Double> = emptyMap(),
    val dependencies: List<String> = emptyList(),
)

/** Revenue breakdown returned by GET /api/revenue and POST /api/cycle/revenue. */
@JsonClass(generateAdapter = true)
data class Revenue(
    @Json(name = "total_revenue") val totalRevenue: Double,
    @Json(name = "annual_projection") val annualProjection: Double,
    val strategies: List<Strategy> = emptyList(),
)

@JsonClass(generateAdapter = true)
data class Strategy(
    val name: String,
    val rate: Double,
    val clients: Int,
    val revenue: Double,
)
