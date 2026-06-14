package com.apex.os.data

import com.apex.os.data.model.Integration
import com.apex.os.data.model.IntegrationDetail
import com.apex.os.data.model.IntegrationRun
import com.apex.os.data.model.Overview
import com.apex.os.data.model.Revenue
import com.apex.os.data.model.SystemRow
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Single source of truth for talking to the APEX backend.
 *
 * The Retrofit client is rebuilt lazily whenever the base URL changes (the
 * user can repoint the app in Settings), so callers always hit the current
 * backend without restarting the app.
 */
class ApexRepository(private val settings: SettingsStore) {

    private val moshi: Moshi =
        Moshi.Builder().add(KotlinJsonAdapterFactory()).build()

    private val okHttp: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .addInterceptor(
            HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BASIC
            },
        )
        .build()

    @Volatile
    private var cachedBaseUrl: String? = null

    @Volatile
    private var api: ApexApi? = null

    private fun api(): ApexApi {
        val current = settings.baseUrl
        val existing = api
        if (existing != null && current == cachedBaseUrl) return existing

        val retrofit = Retrofit.Builder()
            .baseUrl(current)
            .client(okHttp)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
        return retrofit.create(ApexApi::class.java).also {
            api = it
            cachedBaseUrl = current
        }
    }

    suspend fun overview(): Overview = api().overview()
    suspend fun systems(): List<SystemRow> = api().systems()
    suspend fun revenue(): Revenue = api().revenue()
    suspend fun evolve(): Overview = api().evolve()
    suspend fun optimize(): Overview = api().optimize()
    suspend fun runRevenueCycle(): Revenue = api().runRevenueCycle()

    suspend fun integrations(): List<Integration> = api().integrations()
    suspend fun integration(id: String): IntegrationDetail = api().integration(id)
    suspend fun triggerIntegration(id: String): IntegrationRun =
        api().triggerIntegration(id)
}
