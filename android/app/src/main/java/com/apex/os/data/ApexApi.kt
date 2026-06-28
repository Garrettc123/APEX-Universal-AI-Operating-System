package com.apex.os.data

import com.apex.os.data.model.Integration
import com.apex.os.data.model.IntegrationDetail
import com.apex.os.data.model.IntegrationRun
import com.apex.os.data.model.Overview
import com.apex.os.data.model.Revenue
import com.apex.os.data.model.SystemRow
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

/** Retrofit description of the APEX dashboard API (FastAPI, /api/*). */
interface ApexApi {

    @GET("api/overview")
    suspend fun overview(): Overview

    @GET("api/systems")
    suspend fun systems(): List<SystemRow>

    @GET("api/revenue")
    suspend fun revenue(): Revenue

    @POST("api/cycle/evolve")
    suspend fun evolve(): Overview

    @POST("api/cycle/optimize")
    suspend fun optimize(): Overview

    @POST("api/cycle/revenue")
    suspend fun runRevenueCycle(): Revenue

    @GET("api/integrations")
    suspend fun integrations(): List<Integration>

    @GET("api/integrations/{id}")
    suspend fun integration(@Path("id") id: String): IntegrationDetail

    @POST("api/integrations/{id}/trigger")
    suspend fun triggerIntegration(@Path("id") id: String): IntegrationRun
}
